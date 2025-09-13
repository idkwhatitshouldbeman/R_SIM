"""
OpenFOAM Case Generator for Active Fin Control
Creates complete OpenFOAM case directories with all necessary files
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

class OpenFOAMCaseGenerator:
    """Generates complete OpenFOAM cases for active fin control"""
    
    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)
        
    def generate_complete_case(self, case_config: Dict) -> bool:
        """Generate a complete OpenFOAM case"""
        try:
            print(f"🏗️ Generating OpenFOAM case in {self.case_dir}")
            
            # Create directory structure
            self._create_directory_structure()
            
            # Generate system files
            self._generate_system_files(case_config)
            
            # Generate 0 directory files
            self._generate_initial_conditions(case_config)
            
            # Generate constant directory files
            self._generate_constant_files(case_config)
            
            # Copy dynamic mesh configurations
            self._copy_dynamic_mesh_configs()
            
            # Generate mesh (placeholder)
            self._generate_mesh_placeholder()
            
            print("✅ OpenFOAM case generation complete")
            return True
            
        except Exception as e:
            print(f"❌ Error generating OpenFOAM case: {e}")
            return False
    
    def _create_directory_structure(self):
        """Create the standard OpenFOAM directory structure"""
        directories = [
            "system",
            "0", 
            "constant",
            "constant/triSurface",
            "constant/polyMesh",
            "postProcessing"
        ]
        
        for directory in directories:
            (self.case_dir / directory).mkdir(parents=True, exist_ok=True)
    
    def _generate_system_files(self, config: Dict):
        """Generate system directory files"""
        
        # controlDict
        control_dict = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
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

application     pimpleFoam;

startFrom       startTime;

startTime       0;

stopAt          endTime;

endTime         {config.get('endTime', 10)};

deltaT          {config.get('deltaT', 0.001)};

writeControl    timeStep;

writeInterval   {config.get('writeInterval', 100)};

purgeWrite      2;

writeFormat     ascii;

writePrecision  6;

writeCompression off;

timeFormat      general;

timePrecision   6;

runTimeModifiable true;

// Functions for real-time data extraction
functions
{{
    // Extract forces and moments on fins
    finForces
    {{
        type            forces;
        libs            ("libforces.so");
        patches         (fin1 fin2 fin3 fin4);
        rho             rhoInf;
        rhoInf          {config.get('rhoInf', 1.225)};
        CofR            (0 0 0);
        writeControl    timeStep;
        writeInterval   1;
    }}
    
    // Extract pressure field
    pressureField
    {{
        type            fieldMinMax;
        libs            ("libfieldFunctionObjects.so");
        fields          (p);
        writeControl    timeStep;
        writeInterval   1;
    }}
    
    // Extract velocity field
    velocityField
    {{
        type            fieldMinMax;
        libs            ("libfieldFunctionObjects.so");
        fields          (U);
        writeControl    timeStep;
        writeInterval   1;
    }}
}}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"""
        
        (self.case_dir / "system" / "controlDict").write_text(control_dict)
        
        # fvSchemes
        fv_schemes = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSchemes;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

ddtSchemes
{
    default         Euler;
}

gradSchemes
{
    default         Gauss linear;
}

divSchemes
{
    default         none;
    div(phi,U)      Gauss linearUpwind grad(U);
    div(phi,k)      Gauss linearUpwind grad(k);
    div(phi,epsilon) Gauss linearUpwind grad(epsilon);
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear corrected;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         corrected;
}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"""
        
        (self.case_dir / "system" / "fvSchemes").write_text(fv_schemes)
        
        # fvSolution
        fv_solution = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSolution;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

solvers
{
    p
    {
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
    }

    pFinal
    {
        $p;
        tolerance       1e-08;
        relTol          0;
    }

    "(U|k|epsilon)"
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-06;
        relTol          0;
    }
}

PIMPLE
{
    nCorrectors     2;
    nNonOrthogonalCorrectors 0;
    pRefCell        0;
    pRefValue       0;
}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"""
        
        (self.case_dir / "system" / "fvSolution").write_text(fv_solution)
    
    def _generate_initial_conditions(self, config: Dict):
        """Generate 0 directory files"""
        
        # U (velocity)
        U_file = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volVectorField;
    location    "0";
    object      U;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{{
    inlet
    {{
        type            fixedValue;
        value           uniform ({config.get('inletVelocity', 0)} 0 0);
    }}
    
    outlet
    {{
        type            zeroGradient;
    }}
    
    rocketBody
    {{
        type            noSlip;
    }}
    
    fin1
    {{
        type            noSlip;
    }}
    
    fin2
    {{
        type            noSlip;
    }}
    
    fin3
    {{
        type            noSlip;
    }}
    
    fin4
    {{
        type            noSlip;
    }}
    
    symmetry
    {{
        type            symmetry;
    }}
    
    frontAndBack
    {{
        type            empty;
    }}
}}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"""
        
        (self.case_dir / "0" / "U").write_text(U_file)
        
        # p (pressure)
        p_file = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      p;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform {config.get('pressure', 0)};

boundaryField
{{
    inlet
    {{
        type            zeroGradient;
    }}
    
    outlet
    {{
        type            fixedValue;
        value           uniform {config.get('pressure', 0)};
    }}
    
    rocketBody
    {{
        type            zeroGradient;
    }}
    
    fin1
    {{
        type            zeroGradient;
    }}
    
    fin2
    {{
        type            zeroGradient;
    }}
    
    fin3
    {{
        type            zeroGradient;
    }}
    
    fin4
    {{
        type            zeroGradient;
    }}
    
    symmetry
    {{
        type            symmetry;
    }}
    
    frontAndBack
    {{
        type            empty;
    }}
}}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"""
        
        (self.case_dir / "0" / "p").write_text(p_file)
        
        # k (turbulence kinetic energy)
        k_file = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      k;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0.1;

