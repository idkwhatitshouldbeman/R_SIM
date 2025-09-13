"""
Real-time CFD data extraction from OpenFOAM simulations
Extracts attitude, velocity, forces, and other data for control system
"""

import numpy as np
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

class OpenFOAMDataExtractor:
    """Extracts real-time data from OpenFOAM simulation files"""
    
    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)
        self.last_extraction_time = 0
        self.data_cache = {}
        
    def extract_forces_and_moments(self) -> Dict[str, List[float]]:
        """Extract forces and moments from OpenFOAM forces function object"""
        try:
            forces_file = self.case_dir / "postProcessing" / "finForces" / "0" / "forces.dat"
            
            if not forces_file.exists():
                return {"forces": [0, 0, 0], "moments": [0, 0, 0]}
            
            # Read the forces file
            with open(forces_file, 'r') as f:
                lines = f.readlines()
            
            # Parse the last line (most recent data)
            if len(lines) < 2:
                return {"forces": [0, 0, 0], "moments": [0, 0, 0]}
            
            # Skip header line and get last data line
            last_line = lines[-1].strip()
            data = last_line.split()
            
            if len(data) >= 6:
                # Extract forces and moments
                forces = [float(data[1]), float(data[2]), float(data[3])]  # Fx, Fy, Fz
                moments = [float(data[4]), float(data[5]), float(data[6])]  # Mx, My, Mz
                
                return {"forces": forces, "moments": moments}
            else:
                return {"forces": [0, 0, 0], "moments": [0, 0, 0]}
                
        except Exception as e:
            print(f"❌ Error extracting forces: {e}")
            return {"forces": [0, 0, 0], "moments": [0, 0, 0]}
    
    def extract_pressure_field(self) -> Dict[str, float]:
        """Extract pressure field statistics"""
        try:
            pressure_file = self.case_dir / "postProcessing" / "pressureField" / "0" / "fieldMinMax.dat"
            
            if not pressure_file.exists():
                return {"min_pressure": 101325, "max_pressure": 101325, "avg_pressure": 101325}
            
            with open(pressure_file, 'r') as f:
                content = f.read()
            
            # Parse pressure statistics
            min_match = re.search(r'min\(p\) = ([0-9.-]+)', content)
            max_match = re.search(r'max\(p\) = ([0-9.-]+)', content)
            
            min_pressure = float(min_match.group(1)) if min_match else 101325
            max_pressure = float(max_match.group(1)) if max_match else 101325
            avg_pressure = (min_pressure + max_pressure) / 2
            
            return {
                "min_pressure": min_pressure,
                "max_pressure": max_pressure,
                "avg_pressure": avg_pressure
            }
            
        except Exception as e:
            print(f"❌ Error extracting pressure: {e}")
            return {"min_pressure": 101325, "max_pressure": 101325, "avg_pressure": 101325}
    
    def extract_velocity_field(self) -> Dict[str, List[float]]:
        """Extract velocity field statistics"""
        try:
            velocity_file = self.case_dir / "postProcessing" / "velocityField" / "0" / "fieldMinMax.dat"
            
            if not velocity_file.exists():
                return {"min_velocity": [0, 0, 0], "max_velocity": [0, 0, 0], "avg_velocity": [0, 0, 0]}
            
            with open(velocity_file, 'r') as f:
                content = f.read()
            
            # Parse velocity statistics
            min_vel = [0, 0, 0]
            max_vel = [0, 0, 0]
            
            for i, component in enumerate(['x', 'y', 'z']):
                min_match = re.search(rf'min\(U\.{component}\) = ([0-9.-]+)', content)
                max_match = re.search(rf'max\(U\.{component}\) = ([0-9.-]+)', content)
                
                if min_match:
                    min_vel[i] = float(min_match.group(1))
                if max_match:
                    max_vel[i] = float(max_match.group(1))
            
            avg_vel = [(min_vel[i] + max_vel[i]) / 2 for i in range(3)]
            
            return {
                "min_velocity": min_vel,
                "max_velocity": max_vel,
                "avg_velocity": avg_vel
            }
            
        except Exception as e:
            print(f"❌ Error extracting velocity: {e}")
            return {"min_velocity": [0, 0, 0], "max_velocity": [0, 0, 0], "avg_velocity": [0, 0, 0]}
    
    def calculate_attitude_from_moments(self, moments: List[float], dt: float) -> List[float]:
        """Calculate attitude (roll, pitch, yaw) from moments using simple integration"""
        try:
            # This is a simplified attitude calculation
            # In reality, you'd need proper quaternion integration or similar
            
            # Get previous attitude from cache
            prev_attitude = self.data_cache.get('attitude', [0, 0, 0])
            
            # Simple moment-to-angular-acceleration conversion
            # Assuming moment of inertia around each axis
            Ix, Iy, Iz = 0.1, 0.1, 0.05  # kg⋅m² (example values)
            
            # Angular accelerations
            alpha_x = moments[0] / Ix  # Roll acceleration
            alpha_y = moments[1] / Iy  # Pitch acceleration  
            alpha_z = moments[2] / Iz  # Yaw acceleration
            
            # Get previous angular velocities
            prev_omega = self.data_cache.get('angular_velocity', [0, 0, 0])
            
            # Update angular velocities
            omega_x = prev_omega[0] + alpha_x * dt
            omega_y = prev_omega[1] + alpha_y * dt
            omega_z = prev_omega[2] + alpha_z * dt
            
            # Update attitude (simple integration)
            roll = prev_attitude[0] + omega_x * dt
            pitch = prev_attitude[1] + omega_y * dt
            yaw = prev_attitude[2] + omega_z * dt
            
            # Update cache
            self.data_cache['attitude'] = [roll, pitch, yaw]
            self.data_cache['angular_velocity'] = [omega_x, omega_y, omega_z]
            
            return [roll, pitch, yaw]
            
        except Exception as e:
            print(f"❌ Error calculating attitude: {e}")
            return [0, 0, 0]
    
    def calculate_position_from_velocity(self, velocity: List[float], dt: float) -> List[float]:
        """Calculate position from velocity using integration"""
        try:
            # Get previous position from cache
            prev_position = self.data_cache.get('position', [0, 0, 0])
            
            # Simple velocity integration
            x = prev_position[0] + velocity[0] * dt
            y = prev_position[1] + velocity[1] * dt
            z = prev_position[2] + velocity[2] * dt
            
            # Update cache
            self.data_cache['position'] = [x, y, z]
            
            return [x, y, z]
            
        except Exception as e:
            print(f"❌ Error calculating position: {e}")
            return [0, 0, 0]
    
    def extract_all_cfd_data(self, dt: float) -> Dict:
        """Extract all CFD data for the control system"""
        try:
            current_time = time.time()
            
            # Only extract if enough time has passed (avoid too frequent reads)
            if current_time - self.last_extraction_time < 0.01:  # 100 Hz max
                return self.data_cache.get('last_cfd_data', {})
            
            # Extract forces and moments
            forces_moments = self.extract_forces_and_moments()
            forces = forces_moments['forces']
            moments = forces_moments['moments']
            
            # Extract pressure field
            pressure_data = self.extract_pressure_field()
            
            # Extract velocity field
            velocity_data = self.extract_velocity_field()
            velocity = velocity_data['avg_velocity']
            
            # Calculate attitude from moments
            attitude = self.calculate_attitude_from_moments(moments, dt)
            
            # Calculate position from velocity
            position = self.calculate_position_from_velocity(velocity, dt)
            
            # Get angular velocity from cache
            angular_velocity = self.data_cache.get('angular_velocity', [0, 0, 0])
            
            # Compile all data
            cfd_data = {
                'timestamp': current_time,
                'attitude': attitude,  # [roll, pitch, yaw] in degrees
                'velocity': velocity,  # [vx, vy, vz] in m/s
                'position': position,  # [x, y, z] in meters
                'angular_velocity': angular_velocity,  # [wx, wy, wz] in rad/s
                'forces': forces,  # [Fx, Fy, Fz] in N
                'moments': moments,  # [Mx, My, Mz] in N⋅m
                'pressure': pressure_data['avg_pressure'],  # Pa
                'temperature': 288,  # K (assumed constant for now)
                'dt': dt
            }
            
            # Update cache
            self.data_cache['last_cfd_data'] = cfd_data
            self.last_extraction_time = current_time
            
            return cfd_data
            
        except Exception as e:
            print(f"❌ Error extracting CFD data: {e}")
            return self.data_cache.get('last_cfd_data', {})

