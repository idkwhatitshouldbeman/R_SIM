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
    print("Testing Supabase connection...")
    
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
            print("PASS Supabase connection")
            return True
        else:
            print("FAIL Supabase connection")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print("FAIL Supabase connection")
        print(f"Error: {e}")
        return False

def test_simulation_status_crud():
    """Test CRUD operations on simulation_status table"""
    print("\nTesting simulation_status CRUD operations...")
    
    headers = {
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json'
    }
    
    # Generate unique simulation ID
    simulation_id = f"test-sim-{int(time.time())}"
    
    try:
        # CREATE - Insert new simulation status
        print("Creating simulation status...")
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
            print("PASS Create simulation status")
        else:
            print("FAIL Create simulation status")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # READ - Get simulation status
        print("Reading simulation status...")
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/simulation_status?simulation_id=eq.{simulation_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data:
                print("PASS Read simulation status")
                print(f"Status: {data[0]['status']}")
                print(f"Progress: {data[0]['progress']}")
            else:
                print("FAIL Read simulation status - No data returned")
                return False
        else:
            print("FAIL Read simulation status")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # UPDATE - Update simulation status
        print("Updating simulation status...")
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
        
        if response.status_code in [200, 204]:
            print("PASS Update simulation status")
        else:
            print("FAIL Update simulation status")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
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
                print("PASS Verify update")
            else:
                print("FAIL Verify update")
                print(f"Expected status: Running, Got: {data[0]['status'] if data else 'No data'}")
                return False
        else:
            print("FAIL Verify update")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print("FAIL CRUD operations")
        print(f"Error: {e}")
        return False

def test_simulation_results():
    """Test simulation_results table operations"""
    print("\nTesting simulation_results operations...")
    
    headers = {
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json'
    }
    
    simulation_id = f"test-sim-{int(time.time())}"
    
    try:
        # Insert simulation results
        print("Creating simulation results...")
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
            print("PASS Create simulation results")
        else:
            print("FAIL Create simulation results")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Read simulation results
        print("Reading simulation results...")
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/simulation_results?simulation_id=eq.{simulation_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data:
                print("PASS Read simulation results")
                print(f"Max Altitude: {data[0]['results']['max_altitude']}")
                print(f"Max Velocity: {data[0]['results']['max_velocity']}")
            else:
                print("FAIL Read simulation results - No data returned")
                return False
        else:
            print("FAIL Read simulation results")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print("FAIL Simulation results")
        print(f"Error: {e}")
        return False

def test_storage_bucket():
    """Test storage bucket access"""
    print("\nTesting storage bucket access...")
    
    headers = {
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'apikey': SUPABASE_ANON_KEY
    }
    
    try:
        # Try to get bucket info instead of listing files
        response = requests.get(
            f"{SUPABASE_URL}/storage/v1/bucket/mesh-files",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("PASS Storage bucket access")
            bucket_info = response.json()
            print(f"Bucket: {bucket_info.get('name', 'mesh-files')}")
            print(f"Public: {bucket_info.get('public', False)}")
        else:
            print("FAIL Storage bucket access")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print("FAIL Storage bucket")
        print(f"Error: {e}")
        return False

def main():
    """Run all Supabase integration tests"""
    print("SUPABASE INTEGRATION TEST SUITE")
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
            print(f"FAIL {test_name}")
            print(f"Error: {e}")
            results.append((test_name, False))
    
    # Print results
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n{passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\nAll tests passed! Supabase integration is ready!")
        print("\nNext steps:")
        print("1. Deploy the Cloud Function: gcloud functions deploy rocket-cfd-simulator --runtime python311 --trigger-http --allow-unauthenticated")
        print("2. Test the full integration: py test_gcp_integration.py")
    else:
        print("\nSome tests failed. Check the errors above.")
        print("\nCommon fixes:")
        print("- Make sure the database schema is set up (run supabase_schema.sql)")
        print("- Check your Supabase project settings")
        print("- Verify the API keys are correct")

if __name__ == "__main__":
    main()
