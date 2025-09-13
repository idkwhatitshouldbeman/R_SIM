#!/usr/bin/env python3
"""
Fin Geometry Generator for R_SIM
Creates STL files for different fin shapes and sizes
"""

import numpy as np
import trimesh
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class FinGeometryGenerator:
    """Generate fin geometries for CFD simulations"""
    
    def __init__(self, output_dir: str = "backend/fin_geometries"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def create_rectangular_fin(self, 
                             height: float = 25.0, 
                             width: float = 15.0, 
                             thickness: float = 2.0,
                             sweep: float = 0.0) -> trimesh.Trimesh:
        """Create a rectangular fin with optional sweep"""
        
        # Define fin vertices (starting from bottom-left, going counter-clockwise)
        # Bottom face
        bottom_vertices = np.array([
            [0, 0, 0],                    # Bottom-left-front
            [width, 0, 0],                # Bottom-right-front
            [width + sweep, height, 0],   # Top-right-front (with sweep)
            [sweep, height, 0],           # Top-left-front (with sweep)
        ])
        
        # Top face (offset by thickness)
        top_vertices = bottom_vertices.copy()
        top_vertices[:, 2] = thickness
        
        # Combine all vertices
        vertices = np.vstack([bottom_vertices, top_vertices])
        
        # Define faces (triangles)
        faces = []
        
        # Bottom face (2 triangles)
        faces.extend([[0, 1, 2], [0, 2, 3]])
        
        # Top face (2 triangles)
        faces.extend([[4, 6, 5], [4, 7, 6]])
        
        # Side faces
        # Front edge
        faces.extend([[0, 4, 5], [0, 5, 1]])
        # Right edge
        faces.extend([[1, 5, 6], [1, 6, 2]])
        # Back edge
        faces.extend([[2, 6, 7], [2, 7, 3]])
        # Left edge
        faces.extend([[3, 7, 4], [3, 4, 0]])
        
        faces = np.array(faces)
        
        # Create mesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        
        # Fix normals and make watertight
        mesh.fix_normals()
        mesh.fill_holes()
        
        return mesh
    
    def create_trapezoidal_fin(self, 
                              root_chord: float = 15.0,
                              tip_chord: float = 8.0,
                              height: float = 25.0, 
                              thickness: float = 2.0,
                              sweep: float = 5.0) -> trimesh.Trimesh:
        """Create a trapezoidal fin"""
        
        # Define fin vertices
        # Bottom face
        bottom_vertices = np.array([
            [0, 0, 0],                                    # Root leading edge
            [root_chord, 0, 0],                          # Root trailing edge
            [sweep + tip_chord, height, 0],              # Tip trailing edge
            [sweep, height, 0],                          # Tip leading edge
        ])
        
        # Top face (offset by thickness)
        top_vertices = bottom_vertices.copy()
        top_vertices[:, 2] = thickness
        
        # Combine all vertices
        vertices = np.vstack([bottom_vertices, top_vertices])
        
        # Define faces (same as rectangular)
        faces = []
        
        # Bottom face (2 triangles)
        faces.extend([[0, 1, 2], [0, 2, 3]])
        
        # Top face (2 triangles)
        faces.extend([[4, 6, 5], [4, 7, 6]])
        
        # Side faces
        faces.extend([[0, 4, 5], [0, 5, 1]])  # Front edge
        faces.extend([[1, 5, 6], [1, 6, 2]])  # Right edge
        faces.extend([[2, 6, 7], [2, 7, 3]])  # Back edge
        faces.extend([[3, 7, 4], [3, 4, 0]])  # Left edge
        
        faces = np.array(faces)
        
        # Create mesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        mesh.fix_normals()
        mesh.fill_holes()
        
        return mesh
    
    def create_elliptical_fin(self, 
                             height: float = 25.0, 
                             width: float = 15.0, 
                             thickness: float = 2.0,
                             resolution: int = 20) -> trimesh.Trimesh:
        """Create an elliptical fin"""
        
        # Create elliptical profile
        angles = np.linspace(0, np.pi, resolution)
        x = width * np.cos(angles)
        y = height * np.sin(angles)
        
        # Create bottom face vertices
        bottom_vertices = np.column_stack([x, y, np.zeros(len(x))])
        
        # Create top face vertices
        top_vertices = np.column_stack([x, y, np.full(len(x), thickness)])
        
        # Combine vertices
        vertices = np.vstack([bottom_vertices, top_vertices])
        
        # Create faces
        faces = []
        n = len(bottom_vertices)
        
        # Bottom face (fan triangulation from first vertex)
        for i in range(1, n-1):
            faces.append([0, i, i+1])
        
        # Top face (fan triangulation from first vertex)
        for i in range(1, n-1):
            faces.append([n, n+i+1, n+i])
        
        # Side faces
        for i in range(n-1):
            # Two triangles per side segment
            faces.extend([
                [i, n+i, n+i+1],
                [i, n+i+1, i+1]
            ])
        
        faces = np.array(faces)
        
        # Create mesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        mesh.fix_normals()
        mesh.fill_holes()
        
        return mesh
    
    def create_delta_fin(self, 
                        height: float = 25.0, 
                        width: float = 15.0, 
                        thickness: float = 2.0) -> trimesh.Trimesh:
        """Create a delta (triangular) fin"""
        
        # Define triangular fin vertices
        # Bottom face
        bottom_vertices = np.array([
            [0, 0, 0],         # Root leading edge
            [width, 0, 0],     # Root trailing edge
            [width/2, height, 0], # Tip
        ])
        
        # Top face (offset by thickness)
        top_vertices = bottom_vertices.copy()
        top_vertices[:, 2] = thickness
        
        # Combine all vertices
        vertices = np.vstack([bottom_vertices, top_vertices])
        
        # Define faces
        faces = []
        
        # Bottom face (1 triangle)
        faces.append([0, 1, 2])
        
        # Top face (1 triangle)
        faces.append([3, 5, 4])
        
        # Side faces
        faces.extend([
            [0, 3, 4], [0, 4, 1],  # Front edge
            [1, 4, 5], [1, 5, 2],  # Right edge
            [2, 5, 3], [2, 3, 0],  # Left edge
        ])
        
        faces = np.array(faces)
        
        # Create mesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        mesh.fix_normals()
        mesh.fill_holes()
        
        return mesh
    
    def generate_fin_set(self, fin_config: Dict) -> str:
        """Generate a complete set of fins and save as STL"""
        
        fin_shape = fin_config.get('finShape', 'rectangular')
        height = fin_config.get('finHeight', 25.0)
        width = fin_config.get('finWidth', 15.0)
        thickness = fin_config.get('finThickness', 2.0)
        sweep = fin_config.get('finSweep', 0.0)
        count = fin_config.get('finCount', 4)
        
        # Create single fin based on shape
        if fin_shape == 'rectangular':
            fin_mesh = self.create_rectangular_fin(height, width, thickness, sweep)
        elif fin_shape == 'trapezoidal':
            root_chord = width
            tip_chord = width * 0.6  # 60% of root chord
            fin_mesh = self.create_trapezoidal_fin(root_chord, tip_chord, height, thickness, sweep)
        elif fin_shape == 'elliptical':
            fin_mesh = self.create_elliptical_fin(height, width, thickness)
        elif fin_shape == 'delta':
            fin_mesh = self.create_delta_fin(height, width, thickness)
        else:
            # Default to rectangular
            fin_mesh = self.create_rectangular_fin(height, width, thickness, sweep)
        
        # Create filename
        filename = f"fin_{fin_shape}_{height}x{width}x{thickness}_count{count}.stl"
        filepath = self.output_dir / filename
        
        # Save single fin STL
        fin_mesh.export(filepath)
        
        print(f"✅ Generated fin geometry: {filepath}")
        print(f"   Shape: {fin_shape}")
        print(f"   Dimensions: {height} x {width} x {thickness} mm")
        print(f"   Count: {count} fins")
        print(f"   Vertices: {len(fin_mesh.vertices)}")
        print(f"   Faces: {len(fin_mesh.faces)}")
        
        return str(filepath)
    
    def generate_standard_fin_library(self):
        """Generate a library of standard fin geometries"""
        
        print("Generating standard fin library...")
        print("=" * 50)
        
        # Standard configurations
        configs = [
            # Rectangular fins
            {'finShape': 'rectangular', 'finHeight': 25, 'finWidth': 15, 'finThickness': 2, 'finSweep': 0, 'finCount': 4},
            {'finShape': 'rectangular', 'finHeight': 30, 'finWidth': 20, 'finThickness': 3, 'finSweep': 5, 'finCount': 3},
            
            # Trapezoidal fins
            {'finShape': 'trapezoidal', 'finHeight': 25, 'finWidth': 15, 'finThickness': 2, 'finSweep': 5, 'finCount': 4},
            {'finShape': 'trapezoidal', 'finHeight': 35, 'finWidth': 18, 'finThickness': 2.5, 'finSweep': 8, 'finCount': 4},
            
            # Elliptical fins
            {'finShape': 'elliptical', 'finHeight': 25, 'finWidth': 15, 'finThickness': 2, 'finCount': 4},
            {'finShape': 'elliptical', 'finHeight': 30, 'finWidth': 18, 'finThickness': 2.5, 'finCount': 3},
            
            # Delta fins
            {'finShape': 'delta', 'finHeight': 25, 'finWidth': 15, 'finThickness': 2, 'finCount': 4},
            {'finShape': 'delta', 'finHeight': 35, 'finWidth': 20, 'finThickness': 3, 'finCount': 3},
        ]
        
        generated_files = []
        for config in configs:
            try:
                filepath = self.generate_fin_set(config)
                generated_files.append(filepath)
                print()
            except Exception as e:
                print(f"❌ Error generating fin {config}: {e}")
                print()
        
        print(f"✅ Generated {len(generated_files)} fin geometries")
        return generated_files

def main():
    """Generate standard fin library"""
    generator = FinGeometryGenerator()
    generator.generate_standard_fin_library()

if __name__ == "__main__":
    main()
