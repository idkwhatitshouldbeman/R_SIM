#!/usr/bin/env python3
"""
Google Cloud Platform CFD Client
Handles authentication and communication with GCP Cloud Functions for heavy CFD simulations
"""

import os
import json
import requests
import time
from typing import Dict, List, Optional, Any
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

class GCPCFDClient:
    """Client for Google Cloud Platform CFD simulations"""
    
    def __init__(self, service_account_path: str = "centered-scion-471523-a4-b8125d43fa7a.json"):
        self.service_account_path = service_account_path
        self.project_id = "centered-scion-471523-a4"
        self.credentials = None
        self.authed_session = None
        self.function_url = None
        
        # Initialize authentication
        self._setup_authentication()
    
    def _setup_authentication(self):
        """Set up Google Cloud authentication"""
        try:
            # Check if service account file exists
            if not os.path.exists(self.service_account_path):
                print(f"⚠️  GCP service account file not found: {self.service_account_path}")
                print("⚠️  GCP integration will be disabled. Running in simulation mode.")
                self.credentials = None
                self.authed_session = None
                return
            
            # Load service account credentials
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            # Create authorized session
            self.authed_session = AuthorizedSession(self.credentials)
            
            print("✅ Google Cloud authentication successful")
            print(f"📧 Service account: {self.credentials.service_account_email}")
            print(f"🏗️  Project ID: {self.project_id}")
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            raise
    
    def set_function_url(self, function_name: str, region: str = "us-central1"):
        """Set the Cloud Function URL"""
        self.function_url = f"https://{region}-{self.project_id}.cloudfunctions.net/{function_name}"
        print(f"🔗 Function URL set: {self.function_url}")
    
    def test_connection(self) -> bool:
        """Test connection to Cloud Function"""
        if not self.function_url:
            print("❌ Function URL not set")
            return False
        
        try:
            payload = {"test": "connection", "timestamp": time.time()}
            
            print("🧪 Testing Cloud Function connection...")
            response = self.authed_session.post(
                self.function_url, 
                json=payload,
                timeout=30
            )
            
            print(f"📊 Status code: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Connection test successful!")
                return True
            else:
                print("❌ Connection test failed")
                return False
                
        except Exception as e:
            print(f"❌ Connection test error: {e}")
            return False
    
    def submit_cfd_simulation(self, rocket_data: Dict, simulation_config: Dict) -> Dict:
        """Submit a CFD simulation to Google Cloud Function"""
        if not self.authed_session:
            print("⚠️  GCP not available, running in simulation mode")
            return self._simulate_cfd_submission(rocket_data, simulation_config)
        
        if not self.function_url:
            raise ValueError("Function URL not set")
        
        try:
            payload = {
                "rocket_components": rocket_data.get("components", []),
                "rocket_weight": rocket_data.get("weight", 0),
                "rocket_cg": rocket_data.get("cg", 0),
                "simulation_config": simulation_config,
                "timestamp": time.time(),
                "simulation_id": f"sim_{int(time.time())}"
            }
            
            print("🚀 Submitting CFD simulation to Google Cloud...")
            print(f"📦 Payload size: {len(json.dumps(payload))} bytes")
            
            response = self.authed_session.post(
                self.function_url,
                json=payload,
                timeout=300  # 5 minute timeout for submission
            )
            
            print(f"📊 Submission status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Simulation submitted successfully!")
                return result
            else:
                print(f"❌ Submission failed: {response.text}")
                return {"error": f"Submission failed: {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Submission error: {e}")
            return {"error": str(e)}
    
    def _simulate_cfd_submission(self, rocket_data: Dict, simulation_config: Dict) -> Dict:
        """Simulate CFD submission when GCP is not available"""
        simulation_id = f"sim_{int(time.time())}"
        print(f"🎭 Simulating CFD submission (ID: {simulation_id})")
        
        return {
            "success": True,
            "simulation_id": simulation_id,
            "status": "submitted",
            "message": "Simulation submitted (simulation mode)",
            "estimated_completion": time.time() + 300  # 5 minutes
        }
    
    def get_simulation_status(self, simulation_id: str) -> Dict:
        """Get the status of a running simulation"""
        if not self.authed_session:
            return self._simulate_status_check(simulation_id)
        
        if not self.function_url:
            raise ValueError("Function URL not set")
        
        try:
            payload = {
                "action": "status",
                "simulation_id": simulation_id
            }
            
            response = self.authed_session.post(
                self.function_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status check failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def get_simulation_results(self, simulation_id: str) -> Dict:
        """Get the results of a completed simulation"""
        if not self.authed_session:
            return self._simulate_results_get(simulation_id)
        
        if not self.function_url:
            raise ValueError("Function URL not set")
        
        try:
            payload = {
                "action": "results",
                "simulation_id": simulation_id
            }
            
            response = self.authed_session.post(
                self.function_url,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Results retrieval failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def cancel_simulation(self, simulation_id: str) -> Dict:
        """Cancel a running simulation"""
        if not self.authed_session:
            return {"success": True, "message": "Simulation cancelled (simulation mode)"}
        
        if not self.function_url:
            raise ValueError("Function URL not set")
        
        try:
            payload = {
                "action": "cancel",
                "simulation_id": simulation_id
            }
            
            response = self.authed_session.post(
                self.function_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Cancel failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _simulate_status_check(self, simulation_id: str) -> Dict:
        """Simulate status check when GCP is not available"""
        return {
            "success": True,
            "simulation_id": simulation_id,
            "status": "running",
            "progress": 45,
            "message": "Simulation in progress (simulation mode)"
        }
    
    def _simulate_results_get(self, simulation_id: str) -> Dict:
        """Simulate results retrieval when GCP is not available"""
        return {
            "success": True,
            "simulation_id": simulation_id,
            "status": "completed",
            "results": {
                "drag_coefficient": 0.45,
                "lift_coefficient": 0.12,
                "pressure_distribution": "simulated_data",
                "velocity_field": "simulated_data"
            },
            "message": "Results retrieved (simulation mode)"
        }

def main():
    """Test the GCP CFD client"""
    print("🧪 Testing Google Cloud Platform CFD Client")
    print("=" * 50)
    
    try:
        # Initialize client
        client = GCPCFDClient()
        
        # Set function URL (you'll need to update this with your actual function name)
        client.set_function_url("rocket-cfd-simulator")
        
        # Test connection
        if client.test_connection():
            print("\n🎉 GCP CFD Client is ready!")
            
            # Example simulation data
            rocket_data = {
                "components": [
                    {"type": "nose_cone", "length": 0.1, "diameter": 0.05},
                    {"type": "body_tube", "length": 0.3, "diameter": 0.05},
                    {"type": "fins", "count": 3, "height": 0.08, "width": 0.06}
                ],
                "weight": 0.5,
                "cg": 0.15
            }
            
            simulation_config = {
                "solver_type": "pimpleFoam",
                "turbulence_model": "kEpsilon",
                "time_step": 0.001,
                "max_time": 30,
                "inlet_velocity": 50
            }
            
            print("\n🚀 Ready to submit CFD simulations!")
            print("📋 Example payload prepared")
            
        else:
            print("\n❌ GCP CFD Client setup failed")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()
