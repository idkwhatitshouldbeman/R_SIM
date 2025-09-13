"""
Complete Simulation Orchestrator for Active Fin Control
Manages the entire CFD-control feedback loop
"""

import time
import threading
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import shutil

from mesh_morphing import OpenFOAMDynamicMeshManager, create_default_fin_configs
from cfd_data_extractor import CFDDataManager
from gcp_active_fin_integration import GCPActiveFinIntegration

class SimulationOrchestrator:
    """Orchestrates the complete active fin control simulation"""
    
    def __init__(self, case_dir: Path, gcp_project_id: str = None, gcp_bucket: str = None):
        self.case_dir = Path(case_dir)
        self.gcp_project_id = gcp_project_id
        self.gcp_bucket = gcp_bucket
        
        # Initialize components
        self.dynamic_mesh_manager = None
        self.cfd_data_manager = None
        self.gcp_integration = None
        
        # Simulation state
        self.simulation_running = False
        self.control_loop_running = False
        self.simulation_thread = None
        self.control_thread = None
        
        # Configuration
        self.cfd_time_step = 0.01
        self.control_update_rate = 100
        self.use_gcp = bool(gcp_project_id and gcp_bucket)
        
        # Fin configurations (placeholder - will be updated with real geometries later)
        self.fin_configs = create_default_fin_configs()
        
    def setup_simulation(self, fin_configs: Dict = None) -> bool:
        """Setup the complete simulation environment"""
        try:
            print("🚀 Setting up active fin control simulation...")
            
            # Update fin configurations if provided
            if fin_configs:
                self.fin_configs = fin_configs
            
            # Create case directory if it doesn't exist
            self.case_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize dynamic mesh manager
            self.dynamic_mesh_manager = OpenFOAMDynamicMeshManager(self.case_dir)
            
            # Setup dynamic mesh
            if not self.dynamic_mesh_manager.setup_dynamic_mesh(self.fin_configs):
                print("❌ Failed to setup dynamic mesh")
                return False
            
            # Initialize CFD data manager
            self.cfd_data_manager = CFDDataManager(self.case_dir)
            
            # Setup GCP integration if configured
            if self.use_gcp:
                self.gcp_integration = GCPActiveFinIntegration(
                    self.gcp_project_id, 
                    self.gcp_bucket
                )
                
                # Setup GCP simulation
                if not self.gcp_integration.setup_simulation(
                    self.case_dir, 
                    "active_fin_case"
                ):
                    print("❌ Failed to setup GCP simulation")
                    return False
            
            print("✅ Simulation setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up simulation: {e}")
            return False
    
    def start_simulation(self, control_algorithm: str, target_trajectory: Dict = None) -> bool:
        """Start the complete CFD-control simulation"""
        try:
            if self.simulation_running:
                print("⚠️ Simulation already running")
                return False
            
            print("🚀 Starting active fin control simulation...")
            
            # Set default target trajectory
            if target_trajectory is None:
                target_trajectory = {"pitch": 0, "yaw": 0}
            
            # Start CFD simulation
            if self.use_gcp and self.gcp_integration:
                if not self.gcp_integration.start_simulation():
                    print("❌ Failed to start GCP simulation")
                    return False
            else:
                if not self._start_local_simulation():
                    print("❌ Failed to start local simulation")
                    return False
            
            # Start control loop
            self.control_loop_running = True
            self.control_thread = threading.Thread(
                target=self._control_loop,
                args=(control_algorithm, target_trajectory)
            )
            self.control_thread.start()
            
            self.simulation_running = True
            print("✅ Active fin control simulation started")
            return True
            
        except Exception as e:
            print(f"❌ Error starting simulation: {e}")
            return False
    
    def stop_simulation(self) -> bool:
        """Stop the complete simulation"""
        try:
            print("⏹️ Stopping active fin control simulation...")
            
            # Stop control loop
            self.control_loop_running = False
            if self.control_thread:
                self.control_thread.join(timeout=5)
            
            # Stop CFD simulation
            if self.use_gcp and self.gcp_integration:
                self.gcp_integration.stop_simulation()
            else:
                self._stop_local_simulation()
            
            self.simulation_running = False
            print("✅ Simulation stopped")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping simulation: {e}")
            return False
    
    def get_simulation_status(self) -> Dict:
        """Get comprehensive simulation status"""
        try:
            status = {
                "simulation_running": self.simulation_running,
                "control_loop_running": self.control_loop_running,
                "use_gcp": self.use_gcp,
                "case_directory": str(self.case_dir),
                "cfd_time_step": self.cfd_time_step,
                "control_update_rate": self.control_update_rate
            }
            
            # Add GCP status if using GCP
            if self.use_gcp and self.gcp_integration:
                gcp_status = self.gcp_integration.get_status()
                status["gcp_status"] = gcp_status
            
            # Add CFD data status
            if self.cfd_data_manager:
                latest_data = self.cfd_data_manager.get_latest_cfd_data(self.cfd_time_step)
                if latest_data:
                    status["latest_cfd_data"] = {
                        "timestamp": latest_data.get("timestamp", 0),
                        "attitude": latest_data.get("attitude", [0, 0, 0]),
                        "velocity": latest_data.get("velocity", [0, 0, 0]),
                        "position": latest_data.get("position", [0, 0, 0])
                    }
            
            return status
            
        except Exception as e:
            return {
                "error": str(e),
                "simulation_running": False,
                "control_loop_running": False
            }
    
    def _start_local_simulation(self) -> bool:
        """Start local OpenFOAM simulation"""
        try:
            # Start OpenFOAM simulation
            cmd = ["pimpleFoam"]
            process = subprocess.Popen(
                cmd,
                cwd=self.case_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print("✅ Local OpenFOAM simulation started")
            return True
            
        except Exception as e:
            print(f"❌ Error starting local simulation: {e}")
            return False
    
    def _stop_local_simulation(self):
        """Stop local OpenFOAM simulation"""
        try:
            # Kill any running OpenFOAM processes
            subprocess.run(["pkill", "-f", "pimpleFoam"], check=False)
            print("✅ Local simulation stopped")
            
        except Exception as e:
            print(f"❌ Error stopping local simulation: {e}")
    
    def _control_loop(self, control_algorithm: str, target_trajectory: Dict):
        """Main control loop that runs the CFD-control feedback"""
        try:
            print("🎯 Starting control loop...")
            
            # Import js2py for JavaScript execution
            import js2py
            
            # Prepare JavaScript context
            js_context = js2py.EvalJs()
            js_context.targetTrajectory = target_trajectory
            
            # Execute control algorithm
            js_context.eval(control_algorithm)
            
            # Control loop
            while self.control_loop_running:
                try:
                    # Get latest CFD data
                    cfd_data = self.cfd_data_manager.get_latest_cfd_data(self.cfd_time_step)
                    
                    if cfd_data:
                        # Prepare CFD data for JavaScript
                        js_context.cfdData = {
                            'attitude': cfd_data.get('attitude', [0, 0, 0]),
                            'velocity': cfd_data.get('velocity', [0, 0, 0]),
                            'position': cfd_data.get('position', [0, 0, 0]),
                            'angularVelocity': cfd_data.get('angular_velocity', [0, 0, 0]),
                            'pressure': cfd_data.get('pressure', 101325),
                            'temperature': cfd_data.get('temperature', 288)
                        }
                        
                        # Execute control algorithm
                        fin_deflections = js_context.calculateFinDeflections(
                            js_context.cfdData, 
                            js_context.targetTrajectory
                        )
                        
                        # Apply deflection limits
                        max_deflection = 15.0  # degrees
                        limited_deflections = []
                        for deflection in fin_deflections:
                            limited_deflections.append(
                                max(-max_deflection, min(max_deflection, deflection))
                            )
                        
                        # Update fin positions
                        deflections_dict = {
                            "fin1": limited_deflections[0],
                            "fin2": limited_deflections[1],
                            "fin3": limited_deflections[2],
                            "fin4": limited_deflections[3]
                        }
                        
                        # Update mesh with new fin positions
                        if self.dynamic_mesh_manager:
                            self.dynamic_mesh_manager.update_fin_positions(deflections_dict)
                        
                        print(f"🎯 Control update: {deflections_dict}")
                    
                    # Sleep for control update rate
                    time.sleep(1.0 / self.control_update_rate)
                    
                except Exception as e:
                    print(f"❌ Error in control loop: {e}")
                    time.sleep(0.1)  # Short sleep on error
            
            print("⏹️ Control loop stopped")
            
        except Exception as e:
            print(f"❌ Error in control loop: {e}")
    
    def download_results(self, results_dir: Path) -> bool:
        """Download simulation results"""
        try:
            if self.use_gcp and self.gcp_integration:
                return self.gcp_integration.download_results(results_dir)
            else:
                # Copy local results
                local_results = self.case_dir / "postProcessing"
                if local_results.exists():
                    shutil.copytree(local_results, results_dir, dirs_exist_ok=True)
                    print("✅ Local results copied")
                    return True
                else:
                    print("❌ No local results found")
                    return False
                    
        except Exception as e:
            print(f"❌ Error downloading results: {e}")
            return False
    
    def cleanup(self):
        """Clean up all resources"""
        try:
            # Stop simulation
            self.stop_simulation()
            
            # Clean up GCP resources
            if self.use_gcp and self.gcp_integration:
                self.gcp_integration.cleanup()
            
            print("✅ Simulation cleanup complete")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

# Example usage and factory functions
def create_simulation_orchestrator(case_dir: str, gcp_project_id: str = None, 
                                 gcp_bucket: str = None) -> SimulationOrchestrator:
    """Create a simulation orchestrator"""
    return SimulationOrchestrator(Path(case_dir), gcp_project_id, gcp_bucket)

def create_local_simulation(case_dir: str) -> SimulationOrchestrator:
    """Create a local simulation orchestrator"""
    return SimulationOrchestrator(Path(case_dir))

def create_gcp_simulation(case_dir: str, project_id: str, bucket_name: str) -> SimulationOrchestrator:
    """Create a GCP simulation orchestrator"""
    return SimulationOrchestrator(Path(case_dir), project_id, bucket_name)
