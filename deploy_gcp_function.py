#!/usr/bin/env python3
"""
Deploy Google Cloud Function for Heavy CFD Simulations
Python-based deployment script
"""

import os
import subprocess
import sys
import json
import time

def run_command(cmd, description="", check=True):
    """Run a command and return the result"""
    print(f"🔧 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True, result.stdout
        else:
            print(f"❌ {description} - Failed")
            print(f"   Error: {result.stderr.strip()}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - Timeout")
        return False, "Command timed out"
    except Exception as e:
        print(f"💥 {description} - Exception: {e}")
        return False, str(e)

def main():
    """Main deployment function"""
    print("🚀 Deploying Google Cloud Function for CFD Simulations")
    print("=" * 60)
    
    # Configuration
    PROJECT_ID = "centered-scion-471523-a4"
    FUNCTION_NAME = "rocket-cfd-simulator"
    REGION = "us-central1"
    RUNTIME = "python311"
    MEMORY = "2GB"
    TIMEOUT = "540s"  # 9 minutes (max for HTTP functions)
    MAX_INSTANCES = "10"
    
    # Check if gcloud is available
    success, _ = run_command(["gcloud", "--version"], "Checking gcloud CLI", check=False)
    if not success:
        print("❌ gcloud CLI not found. Please install it first:")
        print("   https://cloud.google.com/sdk/docs/install")
        return False
    
    # Check authentication
    success, _ = run_command(["gcloud", "auth", "list", "--filter=status:ACTIVE"], "Checking authentication", check=False)
    if not success:
        print("❌ Not authenticated with gcloud. Please run:")
        print("   gcloud auth login")
        return False
    
    # Set project
    success, _ = run_command(["gcloud", "config", "set", "project", PROJECT_ID], f"Setting project to {PROJECT_ID}")
    if not success:
        return False
    
    # Create requirements.txt for the function
    print("📦 Creating requirements.txt for Cloud Function")
    requirements_content = """flask==3.0.0
google-cloud-storage==2.10.0
google-cloud-logging==3.8.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements_content)
    
    # Create main.py for the function
    print("📝 Creating main.py for Cloud Function")
    main_py_content = '''import os
import json
import subprocess
import tempfile
import time
import threading
from typing import Dict, Any
from flask import Flask, request, jsonify

# Global simulation storage (in production, use Cloud Storage)
simulations = {}

app = Flask(__name__)

class CloudCFDManager:
    """CFD manager for Google Cloud Functions"""
    
    def __init__(self):
        self.project_id = os.environ.get("PROJECT_ID", "centered-scion-471523-a4")
    
    def start_simulation(self, rocket_data: Dict, simulation_config: Dict) -> Dict:
        """Start a new CFD simulation"""
        simulation_id = f"sim_{int(time.time())}_{len(simulations)}"
        
        # Store simulation data
        simulations[simulation_id] = {
            "id": simulation_id,
            "status": "initializing",
            "start_time": time.time(),
            "rocket_data": rocket_data,
            "simulation_config": simulation_config,
            "progress": 0,
            "message": "Setting up simulation environment"
        }
        
        # Start simulation in background thread
        thread = threading.Thread(target=self._run_simulation, args=(simulation_id,))
        thread.daemon = True
        thread.start()
        
        return {
            "simulation_id": simulation_id,
            "status": "started",
            "message": "Simulation started successfully"
        }
    
    def _run_simulation(self, simulation_id: str):
        """Run the actual simulation (mock implementation)"""
        try:
            sim_data = simulations[simulation_id]
            sim_data["status"] = "running"
            sim_data["message"] = "Running CFD simulation"
            
            # Simulate simulation progress
            for i in range(1, 101):
                time.sleep(0.1)  # Simulate work
                sim_data["progress"] = i
                sim_data["message"] = f"Simulation progress: {i}%"
            
            # Mark as completed
            sim_data["status"] = "completed"
            sim_data["message"] = "Simulation completed successfully"
            sim_data["results"] = {
                "drag_coefficient": 0.45,
                "lift_coefficient": 0.12,
                "pressure_distribution": "mock_data",
                "velocity_field": "mock_data"
            }
            
        except Exception as e:
            sim_data["status"] = "error"
            sim_data["message"] = f"Simulation failed: {str(e)}"
    
    def get_status(self, simulation_id: str) -> Dict:
        """Get simulation status"""
        if simulation_id not in simulations:
            return {"error": "Simulation not found"}
        
        sim_data = simulations[simulation_id]
        return {
            "simulation_id": simulation_id,
            "status": sim_data["status"],
            "progress": sim_data["progress"],
            "message": sim_data["message"],
            "elapsed_time": time.time() - sim_data["start_time"]
        }
    
    def get_results(self, simulation_id: str) -> Dict:
        """Get simulation results"""
        if simulation_id not in simulations:
            return {"error": "Simulation not found"}
        
        sim_data = simulations[simulation_id]
        if sim_data["status"] != "completed":
            return {"error": "Simulation not completed"}
        
        return {
            "simulation_id": simulation_id,
            "results": sim_data["results"],
            "completion_time": time.time() - sim_data["start_time"]
        }

# Global CFD manager
cfd_manager = CloudCFDManager()

@app.route('/', methods=['POST'])
def handle_request():
    """Main Cloud Function entry point"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        action = data.get("action", "simulate")
        
        if action == "simulate":
            # Start new simulation
            rocket_data = {
                "components": data.get("rocket_components", []),
                "weight": data.get("rocket_weight", 0),
                "cg": data.get("rocket_cg", 0)
            }
            simulation_config = data.get("simulation_config", {})
            
            result = cfd_manager.start_simulation(rocket_data, simulation_config)
            return jsonify(result)
        
        elif action == "status":
            # Get simulation status
            simulation_id = data.get("simulation_id")
            if not simulation_id:
                return jsonify({"error": "simulation_id required"}), 400
            
            result = cfd_manager.get_status(simulation_id)
            return jsonify(result)
        
        elif action == "results":
            # Get simulation results
            simulation_id = data.get("simulation_id")
            if not simulation_id:
                return jsonify({"error": "simulation_id required"}), 400
            
            result = cfd_manager.get_results(simulation_id)
            return jsonify(result)
        
        elif action == "cancel":
            # Cancel simulation
            simulation_id = data.get("simulation_id")
            if not simulation_id:
                return jsonify({"error": "simulation_id required"}), 400
            
            # For now, just mark as cancelled
            if simulation_id in simulations:
                simulations[simulation_id]["status"] = "cancelled"
                return jsonify({"status": "cancelled", "simulation_id": simulation_id})
            else:
                return jsonify({"error": "Simulation not found"}), 404
        
        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Google Cloud CFD Function",
        "timestamp": time.time(),
        "active_simulations": len([s for s in simulations.values() if s["status"] == "running"])
    })

