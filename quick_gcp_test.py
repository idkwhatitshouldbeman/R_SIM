#!/usr/bin/env python3
"""
Quick Google Cloud Platform Test
Tests authentication and basic connectivity
"""

import os
import sys
import json

def test_service_account_file():
    """Test if the service account file is valid"""
    print("🔍 Testing service account file...")
    
    service_account_path = "centered-scion-471523-a4-b8125d43fa7a.json"
    
    if not os.path.exists(service_account_path):
        print(f"❌ Service account file not found: {service_account_path}")
        return False
    
    try:
        with open(service_account_path, 'r') as f:
            sa_data = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in sa_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        print(f"✅ Service account file is valid")
        print(f"📧 Client email: {sa_data['client_email']}")
        print(f"🏗️  Project ID: {sa_data['project_id']}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in service account file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading service account file: {e}")
        return False

def test_google_auth_imports():
    """Test if Google Auth libraries are available"""
    print("\n🔍 Testing Google Auth imports...")
    
    try:
        from google.oauth2 import service_account
        print("✅ google.oauth2.service_account imported")
    except ImportError as e:
        print(f"❌ Failed to import google.oauth2.service_account: {e}")
        print("💡 Run: pip install google-auth")
        return False
    
    try:
        from google.auth.transport.requests import AuthorizedSession
        print("✅ google.auth.transport.requests imported")
    except ImportError as e:
        print(f"❌ Failed to import AuthorizedSession: {e}")
        return False
    
    try:
        import requests
        print("✅ requests library imported")
    except ImportError as e:
        print(f"❌ Failed to import requests: {e}")
        print("💡 Run: pip install requests")
        return False
    
    return True

def test_authentication():
    """Test Google Cloud authentication"""
    print("\n🔍 Testing Google Cloud authentication...")
    
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
        
        service_account_path = "centered-scion-471523-a4-b8125d43fa7a.json"
        
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        print("✅ Credentials loaded successfully")
        print(f"📧 Service account: {credentials.service_account_email}")
        
        # Create authorized session
        authed_session = AuthorizedSession(credentials)
        print("✅ Authorized session created")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

def test_gcp_cfd_client():
    """Test the GCP CFD client"""
    print("\n🔍 Testing GCP CFD client...")
    
    try:
        # Add backend to path
        sys.path.append('backend')
        from gcp_cfd_client import GCPCFDClient
        
        print("✅ GCP CFD client imported successfully")
        
        # Initialize client
        client = GCPCFDClient()
        print("✅ GCP CFD client initialized")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import GCP CFD client: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize GCP CFD client: {e}")
        return False

def test_function_url():
    """Test if we can construct a valid function URL"""
    print("\n🔍 Testing function URL construction...")
    
    project_id = "centered-scion-471523-a4"
    function_name = "rocket-cfd-simulator"
    region = "us-central1"
    
    function_url = f"https://{region}-{project_id}.cloudfunctions.net/{function_name}"
    print(f"🔗 Function URL: {function_url}")
    
    # Test if we can make a basic request (without authentication for now)
    try:
        import requests
        response = requests.get(f"{function_url}/health", timeout=10)
        print(f"📊 Health check response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Function is deployed and accessible!")
            return True
        elif response.status_code == 401:
            print("✅ Function is deployed (authentication required)")
            return True
        else:
            print(f"⚠️  Function responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not reach function: {e}")
        print("💡 Make sure the function is deployed first")
        return False

def main():
    """Run all tests"""
    print("🧪 Google Cloud Platform Quick Test")
    print("=" * 50)
    
    tests = [
        ("Service Account File", test_service_account_file),
        ("Google Auth Imports", test_google_auth_imports),
        ("Authentication", test_authentication),
        ("GCP CFD Client", test_gcp_cfd_client),
        ("Function URL", test_function_url)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your GCP setup is ready!")
        print("\n📋 Next steps:")
        print("1. Deploy the Cloud Function: ./deploy_gcp_function.sh")
        print("2. Run the full test: python test_gcp_integration.py")
        print("3. Start your application: python backend/f_backend.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Deploy the Cloud Function first")
        print("- Check your service account permissions")

if __name__ == "__main__":
    main()
