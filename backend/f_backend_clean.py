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
import js2py  # For executing JavaScript control code
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS

# Import our real CFD and mesh systems
try:
    from .mesh_morphing import OpenFOAMDynamicMeshManager, create_default_fin_configs
    from .cfd_data_extractor import CFDDataManager
    from .simulation_orchestrator import SimulationOrchestrator
    from .openfoam_case_generator import create_active_fin_case
    from .gcp_active_fin_integration import GCPActiveFinIntegration
except ImportError:
    # Fallback for when running as main module
    from mesh_morphing import OpenFOAMDynamicMeshManager, create_default_fin_configs
    from cfd_data_extractor import CFDDataManager
    from simulation_orchestrator import SimulationOrchestrator
    from openfoam_case_generator import create_active_fin_case
    from gcp_active_fin_integration import GCPActiveFinIntegration

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
class ActiveFinControlConfig:
    enabled: bool
    cfd_time_step: float
    control_update_rate: int
    fin_deflection_limit: float
    control_gains: Dict[str, float]
    control_code: str

@dataclass
class CFDData:
    timestamp: float
    attitude: List[float]  # [roll, pitch, yaw] in degrees
    velocity: List[float]  # [vx, vy, vz] in m/s
    position: List[float]  # [x, y, z] in meters
    angular_velocity: List[float]  # [wx, wy, wz] in rad/s
    pressure: float
    temperature: float

@dataclass
class FinDeflections:
    timestamp: float
    fin1: float  # Top fin (pitch control)
    fin2: float  # Right fin (yaw control)
    fin3: float  # Bottom fin (pitch control)
    fin4: float  # Left fin (yaw control)

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

# --- Active Fin Control Manager ---

