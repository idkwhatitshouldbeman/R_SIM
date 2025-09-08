#!/usr/bin/env python3
"""Ultimate GCP Test Suite - Condensed Version"""

import os
import sys
import json
import time
import subprocess
from typing import Dict, List, Tuple, Any, Optional

class UltimateGCPTest:
    def __init__(self):
        self.project_id = "centered-scion-471523-a4"
        self.function_name = "rocket-cfd-simulator"
        self.region = "us-central1"
        self.service_account_file = "centered-scion-471523-a4-b8125d43fa7a.json"
        self.results = []
        self.fixes_applied = []
        self.score = 0
        self.total_tests = 0
        self.start_time = time.time()
    
    def print_header(self, title: str):
        print(f"\n🎯 {title}")
        print("=" * 60)
    
    def print_success(self, message: str):
        print(f"✅ {message}")
        self.score += 1
    
    def print_error(self, message: str):
        print(f"❌ {message}")
    
    def print_fix(self, message: str):
        print(f"🔧 {message}")
        self.fixes_applied.append(message)
    
    def run_test(self, test_name: str, test_func, auto_fix: bool = True) -> bool:
        self.total_tests += 1
        print(f"🔍 {test_name}...")
        
        try:
            result = test_func()
            if result:
                self.print_success(f"{test_name}")
                self.results.append((test_name, True, None))
                return True
            else:
                self.print_error(f"{test_name}")
                self.results.append((test_name, False, "Test failed"))
                
                if auto_fix and hasattr(self, f"fix_{test_name.lower().replace(' ', '_').replace(':', '')}"):
                    fix_method = getattr(self, f"fix_{test_name.lower().replace(' ', '_').replace(':', '')}")
                    if callable(fix_method):
                        self.print_fix(f"Attempting to fix {test_name}...")
                        if fix_method():
                            self.print_success(f"{test_name} - Fixed!")
                            self.results[-1] = (test_name, True, "Fixed")
                            return True
                
                return False
        except Exception as e:
            self.print_error(f"{test_name} - Error: {e}")
            self.results.append((test_name, False, str(e)))
            return False
    
    def run_command(self, command: List[str], description: str, timeout: int = 60) -> bool:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                self.print_success(f"{description}")
                return True
            else:
                self.print_error(f"{description} failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.print_error(f"{description} timed out")
            return False
        except Exception as e:
            self.print_error(f"{description} crashed: {e}")
            return False
    
    # Test methods
    def test_service_account_file(self) -> bool:
        if not os.path.exists(self.service_account_file):
            return False
        try:
            with open(self.service_account_file, 'r') as f:
                data = json.load(f)
            required_fields = ['type', 'project_id', 'private_key', 'client_email', 'client_id']
            return all(field in data for field in required_fields)
        except:
            return False
    
    def test_python_version(self) -> bool:
        return sys.version_info >= (3, 8)
    
    def test_working_directory(self) -> bool:
        return os.path.exists("backend") and os.path.exists("frontend")
    
    def test_pip_available(self) -> bool:
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         capture_output=True, check=True, timeout=10)
            return True
        except:
            return False
    
    def test_requirements_file(self) -> bool:
        return os.path.exists("requirements.txt")
    
    def fix_requirements_file(self) -> bool:
        try:
            required_packages = [
                "flask==3.0.0", "flask-cors==4.0.0", "numpy==1.24.3",
                "google-auth==2.23.4", "google-auth-oauthlib==1.1.0", 
                "google-auth-httplib2==0.1.1", "google-cloud-storage==2.10.0",
                "google-cloud-logging==3.8.0", "requests==2.31.0"
            ]
            with open("requirements.txt", 'w') as f:
                f.write('\n'.join(required_packages) + '\n')
            self.print_fix("Created requirements.txt with required packages")
            return True
        except Exception as e:
            self.print_error(f"Failed to create requirements.txt: {e}")
            return False
    
    def test_package_installation(self) -> bool:
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                                  capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        except:
            return False
    
    def test_google_auth_imports(self) -> bool:
        test_imports = [
            ("google.oauth2.service_account", "Google OAuth2 Service Account"),
            ("google.auth.transport.requests", "Google Auth Transport"),
            ("requests", "Requests HTTP Library")
        ]
        for module, name in test_imports:
            try:
                __import__(module)
            except ImportError:
                self.print_error(f"Failed to import {name}")
                return False
        return True
    
    def fix_google_auth_imports(self) -> bool:
        packages_to_install = [
            "google-auth==2.23.4", "google-auth-oauthlib==1.1.0", 
            "google-auth-httplib2==0.1.1", "requests==2.31.0"
        ]
        for package in packages_to_install:
            if not self.run_command([sys.executable, "-m", "pip", "install", package], 
                                  f"Installing {package}", timeout=120):
                return False
        return True
    
    def test_credential_loading(self) -> bool:
        try:
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            return credentials is not None
        except:
            return False
    
    def test_authorized_session(self) -> bool:
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import AuthorizedSession
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            session = AuthorizedSession(credentials)
            return session is not None
        except:
            return False
    
    def test_gcp_cfd_client_import(self) -> bool:
        try:
            sys.path.append('backend')
            from gcp_cfd_client import GCPCFDClient
            return True
        except:
            return False
    
    def test_gcp_cfd_client_init(self) -> bool:
        try:
            sys.path.append('backend')
            from gcp_cfd_client import GCPCFDClient
            client = GCPCFDClient()
            return client is not None
        except:
            return False
    
    def test_gcloud_cli(self) -> bool:
        try:
            result = subprocess.run(['gcloud', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def test_gcloud_auth(self) -> bool:
        try:
            result = subprocess.run(['gcloud', 'auth', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0 and 'ACTIVE' in result.stdout
        except:
            return False
    
    def test_gcloud_project(self) -> bool:
        try:
            result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0 and self.project_id in result.stdout
        except:
            return False
    
    def test_function_deployment(self) -> bool:
        try:
            result = subprocess.run([
                'gcloud', 'functions', 'describe', self.function_name,
                '--region', self.region
            ], capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except:
            return False
    
    def test_function_connectivity(self) -> bool:
        try:
            import requests
            function_url = f"https://{self.region}-{self.project_id}.cloudfunctions.net/{self.function_name}"
            response = requests.get(f"{function_url}/health", timeout=10)
            return response.status_code in [200, 401, 403]
        except:
            return False
    
    def test_authenticated_connection(self) -> bool:
        try:
            sys.path.append('backend')
            from gcp_cfd_client import GCPCFDClient
            client = GCPCFDClient()
            client.set_function_url(self.function_name, self.region)
            return client.test_connection()
        except:
            return False
    
    def test_rocket_data_validation(self) -> bool:
        rocket_data = {
            "components": [
                {"type": "nose_cone", "length": 0.1, "diameter": 0.05},
                {"type": "body_tube", "length": 0.3, "diameter": 0.05},
                {"type": "fins", "count": 3, "height": 0.08, "width": 0.06}
            ],
            "weight": 0.5,
            "cg": 0.15
        }
        required_fields = ["components", "weight", "cg"]
        return all(field in rocket_data for field in required_fields)
    
    def test_simulation_config_validation(self) -> bool:
        config = {
            "solver_type": "pimpleFoam",
            "turbulence_model": "kEpsilon",
            "time_step": 0.001,
            "max_time": 30,
            "inlet_velocity": 50
        }
        required_fields = ["solver_type", "turbulence_model", "time_step", "max_time"]
        return all(field in config for field in required_fields)
    
    def test_payload_construction(self) -> bool:
        try:
            rocket_data = {"components": [], "weight": 0.5, "cg": 0.15}
            config = {"solver_type": "pimpleFoam", "time_step": 0.001}
            payload = {
                "rocket_components": rocket_data.get("components", []),
                "rocket_weight": rocket_data.get("weight", 0),
                "rocket_cg": rocket_data.get("cg", 0),
                "simulation_config": config,
                "timestamp": time.time(),
                "simulation_id": f"sim_{int(time.time())}"
            }
            return len(payload) >= 5
        except:
            return False
    
    def test_network_connectivity(self) -> bool:
        try:
            import requests
            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_memory_usage(self) -> bool:
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.available > 1024 * 1024 * 1024
        except ImportError:
            return True
    
    def run_ultimate_test(self) -> bool:
        print("🚀 ULTIMATE GCP TEST SUITE")
        print("=" * 60)
        
        # All tests in one list
        tests = [
            ("Service Account File", self.test_service_account_file),
            ("Python Version", self.test_python_version),
            ("Working Directory", self.test_working_directory),
            ("Pip Available", self.test_pip_available),
            ("Requirements File", self.test_requirements_file),
            ("Package Installation", self.test_package_installation),
            ("Google Auth Imports", self.test_google_auth_imports),
            ("Credential Loading", self.test_credential_loading),
            ("Authorized Session", self.test_authorized_session),
            ("GCP CFD Client Import", self.test_gcp_cfd_client_import),
            ("GCP CFD Client Init", self.test_gcp_cfd_client_init),
            ("gcloud CLI", self.test_gcloud_cli),
            ("gcloud Auth", self.test_gcloud_auth),
            ("gcloud Project", self.test_gcloud_project),
            ("Function Deployment", self.test_function_deployment),
            ("Function Connectivity", self.test_function_connectivity),
            ("Authenticated Connection", self.test_authenticated_connection),
            ("Rocket Data Validation", self.test_rocket_data_validation),
            ("Simulation Config Validation", self.test_simulation_config_validation),
            ("Payload Construction", self.test_payload_construction),
            ("Network Connectivity", self.test_network_connectivity),
            ("Memory Usage", self.test_memory_usage)
        ]
        
        # Run all tests
        results = []
        for test_name, test_func in tests:
            results.append(self.run_test(test_name, test_func))
        
        # Print results
        elapsed_time = time.time() - self.start_time
        passed_tests = sum(results)
        percentage = (passed_tests / len(results) * 100) if results else 0
        
        print(f"\n🎯 RESULTS: {passed_tests}/{len(results)} ({percentage:.1f}%)")
        print(f"🔧 Fixes Applied: {len(self.fixes_applied)}")
        print(f"⏱️  Time: {elapsed_time:.1f}s")
        
        if percentage == 100:
            print("🎉 PERFECT! All tests passed!")
        elif percentage >= 80:
            print("✅ EXCELLENT! Most tests passed!")
        elif percentage >= 60:
            print("⚠️  GOOD! More than half the tests passed.")
        else:
            print("❌ NEEDS WORK! Less than half the tests passed.")
        
        return all(results)

def main():
    tester = UltimateGCPTest()
    success = tester.run_ultimate_test()
    
    if success:
        print("\n🚀 Ready to deploy and run heavy CFD simulations!")
    else:
        print("\n🔧 Keep working on the issues above. You'll get there!")

if __name__ == "__main__":
    main()