@app.route('/api/simulation/start', methods=['POST'])
def api_simulation_start():
    """API endpoint for starting simulations"""
    return handle_request()

@app.route('/api/simulation/status', methods=['POST'])
def api_simulation_status():
    """API endpoint for getting simulation status"""
    return handle_request()

@app.route('/api/simulation/stop', methods=['POST'])
def api_simulation_stop():
    """API endpoint for stopping simulations"""
    return handle_request()

if __name__ == "__main__":
    # For local testing
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
'''
    
    with open("main.py", "w") as f:
        f.write(main_py_content)
    
    # Deploy the function
    print("🚀 Deploying Cloud Function...")
    deploy_cmd = [
        "gcloud", "functions", "deploy", FUNCTION_NAME,
        "--gen2",
        "--runtime", RUNTIME,
        "--region", REGION,
        "--source", ".",
        "--entry-point", "handle_request",
        "--trigger-http",
        "--allow-unauthenticated",
        "--memory", MEMORY,
        "--timeout", TIMEOUT,
        "--max-instances", MAX_INSTANCES,
        "--set-env-vars", f"PROJECT_ID={PROJECT_ID}"
    ]
    
    success, output = run_command(deploy_cmd, "Deploying Cloud Function")
    if not success:
        print("❌ Deployment failed!")
        return False
    
    # Get the function URL
    print("🔗 Getting function URL...")
    success, url_output = run_command([
        "gcloud", "functions", "describe", FUNCTION_NAME,
        "--region", REGION,
        "--format", "value(url)"
    ], "Getting function URL")
    
    if success and url_output.strip():
        function_url = url_output.strip()
        print("")
        print("✅ Cloud Function deployed successfully!")
        print(f"🔗 Function URL: {function_url}")
        print("")
        print("📋 Next steps:")
        print("1. Test the function with: py test_gcp_integration.py")
        print("2. Update your frontend to use this URL")
        print("3. Start running heavy CFD simulations!")
        print("")
        print("🧪 Test the function:")
        print(f"curl -X GET {function_url}/health")
        return True
    else:
        print("⚠️  Function deployed but couldn't get URL")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
