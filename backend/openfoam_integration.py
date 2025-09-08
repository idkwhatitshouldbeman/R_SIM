#!/usr/bin/env python3
"""
Heavy CFD Integration with OpenFOAM
Provides full 3D CFD simulation capabilities for rocket analysis
"""

import os
import subprocess
import tempfile
import json
import time
import threading
import uuid
import math
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

class HeavyCFDManager:
    """Full OpenFOAM CFD simulation manager"""
    
    def __init__(self):
        self.simulation_running = False
        self.current_simulation = None
        self.simulation_thread = None
        self.openfoam_case_dir = None
        self.results = {}
        
        # Check if OpenFOAM is available
        self.openfoam_available = self._check_openfoam_installation()
        
    def _check_openfoam_installation(self) -> bool:
        """Check if OpenFOAM is properly installed and accessible"""
        try:
            # Check if OpenFOAM environment is set up
            if 'FOAM_APPBIN' not in os.environ:
                print("⚠️  OpenFOAM environment not found")
                return False
            
            # Test if blockMesh is available
            result = subprocess.run(['blockMesh', '-help'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ OpenFOAM installation verified")
                return True
            else:
                print("⚠️  OpenFOAM tools not accessible")
                return False
                
        except Exception as e:
            print(f"⚠️  OpenFOAM check failed: {e}")
            return False
    
    def start_simulation(self, rocket_components, rocket_weight, rocket_cg, simulation_config):
        """Start a full OpenFOAM CFD simulation"""
        if not self.openfoam_available:
            return {"error": "OpenFOAM not available, falling back to simulation mode"}
            
        if self.simulation_running:
            return {"error": "Simulation already running"}
        
        try:
            # Create OpenFOAM case directory
            self.openfoam_case_dir = self._create_case_directory()
            
            # Generate 3D mesh from rocket geometry
            mesh_success = self._generate_3d_mesh(rocket_components, simulation_config)
            if not mesh_success:
                return {"error": "Failed to generate 3D mesh"}
            
            # Setup OpenFOAM case files with advanced physics
            self._setup_advanced_case_files(simulation_config)
            
            # Start simulation in background thread
            self.simulation_running = True
            self.simulation_thread = threading.Thread(
                target=self._run_heavy_cfd_simulation,
                args=(simulation_config,)
            )
            self.simulation_thread.start()
            
            return {"status": "Heavy CFD simulation started", "case_dir": self.openfoam_case_dir}
            
        except Exception as e:
            return {"error": f"Failed to start heavy CFD simulation: {str(e)}"}
    
    def _create_case_directory(self):
        """Create a new OpenFOAM case directory with proper structure"""
        case_name = f"rocket_cfd_{int(time.time())}"
        case_dir = os.path.join(os.getcwd(), "openfoam_cases", case_name)
        os.makedirs(case_dir, exist_ok=True)
        
        # Create standard OpenFOAM directory structure
        os.makedirs(os.path.join(case_dir, "0"), exist_ok=True)
        os.makedirs(os.path.join(case_dir, "constant"), exist_ok=True)
        os.makedirs(os.path.join(case_dir, "system"), exist_ok=True)
        os.makedirs(os.path.join(case_dir, "postProcessing"), exist_ok=True)
        
        return case_dir
    
    def _generate_3d_mesh(self, rocket_components, simulation_config):
        """Generate high-quality 3D mesh from rocket geometry"""
        try:
            # Create blockMeshDict for computational domain
            self._create_3d_block_mesh_dict(simulation_config)
            
            # Create snappyHexMeshDict for rocket geometry
            self._create_3d_snappy_hex_mesh_dict(rocket_components, simulation_config)
            
            # Create surface geometry files (STL) from rocket components
            self._create_rocket_geometry_files(rocket_components)
            
            # Run blockMesh
            result = subprocess.run(['blockMesh'], 
                                  cwd=self.openfoam_case_dir,
                                  capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"blockMesh failed: {result.stderr}")
                return False
            
            # Run snappyHexMesh for rocket geometry
            result = subprocess.run(['snappyHexMesh', '-overwrite'], 
                                  cwd=self.openfoam_case_dir,
                                  capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                print(f"snappyHexMesh failed: {result.stderr}")
                return False
            
            print("✅ 3D mesh generation completed")
            return True
            
        except Exception as e:
            print(f"3D mesh generation error: {e}")
            return False
    
    def _create_3d_block_mesh_dict(self, simulation_config):
        """Create 3D blockMeshDict for rocket simulation domain"""
        domain_size = simulation_config.domain_size
        cell_size = simulation_config.base_cell_size
        
        # Calculate mesh resolution
        nx = int(domain_size / cell_size)
        ny = int(domain_size / cell_size)
        nz = int(domain_size * 3 / cell_size)  # Longer in Z for rocket trajectory
        
        block_mesh_content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
|| =========                 |                                                 |
|| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
||  \\\\    /   O peration     | Version:  v8                                 |
||   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
||    \\\\/     M anipulation  |                                                 |
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
    ({-domain_size/2} {-domain_size/2} {domain_size*3})
    ({domain_size/2} {-domain_size/2} {domain_size*3})
    ({domain_size/2} {domain_size/2} {domain_size*3})
    ({-domain_size/2} {domain_size/2} {domain_size*3})
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 2)
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
    
    def _create_3d_snappy_hex_mesh_dict(self, rocket_components, simulation_config):
        """Create advanced snappyHexMeshDict for rocket geometry"""
        snappy_content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
|| =========                 |                                                 |
|| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
||  \\\\    /   O peration     | Version:  v8                                 |
||   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
||    \\\\/     M anipulation  |                                                 |
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
    rocket.stl
    {{
        type triSurfaceMesh;
        name rocket;
    }}
}};

