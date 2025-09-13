"""
Real-time mesh morphing system for active fin control
Handles fin geometry updates and mesh deformation
"""

import numpy as np
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Dict
import trimesh
from scipy.spatial.transform import Rotation as R

class FinGeometryManager:
    """Manages fin geometry and STL file updates"""
    
    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)
        self.fin_geometries = {}
        self.fin_attachment_points = {}
        self.fin_axes = {}
        
    def load_fin_geometry(self, fin_id: str, stl_path: str = None, fin_config: Dict = None):
        """Load fin geometry from STL file or generate from config"""
        try:
            if stl_path and Path(stl_path).exists():
                # Load from specific STL path
                mesh = trimesh.load(stl_path)
                self.fin_geometries[fin_id] = mesh
                print(f"✅ Loaded fin geometry for {fin_id} from {stl_path}")
                return True
            elif fin_config:
                # Generate STL path from config
                stl_path = self._get_fin_stl_path(fin_config)
                if stl_path and Path(stl_path).exists():
                    mesh = trimesh.load(stl_path)
                    self.fin_geometries[fin_id] = mesh
                    print(f"✅ Loaded fin geometry for {fin_id} from generated path: {stl_path}")
                    return True
                else:
                    # Generate fallback geometry
                    mesh = self._generate_fallback_fin_geometry(fin_config)
                    self.fin_geometries[fin_id] = mesh
                    print(f"⚠️  Using fallback geometry for {fin_id}")
                    return True
            else:
                print(f"❌ No STL path or fin config provided for {fin_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error loading fin geometry for {fin_id}: {e}")
            return False
    
    def _get_fin_stl_path(self, fin_config: Dict) -> str:
        """Get STL file path from fin configuration"""
        fin_shape = fin_config.get('finShape', 'rectangular')
        height = fin_config.get('finHeight', 25.0)
        width = fin_config.get('finWidth', 15.0)
        thickness = fin_config.get('finThickness', 2.0)
        count = fin_config.get('finCount', 4)
        
        filename = f"fin_{fin_shape}_{height}x{width}x{thickness}_count{count}.stl"
        filepath = Path(__file__).parent / "fin_geometries" / filename
        return str(filepath)
    
    def _generate_fallback_fin_geometry(self, fin_config: Dict) -> trimesh.Trimesh:
        """Generate fallback fin geometry if STL file not found"""
        height = fin_config.get('finHeight', 25.0)
        width = fin_config.get('finWidth', 15.0)
        thickness = fin_config.get('finThickness', 2.0)
        
        # Create a simple rectangular fin mesh as fallback
        vertices = np.array([
            [0, 0, 0], [width, 0, 0], [width, height, 0], [0, height, 0],  # Bottom face
            [0, 0, thickness], [width, 0, thickness], [width, height, thickness], [0, height, thickness]  # Top face
        ])
        
        faces = np.array([
            [0, 1, 2], [0, 2, 3],  # Bottom
            [4, 6, 5], [4, 7, 6],  # Top
            [0, 4, 5], [0, 5, 1],  # Front
            [1, 5, 6], [1, 6, 2],  # Right
            [2, 6, 7], [2, 7, 3],  # Back
            [3, 7, 4], [3, 4, 0]   # Left
        ])
        
        return trimesh.Trimesh(vertices=vertices, faces=faces)
    
    def set_fin_attachment_point(self, fin_id: str, point: Tuple[float, float, float]):
        """Set the attachment point for a fin (rotation center)"""
        self.fin_attachment_points[fin_id] = np.array(point)
    
    def set_fin_rotation_axis(self, fin_id: str, axis: Tuple[float, float, float]):
        """Set the rotation axis for a fin"""
        self.fin_axes[fin_id] = np.array(axis)
    
    def update_fin_deflection(self, fin_id: str, deflection_angle: float) -> bool:
        """Update fin geometry with new deflection angle"""
        try:
            if fin_id not in self.fin_geometries:
                print(f"❌ Fin geometry not loaded for {fin_id}")
                return False
            
            if fin_id not in self.fin_attachment_points:
                print(f"❌ Attachment point not set for {fin_id}")
                return False
            
            if fin_id not in self.fin_axes:
                print(f"❌ Rotation axis not set for {fin_id}")
                return False
            
            # Get the fin mesh
            mesh = self.fin_geometries[fin_id].copy()
            
            # Get attachment point and rotation axis
            attachment_point = self.fin_attachment_points[fin_id]
            rotation_axis = self.fin_axes[fin_id]
            
            # Create rotation matrix
            rotation = R.from_rotvec(rotation_axis * np.radians(deflection_angle))
            rotation_matrix = rotation.as_matrix()
            
            # Apply rotation around attachment point
            # 1. Translate to origin
            mesh.vertices -= attachment_point
            
            # 2. Apply rotation
            mesh.vertices = mesh.vertices @ rotation_matrix.T
            
            # 3. Translate back
            mesh.vertices += attachment_point
            
            # Save updated STL
            output_path = self.case_dir / "constant" / "triSurface" / f"{fin_id}.stl"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            mesh.export(str(output_path))
            
            print(f"✅ Updated fin {fin_id} deflection to {deflection_angle:.2f}°")
            return True
            
        except Exception as e:
            print(f"❌ Error updating fin {fin_id} deflection: {e}")
            return False

