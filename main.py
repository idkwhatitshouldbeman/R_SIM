import os
import json
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global simulation storage
simulations = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Google Cloud CFD Function",
        "timestamp": time.time(),
        "active_simulations": len([s for s in simulations.values() if s.get("status") == "running"])
    })

@app.route('/api/simulation/start', methods=['POST'])
def api_simulation_start():
    """API endpoint for starting simulations"""
    try:
        data = request.get_json() or {}
        simulation_id = f"sim_{int(time.time())}"
        
        simulations[simulation_id] = {
            "id": simulation_id,
            "status": "started",
            "start_time": time.time(),
            "progress": 0,
            "message": "Simulation started successfully"
        }
        
        return jsonify({
            "simulation_id": simulation_id,
            "status": "started",
            "message": "Simulation started successfully"
        })
    except Exception as e:
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
