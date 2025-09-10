
import os
import subprocess
import tempfile
import json
import time
import threading
import uuid
import math
import numpy as np
import sqlite3
import shutil
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS

# Load OpenFOAM environment
try:
    openfoam_env_path = Path(__file__).parent.parent / "openfoam" / "openfoam_env.py"
    if openfoam_env_path.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("openfoam_env", openfoam_env_path)
        openfoam_env = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(openfoam_env)
        openfoam_env.load_openfoam_environment()
        print("✅ OpenFOAM environment loaded")
    else:
        print("⚠️  OpenFOAM environment not found, using simulation mode")
except Exception as e:
    print(f"⚠️  Could not load OpenFOAM environment: {e}")

# Import heavy CFD integration
try:
    from openfoam_integration import HeavyCFDManager
    heavy_cfd_available = True
    print("✅ Heavy CFD integration loaded")
except ImportError as e:
    print(f"⚠️  Heavy CFD integration not available: {e}")
    heavy_cfd_available = False

# Import Google Cloud CFD integration
try:
    from gcp_cfd_client import GCPCFDClient
    gcp_cfd_available = True
    print("✅ Google Cloud CFD integration loaded")
except ImportError as e:
    print(f"⚠️  Google Cloud CFD integration not available: {e}")
    gcp_cfd_available = False

# --- Data Models ---

@dataclass
class HardwareLimitations:
    servo_max_speed: float
    servo_max_torque: float
    servo_response_time: float
    sensor_noise_level: float
    sensor_update_rate: float
    max_fin_deflection: float
    battery_voltage: float
    processing_delay: float

@dataclass
class SensorData:
    timestamp: float
    altitude: float
    velocity_x: float
    velocity_y: float
    velocity_z: float
    acceleration_x: float
    acceleration_y: float
    acceleration_z: float
    angular_velocity_x: float
    angular_velocity_y: float
    angular_velocity_z: float
    pressure: float
    temperature: float
    gps_latitude: float
    gps_longitude: float

@dataclass
class ControlOutput:
    fin_deflection_1: float
    fin_deflection_2: float
    fin_deflection_3: float
    fin_deflection_4: float
    recovery_trigger: bool
    data_logging: Dict

@dataclass
class MotorSpecification:
    designation: str
    manufacturer: str
    diameter: float
    length: float
    total_mass: float
    propellant_mass: float
    average_thrust: float
    max_thrust: float
    total_impulse: float
    burn_time: float
    impulse_class: str
    delay_time: float
    thrust_curve: List[Tuple[float, float]]
    approved_for_tarc: bool

@dataclass
class AtmosphericConditions:
    altitude: float
    temperature: float
    pressure: float
    density: float
    humidity: float
    wind_speed: float
    wind_direction: float
    turbulence_intensity: float
    visibility: float
    precipitation: str

@dataclass
class LaunchSiteConditions:
    latitude: float
    longitude: float
    elevation: float
    magnetic_declination: float
    local_gravity: float
    ground_temperature: float
    ground_roughness: float

@dataclass
class EnvironmentConfiguration:
    atmospheric_conditions: AtmosphericConditions
    launch_site_conditions: LaunchSiteConditions
    hardware_limitations: HardwareLimitations

@dataclass
class SimulationConfig:
    # CFD Solver Settings
    solver_type: str
    turbulence_model: str
    time_step: float
    max_time: float
    write_interval: int
    
    # Atmospheric Conditions
    launch_altitude: float
    temperature: float
    pressure: float
    humidity: float
    wind_speed: float
    wind_direction: float
    
    # Boundary Conditions
    inlet_velocity: float
    outlet_pressure: float
    wall_condition: str
    domain_size: float
    
    # Mesh Settings
    base_cell_size: float
    boundary_layer_cells: int
    refinement_level: str
    mesh_quality: float
    
    # Analysis Settings
    calculate_drag: bool
    calculate_lift: bool
    calculate_pressure: bool
    calculate_velocity: bool
    output_format: str

@dataclass
class RocketComponent:
    id: int
    type: str
    name: str
    length: float
    diameter: float
    top_diameter: Optional[float]
    bottom_diameter: Optional[float]
    nose_shape: Optional[str]
    fin_shape: Optional[str]
    fin_count: Optional[int]
    fin_height: Optional[float]
    fin_width: Optional[float]
    fin_thickness: Optional[float]
    fin_sweep: Optional[float]
    rail_button_height: Optional[float]
    rail_button_width: Optional[float]
    rail_button_offset: Optional[float]
    attached_to_component: Optional[int]

@dataclass
class SimulationStatus:
    status: str  # 'Initializing', 'Running', 'Complete', 'Error'
    progress: float
    current_time: Optional[float]
    message: str
    cell_count: Optional[int]
    iteration_count: Optional[int]

# --- CppIntegrationManager ---

