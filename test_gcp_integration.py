#!/usr/bin/env python3
"""
Test Google Cloud Platform CFD Integration
"""

import sys
import os
import time
import json

# Add backend to path
sys.path.append('backend')

from gcp_cfd_client import GCPCFDClient

def test_gcp_cfd_integration():
    """Test the complete GCP CFD integration"""
    print("🧪 Testing Google Cloud Platform CFD Integration")
    print("=" * 60)
    
    try:
        # Initialize client
        print("1️⃣ Initializing GCP CFD Client...")
        client = GCPCFDClient()
        
        # Set function URL (update this with your actual deployed function URL)
        function_url = "https://us-central1-centered-scion-471523-a4.cloudfunctions.net/rocket-cfd-simulator"
        client.set_function_url("rocket-cfd-simulator", "us-central1")
        
        # Test connection
        print("\n2️⃣ Testing connection to Cloud Function...")
        if not client.test_connection():
            print("❌ Connection test failed. Make sure the function is deployed.")
            return False
        
        # Prepare test data
        print("\n3️⃣ Preparing test simulation data...")
        rocket_data = {
            "components": [
                {"type": "nose_cone", "length": 0.1, "diameter": 0.05, "shape": "conical"},
                {"type": "body_tube", "length": 0.3, "diameter": 0.05},
                {"type": "fins", "count": 3, "height": 0.08, "width": 0.06, "thickness": 0.003},
                {"type": "rail_button", "height": 0.08, "width": 0.04, "offset": 0.02}
            ],
            "weight": 0.5,
            "cg": 0.15
        }
        
        simulation_config = {
            "solver_type": "pimpleFoam",
            "turbulence_model": "kEpsilon",
            "time_step": 0.001,
            "max_time": 30,
            "inlet_velocity": 50,
            "outlet_pressure": 101325,
            "domain_size": 10,
            "base_cell_size": 0.01,
            "boundary_layer_cells": 5
        }
        
        print("📦 Rocket data prepared:")
        print(f"   - Components: {len(rocket_data['components'])}")
        print(f"   - Weight: {rocket_data['weight']} kg")
        print(f"   - CG: {rocket_data['cg']} m")
        
        print("⚙️  Simulation config prepared:")
        print(f"   - Solver: {simulation_config['solver_type']}")
        print(f"   - Turbulence: {simulation_config['turbulence_model']}")
        print(f"   - Inlet velocity: {simulation_config['inlet_velocity']} m/s")
        
        # Submit simulation
        print("\n4️⃣ Submitting CFD simulation...")
        result = client.submit_cfd_simulation(rocket_data, simulation_config)
        
        if "error" in result:
            print(f"❌ Simulation submission failed: {result['error']}")
            return False
        
        simulation_id = result.get("simulation_id")
        print(f"✅ Simulation submitted successfully!")
        print(f"🆔 Simulation ID: {simulation_id}")
        
        # Monitor simulation
        print("\n5️⃣ Monitoring simulation progress...")
        max_wait_time = 120  # 2 minutes max wait
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = client.get_simulation_status(simulation_id)
            
            if "error" in status:
                print(f"❌ Status check failed: {status['error']}")
                return False
            
            progress = status.get("progress", 0)
            sim_status = status.get("status", "unknown")
            elapsed = status.get("elapsed_time", 0)
            
            print(f"📊 Progress: {progress}% | Status: {sim_status} | Elapsed: {elapsed:.1f}s")
            
            if sim_status == "completed":
                print("✅ Simulation completed!")
                break
            elif sim_status == "error":
                print("❌ Simulation failed!")
                return False
            
            time.sleep(5)  # Check every 5 seconds
        
        # Get results
        print("\n6️⃣ Retrieving simulation results...")
        results = client.get_simulation_results(simulation_id)
        
        if "error" in results:
            print(f"❌ Results retrieval failed: {results['error']}")
            return False
        
        # Display results
        print("🎉 Simulation results retrieved successfully!")
        print("\n📊 CFD Results Summary:")
        print("-" * 40)
        
        sim_results = results.get("results", {})
        print(f"Drag Coefficient: {sim_results.get('drag_coefficient', 'N/A')}")
        print(f"Lift Coefficient: {sim_results.get('lift_coefficient', 'N/A')}")
        
        forces = sim_results.get("forces", {})
        print(f"Drag Force: {forces.get('drag_force', 'N/A')} N")
        print(f"Lift Force: {forces.get('lift_force', 'N/A')} N")
        
        mesh_info = sim_results.get("mesh_info", {})
        print(f"Total Cells: {mesh_info.get('total_cells', 'N/A'):,}")
        print(f"Mesh Quality: {mesh_info.get('quality', 'N/A')}")
        
        print(f"Computation Time: {sim_results.get('computation_time', 'N/A')} seconds")
        
        convergence = sim_results.get("convergence", {})
        print(f"Iterations: {convergence.get('iterations', 'N/A')}")
        
        print("\n✅ GCP CFD Integration Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    success = test_gcp_cfd_integration()
    
    if success:
        print("\n🎉 All tests passed! Your GCP CFD integration is working!")
        print("\n📋 Next steps:")
        print("1. Integrate the GCP client into your main backend")
        print("2. Update your frontend to use the new CFD results")
        print("3. Deploy your application to Render")
        print("4. Start running professional-grade CFD simulations!")
    else:
        print("\n❌ Tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the Cloud Function is deployed")
        print("2. Check that the service account has proper permissions")
        print("3. Verify the function URL is correct")
        print("4. Check the Cloud Function logs for errors")

if __name__ == "__main__":
    main()
