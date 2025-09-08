#!/usr/bin/env python3
"""Test Supabase integration for R_SIM"""

import requests
import json
import time
import uuid

# Supabase configuration
SUPABASE_URL = "https://ovwgplglypjfuqsflyhc.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im92d2dwbGdseXBqZnVxc2ZseWhjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcyOTQ0MDgsImV4cCI6MjA3Mjg3MDQwOH0.YTjAKmshWQ5rFG9an2de8UHu9NA-03U8B6km8XLmjC0"

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🔍 Testing Supabase connection...")
    
    headers = {
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        # Test connection by querying simulation_status table
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/simulation_status?select=*&limit=1",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Supabase connection successful!")
            return True
        else:
            print(f"❌ Supabase connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False

def test_simulation_status_crud():
    """Test CRUD operations on simulation_status table"""
    print("\n🔍 Testing simulation_status CRUD operations...")
    
    headers = {
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json'
    }
    
    # Generate unique simulation ID
    simulation_id = f"test-sim-{int(time.time())}"
    
    try:
        # CREATE - Insert new simulation status
        print("📝 Creating simulation status...")
        create_data = {
            'simulation_id': simulation_id,
            'status': 'Initializing',
            'progress': 0,
            'message': 'Test simulation created'
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/simulation_status",
            headers=headers,
            json=create_data,
            timeout=10
        )
        
        if response.status_code == 201:
            print("✅ Simulation status created successfully!")
        else:
            print(f"❌ Failed to create simulation status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # READ - Get simulation status
        print("📖 Reading simulation status...")
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/simulation_status?simulation_id=eq.{simulation_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data:
                print("✅ Simulation status read successfully!")
                print(f"   Status: {data[0]['status']}")
                print(f"   Progress: {data[0]['progress']}")
            else:
                print("❌ No data returned")
                return False
        else:
            print(f"❌ Failed to read simulation status: {response.status_code}")
            return False
        
        # UPDATE - Update simulation status
        print("✏️  Updating simulation status...")
        update_data = {
            'status': 'Running',
            'progress': 50,
            'message': 'Simulation in progress'
        }
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/simulation_status?simulation_id=eq.{simulation_id}",
            headers=headers,
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Simulation status updated successfully!")
        else:
            print(f"❌ Failed to update simulation status: {response.status_code}")
            return False
        
        # Verify update
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/simulation_status?simulation_id=eq.{simulation_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and data[0]['status'] == 'Running':
                print("✅ Update verified successfully!")
            else:
                print("❌ Update verification failed")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations error: {e}")
        return False

def test_simulation_results():
    """Test simulation_results table operations"""
    print("\n🔍 Testing simulation_results operations...")
    
    headers = {
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json'
    }
    
    simulation_id = f"test-sim-{int(time.time())}"
    
    try:
        # Insert simulation results
        print("📝 Creating simulation results...")
        results_data = {
            'simulation_id': simulation_id,
            'results': {
                'max_altitude': 850.5,
                'max_velocity': 300.2,
                'drag_coefficient': 0.45,
                'computation_time': 120.5
            }
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/simulation_results",
            headers=headers,
            json=results_data,
            timeout=10
        )
        
        if response.status_code == 201:
            print("✅ Simulation results created successfully!")
        else:
            print(f"❌ Failed to create simulation results: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Read simulation results
        print("📖 Reading simulation results...")
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/simulation_results?simulation_id=eq.{simulation_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data:
                print("✅ Simulation results read successfully!")
                print(f"   Max Altitude: {data[0]['results']['max_altitude']}")
                print(f"   Max Velocity: {data[0]['results']['max_velocity']}")
            else:
                print("❌ No results data returned")
                return False
        else:
            print(f"❌ Failed to read simulation results: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Simulation results error: {e}")
        return False

def test_storage_bucket():
    """Test storage bucket access"""
    print("\n🔍 Testing storage bucket access...")
    
    headers = {
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'apikey': SUPABASE_ANON_KEY
    }
    
    try:
        # List files in mesh-files bucket
        response = requests.get(
            f"{SUPABASE_URL}/storage/v1/object/list/mesh-files",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Storage bucket access successful!")
            files = response.json()
            print(f"   Found {len(files)} files in mesh-files bucket")
        else:
            print(f"❌ Storage bucket access failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Storage bucket error: {e}")
        return False

def main():
    """Run all Supabase integration tests"""
    print("🚀 SUPABASE INTEGRATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Supabase Connection", test_supabase_connection),
        ("Simulation Status CRUD", test_simulation_status_crud),
        ("Simulation Results", test_simulation_results),
        ("Storage Bucket", test_storage_bucket)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Supabase integration is ready!")
        print("\n📋 Next steps:")
        print("1. Deploy the Cloud Function: gcloud functions deploy rocket-cfd-simulator --runtime python311 --trigger-http --allow-unauthenticated")
        print("2. Test the full integration: py test_gcp_integration.py")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\n🔧 Common fixes:")
        print("- Make sure the database schema is set up (run supabase_schema.sql)")
        print("- Check your Supabase project settings")
        print("- Verify the API keys are correct")

if __name__ == "__main__":
    main()
