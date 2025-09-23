import os
import sys
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Import the actual backend components
try:
    from gcp_cfd_client import GCPCFDClient
    from openfoam_integration import OpenFOAMIntegration
    from simulation_orchestrator import SimulationOrchestrator
    
    # Initialize the CFD client
    cfd_client = GCPCFDClient()
    openfoam_manager = cfd_client  # Use the GCP client as the manager
    
    print("✅ Backend components loaded successfully")
except Exception as e:
    print(f"⚠️  Backend components not available: {e}")
    openfoam_manager = None

# Global simulation storage
simulations = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Google Cloud CFD Function",
        "timestamp": time.time(),
        "active_simulations": len([s for s in simulations.values() if s.get("status") == "running"]),
        "backend_available": openfoam_manager is not None
    })

@app.route('/api/health', methods=['GET'])
def api_health_check():
    """API health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Google Cloud CFD Function API",
        "timestamp": time.time(),
        "active_simulations": len([s for s in simulations.values() if s.get("status") == "running"]),
        "backend_available": openfoam_manager is not None
    })

@app.route('/api/simulation/start', methods=['POST'])
def api_simulation_start():
    """API endpoint for starting simulations"""
    try:
        data = request.get_json() or {}
        
        # Extract simulation parameters
        rocket_components = data.get('rocketComponents', [])
        rocket_weight = data.get('rocketWeight', 0)
        rocket_cg = data.get('rocketCG', 0)
        simulation_config_data = data.get('simulationConfig', {})
        
        # Create simulation config
        simulation_config = {
            'mesh_quality': simulation_config_data.get('meshQuality', 'medium'),
            'solver_type': simulation_config_data.get('solverType', 'pimpleFoam'),
            'time_step': simulation_config_data.get('timeStep', 0.001),
            'max_iterations': simulation_config_data.get('maxIterations', 1000),
            'convergence_tolerance': simulation_config_data.get('convergenceTolerance', 1e-6),
            'calculate_pressure': simulation_config_data.get('calculatePressure', True),
            'calculate_velocity': simulation_config_data.get('calculateVelocity', True),
            'output_format': simulation_config_data.get('outputFormat', 'vtk')
        }
        
        # Prepare rocket data for simulation
        rocket_data = {
            'components': rocket_components,
            'weight': rocket_weight,
            'cg': rocket_cg
        }
        
        simulation_id = f"sim_{int(time.time())}"
        
        if openfoam_manager:
            # Use real CFD simulation
            result = openfoam_manager.submit_cfd_simulation(rocket_data, simulation_config)
            
            simulations[simulation_id] = {
                "id": simulation_id,
                "status": "started",
                "start_time": time.time(),
                "progress": 0,
                "message": "CFD simulation started successfully",
                "result": result
            }
        else:
            # Fallback to mock simulation
            simulations[simulation_id] = {
                "id": simulation_id,
                "status": "started",
                "start_time": time.time(),
                "progress": 0,
                "message": "Mock simulation started (backend not available)"
            }
        
        return jsonify({
            "simulation_id": simulation_id,
            "status": "started",
            "message": "Simulation started successfully"
        })
        
    except Exception as e:
        print(f"Error in simulation start: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulation/status', methods=['POST'])
def api_simulation_status():
    """API endpoint for getting simulation status"""
    try:
        data = request.get_json() or {}
        simulation_id = data.get("simulation_id")
        
        if not simulation_id or simulation_id not in simulations:
            return jsonify({"error": "Simulation not found"}), 404
        
        sim_data = simulations[simulation_id]
        return jsonify({
            "simulation_id": simulation_id,
            "status": sim_data["status"],
            "progress": sim_data["progress"],
            "message": sim_data["message"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulation/stop', methods=['POST'])
def api_simulation_stop():
    """API endpoint for stopping simulations"""
    try:
        data = request.get_json() or {}
        simulation_id = data.get("simulation_id")
        
        if simulation_id and simulation_id in simulations:
            simulations[simulation_id]["status"] = "stopped"
            return jsonify({"status": "stopped", "simulation_id": simulation_id})
        else:
            return jsonify({"error": "Simulation not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Use PORT environment variable for Cloud Functions
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)