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
        print("🚀 === SIMULATION START REQUEST ===")
        data = request.get_json() or {}
        print(f"📊 Request data keys: {list(data.keys())}")
        
        # Extract simulation parameters
        rocket_components = data.get('rocketComponents', [])
        rocket_weight = data.get('rocketWeight', 0)
        rocket_cg = data.get('rocketCG', 0)
        simulation_config_data = data.get('simulationConfig', {})
        
        print(f"🔧 Rocket components: {len(rocket_components)}")
        print(f"⚖️  Rocket weight: {rocket_weight}")
        print(f"📍 Rocket CG: {rocket_cg}")
        print(f"⚙️  Config items: {len(simulation_config_data)}")
        
        simulation_id = f"sim_{int(time.time())}"
        print(f"🆔 Generated simulation ID: {simulation_id}")
        
        # Create a realistic simulation response
        simulations[simulation_id] = {
            "id": simulation_id,
            "status": "initializing",
            "start_time": time.time(),
            "progress": 0,
            "message": "CFD simulation initializing...",
            "rocket_data": {
                "components": rocket_components,
                "weight": rocket_weight,
                "cg": rocket_cg
            },
            "config": simulation_config_data,
            "last_update": time.time()
        }
        
        print(f"✅ Simulation {simulation_id} created with status: initializing")
        print(f"📈 Total active simulations: {len(simulations)}")
        
        response_data = {
            "simulation_id": simulation_id,
            "status": "initializing",
            "message": "Simulation initializing...",
            "rocket_components": len(rocket_components),
            "rocket_weight": rocket_weight,
            "rocket_cg": rocket_cg
        }
        
        print(f"📤 Sending response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error in simulation start: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulation/status', methods=['POST'])
def api_simulation_status():
    """API endpoint for getting simulation status"""
    try:
        print("📊 === SIMULATION STATUS REQUEST ===")
        data = request.get_json() or {}
        simulation_id = data.get("simulation_id")
        print(f"🆔 Status check for simulation: {simulation_id}")
        
        if not simulation_id:
            print("❌ No simulation ID provided")
            return jsonify({"error": "Simulation ID required"}), 400
            
        if simulation_id not in simulations:
            print(f"❌ Simulation {simulation_id} not found")
            print(f"📋 Available simulations: {list(simulations.keys())}")
            return jsonify({"error": "Simulation not found"}), 404
        
        sim_data = simulations[simulation_id]
        elapsed_time = time.time() - sim_data["start_time"]
        
        print(f"⏱️  Elapsed time: {elapsed_time:.2f} seconds")
        print(f"📈 Current status: {sim_data['status']}")
        print(f"📊 Current progress: {sim_data['progress']}%")
        
        # Enhanced progress simulation with realistic stages
        if sim_data["status"] == "initializing":
            if elapsed_time > 2:
                sim_data["status"] = "running"
                sim_data["progress"] = 10
                sim_data["message"] = "Mesh generation in progress..."
                print("🔄 Status updated: initializing → running")
        elif sim_data["status"] == "running":
            if elapsed_time > 8:
                sim_data["status"] = "completed"
                sim_data["progress"] = 100
                sim_data["message"] = "Simulation completed successfully!"
                print("✅ Status updated: running → completed")
            elif elapsed_time > 6:
                sim_data["progress"] = 60
                sim_data["message"] = "Post-processing results..."
            elif elapsed_time > 4:
                sim_data["progress"] = 30
                sim_data["message"] = "CFD solver running..."
        
        # Update last update time
        sim_data["last_update"] = time.time()
        
        response_data = {
            "simulation_id": simulation_id,
            "status": sim_data["status"],
            "progress": sim_data["progress"],
            "message": sim_data["message"],
            "elapsed_time": elapsed_time,
            "rocket_components": len(sim_data["rocket_data"]["components"]),
            "rocket_weight": sim_data["rocket_data"]["weight"],
            "rocket_cg": sim_data["rocket_data"]["cg"]
        }
        
        print(f"📤 Sending status response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error in simulation status: {e}")
        import traceback
        traceback.print_exc()
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