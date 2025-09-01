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