class CFDDataManager:
    """Manages CFD data extraction and processing"""
    
    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)
        self.extractor = OpenFOAMDataExtractor(case_dir)
        self.data_history = []
        self.max_history = 1000  # Keep last 1000 data points
        
    def get_latest_cfd_data(self, dt: float) -> Dict:
        """Get the latest CFD data"""
        cfd_data = self.extractor.extract_all_cfd_data(dt)
        
        # Add to history
        self.data_history.append(cfd_data.copy())
        if len(self.data_history) > self.max_history:
            self.data_history.pop(0)
        
        return cfd_data
    
    def get_data_history(self, n_points: int = 100) -> List[Dict]:
        """Get the last n_points of CFD data history"""
        return self.data_history[-n_points:] if self.data_history else []
    
    def get_attitude_history(self, n_points: int = 100) -> List[List[float]]:
        """Get attitude history for plotting"""
        history = self.get_data_history(n_points)
        return [data.get('attitude', [0, 0, 0]) for data in history]
    
    def get_velocity_history(self, n_points: int = 100) -> List[List[float]]:
        """Get velocity history for plotting"""
        history = self.get_data_history(n_points)
        return [data.get('velocity', [0, 0, 0]) for data in history]
    
    def get_forces_history(self, n_points: int = 100) -> List[List[float]]:
        """Get forces history for plotting"""
        history = self.get_data_history(n_points)
        return [data.get('forces', [0, 0, 0]) for data in history]

# Example usage
def create_cfd_data_extractor(case_dir: str) -> CFDDataManager:
    """Create a CFD data extractor for a given case directory"""
    return CFDDataManager(Path(case_dir))