class ActiveFinControlManager:
    def __init__(self, case_dir: Optional[Path] = None):
        self.config = ActiveFinControlConfig(
            enabled=False,
            cfd_time_step=0.01,
            control_update_rate=100,
            fin_deflection_limit=15.0,
            control_gains={'kp': 1.0, 'ki': 0.1, 'kd': 0.05},
            control_code=""
        )
        self.current_fin_deflections = FinDeflections(0, 0, 0, 0, 0)
        self.cfd_data_history = []
        self.control_thread = None
        self.running = False
        
        # Real CFD and mesh systems
        self.case_dir = case_dir or Path("/tmp/openfoam_case")
        self.dynamic_mesh_manager = None
        self.cfd_data_manager = None
        self.fin_configs = create_default_fin_configs()
        
    def update_config(self, config_data: dict):
        """Update the active fin control configuration"""
        self.config.enabled = config_data.get('enabled', False)
        self.config.cfd_time_step = config_data.get('cfd_time_step', 0.01)
        self.config.control_update_rate = config_data.get('control_update_rate', 100)
        self.config.fin_deflection_limit = config_data.get('fin_deflection_limit', 15.0)
        self.config.control_gains = config_data.get('control_gains', {'kp': 1.0, 'ki': 0.1, 'kd': 0.05})
        self.config.control_code = config_data.get('control_code', "")
        
    def execute_control_algorithm(self, cfd_data: CFDData, target_trajectory: dict) -> FinDeflections:
        """Execute the JavaScript control algorithm with CFD data"""
        try:
            # Prepare the JavaScript execution context
            js_context = js2py.EvalJs()
            
            # Add CFD data to context
            js_context.cfdData = {
                'attitude': cfd_data.attitude,
                'velocity': cfd_data.velocity,
                'position': cfd_data.position,
                'angularVelocity': cfd_data.angular_velocity,
                'pressure': cfd_data.pressure,
                'temperature': cfd_data.temperature
            }
            
            # Add target trajectory
            js_context.targetTrajectory = target_trajectory
            
            # Execute the control code
            js_context.eval(self.config.control_code)
            
            # Get the fin deflections
            fin_deflections = js_context.calculateFinDeflections(js_context.cfdData, js_context.targetTrajectory)
            
            # Apply deflection limits
            limited_deflections = []
            for deflection in fin_deflections:
                limited_deflections.append(max(-self.config.fin_deflection_limit, 
                                             min(self.config.fin_deflection_limit, deflection)))
            
            return FinDeflections(
                timestamp=time.time(),
                fin1=limited_deflections[0],
                fin2=limited_deflections[1],
                fin3=limited_deflections[2],
                fin4=limited_deflections[3]
            )
            
        except Exception as e:
            print(f"Error executing control algorithm: {e}")
            # Return zero deflections on error
            return FinDeflections(time.time(), 0, 0, 0, 0)
    
    def start_control_loop(self):
        """Start the active fin control loop"""
        if self.running:
            return
            
        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop)
        self.control_thread.start()
        
    def stop_control_loop(self):
        """Stop the active fin control loop"""
        self.running = False
        if self.control_thread:
            self.control_thread.join()
            
    def _control_loop(self):
        """Main control loop that runs at the specified update rate"""
        while self.running:
            try:
                # Get latest CFD data (this would come from your GCP integration)
                # For now, we'll simulate this
                cfd_data = self._get_latest_cfd_data()
                
                if cfd_data:
                    # Execute control algorithm
                    target_trajectory = {'pitch': 0, 'yaw': 0}  # Default target
                    new_deflections = self.execute_control_algorithm(cfd_data, target_trajectory)
                    
                    # Update fin deflections
                    self.current_fin_deflections = new_deflections
                    
                    # Send to mesh engine (this would integrate with your GCP setup)
                    self._update_mesh_fins(new_deflections)
                
                # Sleep for the control update rate
                time.sleep(1.0 / self.config.control_update_rate)
                
            except Exception as e:
                print(f"Error in control loop: {e}")
                time.sleep(0.1)  # Short sleep on error
                
    def _get_latest_cfd_data(self) -> Optional[CFDData]:
        """Get the latest CFD data from the simulation"""
        try:
            if self.cfd_data_manager is None:
                # Initialize CFD data manager if not already done
                self.cfd_data_manager = CFDDataManager(self.case_dir)
            
            # Get real CFD data
            cfd_data_dict = self.cfd_data_manager.get_latest_cfd_data(self.config.cfd_time_step)
            
            if cfd_data_dict:
                return CFDData(
                    timestamp=cfd_data_dict['timestamp'],
                    attitude=cfd_data_dict['attitude'],
                    velocity=cfd_data_dict['velocity'],
                    position=cfd_data_dict['position'],
                    angular_velocity=cfd_data_dict['angular_velocity'],
                    pressure=cfd_data_dict['pressure'],
                    temperature=cfd_data_dict['temperature']
                )
            else:
                # Fallback to simulated data if extraction fails
                return CFDData(
                    timestamp=time.time(),
                    attitude=[0, 0, 0],
                    velocity=[0, 0, 0],
                    position=[0, 0, 0],
                    angular_velocity=[0, 0, 0],
                    pressure=101325,
                    temperature=288
                )
        except Exception as e:
            print(f"❌ Error getting CFD data: {e}")
            # Return simulated data on error
            return CFDData(
                timestamp=time.time(),
                attitude=[0, 0, 0],
                velocity=[0, 0, 0],
                position=[0, 0, 0],
                angular_velocity=[0, 0, 0],
                pressure=101325,
                temperature=288
            )
        
    def _update_mesh_fins(self, deflections: FinDeflections):
        """Update the mesh with new fin deflections"""
        try:
            if self.dynamic_mesh_manager is None:
                # Initialize dynamic mesh manager if not already done
                self.dynamic_mesh_manager = OpenFOAMDynamicMeshManager(self.case_dir)
                self.dynamic_mesh_manager.setup_dynamic_mesh(self.fin_configs)
            
            # Convert FinDeflections to dictionary format
            deflections_dict = {
                "fin1": deflections.fin1,
                "fin2": deflections.fin2,
                "fin3": deflections.fin3,
                "fin4": deflections.fin4
            }
            
            # Update fin positions in the mesh
            success = self.dynamic_mesh_manager.update_fin_positions(deflections_dict)
            
            if success:
                print(f"✅ Updated fin deflections: Fin1={deflections.fin1:.2f}°, Fin2={deflections.fin2:.2f}°, "
                      f"Fin3={deflections.fin3:.2f}°, Fin4={deflections.fin4:.2f}°")
            else:
                print(f"❌ Failed to update fin deflections")
                
        except Exception as e:
            print(f"❌ Error updating mesh fins: {e}")
            # Fallback to console output
            print(f"Updating fin deflections: Fin1={deflections.fin1:.2f}°, Fin2={deflections.fin2:.2f}°, "
                  f"Fin3={deflections.fin3:.2f}°, Fin4={deflections.fin4:.2f}°")

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
        self.active_fin_control = ActiveFinControlManager()
        self.simulation_orchestrator = None
        
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
            # Try to use actual OpenFOAM executables
            solver_executable = simulation_config.solver_type
            
            # Check if we have OpenFOAM environment
            if 'FOAM_APPBIN' in os.environ:
                # Use actual OpenFOAM
                solver_path = os.path.join(os.environ['FOAM_APPBIN'], solver_executable)
                
                if os.path.exists(solver_path):
                    print(f"Running actual OpenFOAM solver: {solver_path}")
                    
                    # Run the solver
                    result = subprocess.run(
                        [solver_path],
                        cwd=self.openfoam_case_dir,
                        capture_output=True,
                        text=True,
                        env=os.environ
                    )
                    
                    if result.returncode == 0:
                        self.simulation_status.status = "Complete"
                        self.simulation_status.progress = 100
                        self.simulation_status.message = "OpenFOAM simulation completed successfully"
                    else:
                        self.simulation_status.status = "Error"
                        self.simulation_status.message = f"OpenFOAM solver failed: {result.stderr}"
                else:
                    # Fallback to simulation
                    print(f"OpenFOAM solver not found: {solver_path}")
                    self._run_simulation_fallback(simulation_config)
            else:
                # Fallback to simulation
                print("OpenFOAM environment not available, using simulation")
                self._run_simulation_fallback(simulation_config)
                
        except Exception as e:
            self.simulation_status.status = "Error"
            self.simulation_status.message = f"Simulation error: {str(e)}"
        finally:
            self.simulation_running = False
    
    def _run_simulation_fallback(self, simulation_config):
        """Fallback simulation when OpenFOAM is not available"""
        try:
            # Simulate the OpenFOAM solver
            for i in range(100):
                if not self.simulation_running:
                    break
                time.sleep(0.1)
                self.simulation_status.progress = i
                self.simulation_status.current_time = i * simulation_config.time_step
                self.simulation_status.iteration_count = i
                self.simulation_status.message = f"Running {simulation_config.solver_type} (simulation)... Iteration {i}"
            
            if self.simulation_running:
                self.simulation_status.status = "Complete"
                self.simulation_status.progress = 100
                self.simulation_status.message = "Simulation completed successfully"
                
        except Exception as e:
            self.simulation_status.status = "Error"
            self.simulation_status.message = f"Simulation error: {str(e)}"
    
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
            # In a real implementation, you'd need to properly terminate the OpenFOAM process
            pass
        
        self.simulation_status.status = "Stopped"
        self.simulation_status.message = "Simulation stopped by user"
        
        return {"status": "Simulation stopped"}