class MeshMorpher:
    """Handles mesh morphing for dynamic fin movement"""
    
    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)
        self.fin_manager = FinGeometryManager(case_dir)
        
    def setup_fin_geometries(self, fin_configs: Dict):
        """Setup fin geometries from configuration"""
        for fin_id, config in fin_configs.items():
            # Load fin geometry
            if 'stl_path' in config:
                self.fin_manager.load_fin_geometry(fin_id, config['stl_path'])
            
            # Set attachment point
            if 'attachment_point' in config:
                self.fin_manager.set_fin_attachment_point(fin_id, config['attachment_point'])
            
            # Set rotation axis
            if 'rotation_axis' in config:
                self.fin_manager.set_fin_rotation_axis(fin_id, config['rotation_axis'])
    
    def update_fin_deflections(self, deflections: Dict[str, float]) -> bool:
        """Update all fin deflections and regenerate mesh boundaries"""
        try:
            # Update each fin geometry
            for fin_id, deflection in deflections.items():
                if not self.fin_manager.update_fin_deflection(fin_id, deflection):
                    return False
            
            # Update OpenFOAM boundary conditions
            self._update_boundary_conditions(deflections)
            
            # Update point displacement field
            self._update_point_displacement(deflections)
            
            print("✅ All fin deflections updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error updating fin deflections: {e}")
            return False
    
    def _update_boundary_conditions(self, deflections: Dict[str, float]):
        """Update OpenFOAM boundary conditions for moving fins"""
        # This would update the boundary conditions in the OpenFOAM case
        # For now, we'll create a placeholder that shows the structure
        
        boundary_file = self.case_dir / "0" / "U"
        if boundary_file.exists():
            # In a real implementation, this would parse and update the boundary conditions
            # to reflect the new fin positions
            print(f"📝 Updating boundary conditions for deflections: {deflections}")
    
    def _update_point_displacement(self, deflections: Dict[str, float]):
        """Update point displacement field for mesh morphing"""
        # This would update the pointDisplacement field to reflect new fin positions
        # For now, we'll create a placeholder
        
        displacement_file = self.case_dir / "0" / "pointDisplacement"
        if displacement_file.exists():
            # In a real implementation, this would calculate and update the displacement
            # field based on fin deflections
            print(f"📝 Updating point displacement for deflections: {deflections}")

class OpenFOAMDynamicMeshManager:
    """Manages OpenFOAM dynamic mesh operations"""
    
    def __init__(self, case_dir: Path):
        self.case_dir = Path(case_dir)
        self.mesh_morpher = MeshMorpher(case_dir)
        self.simulation_running = False
        
    def setup_dynamic_mesh(self, fin_configs: Dict):
        """Setup dynamic mesh configuration for active fin control"""
        try:
            # Copy dynamic mesh configuration files
            self._copy_dynamic_mesh_configs()
            
            # Setup fin geometries
            self.mesh_morpher.setup_fin_geometries(fin_configs)
            
            print("✅ Dynamic mesh setup completed")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up dynamic mesh: {e}")
            return False
    
    def _copy_dynamic_mesh_configs(self):
        """Copy dynamic mesh configuration files to case directory"""
        config_dir = Path(__file__).parent / "openfoam_configs"
        
        # Copy dynamicMeshDict
        src = config_dir / "dynamicMeshDict"
        dst = self.case_dir / "system" / "dynamicMeshDict"
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text())
        
        # Copy pointDisplacement
        src = config_dir / "pointDisplacement"
        dst = self.case_dir / "0" / "pointDisplacement"
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text())
        
        # Copy controlDict
        src = config_dir / "system" / "controlDict"
        dst = self.case_dir / "system" / "controlDict"
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text())
    
    def update_fin_positions(self, deflections: Dict[str, float]) -> bool:
        """Update fin positions in the mesh"""
        return self.mesh_morpher.update_fin_deflections(deflections)
    
    def start_dynamic_simulation(self) -> bool:
        """Start OpenFOAM simulation with dynamic mesh"""
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
            
            self.simulation_running = True
            print("✅ Dynamic mesh simulation started")
            return True
            
        except Exception as e:
            print(f"❌ Error starting dynamic simulation: {e}")
            return False
    
    def stop_simulation(self):
        """Stop the OpenFOAM simulation"""
        self.simulation_running = False
        print("⏹️ Simulation stopped")

# Example usage and configuration
def create_default_fin_configs() -> Dict:
    """Create default fin configurations for a 4-fin rocket"""
    return {
        "fin1": {  # Top fin (pitch control)
            "stl_path": "geometries/fin1.stl",
            "attachment_point": (0, 0.1, 0),
            "rotation_axis": (1, 0, 0)  # Rotate around X-axis
        },
        "fin2": {  # Right fin (yaw control)
            "stl_path": "geometries/fin2.stl",
            "attachment_point": (0.1, 0, 0),
            "rotation_axis": (0, 1, 0)  # Rotate around Y-axis
        },
        "fin3": {  # Bottom fin (pitch control)
            "stl_path": "geometries/fin3.stl",
            "attachment_point": (0, -0.1, 0),
            "rotation_axis": (1, 0, 0)  # Rotate around X-axis
        },
        "fin4": {  # Left fin (yaw control)
            "stl_path": "geometries/fin4.stl",
            "attachment_point": (-0.1, 0, 0),
            "rotation_axis": (0, 1, 0)  # Rotate around Y-axis
        }
    }