class CPPControlSystem:
    def __init__(self, hardware_limits: HardwareLimitations):
        self.hardware_limits = hardware_limits
        self.compiled_programs = {}
        self.active_simulations = {}
        
    def validate_cpp_code(self, cpp_code: str) -> Tuple[bool, str]:
        forbidden_includes = [
            '#include <fstream>', '#include <filesystem>', '#include <system>',
            'system(', 'exec(', 'fork(', 'kill(', 'exit(', 'abort(',
            'std::system', 'std::exit', 'std::abort'
        ]
        for forbidden in forbidden_includes:
            if forbidden in cpp_code:
                return False, f"Forbidden operation detected: {forbidden}"
        
        if 'ControlOutput control_function(SensorData sensor_data)' not in cpp_code:
            return False, "Missing required function: ControlOutput control_function(SensorData sensor_data)"
        
        return True, "Code validation passed"
    
    def compile_cpp_code(self, cpp_code: str, program_id: str) -> Tuple[bool, str]:
        is_valid, validation_msg = self.validate_cpp_code(cpp_code)
        if not is_valid:
            return False, validation_msg
        
        try:
            temp_dir = tempfile.mkdtemp(prefix=f"rocket_control_{program_id}_")
            header_content = self._generate_header_file()
            header_path = os.path.join(temp_dir, "rocket_control.h")
            with open(header_path, 'w') as f:
                f.write(header_content)
            
            main_content = self._generate_main_file(cpp_code)
            cpp_path = os.path.join(temp_dir, "control_program.cpp")
            with open(cpp_path, 'w') as f:
                f.write(main_content)
            
            executable_path = os.path.join(temp_dir, "control_program")
            compile_cmd = [
                'g++', '-std=c++17', '-O2', '-Wall', '-Wextra',
                '-fstack-protector-strong', '-D_FORTIFY_SOURCE=2',
                '-o', executable_path, cpp_path
            ]
            
            result = subprocess.run(
                compile_cmd, capture_output=True, text=True, timeout=30, cwd=temp_dir
            )
            
            if result.returncode == 0:
                self.compiled_programs[program_id] = {
                    'executable_path': executable_path,
                    'temp_dir': temp_dir,
                    'compile_time': time.time()
                }
                return True, "Compilation successful"
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False, f"Compilation failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Compilation timeout"
        except Exception as e:
            return False, f"Compilation error: {str(e)}"
    
    def _generate_header_file(self) -> str:
        return """
#ifndef ROCKET_CONTROL_H
#define ROCKET_CONTROL_H

#include <vector>
#include <map>
#include <string>

struct SensorData {
    double timestamp;
    double altitude;
    double velocity_x, velocity_y, velocity_z;
    double acceleration_x, acceleration_y, acceleration_z;
    double angular_velocity_x, angular_velocity_y, angular_velocity_z;
    double pressure;
    double temperature;
    double gps_latitude, gps_longitude;
};

struct ControlOutput {
    double fin_deflection_1;
    double fin_deflection_2;
    double fin_deflection_3;
    double fin_deflection_4;
    bool recovery_trigger;
    std::map<std::string, double> data_logging;
};

extern "C" ControlOutput control_function(SensorData sensor_data);

#endif // ROCKET_CONTROL_H
"""
    
    def _generate_main_file(self, user_cpp_code: str) -> str:
        return f"""#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <cmath>

#include "rocket_control.h"

// User's control code will be inserted here
{user_cpp_code}

// Main function for testing (not used in simulation, but for compilation)
int main() {{
    SensorData test_sensor_data = {{
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 101325.0, 20.0, 0.0, 0.0
    }};
    ControlOutput output = control_function(test_sensor_data);
    std::cout << "Fin 1: " << output.fin_deflection_1 << std::endl;
    return 0;
}}
"""

# --- MotorDatabase ---

class MotorDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'database', 'motors.db')
        self.db_path = db_path
        self._ensure_database_exists()
        self._populate_tarc_motors()
    
    def _ensure_database_exists(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS motors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, designation TEXT UNIQUE NOT NULL,
                    manufacturer TEXT NOT NULL, diameter REAL NOT NULL, length REAL NOT NULL,
                    total_mass REAL NOT NULL, propellant_mass REAL NOT NULL, average_thrust REAL NOT NULL,
                    max_thrust REAL NOT NULL, total_impulse REAL NOT NULL, burn_time REAL NOT NULL,
                    impulse_class TEXT NOT NULL, delay_time REAL NOT NULL, approved_for_tarc BOOLEAN NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS thrust_curves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, motor_id INTEGER NOT NULL,
                    time_point REAL NOT NULL, thrust_value REAL NOT NULL,
                    FOREIGN KEY (motor_id) REFERENCES motors (id)
                )
            ''')
            conn.commit()
    
    def _populate_tarc_motors(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM motors')
            if cursor.fetchone()[0] > 0:
                return
        
        tarc_motors = [
            {'designation': 'Estes A8-3', 'manufacturer': 'Estes', 'diameter': 18.0, 'length': 70.0, 'total_mass': 8.5, 'propellant_mass': 1.9, 'average_thrust': 2.5, 'max_thrust': 9.5, 'total_impulse': 2.5, 'burn_time': 1.0, 'impulse_class': 'A', 'delay_time': 3.0, 'approved_for_tarc': True, 'thrust_curve': self._generate_thrust_curve('A8', 1.0, 2.5, 9.5)},
            {'designation': 'Estes B6-4', 'manufacturer': 'Estes', 'diameter': 18.0, 'length': 70.0, 'total_mass': 11.5, 'propellant_mass': 4.6, 'average_thrust': 4.3, 'max_thrust': 12.8, 'total_impulse': 5.0, 'burn_time': 1.6, 'impulse_class': 'B', 'delay_time': 4.0, 'approved_for_tarc': True, 'thrust_curve': self._generate_thrust_curve('B6', 1.6, 4.3, 12.8)},
            {'designation': 'Estes C6-5', 'manufacturer': 'Estes', 'diameter': 18.0, 'length': 70.0, 'total_mass': 17.5, 'propellant_mass': 8.8, 'average_thrust': 5.0, 'max_thrust': 14.1, 'total_impulse': 10.0, 'burn_time': 2.0, 'impulse_class': 'C', 'delay_time': 5.0, 'approved_for_tarc': True, 'thrust_curve': self._generate_thrust_curve('C6', 2.0, 5.0, 14.1)},
            {'designation': 'Estes D12-5', 'manufacturer': 'Estes', 'diameter': 24.0, 'length': 70.0, 'total_mass': 37.7, 'propellant_mass': 17.6, 'average_thrust': 8.8, 'max_thrust': 25.0, 'total_impulse': 20.0, 'burn_time': 2.3, 'impulse_class': 'D', 'delay_time': 5.0, 'approved_for_tarc': True, 'thrust_curve': self._generate_thrust_curve('D12', 2.3, 8.8, 25.0)},
        ]
        for motor_data in tarc_motors:
            self.add_motor(MotorSpecification(**motor_data))
    
    def _generate_thrust_curve(self, motor_type: str, burn_time: float, avg_thrust: float, max_thrust: float) -> List[Tuple[float, float]]:
        time_points = np.linspace(0, burn_time, 100)
        thrust_values = []
        for t in time_points:
            if motor_type.startswith(('A', 'B')):
                if t < 0.1: thrust = max_thrust * (t / 0.1)
                elif t < burn_time - 0.1: thrust = avg_thrust + 0.2 * avg_thrust * np.sin(10 * t)
                else: thrust = avg_thrust * (burn_time - t) / 0.1
            else:
                if t < 0.2: thrust = max_thrust * (t / 0.2)
                elif t < burn_time * 0.3: thrust = max_thrust * 0.9
                elif t < burn_time * 0.8: thrust = avg_thrust + 0.3 * avg_thrust * np.sin(8 * t)
                else: thrust = avg_thrust * (burn_time - t) / (burn_time * 0.2)
            thrust_values.append((t, max(0, thrust)))
        return thrust_values
    
    def add_motor(self, motor: MotorSpecification) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO motors (designation, manufacturer, diameter, length, total_mass, propellant_mass, average_thrust, max_thrust, total_impulse, burn_time, impulse_class, delay_time, approved_for_tarc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (motor.designation, motor.manufacturer, motor.diameter, motor.length, motor.total_mass, motor.propellant_mass, motor.average_thrust, motor.max_thrust, motor.total_impulse, motor.burn_time, motor.impulse_class, motor.delay_time, motor.approved_for_tarc))
                motor_id = cursor.lastrowid
                cursor.execute('DELETE FROM thrust_curves WHERE motor_id = ?', (motor_id,))
                for time_point, thrust_value in motor.thrust_curve:
                    cursor.execute('INSERT INTO thrust_curves (motor_id, time_point, thrust_value) VALUES (?, ?, ?)', (motor_id, time_point, thrust_value))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding motor: {e}")
            return False
    
    def get_motor(self, designation: str) -> Optional[MotorSpecification]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM motors WHERE designation = ?', (designation,))
                motor_row = cursor.fetchone()
                if not motor_row: return None
                cursor.execute('SELECT time_point, thrust_value FROM thrust_curves WHERE motor_id = ? ORDER BY time_point', (motor_row[0],))
                thrust_curve = cursor.fetchall()
                return MotorSpecification(designation=motor_row[1], manufacturer=motor_row[2], diameter=motor_row[3], length=motor_row[4], total_mass=motor_row[5], propellant_mass=motor_row[6], average_thrust=motor_row[7], max_thrust=motor_row[8], total_impulse=motor_row[9], burn_time=motor_row[10], impulse_class=motor_row[11], delay_time=motor_row[12], thrust_curve=thrust_curve, approved_for_tarc=bool(motor_row[13]))
        except Exception as e:
            print(f"Error getting motor: {e}")
            return None

    def get_all_motors(self, tarc_only: bool = False) -> List[MotorSpecification]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = 'SELECT * FROM motors'
                params = ()
                if tarc_only:
                    query += ' WHERE approved_for_tarc = ?'
                    params = (True,)
                cursor.execute(query, params)
                motor_rows = cursor.fetchall()
                
                motors = []
                for motor_row in motor_rows:
                    cursor.execute('SELECT time_point, thrust_value FROM thrust_curves WHERE motor_id = ? ORDER BY time_point', (motor_row[0],))
                    thrust_curve = cursor.fetchall()
                    motors.append(MotorSpecification(designation=motor_row[1], manufacturer=motor_row[2], diameter=motor_row[3], length=motor_row[4], total_mass=motor_row[5], propellant_mass=motor_row[6], average_thrust=motor_row[7], max_thrust=motor_row[8], total_impulse=motor_row[9], burn_time=motor_row[10], impulse_class=motor_row[11], delay_time=motor_row[12], thrust_curve=thrust_curve, approved_for_tarc=bool(motor_row[13])))
                return motors
        except Exception as e:
            print(f"Error getting all motors: {e}")
            return []

# --- EnvironmentManager ---

class EnvironmentManager:
    def __init__(self):
        self.standard_atmosphere = self._create_standard_atmosphere()
        self.common_launch_sites = self._create_common_launch_sites()
    
    def _create_standard_atmosphere(self) -> Dict[float, AtmosphericConditions]:
        altitudes = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
        atmosphere = {}
        for alt in altitudes:
            if alt <= 11000:
                temp_k = 288.15 - 0.0065 * alt
                pressure = 101325 * (temp_k / 288.15) ** 5.2561
            else:
                temp_k = 216.65
                pressure = 22632 * math.exp(-0.0001577 * (alt - 11000))
            temp_c = temp_k - 273.15
            density = pressure / (287.05 * temp_k)
            atmosphere[alt] = AtmosphericConditions(altitude=alt, temperature=temp_c, pressure=pressure, density=density, humidity=50.0, wind_speed=0.0, wind_direction=0.0, turbulence_intensity=5.0, visibility=10000.0, precipitation="none")
        return atmosphere
    
    def _create_common_launch_sites(self) -> Dict[str, LaunchSiteConditions]:
        return {
            "NAR_TARC_Finals": LaunchSiteConditions(latitude=38.9072, longitude=-77.0369, elevation=50.0, magnetic_declination=-10.5, local_gravity=9.80665, ground_temperature=20.0, ground_roughness=0.1),
            "Estes_Field": LaunchSiteConditions(latitude=39.7392, longitude=-104.9903, elevation=1609.0, magnetic_declination=8.5, local_gravity=9.80665, ground_temperature=15.0, ground_roughness=0.05),
            "Black_Rock_Desert": LaunchSiteConditions(latitude=40.8, longitude=-119.0, elevation=1200.0, magnetic_declination=13.0, local_gravity=9.80665, ground_temperature=25.0, ground_roughness=0.02),
        }
    
    def get_atmospheric_conditions(self, altitude: float, base_conditions: AtmosphericConditions = None) -> AtmosphericConditions:
        if base_conditions is None:
            if altitude in self.standard_atmosphere: return self.standard_atmosphere[altitude]
            altitudes = sorted(self.standard_atmosphere.keys())
            if altitude <= altitudes[0]: return self.standard_atmosphere[altitudes[0]]
            if altitude >= altitudes[-1]: return self.standard_atmosphere[altitudes[-1]]
            for i in range(len(altitudes) - 1):
                if altitudes[i] <= altitude <= altitudes[i + 1]:
                    alt1, alt2 = altitudes[i], altitudes[i + 1]
                    cond1, cond2 = self.standard_atmosphere[alt1], self.standard_atmosphere[alt2]
                    factor = (altitude - alt1) / (alt2 - alt1)
                    return AtmosphericConditions(altitude=altitude, temperature=cond1.temperature + factor * (cond2.temperature - cond1.temperature), pressure=cond1.pressure + factor * (cond2.pressure - cond1.pressure), density=cond1.density + factor * (cond2.density - cond1.density), humidity=cond1.humidity, wind_speed=cond1.wind_speed, wind_direction=cond1.wind_direction, turbulence_intensity=cond1.turbulence_intensity, visibility=cond1.visibility, precipitation=cond1.precipitation)
        else:
            return self._adjust_for_altitude(base_conditions, target_altitude=altitude)
    
    def _adjust_for_altitude(self, base_conditions: AtmosphericConditions, target_altitude: float) -> AtmosphericConditions:
        altitude_diff = target_altitude - base_conditions.altitude
        temp_adjustment = -0.0065 * altitude_diff
        new_temperature = base_conditions.temperature + temp_adjustment
        temp_k_base, temp_k_new = base_conditions.temperature + 273.15, new_temperature + 273.15
        pressure_ratio = math.exp(-altitude_diff / (287.05 * temp_k_base / 9.80665)) if abs(altitude_diff) < 100 else (temp_k_new / temp_k_base) ** 5.2561
        new_pressure = base_conditions.pressure * pressure_ratio
        new_density = new_pressure / (287.05 * temp_k_new)
        wind_factor = 1.0 + altitude_diff / 10000.0
        new_wind_speed = base_conditions.wind_speed * max(0.1, wind_factor)
        return AtmosphericConditions(altitude=target_altitude, temperature=new_temperature, pressure=new_pressure, density=new_density, humidity=base_conditions.humidity * 0.9 ** (altitude_diff / 1000), wind_speed=new_wind_speed, wind_direction=base_conditions.wind_direction, turbulence_intensity=base_conditions.turbulence_intensity, visibility=base_conditions.visibility, precipitation=base_conditions.precipitation)

    def get_launch_sites(self):
        return {"launch_sites": {name: asdict(site) for name, site in self.common_launch_sites.items()}}

# --- CFD Engine ---

class CFDEngine:
    def __init__(self, rocket_geometry, environment):
        self.rocket_geometry = rocket_geometry
        self.environment = environment
        self.simulation_status = "idle"
        self.simulation_progress = 0
        self.simulation_results = {}
        self.simulation_thread = None

    def _run_simulation_task(self):
        self.simulation_status = "running"
        self.simulation_progress = 0
        self.simulation_message = "Initializing CFD solver..."
        
        # Simulate a long-running CFD process
        for i in range(101):
            time.sleep(0.1) # Simulate work
            self.simulation_progress = i
            self.simulation_message = f"Running CFD simulation... Progress: {i}%"

        self.simulation_results = {
            "max_altitude": 850 + np.random.rand() * 50,
            "max_velocity": 300 + np.random.rand() * 20,
            "drag_coefficient": 0.4 + np.random.rand() * 0.1,
            "computation_time": 10.0 + np.random.rand() * 5.0
        }
        self.simulation_status = "completed"
        self.simulation_message = "Simulation completed!"

    def run_simulation(self):
        if self.simulation_status == "running":
            return False, "Simulation already running."
        self.simulation_thread = threading.Thread(target=self._run_simulation_task)
        self.simulation_thread.start()
        return True, "Simulation started."

    def get_status(self):
        return {
            "status": self.simulation_status,
            "progress": self.simulation_progress,
            "message": self.simulation_message,
            "results": self.simulation_results if self.simulation_status == "completed" else None
        }

# --- OpenFOAM Integration Manager ---

class OpenFOAMManager:
    def __init__(self):
        self.simulation_running = False
        self.current_simulation = None
        self.simulation_status = SimulationStatus(
            status="Idle",
            progress=0,
            current_time=None,
            message="No simulation running",
            cell_count=None,
            iteration_count=None
        )
        self.simulation_thread = None
        self.openfoam_case_dir = None
        self.results = {}
        
    def start_simulation(self, rocket_components, rocket_weight, rocket_cg, simulation_config):
        """Start a new OpenFOAM simulation"""
        if self.simulation_running:
            return {"error": "Simulation already running"}
            
        try:
            # Create OpenFOAM case directory
            self.openfoam_case_dir = self._create_case_directory()
            
            # Generate mesh from rocket geometry
            mesh_success = self._generate_mesh(rocket_components, simulation_config)
            if not mesh_success:
                return {"error": "Failed to generate mesh"}
            
            # Setup OpenFOAM case files
            self._setup_case_files(simulation_config)
            
            # Start simulation in background thread
            self.simulation_running = True
            self.simulation_status = SimulationStatus(
                status="Running",
                progress=0,
                current_time=0,
                message="Starting OpenFOAM solver",
                cell_count=None,
                iteration_count=0
            )
            
            self.simulation_thread = threading.Thread(
                target=self._run_openfoam_simulation,
                args=(simulation_config,)
            )
            self.simulation_thread.start()
            
            return {"status": "Simulation started", "case_dir": self.openfoam_case_dir}
            
        except Exception as e:
            return {"error": f"Failed to start simulation: {str(e)}"}
    
    def _create_case_directory(self):
        """Create a new OpenFOAM case directory"""
        case_name = f"rocket_sim_{int(time.time())}"
        case_dir = os.path.join(os.getcwd(), "openfoam_cases", case_name)
        os.makedirs(case_dir, exist_ok=True)
        
        # Create standard OpenFOAM directory structure
        os.makedirs(os.path.join(case_dir, "0"), exist_ok=True)
        os.makedirs(os.path.join(case_dir, "constant"), exist_ok=True)
        os.makedirs(os.path.join(case_dir, "system"), exist_ok=True)
        
        return case_dir
    
    def _generate_mesh(self, rocket_components, simulation_config):
        """Generate mesh from rocket geometry using blockMesh and snappyHexMesh"""
        try:
            # Create blockMeshDict
            self._create_block_mesh_dict(simulation_config)
            
            # Create snappyHexMeshDict for rocket geometry
            self._create_snappy_hex_mesh_dict(rocket_components, simulation_config)
            
            # For now, just simulate mesh generation
            time.sleep(2)  # Simulate mesh generation time
            return True
            
        except Exception as e:
            print(f"Mesh generation error: {e}")
            return False
    
    def _create_block_mesh_dict(self, simulation_config):
        """Create blockMeshDict file"""
        domain_size = simulation_config.domain_size
        cell_size = simulation_config.base_cell_size
        
        nx = int(domain_size / cell_size)
        ny = int(domain_size / cell_size)
        nz = int(domain_size * 2 / cell_size)  # Longer in Z direction for rocket
        
        block_mesh_content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  dev                                  |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

convertToMeters 1;

vertices
(
    ({-domain_size/2} {-domain_size/2} 0)
    ({domain_size/2} {-domain_size/2} 0)
    ({domain_size/2} {domain_size/2} 0)
    ({-domain_size/2} {domain_size/2} 0)
    ({-domain_size/2} {-domain_size/2} {domain_size*2})
    ({domain_size/2} {-domain_size/2} {domain_size*2})
    ({domain_size/2} {domain_size/2} {domain_size*2})
    ({-domain_size/2} {domain_size/2} {domain_size*2})
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)
);

boundary
(
    inlet
    {{
        type patch;
        faces
        (
            (0 4 7 3)
        );
    }}
    
    outlet
    {{
        type patch;
        faces
        (
            (1 2 6 5)
        );
    }}
    
    ground
    {{
        type wall;
        faces
        (
            (0 3 2 1)
        );
    }}
    
    top
    {{
        type patch;
        faces
        (
            (4 5 6 7)
        );
    }}
    
    sides
    {{
        type patch;
        faces
        (
            (0 1 5 4)
            (2 3 7 6)
        );
    }}
);

mergePatchPairs
(
);

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "system", "blockMeshDict"), "w") as f:
            f.write(block_mesh_content)
    
    def _create_snappy_hex_mesh_dict(self, rocket_components, simulation_config):
        """Create snappyHexMeshDict for rocket geometry"""
        # This is a simplified version - in practice, you'd need to create
        # STL files for the rocket geometry
        snappy_content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  dev                                  |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      snappyHexMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

castellatedMesh true;
snap            true;
addLayers       true;

geometry
{{
    // Rocket geometry would be defined here
    // For now, we'll use a simple cylinder approximation
}};

castellatedMeshControls
{{
    maxLocalCells 1000000;
    maxGlobalCells 2000000;
    minSize 0.001;
    maxLoadUnbalance 0.10;
    nSmoothScale 4;
    errorReduction 0.75;
}};

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 30;
    nRelaxIter 5;
    nFeatureSnapIter 10;
}};

addLayersControls
{{
    relativeSizes true;
    layers
    {{
        // Boundary layer refinement
    }};
    
    expansionRatio 1.2;
    finalLayerThickness 0.7;
    minThickness 0.1;
    nGrow 0;
    featureAngle 60;
    slipFeatureAngle 30;
    nRelaxIter 3;
    nSmoothSurfaceNormals 1;
    nSmoothNormals 3;
    nSmoothThickness 10;
    maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3;
    minMedianAxisAngle 90;
    nBufferCellsNoExtrude 0;
    nLayerIter 50;
    nRelaxIter 5;
}};

meshQualityControls
{{
    maxNonOrtho 65;
    maxBoundarySkewness 20;
    maxInternalSkewness 4;
    maxConcave 80;
    minVol 1e-13;
    minTetQuality 1e-15;
    minArea -1;
    minTwist 0.02;
    minDeterminant 0.001;
    minFaceWeight 0.02;
    minVolRatio 0.01;
    minTriangleTwist -1;
    nSmoothScale 4;
    errorReduction 0.75;
}};

debug 0;
mergeTolerance 1e-6;

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "system", "snappyHexMeshDict"), "w") as f:
            f.write(snappy_content)
    
    def _setup_case_files(self, simulation_config):
        """Setup OpenFOAM case files (controlDict, fvSchemes, fvSolution, etc.)"""
        # Create controlDict
        control_dict = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  dev                                  |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      controlDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

application     {simulation_config.solver_type};

startFrom       startTime;

startTime       0;

stopAt          endTime;

endTime         {simulation_config.max_time};

deltaT          {simulation_config.time_step};

writeControl    timeStep;

writeInterval   {simulation_config.write_interval};

purgeWrite      0;

writeFormat     ascii;

writePrecision  6;

writeCompression off;

timeFormat      general;

timePrecision   6;

runTimeModifiable true;

functions
{{
    #includeFunc residuals
}};

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "system", "controlDict"), "w") as f:
            f.write(control_dict)
    
    def _run_openfoam_simulation(self, simulation_config):
        """Run the OpenFOAM solver"""
        try:
            # For now, simulate the OpenFOAM solver
            for i in range(100):
                if not self.simulation_running:
                    break
                time.sleep(0.1)
                self.simulation_status.progress = i
                self.simulation_status.current_time = i * simulation_config.time_step
                self.simulation_status.iteration_count = i
                self.simulation_status.message = f"Running {simulation_config.solver_type}... Iteration {i}"
            
            if self.simulation_running:
                self.simulation_status.status = "Complete"
                self.simulation_status.progress = 100
                self.simulation_status.message = "Simulation completed successfully"
                
        except Exception as e:
            self.simulation_status.status = "Error"
            self.simulation_status.message = f"Simulation error: {str(e)}"
        finally:
            self.simulation_running = False
    

    
    def get_status(self):
        """Get current simulation status"""
        status_dict = asdict(self.simulation_status)
        if self.results and self.simulation_status.status == "Complete":
            status_dict["results"] = self.results
        return status_dict
    
    def stop_simulation(self):
        """Stop the current simulation"""
        self.simulation_running = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            pass
        
        self.simulation_status.status = "Stopped"
        self.simulation_status.message = "Simulation stopped by user"
        
        return {"status": "Simulation stopped"}
        
    def start_simulation(self, rocket_components, rocket_weight, rocket_cg, simulation_config):
        """Start a new OpenFOAM simulation"""
        if self.simulation_running:
            return {"error": "Simulation already running"}
            
        try:
            # Create OpenFOAM case directory
            self.openfoam_case_dir = self._create_case_directory()
            
            # Generate mesh from rocket geometry
            mesh_success = self._generate_mesh(rocket_components, simulation_config)
            if not mesh_success:
                return {"error": "Failed to generate mesh"}
            
            # Setup OpenFOAM case files
            self._setup_case_files(simulation_config)
            
            # Start simulation in background thread
            self.simulation_running = True
            self.simulation_status = SimulationStatus(
                status="Running",
                progress=0,
                current_time=0,
                message="Starting OpenFOAM solver",
                cell_count=None,
                iteration_count=0
            )
            
            self.simulation_thread = threading.Thread(
                target=self._run_openfoam_simulation,
                args=(simulation_config,)
            )
            self.simulation_thread.start()
            
            return {"status": "Simulation started", "case_dir": self.openfoam_case_dir}
            
        except Exception as e:
            return {"error": f"Failed to start simulation: {str(e)}"}
    
    def _create_case_directory(self):
        """Create a new OpenFOAM case directory"""
        case_name = f"rocket_sim_{int(time.time())}"
        case_dir = os.path.join(os.getcwd(), "openfoam_cases", case_name)
        os.makedirs(case_dir, exist_ok=True)
        
        # Create standard OpenFOAM directory structure
        os.makedirs(os.path.join(case_dir, "0"), exist_ok=True)
        os.makedirs(os.path.join(case_dir, "constant"), exist_ok=True)
        os.makedirs(os.path.join(case_dir, "system"), exist_ok=True)
        
        return case_dir
    
    def _generate_mesh(self, rocket_components, simulation_config):
        """Generate mesh from rocket geometry using blockMesh and snappyHexMesh"""
        try:
            # Create blockMeshDict
            self._create_block_mesh_dict(simulation_config)
            
            # Create snappyHexMeshDict for rocket geometry
            self._create_snappy_hex_mesh_dict(rocket_components, simulation_config)
            
            # For now, just simulate mesh generation
            time.sleep(2)  # Simulate mesh generation time
            return True
            
        except Exception as e:
            print(f"Mesh generation error: {e}")
            return False
    
    def _create_block_mesh_dict(self, simulation_config):
        """Create blockMeshDict file"""
        domain_size = simulation_config.domain_size
        cell_size = simulation_config.base_cell_size
        
        nx = int(domain_size / cell_size)
        ny = int(domain_size / cell_size)
        nz = int(domain_size * 2 / cell_size)  # Longer in Z direction for rocket
        
        block_mesh_content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  dev                                  |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

convertToMeters 1;

vertices
(
    ({-domain_size/2} {-domain_size/2} 0)
    ({domain_size/2} {-domain_size/2} 0)
    ({domain_size/2} {domain_size/2} 0)
    ({-domain_size/2} {domain_size/2} 0)
    ({-domain_size/2} {-domain_size/2} {domain_size*2})
    ({domain_size/2} {-domain_size/2} {domain_size*2})
    ({domain_size/2} {domain_size/2} {domain_size*2})
    ({-domain_size/2} {domain_size/2} {domain_size*2})
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)
);

boundary
(
    inlet
    {{
        type patch;
        faces
        (
            (0 4 7 3)
        );
    }}
    
    outlet
    {{
        type patch;
        faces
        (
            (1 2 6 5)
        );
    }}
    
    ground
    {{
        type wall;
        faces
        (
            (0 3 2 1)
        );
    }}
    
    top
    {{
        type patch;
        faces
        (
            (4 5 6 7)
        );
    }}
    
    sides
    {{
        type patch;
        faces
        (
            (0 1 5 4)
            (2 3 7 6)
        );
    }}
);

mergePatchPairs
(
);

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "system", "blockMeshDict"), "w") as f:
            f.write(block_mesh_content)
    
    def _create_snappy_hex_mesh_dict(self, rocket_components, simulation_config):
        """Create snappyHexMeshDict for rocket geometry"""
        # This is a simplified version - in practice, you'd need to create
        # STL files for the rocket geometry
        snappy_content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  dev                                  |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      snappyHexMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

castellatedMesh true;
snap            true;
addLayers       true;

geometry
{{
    // Rocket geometry would be defined here
    // For now, we'll use a simple cylinder approximation
}};

castellatedMeshControls
{{
    maxLocalCells 1000000;
    maxGlobalCells 2000000;
    minSize 0.001;
    maxLoadUnbalance 0.10;
    nSmoothScale 4;
    errorReduction 0.75;
}};

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 30;
    nRelaxIter 5;
    nFeatureSnapIter 10;
}};

addLayersControls
{{
    relativeSizes true;
    layers
    {{
        // Boundary layer refinement
    }};
    
    expansionRatio 1.2;
    finalLayerThickness 0.7;
    minThickness 0.1;
    nGrow 0;
    featureAngle 60;
    slipFeatureAngle 30;
    nRelaxIter 3;
    nSmoothSurfaceNormals 1;
    nSmoothNormals 3;
    nSmoothThickness 10;
    maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3;
    minMedianAxisAngle 90;
    nBufferCellsNoExtrude 0;
    nLayerIter 50;
    nRelaxIter 5;
}};

meshQualityControls
{{
    maxNonOrtho 65;
    maxBoundarySkewness 20;
    maxInternalSkewness 4;
    maxConcave 80;
    minVol 1e-13;
    minTetQuality 1e-15;
    minArea -1;
    minTwist 0.02;
    minDeterminant 0.001;
    minFaceWeight 0.02;
    minVolRatio 0.01;
    minTriangleTwist -1;
    nSmoothScale 4;
    errorReduction 0.75;
}};

debug 0;
mergeTolerance 1e-6;

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "system", "snappyHexMeshDict"), "w") as f:
            f.write(snappy_content)
    
    def _setup_case_files(self, simulation_config):
        """Setup OpenFOAM case files (controlDict, fvSchemes, fvSolution, etc.)"""
        # Create controlDict
        control_dict = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  dev                                  |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      controlDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

application     {simulation_config.solver_type};

startFrom       startTime;

startTime       0;

stopAt          endTime;

endTime         {simulation_config.max_time};

deltaT          {simulation_config.time_step};

writeControl    timeStep;

writeInterval   {simulation_config.write_interval};

purgeWrite      0;

writeFormat     ascii;

writePrecision  6;

writeCompression off;

timeFormat      general;

timePrecision   6;

runTimeModifiable true;

functions
{{
    #includeFunc residuals
}};

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "system", "controlDict"), "w") as f:
            f.write(control_dict)
    
    def _run_openfoam_simulation(self, simulation_config):
        """Run the OpenFOAM solver"""
        try:
            # For now, simulate the OpenFOAM solver
            for i in range(100):
                if not self.simulation_running:
                    break
                time.sleep(0.1)
                self.simulation_status.progress = i
                self.simulation_status.current_time = i * simulation_config.time_step
                self.simulation_status.iteration_count = i
                self.simulation_status.message = f"Running {simulation_config.solver_type}... Iteration {i}"
            
            if self.simulation_running:
                self.simulation_status.status = "Complete"
                self.simulation_status.progress = 100
                self.simulation_status.message = "Simulation completed successfully"
                
        except Exception as e:
            self.simulation_status.status = "Error"
            self.simulation_status.message = f"Simulation error: {str(e)}"
        finally:
            self.simulation_running = False
    
    def get_status(self):
        """Get current simulation status"""
        return asdict(self.simulation_status)
    
    def stop_simulation(self):
        """Stop the current simulation"""
        self.simulation_running = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            # In a real implementation, you'd need to properly terminate the OpenFOAM process
            pass
        
        self.simulation_status.status = "Stopped"
        self.simulation_status.message = "Simulation stopped by user"
        
        return {"status": "Simulation stopped"}

# --- Flask App and Routes ---

# Get the absolute path to the frontend dist directory
import os
backend_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dist_dir = os.path.join(backend_dir, '..', 'frontend', 'dist')

# Debug: Print the paths
print(f"Backend directory: {backend_dir}")
print(f"Frontend dist directory: {frontend_dist_dir}")
print(f"Frontend dist exists: {os.path.exists(frontend_dist_dir)}")
if os.path.exists(frontend_dist_dir):
    print(f"Files in frontend dist: {os.listdir(frontend_dist_dir)}")

app = Flask(__name__, static_folder=frontend_dist_dir, static_url_path='/')
CORS(app)

motor_db = MotorDatabase(db_path=os.path.join(os.path.dirname(__file__), 'database', 'motors.db'))
env_manager = EnvironmentManager()
cfd_engine = CFDEngine(rocket_geometry=None, environment=None) # Geometry and environment will be passed via API

# Initialize CFD managers
# Check if we're in cloud mode (Render deployment)
simulation_mode = os.environ.get('SIMULATION_MODE', 'local').lower()

if simulation_mode == 'cloud' and gcp_cfd_available:
    openfoam_manager = GCPCFDClient()
    print("☁️  Google Cloud CFD manager initialized (Cloud Mode)")
elif gcp_cfd_available:
    openfoam_manager = GCPCFDClient()
    print("☁️  Google Cloud CFD manager initialized")
elif heavy_cfd_available and simulation_mode != 'cloud':
    openfoam_manager = HeavyCFDManager()
    print("🚀 Heavy CFD manager initialized")
else:
    openfoam_manager = OpenFOAMManager()
    print("⚠️  Using simulation mode OpenFOAM manager")

hardware_limits = HardwareLimitations(
    servo_max_speed=180.0,
    servo_max_torque=0.5,
    servo_response_time=0.02,
    sensor_noise_level=5.0,
    sensor_update_rate=100.0,
    max_fin_deflection=15.0,
    battery_voltage=7.4,
    processing_delay=0.001
)
cpp_control_system = CPPControlSystem(hardware_limits)

@app.route("/api/environment/motors", methods=["GET"])
def get_all_motors_route():
    tarc_only = request.args.get("tarc_only", "false").lower() == "true"
    motors = motor_db.get_all_motors(tarc_only=tarc_only)
    return jsonify({"motors": [asdict(m) for m in motors]})

@app.route("/api/environment/launch-sites", methods=["GET"])
def get_launch_sites_route():
    return jsonify(env_manager.get_launch_sites())

@app.route("/api/control-code/compile", methods=["POST"])
def compile_control_code():
    data = request.get_json()
    code = data.get("code")
    program_id = str(uuid.uuid4())
    success, message = cpp_control_system.compile_cpp_code(code, program_id)
    return jsonify({"success": success, "message": message, "program_id": program_id if success else None})

@app.route("/api/simulation/start", methods=["POST"])
def start_simulation():
    data = request.get_json()
    
    # Extract data from request
    rocket_components = data.get('rocketComponents', [])
    rocket_weight = data.get('rocketWeight', 0)
    rocket_cg = data.get('rocketCG', 0)
    simulation_config_data = data.get('simulationConfig', {})
    
    # Convert simulation config to dataclass
    simulation_config = SimulationConfig(
        solver_type=simulation_config_data.get('solverType', 'pimpleFoam'),
        turbulence_model=simulation_config_data.get('turbulenceModel', 'LES'),
        time_step=simulation_config_data.get('timeStep', 0.001),
        max_time=simulation_config_data.get('maxTime', 30),
        write_interval=simulation_config_data.get('writeInterval', 100),
        launch_altitude=simulation_config_data.get('launchAltitude', 0),
        temperature=simulation_config_data.get('temperature', 15),
        pressure=simulation_config_data.get('pressure', 101325),
        humidity=simulation_config_data.get('humidity', 50),
        wind_speed=simulation_config_data.get('windSpeed', 0),
        wind_direction=simulation_config_data.get('windDirection', 0),
        inlet_velocity=simulation_config_data.get('inletVelocity', 0),
        outlet_pressure=simulation_config_data.get('outletPressure', 101325),
        wall_condition=simulation_config_data.get('wallCondition', 'noSlip'),
        domain_size=simulation_config_data.get('domainSize', 10),
        base_cell_size=simulation_config_data.get('baseCellSize', 0.01),
        boundary_layer_cells=simulation_config_data.get('boundaryLayerCells', 5),
        refinement_level=simulation_config_data.get('refinementLevel', 'medium'),
        mesh_quality=simulation_config_data.get('meshQuality', 0.3),
        calculate_drag=simulation_config_data.get('calculateDrag', True),
        calculate_lift=simulation_config_data.get('calculateLift', True),
        calculate_pressure=simulation_config_data.get('calculatePressure', True),
        calculate_velocity=simulation_config_data.get('calculateVelocity', True),
        output_format=simulation_config_data.get('outputFormat', 'vtk')
    )
    
    # Start OpenFOAM simulation
    result = openfoam_manager.start_simulation(
        rocket_components, rocket_weight, rocket_cg, simulation_config
    )
    
    if "error" in result:
        return jsonify({"success": False, "message": result["error"]}), 400
    else:
        return jsonify({"success": True, "message": result["status"]})

@app.route("/api/simulation/status", methods=["GET"])
def get_simulation_status():
    status = openfoam_manager.get_status()
    return jsonify(status)

@app.route("/api/simulation/stop", methods=["POST"])
def stop_simulation():
    result = openfoam_manager.stop_simulation()
    return jsonify(result)

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint for Render deployment"""
    return jsonify({
        "status": "healthy",
        "heavy_cfd_available": heavy_cfd_available,
        "openfoam_status": openfoam_manager.get_status()
    })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve the React frontend and handle client-side routing"""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        # Serve static files (JS, CSS, images, etc.)
        return app.send_static_file(path)
    else:
        # Serve index.html for all other routes (React Router)
        return app.send_static_file('index.html')

@app.route("/api/simulation/mesh", methods=["POST"])
def generate_mesh():
    data = request.get_json()
    
    # Extract data from request
    rocket_components = data.get('rocketComponents', [])
    simulation_config_data = data.get('simulationConfig', {})
    
    # Convert simulation config to dataclass
    simulation_config = SimulationConfig(
        solver_type=simulation_config_data.get('solverType', 'pimpleFoam'),
        turbulence_model=simulation_config_data.get('turbulenceModel', 'LES'),
        time_step=simulation_config_data.get('timeStep', 0.001),
        max_time=simulation_config_data.get('maxTime', 30),
        write_interval=simulation_config_data.get('writeInterval', 100),
        launch_altitude=simulation_config_data.get('launchAltitude', 0),
        temperature=simulation_config_data.get('temperature', 15),
        pressure=simulation_config_data.get('pressure', 101325),
        humidity=simulation_config_data.get('humidity', 50),
        wind_speed=simulation_config_data.get('windSpeed', 0),
        wind_direction=simulation_config_data.get('windDirection', 0),
        inlet_velocity=simulation_config_data.get('inletVelocity', 0),
        outlet_pressure=simulation_config_data.get('outletPressure', 101325),
        wall_condition=simulation_config_data.get('wallCondition', 'noSlip'),
        domain_size=simulation_config_data.get('domainSize', 10),
        base_cell_size=simulation_config_data.get('baseCellSize', 0.01),
        boundary_layer_cells=simulation_config_data.get('boundaryLayerCells', 5),
        refinement_level=simulation_config_data.get('refinementLevel', 'medium'),
        mesh_quality=simulation_config_data.get('meshQuality', 0.3),
        calculate_drag=simulation_config_data.get('calculateDrag', True),
        calculate_lift=simulation_config_data.get('calculateLift', True),
        calculate_pressure=simulation_config_data.get('calculatePressure', True),
        calculate_velocity=simulation_config_data.get('calculateVelocity', True),
        output_format=simulation_config_data.get('outputFormat', 'vtk')
    )
    
    # Create temporary case directory for mesh generation
    case_name = f"mesh_gen_{int(time.time())}"
    case_dir = os.path.join(os.getcwd(), "openfoam_cases", case_name)
    os.makedirs(case_dir, exist_ok=True)
    os.makedirs(os.path.join(case_dir, "system"), exist_ok=True)
    
    try:
        # Create blockMeshDict
        domain_size = simulation_config.domain_size
        cell_size = simulation_config.base_cell_size
        
        nx = int(domain_size / cell_size)
        ny = int(domain_size / cell_size)
        nz = int(domain_size * 2 / cell_size)
        
        block_mesh_content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  dev                                  |
|   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

convertToMeters 1;

vertices
(
    ({-domain_size/2} {-domain_size/2} 0)
    ({domain_size/2} {-domain_size/2} 0)
    ({domain_size/2} {domain_size/2} 0)
    ({-domain_size/2} {domain_size/2} 0)
    ({-domain_size/2} {-domain_size/2} {domain_size*2})
    ({domain_size/2} {-domain_size/2} {domain_size*2})
    ({domain_size/2} {domain_size/2} {domain_size*2})
    ({-domain_size/2} {domain_size/2} {domain_size*2})
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)
);

boundary
(
    inlet
    {{
        type patch;
        faces
        (
            (0 4 7 3)
        );
    }}
    
    outlet
    {{
        type patch;
        faces
        (
            (1 2 6 5)
        );
    }}
    
    ground
    {{
        type wall;
        faces
        (
            (0 3 2 1)
        );
    }}
    
    top
    {{
        type patch;
        faces
        (
            (4 5 6 7)
        );
    }}
    
    sides
    {{
        type patch;
        faces
        (
            (0 1 5 4)
            (2 3 7 6)
        );
    }}
);

mergePatchPairs
(
);

// ************************************************************************* //
"""
        
        with open(os.path.join(case_dir, "system", "blockMeshDict"), "w") as f:
            f.write(block_mesh_content)
        
        # Simulate mesh generation
        time.sleep(2)
        
        # Calculate approximate cell count
        cell_count = nx * ny * nz
        
        return jsonify({
            "success": True,
            "message": "Mesh generated successfully",
            "cellCount": cell_count,
            "caseDir": case_dir
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to generate mesh: {str(e)}"
        }), 500
    return jsonify(status)

if __name__ == '__main__':
    # Ensure the database directory exists
    os.makedirs(os.path.join(os.path.dirname(__file__), 'database'), exist_ok=True)
    
    # Get port from environment variable (for Render deployment) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)