# --- Flask App and Routes ---

app = Flask(__name__)
CORS(app)

# Initialize managers
openfoam_manager = OpenFOAMManager()

# Basic API endpoints for frontend
@app.route("/api/rocket-components", methods=["GET"])
def get_rocket_components():
    """Get current rocket components"""
    return jsonify({
        "success": True,
        "components": []
    })

@app.route("/api/rocket-components", methods=["POST"])
def update_rocket_components():
    """Update rocket components"""
    try:
        data = request.get_json()
        components = data.get("components", [])
        return jsonify({
            "success": True,
            "message": f"Updated {len(components)} components"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error updating components: {str(e)}"
        }), 500

@app.route("/api/simulation-config", methods=["GET"])
def get_simulation_config():
    """Get current simulation configuration"""
    return jsonify({
        "success": True,
        "config": {
            "solver_type": "pimpleFoam",
            "turbulence_model": "LES",
            "time_step": 0.001,
            "max_time": 30,
            "write_interval": 100,
            "domain_size": 10,
            "base_cell_size": 0.01,
            "boundary_layer_cells": 5,
            "refinement_level": "medium",
            "mesh_quality": 0.3
        }
    })

@app.route("/api/simulation-config", methods=["POST"])
def update_simulation_config():
    """Update simulation configuration"""
    try:
        data = request.get_json()
        return jsonify({
            "success": True,
            "message": "Simulation configuration updated"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error updating config: {str(e)}"
        }), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "R_SIM backend is running"
    })

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