boundaryField
{
    inlet
    {
        type            fixedValue;
        value           uniform 0.1;
    }
    
    outlet
    {
        type            zeroGradient;
    }
    
    rocketBody
    {
        type            kqRWallFunction;
        value           uniform 0.1;
    }
    
    fin1
    {
        type            kqRWallFunction;
        value           uniform 0.1;
    }
    
    fin2
    {
        type            kqRWallFunction;
        value           uniform 0.1;
    }
    
    fin3
    {
        type            kqRWallFunction;
        value           uniform 0.1;
    }
    
    fin4
    {
        type            kqRWallFunction;
        value           uniform 0.1;
    }
    
    symmetry
    {
        type            symmetry;
    }
    
    frontAndBack
    {
        type            empty;
    }
}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"""
        
        (self.case_dir / "0" / "k").write_text(k_file)
        
        # epsilon (turbulence dissipation rate)
        epsilon_file = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      epsilon;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -3 0 0 0 0];

internalField   uniform 0.1;

boundaryField
{
    inlet
    {
        type            fixedValue;
        value           uniform 0.1;
    }
    
    outlet
    {
        type            zeroGradient;
    }
    
    rocketBody
    {
        type            epsilonWallFunction;
        value           uniform 0.1;
    }
    
    fin1
    {
        type            epsilonWallFunction;
        value           uniform 0.1;
    }
    
    fin2
    {
        type            epsilonWallFunction;
        value           uniform 0.1;
    }
    
    fin3
    {
        type            epsilonWallFunction;
        value           uniform 0.1;
    }
    
    fin4
    {
        type            epsilonWallFunction;
        value           uniform 0.1;
    }
    
    symmetry
    {
        type            symmetry;
    }
    
    frontAndBack
    {
        type            empty;
    }
}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"""
        
        (self.case_dir / "0" / "epsilon").write_text(epsilon_file)
    
    def _generate_constant_files(self, config: Dict):
        """Generate constant directory files"""
        
        # transportProperties
        transport_properties = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      transportProperties;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

transportModel  Newtonian;

nu              [0 2 -1 0 0 0 0] {config.get('nu', 1.5e-05)};

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"""
        
        (self.case_dir / "constant" / "transportProperties").write_text(transport_properties)
        
        # turbulenceProperties
        turbulence_properties = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2212                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      turbulenceProperties;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

simulationType  RAS;

RAS
{
    RASModel        kEpsilon;
    turbulence      on;
    printCoeffs     on;
}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"""
        
        (self.case_dir / "constant" / "turbulenceProperties").write_text(turbulence_properties)
    
    def _copy_dynamic_mesh_configs(self):
        """Copy dynamic mesh configuration files"""
        config_dir = Path(__file__).parent / "openfoam_configs"
        
        # Copy dynamicMeshDict
        src = config_dir / "dynamicMeshDict"
        dst = self.case_dir / "system" / "dynamicMeshDict"
        if src.exists():
            dst.write_text(src.read_text())
        
        # Copy pointDisplacement
        src = config_dir / "pointDisplacement"
        dst = self.case_dir / "0" / "pointDisplacement"
        if src.exists():
            dst.write_text(src.read_text())
    
    def _generate_mesh_placeholder(self):
        """Generate a placeholder mesh file"""
        mesh_info = """# OpenFOAM Mesh Placeholder

This directory should contain the mesh files:
- points
- faces  
- owner
- neighbour
- boundary

To generate a real mesh, use blockMesh or snappyHexMesh.

For active fin control, the mesh should include:
- fin1, fin2, fin3, fin4 boundary patches
- rocketBody boundary patch
- inlet and outlet boundary patches
- symmetry boundary patches
"""
        
        (self.case_dir / "constant" / "polyMesh" / "README.md").write_text(mesh_info)

# Factory functions
def create_openfoam_case(case_dir: str, config: Dict = None) -> bool:
    """Create a complete OpenFOAM case"""
    if config is None:
        config = {
            'endTime': 10,
            'deltaT': 0.001,
            'writeInterval': 100,
            'rhoInf': 1.225,
            'inletVelocity': 0,
            'pressure': 0,
            'nu': 1.5e-05
        }
    
    generator = OpenFOAMCaseGenerator(Path(case_dir))
    return generator.generate_complete_case(config)

def create_active_fin_case(case_dir: str) -> bool:
    """Create an OpenFOAM case specifically for active fin control"""
    config = {
        'endTime': 30,
        'deltaT': 0.01,
        'writeInterval': 10,
        'rhoInf': 1.225,
        'inletVelocity': 0,
        'pressure': 0,
        'nu': 1.5e-05
    }
    
    return create_openfoam_case(case_dir, config)
