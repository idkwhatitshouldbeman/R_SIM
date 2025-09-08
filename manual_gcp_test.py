#!/usr/bin/env python3
"""
Manual Google Cloud Platform Test
Step-by-step testing without external dependencies
"""

import json
import os

def step1_check_service_account():
    """Step 1: Check service account file"""
    print("Step 1: Checking service account file...")
    
    sa_file = "centered-scion-471523-a4-b8125d43fa7a.json"
    
    if not os.path.exists(sa_file):
        print(f"❌ File not found: {sa_file}")
        return False
    
    try:
        with open(sa_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ File exists and is valid JSON")
        print(f"📧 Client email: {data.get('client_email', 'N/A')}")
        print(f"🏗️  Project ID: {data.get('project_id', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def step2_check_packages():
    """Step 2: Check if required packages are installed"""
    print("\nStep 2: Checking required packages...")
    
    packages = [
        'google-auth',
        'google-auth-oauthlib', 
        'google-auth-httplib2',
        'requests'
    ]
    
    missing = []
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n💡 Install missing packages:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def step3_test_imports():
    """Step 3: Test Google Auth imports"""
    print("\nStep 3: Testing Google Auth imports...")
    
    try:
        from google.oauth2 import service_account
        print("✅ google.oauth2.service_account")
    except ImportError as e:
        print(f"❌ google.oauth2.service_account: {e}")
        return False
    
    try:
        from google.auth.transport.requests import AuthorizedSession
        print("✅ google.auth.transport.requests.AuthorizedSession")
    except ImportError as e:
        print(f"❌ AuthorizedSession: {e}")
        return False
    
    return True

def step4_test_credentials():
    """Step 4: Test loading credentials"""
    print("\nStep 4: Testing credential loading...")
    
    try:
        from google.oauth2 import service_account
        
        sa_file = "centered-scion-471523-a4-b8125d43fa7a.json"
        credentials = service_account.Credentials.from_service_account_file(
            sa_file,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        print("✅ Credentials loaded successfully")
        print(f"📧 Service account: {credentials.service_account_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to load credentials: {e}")
        return False

def step5_test_session():
    """Step 5: Test creating authorized session"""
    print("\nStep 5: Testing authorized session...")
    
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
        
        sa_file = "centered-scion-471523-a4-b8125d43fa7a.json"
        credentials = service_account.Credentials.from_service_account_file(
            sa_file,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        session = AuthorizedSession(credentials)
        print("✅ Authorized session created")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        return False

def step6_test_function_url():
    """Step 6: Test function URL construction"""
    print("\nStep 6: Testing function URL...")
    
    project_id = "centered-scion-471523-a4"
    function_name = "rocket-cfd-simulator"
    region = "us-central1"
    
    function_url = f"https://{region}-{project_id}.cloudfunctions.net/{function_name}"
    print(f"🔗 Function URL: {function_url}")
    
    # Test basic connectivity
    try:
        import requests
        print("🧪 Testing basic connectivity...")
        
        # Try to reach the function (might get 401, which is expected)
        response = requests.get(f"{function_url}/health", timeout=5)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code in [200, 401, 403]:
            print("✅ Function is reachable!")
            return True
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach function: {e}")
        print("💡 Function might not be deployed yet")
        return False

def main():
    """Run manual tests step by step"""
    print("🧪 Manual Google Cloud Platform Test")
    print("=" * 50)
    
    steps = [
        ("Service Account File", step1_check_service_account),
        ("Required Packages", step2_check_packages),
        ("Google Auth Imports", step3_test_imports),
        ("Credential Loading", step4_test_credentials),
        ("Authorized Session", step5_test_session),
        ("Function URL", step6_test_function_url)
    ]
    
    results = []
    
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append((step_name, result))
            
            if not result:
                print(f"\n❌ Stopping at failed step: {step_name}")
                break
                
        except Exception as e:
            print(f"❌ Step crashed: {e}")
            results.append((step_name, False))
            break
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("=" * 50)
    
    for step_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {step_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n🎯 {passed}/{total} steps completed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for deployment!")
        print("\n📋 Next steps:")
        print("1. Deploy Cloud Function: ./deploy_gcp_function.sh")
        print("2. Run full test: python test_gcp_integration.py")
    else:
        print("\n⚠️  Some steps failed. Fix the issues above first.")

if __name__ == "__main__":
    main()