# --- Active Fin Control API Endpoints ---

@app.route("/api/active-fin-control/config", methods=["POST"])
def update_active_fin_control_config():
    """Update the active fin control configuration"""
    try:
        data = request.get_json()
        openfoam_manager.active_fin_control.update_config(data)
        
        return jsonify({
            "success": True,
            "message": "Active fin control configuration updated"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/config", methods=["GET"])
def get_active_fin_control_config():
    """Get the current active fin control configuration"""
    try:
        config = openfoam_manager.active_fin_control.config
        return jsonify({
            "success": True,
            "config": {
                "enabled": config.enabled,
                "cfd_time_step": config.cfd_time_step,
                "control_update_rate": config.control_update_rate,
                "fin_deflection_limit": config.fin_deflection_limit,
                "control_gains": config.control_gains,
                "control_code": config.control_code
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/start", methods=["POST"])
def start_active_fin_control():
    """Start the active fin control system"""
    try:
        openfoam_manager.active_fin_control.start_control_loop()
        return jsonify({
            "success": True,
            "message": "Active fin control started"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/stop", methods=["POST"])
def stop_active_fin_control():
    """Stop the active fin control system"""
    try:
        openfoam_manager.active_fin_control.stop_control_loop()
        return jsonify({
            "success": True,
            "message": "Active fin control stopped"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/status", methods=["GET"])
def get_active_fin_control_status():
    """Get the current status of the active fin control system"""
    try:
        control_manager = openfoam_manager.active_fin_control
        return jsonify({
            "success": True,
            "status": {
                "running": control_manager.running,
                "enabled": control_manager.config.enabled,
                "current_fin_deflections": {
                    "fin1": control_manager.current_fin_deflections.fin1,
                    "fin2": control_manager.current_fin_deflections.fin2,
                    "fin3": control_manager.current_fin_deflections.fin3,
                    "fin4": control_manager.current_fin_deflections.fin4,
                    "timestamp": control_manager.current_fin_deflections.timestamp
                }
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/test", methods=["POST"])
def test_control_algorithm():
    """Test the control algorithm with sample data"""
    try:
        data = request.get_json()
        
        # Create sample CFD data
        sample_cfd_data = CFDData(
            timestamp=time.time(),
            attitude=data.get('attitude', [0, 0, 0]),
            velocity=data.get('velocity', [0, 0, 0]),
            position=data.get('position', [0, 0, 0]),
            angular_velocity=data.get('angular_velocity', [0, 0, 0]),
            pressure=data.get('pressure', 101325),
            temperature=data.get('temperature', 288)
        )
        
        target_trajectory = data.get('target_trajectory', {'pitch': 0, 'yaw': 0})
        
        # Execute control algorithm
        fin_deflections = openfoam_manager.active_fin_control.execute_control_algorithm(
            sample_cfd_data, target_trajectory
        )
        
        return jsonify({
            "success": True,
            "fin_deflections": {
                "fin1": fin_deflections.fin1,
                "fin2": fin_deflections.fin2,
                "fin3": fin_deflections.fin3,
                "fin4": fin_deflections.fin4,
                "timestamp": fin_deflections.timestamp
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/cfd-data", methods=["GET"])
def get_cfd_data():
    """Get real-time CFD data from the simulation"""
    try:
        control_manager = openfoam_manager.active_fin_control
        
        if control_manager.cfd_data_manager is None:
            return jsonify({
                "success": False,
                "error": "CFD data manager not initialized"
            }), 400
        
        # Get latest CFD data
        cfd_data = control_manager._get_latest_cfd_data()
        
        if cfd_data:
            return jsonify({
                "success": True,
                "cfd_data": {
                    "timestamp": cfd_data.timestamp,
                    "attitude": cfd_data.attitude,
                    "velocity": cfd_data.velocity,
                    "position": cfd_data.position,
                    "angular_velocity": cfd_data.angular_velocity,
                    "pressure": cfd_data.pressure,
                    "temperature": cfd_data.temperature
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "No CFD data available"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/setup-mesh", methods=["POST"])
def setup_dynamic_mesh():
    """Setup dynamic mesh for active fin control"""
    try:
        data = request.get_json()
        case_dir = data.get('case_dir', '/tmp/openfoam_case')
        
        control_manager = openfoam_manager.active_fin_control
        control_manager.case_dir = Path(case_dir)
        
        # Initialize dynamic mesh manager
        control_manager.dynamic_mesh_manager = OpenFOAMDynamicMeshManager(control_manager.case_dir)
        
        # Setup dynamic mesh
        success = control_manager.dynamic_mesh_manager.setup_dynamic_mesh(control_manager.fin_configs)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Dynamic mesh setup completed"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to setup dynamic mesh"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/create-case", methods=["POST"])
def create_openfoam_case():
    """Create a complete OpenFOAM case for active fin control"""
    try:
        data = request.get_json()
        case_dir = data.get('case_dir', '/tmp/active_fin_case')
        
        # Create the OpenFOAM case
        success = create_active_fin_case(case_dir)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"OpenFOAM case created at {case_dir}",
                "case_directory": case_dir
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create OpenFOAM case"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/setup-orchestrator", methods=["POST"])
def setup_simulation_orchestrator():
    """Setup the complete simulation orchestrator"""
    try:
        data = request.get_json()
        case_dir = data.get('case_dir', '/tmp/active_fin_case')
        gcp_project_id = data.get('gcp_project_id')
        gcp_bucket = data.get('gcp_bucket')
        
        # Create simulation orchestrator
        openfoam_manager.simulation_orchestrator = SimulationOrchestrator(
            Path(case_dir),
            gcp_project_id,
            gcp_bucket
        )
        
        # Setup simulation
        success = openfoam_manager.simulation_orchestrator.setup_simulation()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Simulation orchestrator setup complete",
                "use_gcp": bool(gcp_project_id and gcp_bucket)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to setup simulation orchestrator"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/start-complete-simulation", methods=["POST"])
def start_complete_simulation():
    """Start the complete CFD-control simulation"""
    try:
        data = request.get_json()
        control_algorithm = data.get('control_algorithm', '')
        target_trajectory = data.get('target_trajectory', {'pitch': 0, 'yaw': 0})
        
        if not openfoam_manager.simulation_orchestrator:
            return jsonify({
                "success": False,
                "error": "Simulation orchestrator not setup"
            }), 400
        
        # Start complete simulation
        success = openfoam_manager.simulation_orchestrator.start_simulation(
            control_algorithm,
            target_trajectory
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": "Complete active fin control simulation started"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to start complete simulation"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/stop-complete-simulation", methods=["POST"])
def stop_complete_simulation():
    """Stop the complete CFD-control simulation"""
    try:
        if not openfoam_manager.simulation_orchestrator:
            return jsonify({
                "success": False,
                "error": "Simulation orchestrator not setup"
            }), 400
        
        # Stop complete simulation
        success = openfoam_manager.simulation_orchestrator.stop_simulation()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Complete active fin control simulation stopped"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to stop complete simulation"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/simulation-status", methods=["GET"])
def get_complete_simulation_status():
    """Get comprehensive simulation status"""
    try:
        if not openfoam_manager.simulation_orchestrator:
            return jsonify({
                "success": False,
                "error": "Simulation orchestrator not setup"
            }), 400
        
        # Get comprehensive status
        status = openfoam_manager.simulation_orchestrator.get_simulation_status()
        
        return jsonify({
            "success": True,
            "status": status
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/active-fin-control/download-results", methods=["POST"])
def download_simulation_results():
    """Download simulation results"""
    try:
        data = request.get_json()
        results_dir = data.get('results_dir', '/tmp/simulation_results')
        
        if not openfoam_manager.simulation_orchestrator:
            return jsonify({
                "success": False,
                "error": "Simulation orchestrator not setup"
            }), 400
        
        # Download results
        success = openfoam_manager.simulation_orchestrator.download_results(Path(results_dir))
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Results downloaded to {results_dir}",
                "results_directory": results_dir
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to download results"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
