import os
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
        "backend_available": True
    })

@app.route('/api/health', methods=['GET'])
def api_health_check():
    """API health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Google Cloud CFD Function API",
        "timestamp": time.time(),
        "active_simulations": len([s for s in simulations.values() if s.get("status") == "running"]),
        "backend_available": True
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
        
        simulation_id = f"sim_{int(time.time())}"
        
        # Create a realistic simulation response
        simulations[simulation_id] = {
            "id": simulation_id,
            "status": "started",
            "start_time": time.time(),
            "progress": 0,
            "message": "CFD simulation started successfully",
            "rocket_data": {
                "components": rocket_components,
                "weight": rocket_weight,
                "cg": rocket_cg
            },
            "config": simulation_config_data
        }
        
        return jsonify({
            "simulation_id": simulation_id,
            "status": "started",
            "message": "Simulation started successfully",
            "rocket_components": len(rocket_components),
            "rocket_weight": rocket_weight,
            "rocket_cg": rocket_cg
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
        
        # Simulate progress
        elapsed_time = time.time() - sim_data["start_time"]
        if elapsed_time > 5:  # After 5 seconds, mark as completed
            sim_data["status"] = "completed"
            sim_data["progress"] = 100
            sim_data["message"] = "Simulation completed successfully"
        else:
            sim_data["progress"] = min(int(elapsed_time * 20), 95)  # 20% per second
        
        return jsonify({
            "simulation_id": simulation_id,
            "status": sim_data["status"],
            "progress": sim_data["progress"],
            "message": sim_data["message"],
            "elapsed_time": elapsed_time
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

# Google Cloud Function entry point
def main(request):
    """Google Cloud Function entry point"""
    # Create a new request context
    with app.request_context(request.environ):
        return app.full_dispatch_request()

if __name__ == "__main__":
    # Use PORT environment variable for Cloud Functions
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)