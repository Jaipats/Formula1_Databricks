#!/usr/bin/env python3
"""
Diagnostic script to check car_data availability for different years
"""
import requests
import sys

def check_car_data_availability(year: int, sample_size: int = 3):
    """Check if car_data is available for a given year"""
    base_url = "https://api.openf1.org/v1"
    
    print(f"\n{'='*70}")
    print(f"Checking car_data availability for {year}")
    print(f"{'='*70}\n")
    
    # Step 1: Get sessions for the year
    print(f"1. Fetching sessions for {year}...")
    sessions_url = f"{base_url}/sessions"
    sessions_response = requests.get(sessions_url, params={'year': year})
    
    if sessions_response.status_code != 200:
        print(f"   ❌ Failed to fetch sessions: {sessions_response.status_code}")
        return
    
    sessions = sessions_response.json()
    print(f"   ✅ Found {len(sessions)} sessions for {year}")
    
    if not sessions:
        print(f"   ⚠️  No sessions found for {year}")
        return
    
    # Sample a few sessions
    sample_sessions = sessions[:sample_size]
    print(f"   Checking first {len(sample_sessions)} sessions...\n")
    
    available_count = 0
    unavailable_count = 0
    
    for session in sample_sessions:
        session_key = session['session_key']
        session_name = session.get('session_name', 'Unknown')
        meeting_name = session.get('meeting_official_name', 'Unknown')
        
        print(f"2. Session: {meeting_name} - {session_name} (key: {session_key})")
        
        # Step 2: Get drivers for this session
        drivers_url = f"{base_url}/drivers"
        drivers_response = requests.get(drivers_url, params={'session_key': session_key})
        
        if drivers_response.status_code != 200:
            print(f"   ❌ Failed to fetch drivers: {drivers_response.status_code}")
            continue
        
        drivers = drivers_response.json()
        if not drivers:
            print(f"   ⚠️  No drivers found")
            continue
        
        print(f"   Found {len(drivers)} drivers")
        
        # Step 3: Try to get car_data for the first driver
        first_driver = drivers[0]
        driver_number = first_driver['driver_number']
        driver_name = f"{first_driver.get('first_name', '')} {first_driver.get('last_name', '')}"
        
        print(f"   Testing car_data for driver #{driver_number} ({driver_name})...")
        
        car_data_url = f"{base_url}/car_data"
        car_data_response = requests.get(car_data_url, params={
            'session_key': session_key,
            'driver_number': driver_number,
            'speed>=': 100  # With speed filter
        })
        
        if car_data_response.status_code == 200:
            car_data = car_data_response.json()
            if car_data:
                print(f"   ✅ car_data AVAILABLE: {len(car_data)} records (with speed>=100)")
                available_count += 1
            else:
                print(f"   ⚠️  car_data returns empty list (no data with speed>=100)")
                # Try without filter
                car_data_response2 = requests.get(car_data_url, params={
                    'session_key': session_key,
                    'driver_number': driver_number
                })
                if car_data_response2.status_code == 200:
                    car_data2 = car_data_response2.json()
                    if car_data2:
                        print(f"   ⚠️  BUT available WITHOUT speed filter: {len(car_data2)} records")
                        print(f"   💡 Recommendation: Lower or remove speed_gte filter")
                    else:
                        print(f"   ❌ car_data not available even without filter")
                        unavailable_count += 1
        elif car_data_response.status_code == 422:
            print(f"   ❌ car_data NOT AVAILABLE (422 error)")
            unavailable_count += 1
        else:
            print(f"   ❌ Unexpected error: {car_data_response.status_code}")
            unavailable_count += 1
        
        print()
    
    print(f"\n{'='*70}")
    print(f"SUMMARY for {year}:")
    print(f"{'='*70}")
    print(f"Sessions checked: {len(sample_sessions)}")
    print(f"✅ car_data available: {available_count}")
    print(f"❌ car_data unavailable: {unavailable_count}")
    
    if unavailable_count == len(sample_sessions):
        print(f"\n⚠️  WARNING: No car_data found for ANY session in {year}")
        print(f"💡 This likely means {year} data is incomplete or not yet available")
        print(f"💡 Recommendation: Try year 2024 or 2023 for complete data")
    elif available_count == 0 and unavailable_count < len(sample_sessions):
        print(f"\n⚠️  car_data might be available for some sessions")
        print(f"💡 Try removing or lowering the speed_gte filter")
    
    print(f"{'='*70}\n")


if __name__ == "__main__":
    # Check 2025 (current config)
    check_car_data_availability(2025, sample_size=3)
    
    # Also check 2024 for comparison
    print("\n" + "="*70)
    print("For comparison, let's also check 2024:")
    print("="*70)
    check_car_data_availability(2024, sample_size=3)
    
    print("\n" + "="*70)
    print("CONCLUSION:")
    print("="*70)
    print("""
If 2025 shows no car_data but 2024 does, you should:

1. Update config/pipeline_config.yaml:
   data:
     target_year: 2024  # Change from 2025 to 2024

2. Or wait for 2025 season to complete and data to become available

3. Or remove/lower the speed filter if it's too restrictive:
   car_data_filters:
     speed_gte: 50  # Lower from 100 to 50
     # or remove speed_gte entirely
""")

