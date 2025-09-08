#!/usr/bin/env python3
"""
Fix Google Cloud Platform Issues
Automatically fixes common GCP setup issues
"""

import os
import sys
import subprocess
import json
from typing import List, Tuple

class GCPIssueFixer:
    """Automatically fixes common GCP setup issues"""
    
    def __init__(self):
        self.fixes_applied = []
        self.project_id = "centered-scion-471523-a4"
        self.service_account_file = "centered-scion-471523-a4-b8125d43fa7a.json"
    
    def fix_missing_packages(self) -> bool:
        """Fix missing Google Auth packages"""
        print("🔧 Fixing missing Google Auth packages...")
        
        packages_to_install = [
            "google-auth==2.23.4",
            "google-auth-oauthlib==1.1.0", 
            "google-auth-httplib2==0.1.1",
            "google-cloud-storage==2.10.0",
            "google-cloud-logging==3.8.0",
            "requests==2.31.0"
        ]
        
        try:
            for package in packages_to_install:
                print(f"📦 Installing {package}...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print(f"✅ {package} installed successfully")
                    self.fixes_applied.append(f"Installed {package}")
                else:
                    print(f"❌ Failed to install {package}: {result.stderr}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error installing packages: {e}")
            return False
    
    def fix_requirements_file(self) -> bool:
        """Fix requirements.txt file"""
        print("🔧 Fixing requirements.txt file...")
        
        try:
            # Read current requirements
            current_requirements = []
            if os.path.exists("requirements.txt"):
                with open("requirements.txt", 'r') as f:
                    current_requirements = f.read().strip().split('\n')
            
            # Add missing packages
            required_packages = [
                "flask==3.0.0",
                "flask-cors==4.0.0", 
                "numpy==1.24.3",
                "google-auth==2.23.4",
                "google-auth-oauthlib==1.1.0",
                "google-auth-httplib2==0.1.1",
                "google-cloud-storage==2.10.0",
                "google-cloud-logging==3.8.0",
                "requests==2.31.0"
            ]
            
            # Merge requirements
            all_requirements = list(set(current_requirements + required_packages))
            all_requirements.sort()
            
            # Write updated requirements
            with open("requirements.txt", 'w') as f:
                f.write('\n'.join(all_requirements) + '\n')
            
            print("✅ requirements.txt updated")
            self.fixes_applied.append("Updated requirements.txt")
            return True
            
        except Exception as e:
            print(f"❌ Error updating requirements.txt: {e}")
            return False
    
    def fix_gcloud_setup(self) -> bool:
        """Fix gcloud CLI setup"""
        print("🔧 Fixing gcloud CLI setup...")
        
        try:
            # Check if gcloud is installed
            result = subprocess.run(['gcloud', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print("❌ gcloud CLI not found. Please install it first:")
                print("   https://cloud.google.com/sdk/docs/install")
                return False
            
            print("✅ gcloud CLI is installed")
            
            # Check authentication
            result = subprocess.run(['gcloud', 'auth', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            
            if 'ACTIVE' not in result.stdout:
                print("⚠️  No active authentication found.")
                print("💡 Run: gcloud auth login")
                return False
            
            print("✅ gcloud authentication is active")
            
            # Set project
            result = subprocess.run(['gcloud', 'config', 'set', 'project', self.project_id], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"✅ Project set to {self.project_id}")
                self.fixes_applied.append(f"Set gcloud project to {self.project_id}")
            else:
                print(f"❌ Failed to set project: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error fixing gcloud setup: {e}")
            return False
    
    def fix_service_account_permissions(self) -> bool:
        """Check and fix service account permissions"""
        print("🔧 Checking service account permissions...")
        
        try:
            # Read service account file
            with open(self.service_account_file, 'r') as f:
                sa_data = json.load(f)
            
            client_email = sa_data.get('client_email')
            print(f"📧 Service account: {client_email}")
            
            # Check if service account has required roles
            required_roles = [
                "roles/cloudfunctions.invoker",
                "roles/cloudfunctions.developer",
                "roles/storage.objectViewer"
            ]
            
            print("🔍 Checking service account roles...")
            for role in required_roles:
                result = subprocess.run([
                    'gcloud', 'projects', 'get-iam-policy', self.project_id,
                    '--flatten', 'bindings[].members',
                    '--format', 'table(bindings.role)',
                    '--filter', f'bindings.members:{client_email}'
                ], capture_output=True, text=True, timeout=30)
                
                if role in result.stdout:
                    print(f"✅ {role}")
                else:
                    print(f"⚠️  Missing role: {role}")
                    print(f"💡 Grant role: gcloud projects add-iam-policy-binding {self.project_id} --member='serviceAccount:{client_email}' --role='{role}'")
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking service account permissions: {e}")
            return False
    
    def fix_function_deployment(self) -> bool:
        """Fix Cloud Function deployment"""
        print("🔧 Fixing Cloud Function deployment...")
        
        try:
            # Check if deployment script exists
            if not os.path.exists("deploy_gcp_function.sh"):
                print("❌ Deployment script not found")
                return False
            
            # Make script executable
            os.chmod("deploy_gcp_function.sh", 0o755)
            print("✅ Made deployment script executable")
            
            # Check if function is already deployed
            result = subprocess.run([
                'gcloud', 'functions', 'describe', 'rocket-cfd-simulator',
                '--region', 'us-central1'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Cloud Function is already deployed")
                return True
            else:
                print("⚠️  Cloud Function not deployed yet")
                print("💡 Run: ./deploy_gcp_function.sh")
                return False
                
        except Exception as e:
            print(f"❌ Error checking function deployment: {e}")
            return False
    
    def fix_import_issues(self) -> bool:
        """Fix Python import issues"""
        print("🔧 Fixing Python import issues...")
        
        try:
            # Test imports after package installation
            test_imports = [
                ("google.oauth2.service_account", "Google OAuth2 Service Account"),
                ("google.auth.transport.requests", "Google Auth Transport"),
                ("requests", "Requests HTTP Library")
            ]
            
            for module, name in test_imports:
                try:
                    __import__(module)
                    print(f"✅ {name} import successful")
                except ImportError as e:
                    print(f"❌ {name} import failed: {e}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing imports: {e}")
            return False
    
    def fix_all_issues(self) -> bool:
        """Fix all common GCP issues"""
        print("🔧 GOOGLE CLOUD PLATFORM ISSUE FIXER")
        print("=" * 50)
        
        fixes = [
            ("Fix requirements.txt", self.fix_requirements_file),
            ("Install missing packages", self.fix_missing_packages),
            ("Fix import issues", self.fix_import_issues),
            ("Fix gcloud setup", self.fix_gcloud_setup),
            ("Check service account permissions", self.fix_service_account_permissions),
            ("Check function deployment", self.fix_function_deployment)
        ]
        
        for fix_name, fix_func in fixes:
            print(f"\n🔧 {fix_name}...")
            try:
                result = fix_func()
                if result:
                    print(f"✅ {fix_name} completed")
                else:
                    print(f"❌ {fix_name} failed")
            except Exception as e:
                print(f"❌ {fix_name} crashed: {e}")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 FIXES APPLIED:")
        print("=" * 50)
        
        if self.fixes_applied:
            for fix in self.fixes_applied:
                print(f"✅ {fix}")
        else:
            print("⚠️  No fixes were applied")
        
        print("\n📋 NEXT STEPS:")
        print("1. Run the test again: python quick_gcp_test.py")
        print("2. If tests pass, deploy the function: ./deploy_gcp_function.sh")
        print("3. Run full integration test: python test_gcp_integration.py")
        
        return len(self.fixes_applied) > 0

def main():
    """Run the issue fixer"""
    fixer = GCPIssueFixer()
    fixer.fix_all_issues()

if __name__ == "__main__":
    main()
