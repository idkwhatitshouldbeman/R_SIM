#!/usr/bin/env python3
"""
Interactive Google Cloud Platform Test
Guides you through testing and fixing GCP integration step by step
"""

import os
import sys
import json
import time
import subprocess
from typing import Dict, List, Tuple

class InteractiveGCPTest:
    """Interactive test suite with guided fixes"""
    
    def __init__(self):
        self.project_id = "centered-scion-471523-a4"
        self.function_name = "rocket-cfd-simulator"
        self.region = "us-central1"
        self.service_account_file = "centered-scion-471523-a4-b8125d43fa7a.json"
        self.score = 0
        self.total_tests = 0
    
    def print_header(self, title: str):
        """Print a nice header"""
        print("\n" + "=" * 60)
        print(f"🎯 {title}")
        print("=" * 60)
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"✅ {message}")
        self.score += 1
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"❌ {message}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"⚠️  {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ️  {message}")
    
    def ask_yes_no(self, question: str) -> bool:
        """Ask a yes/no question"""
        while True:
            response = input(f"❓ {question} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please answer 'y' or 'n'")
    
    def run_command(self, command: List[str], description: str) -> bool:
        """Run a command and return success status"""
        print(f"🔧 {description}...")
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                self.print_success(f"{description} completed")
                return True
            else:
                self.print_error(f"{description} failed: {result.stderr}")
                return False
        except Exception as e:
            self.print_error(f"{description} crashed: {e}")
            return False
    
    def test_step_1_environment(self) -> bool:
        """Test Step 1: Environment Setup"""
        self.print_header("STEP 1: ENVIRONMENT SETUP")
        
        # Test 1.1: Service account file
        self.total_tests += 1
        if os.path.exists(self.service_account_file):
            self.print_success("Service account file exists")
        else:
            self.print_error("Service account file not found")
            return False
        
        # Test 1.2: Service account content
        self.total_tests += 1
        try:
            with open(self.service_account_file, 'r') as f:
                sa_data = json.load(f)
            
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            if all(field in sa_data for field in required_fields):
                self.print_success("Service account file is valid")
                self.print_info(f"Project ID: {sa_data['project_id']}")
                self.print_info(f"Client Email: {sa_data['client_email']}")
            else:
                self.print_error("Service account file is missing required fields")
                return False
        except Exception as e:
            self.print_error(f"Service account file is invalid: {e}")
            return False
        
        # Test 1.3: Python version
        self.total_tests += 1
        if sys.version_info >= (3, 8):
            self.print_success(f"Python version {sys.version_info.major}.{sys.version_info.minor} is supported")
        else:
            self.print_error(f"Python version {sys.version_info.major}.{sys.version_info.minor} is too old (need 3.8+)")
            return False
        
        return True
    
    def test_step_2_packages(self) -> bool:
        """Test Step 2: Package Installation"""
        self.print_header("STEP 2: PACKAGE INSTALLATION")
        
        # Test 2.1: Check pip
        self.total_tests += 1
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         capture_output=True, check=True)
            self.print_success("pip is available")
        except:
            self.print_error("pip is not available")
            return False
        
        # Test 2.2: Check requirements.txt
        self.total_tests += 1
        if os.path.exists("requirements.txt"):
            self.print_success("requirements.txt exists")
        else:
            self.print_error("requirements.txt not found")
            return False
        
        # Test 2.3: Install packages
        self.total_tests += 1
        if self.ask_yes_no("Do you want to install/update required packages?"):
            if self.run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              "Installing required packages"):
                self.print_success("Packages installed successfully")
            else:
                self.print_error("Package installation failed")
                return False
        else:
            self.print_warning("Skipping package installation")
        
        # Test 2.4: Test imports
        test_imports = [
            ("google.oauth2.service_account", "Google OAuth2"),
            ("google.auth.transport.requests", "Google Auth Transport"),
            ("requests", "Requests HTTP Library")
        ]
        
        for module, name in test_imports:
            self.total_tests += 1
            try:
                __import__(module)
                self.print_success(f"{name} import successful")
            except ImportError as e:
                self.print_error(f"{name} import failed: {e}")
                if self.ask_yes_no(f"Try to install {name} manually?"):
                    package_name = module.split('.')[0].replace('_', '-')
                    self.run_command([sys.executable, "-m", "pip", "install", package_name], 
                                   f"Installing {package_name}")
                return False
        
        return True
    
    def test_step_3_authentication(self) -> bool:
        """Test Step 3: Google Cloud Authentication"""
        self.print_header("STEP 3: GOOGLE CLOUD AUTHENTICATION")
        
        # Test 3.1: Load credentials
        self.total_tests += 1
        try:
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            self.print_success("Credentials loaded successfully")
            self.print_info(f"Service account: {credentials.service_account_email}")
        except Exception as e:
            self.print_error(f"Failed to load credentials: {e}")
            return False
        
        # Test 3.2: Create session
        self.total_tests += 1
        try:
            from google.auth.transport.requests import AuthorizedSession
            session = AuthorizedSession(credentials)
            self.print_success("Authorized session created")
        except Exception as e:
            self.print_error(f"Failed to create session: {e}")
            return False
        
        # Test 3.3: Test token
        self.total_tests += 1
        try:
            token = credentials.token
            if token:
                self.print_success("Access token generated")
            else:
                self.print_warning("No access token available (this might be normal)")
        except Exception as e:
            self.print_warning(f"Token generation issue: {e}")
        
        return True
    
    def test_step_4_gcp_client(self) -> bool:
        """Test Step 4: GCP CFD Client"""
        self.print_header("STEP 4: GCP CFD CLIENT")
        
        # Test 4.1: Import client
        self.total_tests += 1
        try:
            sys.path.append('backend')
            from gcp_cfd_client import GCPCFDClient
            self.print_success("GCP CFD client imported")
        except Exception as e:
            self.print_error(f"Failed to import GCP CFD client: {e}")
            return False
        
        # Test 4.2: Initialize client
        self.total_tests += 1
        try:
            client = GCPCFDClient()
            self.print_success("GCP CFD client initialized")
        except Exception as e:
            self.print_error(f"Failed to initialize client: {e}")
            return False
        
        # Test 4.3: Set function URL
        self.total_tests += 1
        try:
            client.set_function_url(self.function_name, self.region)
            self.print_success("Function URL set")
            self.print_info(f"Function URL: {client.function_url}")
        except Exception as e:
            self.print_error(f"Failed to set function URL: {e}")
            return False
        
        return True
    
    def test_step_5_cloud_function(self) -> bool:
        """Test Step 5: Cloud Function Deployment"""
        self.print_header("STEP 5: CLOUD FUNCTION DEPLOYMENT")
        
        # Test 5.1: Check gcloud CLI
        self.total_tests += 1
        try:
            result = subprocess.run(['gcloud', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.print_success("gcloud CLI is available")
            else:
                self.print_error("gcloud CLI not found")
                if self.ask_yes_no("Do you want to install gcloud CLI?"):
                    self.print_info("Please install gcloud CLI from: https://cloud.google.com/sdk/docs/install")
                return False
        except:
            self.print_error("gcloud CLI not found")
            return False
        
        # Test 5.2: Check authentication
        self.total_tests += 1
        try:
            result = subprocess.run(['gcloud', 'auth', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            if 'ACTIVE' in result.stdout:
                self.print_success("gcloud authentication is active")
            else:
                self.print_error("No active gcloud authentication")
                if self.ask_yes_no("Do you want to authenticate with gcloud?"):
                    self.run_command(['gcloud', 'auth', 'login'], "Authenticating with gcloud")
                return False
        except:
            self.print_error("gcloud authentication check failed")
            return False
        
        # Test 5.3: Check project
        self.total_tests += 1
        try:
            result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                                  capture_output=True, text=True, timeout=10)
            if self.project_id in result.stdout:
                self.print_success(f"Project is set to {self.project_id}")
            else:
                self.print_warning(f"Project not set to {self.project_id}")
                if self.ask_yes_no(f"Set project to {self.project_id}?"):
                    self.run_command(['gcloud', 'config', 'set', 'project', self.project_id], 
                                   "Setting gcloud project")
        except:
            self.print_error("gcloud project check failed")
            return False
        
        # Test 5.4: Check function deployment
        self.total_tests += 1
        try:
            result = subprocess.run([
                'gcloud', 'functions', 'describe', self.function_name,
                '--region', self.region
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.print_success("Cloud Function is deployed")
            else:
                self.print_warning("Cloud Function not deployed yet")
                if self.ask_yes_no("Deploy the Cloud Function now?"):
                    if os.path.exists("deploy_gcp_function.sh"):
                        os.chmod("deploy_gcp_function.sh", 0o755)
                        self.run_command(["./deploy_gcp_function.sh"], "Deploying Cloud Function")
                    else:
                        self.print_error("Deployment script not found")
                return False
        except:
            self.print_error("Function deployment check failed")
            return False
        
        return True
    
    def test_step_6_connectivity(self) -> bool:
        """Test Step 6: Function Connectivity"""
        self.print_header("STEP 6: FUNCTION CONNECTIVITY")
        
        # Test 6.1: Test function URL
        self.total_tests += 1
        try:
            import requests
            function_url = f"https://{self.region}-{self.project_id}.cloudfunctions.net/{self.function_name}"
            response = requests.get(f"{function_url}/health", timeout=10)
            
            if response.status_code == 200:
                self.print_success("Function is accessible and healthy")
            elif response.status_code in [401, 403]:
                self.print_success("Function is accessible (authentication required)")
            else:
                self.print_warning(f"Function responded with status: {response.status_code}")
        except Exception as e:
            self.print_error(f"Function connectivity test failed: {e}")
            return False
        
        # Test 6.2: Test authenticated connection
        self.total_tests += 1
        try:
            sys.path.append('backend')
            from gcp_cfd_client import GCPCFDClient
            
            client = GCPCFDClient()
            client.set_function_url(self.function_name, self.region)
            
            if client.test_connection():
                self.print_success("Authenticated connection test passed")
            else:
                self.print_error("Authenticated connection test failed")
                return False
        except Exception as e:
            self.print_error(f"Authenticated connection test crashed: {e}")
            return False
        
        return True
    
    def run_interactive_test(self) -> bool:
        """Run the complete interactive test suite"""
        print("🎮 INTERACTIVE GOOGLE CLOUD PLATFORM TEST")
        print("=" * 60)
        print("This test will guide you through each step and help fix issues!")
        print("=" * 60)
        
        if not self.ask_yes_no("Ready to start the interactive test?"):
            print("👋 Test cancelled. Run again when ready!")
            return False
        
        test_steps = [
            ("Environment Setup", self.test_step_1_environment),
            ("Package Installation", self.test_step_2_packages),
            ("Google Cloud Authentication", self.test_step_3_authentication),
            ("GCP CFD Client", self.test_step_4_gcp_client),
            ("Cloud Function Deployment", self.test_step_5_cloud_function),
            ("Function Connectivity", self.test_step_6_connectivity)
        ]
        
        for step_name, step_func in test_steps:
            print(f"\n🎯 Starting: {step_name}")
            if not step_func():
                self.print_error(f"Step '{step_name}' failed!")
                if not self.ask_yes_no("Continue with remaining steps?"):
                    break
            else:
                self.print_success(f"Step '{step_name}' completed!")
        
        # Final results
        self.print_final_results()
        
        return self.score == self.total_tests
    
    def print_final_results(self):
        """Print final test results"""
        self.print_header("FINAL RESULTS")
        
        percentage = (self.score / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"🎯 Score: {self.score}/{self.total_tests} ({percentage:.1f}%)")
        
        if percentage == 100:
            print("🎉 PERFECT! All tests passed!")
            print("\n📋 You're ready to:")
            print("1. Run full integration test: python test_gcp_integration.py")
            print("2. Start your application: python backend/f_backend.py")
            print("3. Begin running heavy CFD simulations!")
        elif percentage >= 80:
            print("✅ EXCELLENT! Most tests passed!")
            print("\n📋 You're almost ready. Fix the remaining issues and try again.")
        elif percentage >= 60:
            print("⚠️  GOOD! More than half the tests passed.")
            print("\n📋 You're making progress. Keep fixing the issues!")
        else:
            print("❌ NEEDS WORK! Less than half the tests passed.")
            print("\n📋 Don't worry! Follow the error messages above to fix the issues.")
        
        print(f"\n🔧 To run this test again: python {__file__}")

def main():
    """Run interactive test"""
    tester = InteractiveGCPTest()
    success = tester.run_interactive_test()
    
    if success:
        print("\n🚀 Ready to deploy and run heavy CFD simulations!")
    else:
        print("\n🔧 Keep working on the issues above. You'll get there!")

if __name__ == "__main__":
    main()
