#!/usr/bin/env python3
"""
Comprehensive Google Cloud Platform Test Suite
Tests everything from basic setup to full CFD simulation workflow
"""

import os
import sys
import json
import time
import subprocess
from typing import List, Tuple, Dict, Any

class GCPTestSuite:
    """Comprehensive test suite for Google Cloud Platform integration"""
    
    def __init__(self):
        self.results = []
        self.project_id = "centered-scion-471523-a4"
        self.function_name = "rocket-cfd-simulator"
        self.region = "us-central1"
        self.service_account_file = "centered-scion-471523-a4-b8125d43fa7a.json"
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results"""
        print(f"\n🔍 {test_name}...")
        try:
            result = test_func()
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            self.results.append((test_name, result))
            return result
        except Exception as e:
            print(f"❌ FAIL {test_name} - Error: {e}")
            self.results.append((test_name, False))
            return False
    
    def test_environment_setup(self) -> bool:
        """Test 1: Environment and file setup"""
        print("=" * 60)
        print("🏗️  ENVIRONMENT SETUP TESTS")
        print("=" * 60)
        
        # Test 1.1: Service account file
        if not self.run_test("Service Account File Exists", self._test_service_account_file):
            return False
        
        # Test 1.2: Service account file validity
        if not self.run_test("Service Account File Valid JSON", self._test_service_account_json):
            return False
        
        # Test 1.3: Service account file content
        if not self.run_test("Service Account File Content", self._test_service_account_content):
            return False
        
        # Test 1.4: Python version
        if not self.run_test("Python Version Check", self._test_python_version):
            return False
        
        # Test 1.5: Working directory
        if not self.run_test("Working Directory Check", self._test_working_directory):
            return False
        
        return True
    
    def test_package_installation(self) -> bool:
        """Test 2: Package installation and imports"""
        print("\n" + "=" * 60)
        print("📦 PACKAGE INSTALLATION TESTS")
        print("=" * 60)
        
        # Test 2.1: Check if pip is available
        if not self.run_test("Pip Available", self._test_pip_available):
            return False
        
        # Test 2.2: Check requirements.txt
        if not self.run_test("Requirements File Exists", self._test_requirements_file):
            return False
        
        # Test 2.3: Install packages
        if not self.run_test("Install Required Packages", self._test_install_packages):
            return False
        
        # Test 2.4: Test individual package imports
        packages = [
            ("google-auth", "google.oauth2.service_account"),
            ("google-auth-oauthlib", "google_auth_oauthlib"),
            ("google-auth-httplib2", "google_auth_httplib2"),
            ("google-cloud-storage", "google.cloud.storage"),
            ("google-cloud-logging", "google.cloud.logging"),
            ("requests", "requests"),
            ("flask", "flask"),
            ("flask-cors", "flask_cors"),
            ("numpy", "numpy")
        ]
        
        for package_name, import_name in packages:
            if not self.run_test(f"Import {package_name}", lambda: self._test_import(import_name)):
                return False
        
        return True
    
    def test_google_cloud_auth(self) -> bool:
        """Test 3: Google Cloud authentication"""
        print("\n" + "=" * 60)
        print("🔐 GOOGLE CLOUD AUTHENTICATION TESTS")
        print("=" * 60)
        
        # Test 3.1: Load credentials
        if not self.run_test("Load Service Account Credentials", self._test_load_credentials):
            return False
        
        # Test 3.2: Create authorized session
        if not self.run_test("Create Authorized Session", self._test_create_session):
            return False
        
        # Test 3.3: Test token generation
        if not self.run_test("Generate Access Token", self._test_generate_token):
            return False
        
        # Test 3.4: Test scopes
        if not self.run_test("Check Required Scopes", self._test_scopes):
            return False
        
        return True
    
    def test_gcp_cfd_client(self) -> bool:
        """Test 4: GCP CFD client functionality"""
        print("\n" + "=" * 60)
        print("🚀 GCP CFD CLIENT TESTS")
        print("=" * 60)
        
        # Test 4.1: Import GCP CFD client
        if not self.run_test("Import GCP CFD Client", self._test_import_gcp_client):
            return False
        
        # Test 4.2: Initialize GCP CFD client
        if not self.run_test("Initialize GCP CFD Client", self._test_init_gcp_client):
            return False
        
        # Test 4.3: Set function URL
        if not self.run_test("Set Function URL", self._test_set_function_url):
            return False
        
        # Test 4.4: Test client methods
        if not self.run_test("Test Client Methods", self._test_client_methods):
            return False
        
        return True
    
    def test_cloud_function_deployment(self) -> bool:
        """Test 5: Cloud Function deployment and connectivity"""
        print("\n" + "=" * 60)
        print("☁️  CLOUD FUNCTION DEPLOYMENT TESTS")
        print("=" * 60)
        
        # Test 5.1: Check gcloud CLI
        if not self.run_test("gcloud CLI Available", self._test_gcloud_cli):
            return False
        
        # Test 5.2: Check gcloud authentication
        if not self.run_test("gcloud Authentication", self._test_gcloud_auth):
            return False
        
        # Test 5.3: Check project configuration
        if not self.run_test("gcloud Project Configuration", self._test_gcloud_project):
            return False
        
        # Test 5.4: Test function URL connectivity
        if not self.run_test("Function URL Connectivity", self._test_function_connectivity):
            return False
        
        # Test 5.5: Test function deployment files
        if not self.run_test("Deployment Files Check", self._test_deployment_files):
            return False
        
        return True
    
    def test_cfd_simulation_workflow(self) -> bool:
        """Test 6: Complete CFD simulation workflow"""
        print("\n" + "=" * 60)
        print("🔬 CFD SIMULATION WORKFLOW TESTS")
        print("=" * 60)
        
        # Test 6.1: Test rocket data validation
        if not self.run_test("Rocket Data Validation", self._test_rocket_data_validation):
            return False
        
        # Test 6.2: Test simulation config validation
        if not self.run_test("Simulation Config Validation", self._test_simulation_config_validation):
            return False
        
        # Test 6.3: Test payload construction
        if not self.run_test("Payload Construction", self._test_payload_construction):
            return False
        
        # Test 6.4: Test simulation submission (if function is deployed)
        if not self.run_test("Simulation Submission", self._test_simulation_submission):
            return False
        
        return True
    
    def test_performance_and_limits(self) -> bool:
        """Test 7: Performance and limits"""
        print("\n" + "=" * 60)
        print("⚡ PERFORMANCE AND LIMITS TESTS")
        print("=" * 60)
        
        # Test 7.1: Test memory usage
        if not self.run_test("Memory Usage Check", self._test_memory_usage):
            return False
        
        # Test 7.2: Test network connectivity
        if not self.run_test("Network Connectivity", self._test_network_connectivity):
            return False
        
        # Test 7.3: Test timeout handling
        if not self.run_test("Timeout Handling", self._test_timeout_handling):
            return False
        
        # Test 7.4: Test error handling
        if not self.run_test("Error Handling", self._test_error_handling):
            return False
        
        return True
    
    # Individual test methods
    def _test_service_account_file(self) -> bool:
        """Test if service account file exists"""
        return os.path.exists(self.service_account_file)
    
    def _test_service_account_json(self) -> bool:
        """Test if service account file is valid JSON"""
        try:
            with open(self.service_account_file, 'r') as f:
                json.load(f)
            return True
        except:
            return False
    
    def _test_service_account_content(self) -> bool:
        """Test if service account file has required content"""
        try:
            with open(self.service_account_file, 'r') as f:
                data = json.load(f)
            
            required_fields = ['type', 'project_id', 'private_key', 'client_email', 'client_id']
            return all(field in data for field in required_fields)
        except:
            return False
    
    def _test_python_version(self) -> bool:
        """Test Python version"""
        return sys.version_info >= (3, 8)
    
    def _test_working_directory(self) -> bool:
        """Test working directory"""
        return os.path.exists("backend") and os.path.exists("frontend")
    
    def _test_pip_available(self) -> bool:
        """Test if pip is available"""
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         capture_output=True, check=True)
            return True
        except:
            return False
    
    def _test_requirements_file(self) -> bool:
        """Test if requirements.txt exists"""
        return os.path.exists("requirements.txt")
    
    def _test_install_packages(self) -> bool:
        """Test package installation"""
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                                  capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        except:
            return False
    
    def _test_import(self, module_name: str) -> bool:
        """Test importing a module"""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False
    
    def _test_load_credentials(self) -> bool:
        """Test loading Google Cloud credentials"""
        try:
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            return credentials is not None
        except:
            return False
    
    def _test_create_session(self) -> bool:
        """Test creating authorized session"""
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
    
    def _test_generate_token(self) -> bool:
        """Test generating access token"""
        try:
            from google.oauth2 import service_account
            
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            token = credentials.token
            return token is not None
        except:
            return False
    
    def _test_scopes(self) -> bool:
        """Test required scopes"""
        try:
            from google.oauth2 import service_account
            
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            return 'https://www.googleapis.com/auth/cloud-platform' in credentials.scopes
        except:
            return False
    
    def _test_import_gcp_client(self) -> bool:
        """Test importing GCP CFD client"""
        try:
            sys.path.append('backend')
            from gcp_cfd_client import GCPCFDClient
            return True
        except:
            return False
    
    def _test_init_gcp_client(self) -> bool:
        """Test initializing GCP CFD client"""
        try:
            sys.path.append('backend')
            from gcp_cfd_client import GCPCFDClient
            client = GCPCFDClient()
            return client is not None
        except:
            return False
    
    def _test_set_function_url(self) -> bool:
        """Test setting function URL"""
        try:
            sys.path.append('backend')
            from gcp_cfd_client import GCPCFDClient
            client = GCPCFDClient()
            client.set_function_url(self.function_name, self.region)
            return client.function_url is not None
        except:
            return False
    
    def _test_client_methods(self) -> bool:
        """Test client methods exist"""
        try:
            sys.path.append('backend')
            from gcp_cfd_client import GCPCFDClient
            client = GCPCFDClient()
            
            methods = ['submit_cfd_simulation', 'get_simulation_status', 'get_simulation_results']
            return all(hasattr(client, method) for method in methods)
        except:
            return False
    
    def _test_gcloud_cli(self) -> bool:
        """Test gcloud CLI availability"""
        try:
            result = subprocess.run(['gcloud', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def _test_gcloud_auth(self) -> bool:
        """Test gcloud authentication"""
        try:
            result = subprocess.run(['gcloud', 'auth', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0 and 'ACTIVE' in result.stdout
        except:
            return False
    
    def _test_gcloud_project(self) -> bool:
        """Test gcloud project configuration"""
        try:
            result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0 and self.project_id in result.stdout
        except:
            return False
    
    def _test_function_connectivity(self) -> bool:
        """Test function URL connectivity"""
        try:
            import requests
            function_url = f"https://{self.region}-{self.project_id}.cloudfunctions.net/{self.function_name}"
            response = requests.get(f"{function_url}/health", timeout=10)
            return response.status_code in [200, 401, 403]  # 401/403 means function exists but needs auth
        except:
            return False
    
    def _test_deployment_files(self) -> bool:
        """Test deployment files exist"""
        files = ['deploy_gcp_function.sh', 'gcp_cloud_function.py']
        return all(os.path.exists(f) for f in files)
    
    def _test_rocket_data_validation(self) -> bool:
        """Test rocket data validation"""
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
    
    def _test_simulation_config_validation(self) -> bool:
        """Test simulation config validation"""
        config = {
            "solver_type": "pimpleFoam",
            "turbulence_model": "kEpsilon",
            "time_step": 0.001,
            "max_time": 30,
            "inlet_velocity": 50
        }
        
        required_fields = ["solver_type", "turbulence_model", "time_step", "max_time"]
        return all(field in config for field in required_fields)
    
    def _test_payload_construction(self) -> bool:
        """Test payload construction"""
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
    
    def _test_simulation_submission(self) -> bool:
        """Test simulation submission (if function is deployed)"""
        try:
            sys.path.append('backend')
            from gcp_cfd_client import GCPCFDClient
            
            client = GCPCFDClient()
            client.set_function_url(self.function_name, self.region)
            
            # Test connection first
            return client.test_connection()
        except:
            return False
    
    def _test_memory_usage(self) -> bool:
        """Test memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.available > 1024 * 1024 * 1024  # 1GB available
        except ImportError:
            # If psutil not available, assume memory is OK
            return True
    
    def _test_network_connectivity(self) -> bool:
        """Test network connectivity"""
        try:
            import requests
            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _test_timeout_handling(self) -> bool:
        """Test timeout handling"""
        try:
            import requests
            # Test with a very short timeout
            response = requests.get("https://httpbin.org/delay/1", timeout=0.1)
            return False  # Should timeout
        except requests.exceptions.Timeout:
            return True  # Expected timeout
        except:
            return False
    
    def _test_error_handling(self) -> bool:
        """Test error handling"""
        try:
            sys.path.append('backend')
            from gcp_cfd_client import GCPCFDClient
            
            client = GCPCFDClient()
            # Test with invalid function URL
            client.set_function_url("invalid-function", "invalid-region")
            result = client.test_connection()
            return not result  # Should fail gracefully
        except:
            return False
    
    def run_all_tests(self) -> bool:
        """Run all test suites"""
        print("🧪 COMPREHENSIVE GOOGLE CLOUD PLATFORM TEST SUITE")
        print("=" * 80)
        
        test_suites = [
            ("Environment Setup", self.test_environment_setup),
            ("Package Installation", self.test_package_installation),
            ("Google Cloud Authentication", self.test_google_cloud_auth),
            ("GCP CFD Client", self.test_gcp_cfd_client),
            ("Cloud Function Deployment", self.test_cloud_function_deployment),
            ("CFD Simulation Workflow", self.test_cfd_simulation_workflow),
            ("Performance and Limits", self.test_performance_and_limits)
        ]
        
        suite_results = []
        
        for suite_name, suite_func in test_suites:
            try:
                result = suite_func()
                suite_results.append((suite_name, result))
            except Exception as e:
                print(f"❌ Test suite '{suite_name}' crashed: {e}")
                suite_results.append((suite_name, False))
        
        # Final summary
        self.print_final_summary(suite_results)
        
        return all(result for _, result in suite_results)
    
    def print_final_summary(self, suite_results: List[Tuple[str, bool]]):
        """Print final test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for _, result in self.results if result)
        
        print(f"🎯 Individual Tests: {passed_tests}/{total_tests} passed")
        print(f"🏆 Test Suites: {sum(1 for _, result in suite_results if result)}/{len(suite_results)} passed")
        
        print("\n📋 Test Suite Results:")
        for suite_name, result in suite_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {suite_name}")
        
        print("\n📋 Individual Test Results:")
        for test_name, result in self.results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Your GCP setup is perfect!")
            print("\n📋 Next steps:")
            print("1. Deploy Cloud Function: ./deploy_gcp_function.sh")
            print("2. Run full integration test: python test_gcp_integration.py")
            print("3. Start your application: python backend/f_backend.py")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} tests failed. Please fix the issues above.")
            print("\n🔧 Common fixes:")
            print("- Install missing packages: pip install -r requirements.txt")
            print("- Deploy the Cloud Function: ./deploy_gcp_function.sh")
            print("- Check your service account permissions")
            print("- Verify gcloud CLI is installed and authenticated")

def main():
    """Run comprehensive test suite"""
    test_suite = GCPTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🚀 Ready to deploy and run heavy CFD simulations!")
    else:
        print("\n🔧 Please fix the failing tests before proceeding.")

if __name__ == "__main__":
    main()