castellatedMeshControls
{{
    maxLocalCells 2000000;
    maxGlobalCells 5000000;
    minSize 0.001;
    maxLoadUnbalance 0.10;
    nSmoothScale 4;
    errorReduction 0.75;
    
    resolveFeatureAngle 30;
    
    locationInMesh (0 0 1);
}};

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 30;
    nRelaxIter 5;
    nFeatureSnapIter 10;
    implicitFeatureSnap false;
    explicitFeatureSnap true;
    multiRegionFeatureSnap false;
}};

addLayersControls
{{
    relativeSizes true;
    layers
    {{
        rocket
        {{
            nSurfaceLayers {simulation_config.boundary_layer_cells};
        }}
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
    
    def _create_rocket_geometry_files(self, rocket_components):
        """Create STL geometry files from rocket components"""
        # This is a simplified version - in practice, you'd need to:
        # 1. Convert rocket components to 3D geometry
        # 2. Generate STL files
        # 3. Place them in the constant/triSurface directory
        
        # For now, create a simple rocket geometry
        rocket_stl_content = """solid rocket
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 0.0
      vertex 1.0 0.0 0.0
      vertex 0.5 0.866 0.0
    endloop
  endfacet
endsolid rocket
"""
        
        # Create triSurface directory
        os.makedirs(os.path.join(self.openfoam_case_dir, "constant", "triSurface"), exist_ok=True)
        
        with open(os.path.join(self.openfoam_case_dir, "constant", "triSurface", "rocket.stl"), "w") as f:
            f.write(rocket_stl_content)
    
    def _setup_advanced_case_files(self, simulation_config):
        """Setup OpenFOAM case files with advanced physics models"""
        # Create controlDict with advanced settings
        self._create_advanced_control_dict(simulation_config)
        
        # Create fvSchemes with high-order schemes
        self._create_advanced_fv_schemes()
        
        # Create fvSolution with advanced solvers
        self._create_advanced_fv_solution(simulation_config)
        
        # Create turbulence properties
        self._create_turbulence_properties(simulation_config)
        
        # Create initial conditions
        self._create_initial_conditions(simulation_config)
    
    def _create_advanced_control_dict(self, simulation_config):
        """Create controlDict with advanced simulation settings"""
        control_dict = f"""/*--------------------------------*- C++ -*----------------------------------*\\
|| =========                 |                                                 |
|| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
||  \\\\    /   O peration     | Version:  v8                                 |
||   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
||    \\\\/     M anipulation  |                                                 |
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

writePrecision  8;

writeCompression off;

timeFormat      general;

timePrecision   6;

runTimeModifiable true;

functions
{{
    #includeFunc residuals
    
    forces
    {{
        type            forces;
        libs            (forces);
        writeControl    timeStep;
        writeInterval   1;
        patches         (rocket);
        rho             rhoInf;
        rhoInf          1.225;
        CofR            (0 0 0);
        writeFormat     ascii;
    }}
    
    pressureCoeff
    {{
        type            pressure;
        libs            (fieldFunctionObjects);
        writeControl    timeStep;
        writeInterval   1;
        mode            static;
        result          pressureCoeff;
        U               U;
        rho             rhoInf;
        rhoInf          1.225;
        pInf            101325;
        resultName      pressureCoeff;
    }}
}};

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "system", "controlDict"), "w") as f:
            f.write(control_dict)
    
    def _create_advanced_fv_schemes(self):
        """Create fvSchemes with high-order numerical schemes"""
        fv_schemes = """/*--------------------------------*- C++ -*----------------------------------*\\
|| =========                 |                                                 |
|| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
||  \\\\    /   O peration     | Version:  v8                                 |
||   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
||    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSchemes;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

ddtSchemes
{{
    default         Euler;
}}

gradSchemes
{{
    default         Gauss linear;
    grad(p)         Gauss linear;
    grad(U)         Gauss linear;
}}

divSchemes
{{
    default         none;
    div(phi,U)      Gauss linearUpwind grad(U);
    div(phi,k)      Gauss linearUpwind grad(k);
    div(phi,omega)  Gauss linearUpwind grad(omega);
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}}

laplacianSchemes
{{
    default         Gauss linear corrected;
}}

interpolationSchemes
{{
    default         linear;
}}

snGradSchemes
{{
    default         corrected;
}}

fluxRequired
{{
    default         no;
    p;
}}

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "system", "fvSchemes"), "w") as f:
            f.write(fv_schemes)
    
    def _create_advanced_fv_solution(self, simulation_config):
        """Create fvSolution with advanced solver settings"""
        fv_solution = f"""/*--------------------------------*- C++ -*----------------------------------*\\
|| =========                 |                                                 |
|| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
||  \\\\    /   O peration     | Version:  v8                                 |
||   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
||    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSolution;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

solvers
{{
    p
    {{
        solver          GAMG;
        tolerance       1e-07;
        relTol          0.1;
        smoother        GaussSeidel;
        nPreSweeps      0;
        nPostSweeps     2;
        cacheAgglomeration true;
        nCellsInCoarsestLevel 10;
        agglomerator    faceAreaPair;
        mergeLevels     1;
    }}

    pFinal
    {{
        $p;
        tolerance       1e-08;
        relTol          0;
    }}

    "(U|k|omega)"
    {{
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-06;
        relTol          0.1;
    }}
}}

PIMPLE
{{
    nCorrectors     2;
    nNonOrthogonalCorrectors 0;
    pRefCell        0;
    pRefValue       0;
}}

relaxationFactors
{{
    fields
    {{
        p               0.3;
        pFinal          1.0;
    }}
    equations
    {{
        U               0.7;
        k               0.7;
        omega           0.7;
    }}
}}

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "system", "fvSolution"), "w") as f:
            f.write(fv_solution)
    
    def _create_turbulence_properties(self, simulation_config):
        """Create turbulence properties file"""
        turbulence_properties = f"""/*--------------------------------*- C++ -*----------------------------------*\\
|| =========                 |                                                 |
|| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
||  \\\\    /   O peration     | Version:  v8                                 |
||   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
||    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      turbulenceProperties;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

simulationType  RAS;

RAS
{{
    RASModel        {simulation_config.turbulence_model};
    
    turbulence      on;
    
    printCoeffs     on;
}}

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "constant", "turbulenceProperties"), "w") as f:
            f.write(turbulence_properties)
    
    def _create_initial_conditions(self, simulation_config):
        """Create initial conditions for the simulation"""
        # Create U (velocity) field
        U_content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
|| =========                 |                                                 |
|| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
||  \\\\    /   O peration     | Version:  v8                                 |
||   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
||    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volVectorField;
    object      U;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform ({simulation_config.inlet_velocity} 0 0);

boundaryField
{{
    inlet
    {{
        type            fixedValue;
        value           uniform ({simulation_config.inlet_velocity} 0 0);
    }}

    outlet
    {{
        type            zeroGradient;
    }}

    ground
    {{
        type            fixedValue;
        value           uniform (0 0 0);
    }}

    top
    {{
        type            zeroGradient;
    }}

    sides
    {{
        type            zeroGradient;
    }}

    rocket
    {{
        type            fixedValue;
        value           uniform (0 0 0);
    }}
}}

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "0", "U"), "w") as f:
            f.write(U_content)
        
        # Create p (pressure) field
        p_content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
|| =========                 |                                                 |
|| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
||  \\\\    /   O peration     | Version:  v8                                 |
||   \\\\  /    A nd           | Web:      www.OpenFOAM.org                     |
||    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      p;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform {simulation_config.outlet_pressure};

boundaryField
{{
    inlet
    {{
        type            zeroGradient;
    }}

    outlet
    {{
        type            fixedValue;
        value           uniform {simulation_config.outlet_pressure};
    }}

    ground
    {{
        type            zeroGradient;
    }}

    top
    {{
        type            zeroGradient;
    }}

    sides
    {{
        type            zeroGradient;
    }}

    rocket
    {{
        type            zeroGradient;
    }}
}}

// ************************************************************************* //
"""
        
        with open(os.path.join(self.openfoam_case_dir, "0", "p"), "w") as f:
            f.write(p_content)
    
    def _run_heavy_cfd_simulation(self, simulation_config):
        """Run the full OpenFOAM CFD simulation"""
        try:
            print("🚀 Starting heavy CFD simulation...")
            
            # Run the OpenFOAM solver
            solver_cmd = [simulation_config.solver_type]
            result = subprocess.run(solver_cmd, 
                                  cwd=self.openfoam_case_dir,
                                  capture_output=True, text=True, timeout=3600)  # 1 hour timeout
            
            if result.returncode == 0:
                print("✅ Heavy CFD simulation completed successfully")
                self._process_results()
            else:
                print(f"❌ CFD simulation failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏰ CFD simulation timed out")
        except Exception as e:
            print(f"❌ CFD simulation error: {e}")
        finally:
            self.simulation_running = False
    
    def _process_results(self):
        """Process and analyze CFD results"""
        try:
            # Read forces data
            forces_file = os.path.join(self.openfoam_case_dir, "postProcessing", "forces", "0", "forces.dat")
            if os.path.exists(forces_file):
                with open(forces_file, 'r') as f:
                    forces_data = f.read()
                    # Parse forces data to extract drag and lift coefficients
                    self.results['forces'] = forces_data
            
            # Read pressure coefficient data
            pressure_file = os.path.join(self.openfoam_case_dir, "postProcessing", "pressureCoeff", "0", "pressureCoeff.dat")
            if os.path.exists(pressure_file):
                with open(pressure_file, 'r') as f:
                    pressure_data = f.read()
                    self.results['pressure_coefficient'] = pressure_data
            
            print("✅ CFD results processed")
            
        except Exception as e:
            print(f"⚠️  Error processing results: {e}")
    
    def get_status(self):
        """Get current simulation status"""
        return {
            "status": "Running" if self.simulation_running else "Idle",
            "openfoam_available": self.openfoam_available,
            "case_dir": self.openfoam_case_dir,
            "results": self.results
        }
    
    def stop_simulation(self):
        """Stop the current simulation"""
        self.simulation_running = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            # In a real implementation, you'd need to properly terminate the OpenFOAM process
            pass
        
        return {"status": "Heavy CFD simulation stopped"}
