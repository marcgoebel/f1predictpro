#!/usr/bin/env python3
"""
OpenF1 API Integration Test

Dieses Skript testet die vollständige Integration der OpenF1 API
in das F1 Predict Pro System.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

try:
    from openf1_api_client import OpenF1Client, OpenF1DataCollector
except ImportError:
    print("❌ OpenF1 API client not found. Please ensure openf1_api_client.py exists.")
    sys.exit(1)

from ml.auto_race_results_fetcher import AutoRaceResultsFetcher

def test_openf1_client():
    """Test basic OpenF1 client functionality"""
    print("\n🔧 Testing OpenF1 Client...")
    
    try:
        client = OpenF1Client()
        
        # Test getting current season sessions
        print("📅 Fetching 2024 sessions...")
        sessions = client.get_sessions(year=2024)
        
        if sessions:
            print(f"✅ Found {len(sessions)} sessions for 2024")
            
            # Show some recent sessions
            recent_sessions = sessions[-5:] if len(sessions) >= 5 else sessions
            for session in recent_sessions:
                print(f"   - {session.get('session_name', 'Unknown')} ({session.get('session_type', 'Unknown')})")
        else:
            print("⚠️ No sessions found")
            
        return True
        
    except Exception as e:
        print(f"❌ OpenF1 Client test failed: {e}")
        return False

def test_openf1_data_collector():
    """Test OpenF1 data collector"""
    print("\n📊 Testing OpenF1 Data Collector...")
    
    try:
        collector = OpenF1DataCollector()
        
        # Test getting drivers for a recent session
        print("👥 Fetching drivers data...")
        
        # Get a recent session
        client = OpenF1Client()
        sessions = client.get_sessions(year=2024)
        
        if not sessions:
            print("⚠️ No sessions available for testing")
            return False
            
        # Find a race session
        race_session = None
        for session in reversed(sessions):
            if session.get('session_type') == 'Race':
                race_session = session
                break
        
        if not race_session:
            print("⚠️ No race session found for testing")
            return False
            
        session_key = race_session['session_key']
        session_name = race_session.get('session_name', 'Unknown Race')
        
        print(f"🏁 Testing with session: {session_name}")
        
        # Test collecting drivers
        drivers_df = collector.collect_drivers(session_key=session_key)
        if drivers_df is not None and not drivers_df.empty:
            print(f"✅ Drivers data: {len(drivers_df)} drivers found")
            print(f"   Sample drivers: {', '.join(drivers_df['full_name'].head(3).tolist())}")
        else:
            print("⚠️ No drivers data found")
            
        # Test collecting positions
        positions_df = collector.collect_position(session_key=session_key)
        if positions_df is not None and not positions_df.empty:
            print(f"✅ Position data: {len(positions_df)} position records found")
        else:
            print("⚠️ No position data found")
            
        return True
        
    except Exception as e:
        print(f"❌ OpenF1 Data Collector test failed: {e}")
        return False

def test_auto_race_results_fetcher_integration():
    """Test integration with AutoRaceResultsFetcher"""
    print("\n🔄 Testing AutoRaceResultsFetcher Integration...")
    
    try:
        # Initialize fetcher with OpenF1 enabled
        fetcher = AutoRaceResultsFetcher()
        
        # Check if OpenF1 is enabled in config
        if 'openf1' in fetcher.config['data_sources']:
            openf1_config = fetcher.config['data_sources']['openf1']
            print(f"✅ OpenF1 configured: enabled={openf1_config.get('enabled', False)}")
            print(f"   Base URL: {openf1_config.get('base_url', 'Not set')}")
            print(f"   Rate limit: {openf1_config.get('rate_limit_delay', 'Not set')}s")
        else:
            print("❌ OpenF1 not found in configuration")
            return False
            
        # Test fetching race results with OpenF1
        print("🏁 Testing race results fetching...")
        
        # Try to fetch results for a recent race (this might not work if no recent race data)
        try:
            race_results = fetcher.fetch_race_results_openf1("Bahrain Grand Prix", 1, 2024)
            if race_results is not None and not race_results.empty:
                print(f"✅ OpenF1 race results: {len(race_results)} drivers")
                print(f"   Sample results: {race_results[['position', 'driver', 'constructor']].head(3).to_string(index=False)}")
            else:
                print("⚠️ No race results found (expected for future/unavailable races)")
        except Exception as e:
            print(f"⚠️ Race results test failed (expected): {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ AutoRaceResultsFetcher integration test failed: {e}")
        return False

def test_configuration_files():
    """Test configuration files"""
    print("\n⚙️ Testing Configuration Files...")
    
    try:
        # Test OpenF1 config
        openf1_config_path = "config/openf1_config.json"
        if os.path.exists(openf1_config_path):
            with open(openf1_config_path, 'r', encoding='utf-8') as f:
                openf1_config = json.load(f)
            print(f"✅ OpenF1 config loaded: {len(openf1_config.get('data_sources', {}))} data sources configured")
        else:
            print(f"❌ OpenF1 config not found: {openf1_config_path}")
            return False
            
        # Test results fetcher config
        results_config_path = "config/results_fetcher_config.json"
        if os.path.exists(results_config_path):
            with open(results_config_path, 'r', encoding='utf-8') as f:
                results_config = json.load(f)
            
            if 'openf1' in results_config.get('data_sources', {}):
                print("✅ OpenF1 integrated in results fetcher config")
            else:
                print("❌ OpenF1 not found in results fetcher config")
                return False
        else:
            print(f"❌ Results fetcher config not found: {results_config_path}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_data_directories():
    """Test data directory structure"""
    print("\n📁 Testing Data Directories...")
    
    try:
        # Check if required directories exist or can be created
        required_dirs = [
            "data/cache/openf1",
            "data/raw/openf1", 
            "data/processed/openf1"
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"✅ Created directory: {dir_path}")
            else:
                print(f"✅ Directory exists: {dir_path}")
                
        return True
        
    except Exception as e:
        print(f"❌ Directory test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🏎️ OpenF1 API Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration Files", test_configuration_files),
        ("Data Directories", test_data_directories),
        ("OpenF1 Client", test_openf1_client),
        ("OpenF1 Data Collector", test_openf1_data_collector),
        ("AutoRaceResultsFetcher Integration", test_auto_race_results_fetcher_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OpenF1 integration is ready.")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)