#!/usr/bin/env python3
"""
OpenF1 Data Collection Script

Dieses Skript sammelt automatisch F1-Daten von der OpenF1 API
und speichert sie in strukturierter Form für die weitere Analyse.
"""

import os
import sys
import json
import argparse
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from openf1_api_client import OpenF1Client, OpenF1DataCollector

class OpenF1DataCollectionManager:
    """Manager für die automatische OpenF1 Datensammlung"""
    
    def __init__(self, config_file="config/openf1_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.client = OpenF1Client()
        self.collector = OpenF1DataCollector(config_file=config_file)
        
    def load_config(self):
        """Lade OpenF1 Konfiguration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Config file not found: {self.config_file}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Standard-Konfiguration"""
        return {
            "integration": {
                "auto_collect_enabled": True,
                "collect_data_types": ["drivers", "positions", "laps", "intervals", "pit_stops", "weather"]
            },
            "output_paths": {
                "raw_data": "data/raw/openf1",
                "processed_data": "data/processed/openf1"
            }
        }
    
    def get_recent_sessions(self, year=None, session_type=None, limit=10):
        """Hole aktuelle Sessions"""
        if year is None:
            year = datetime.now().year
            
        try:
            sessions = self.client.get_sessions(year=year)
            
            if session_type:
                sessions = [s for s in sessions if s.get('session_type') == session_type]
            
            # Sort by date (newest first)
            sessions.sort(key=lambda x: x.get('date_start', ''), reverse=True)
            
            return sessions[:limit]
            
        except Exception as e:
            print(f"❌ Error fetching sessions: {e}")
            return []
    
    def collect_session_data(self, session_key, session_name="Unknown", data_types=None):
        """Sammle alle Daten für eine Session"""
        if data_types is None:
            data_types = self.config['integration']['collect_data_types']
        
        print(f"\n📊 Collecting data for session: {session_name} (Key: {session_key})")
        
        collected_data = {}
        
        # Drivers
        if "drivers" in data_types:
            try:
                drivers_df = self.collector.collect_drivers(session_key=session_key)
                if drivers_df is not None and not drivers_df.empty:
                    collected_data['drivers'] = drivers_df
                    print(f"✅ Drivers: {len(drivers_df)} records")
                else:
                    print("⚠️ No drivers data")
            except Exception as e:
                print(f"❌ Drivers collection failed: {e}")
        
        # Positions
        if "positions" in data_types:
            try:
                positions_df = self.collector.collect_position(session_key=session_key)
                if positions_df is not None and not positions_df.empty:
                    collected_data['positions'] = positions_df
                    print(f"✅ Positions: {len(positions_df)} records")
                else:
                    print("⚠️ No positions data")
            except Exception as e:
                print(f"❌ Positions collection failed: {e}")
        
        # Laps
        if "laps" in data_types:
            try:
                laps_df = self.collector.collect_laps(session_key=session_key)
                if laps_df is not None and not laps_df.empty:
                    collected_data['laps'] = laps_df
                    print(f"✅ Laps: {len(laps_df)} records")
                else:
                    print("⚠️ No laps data")
            except Exception as e:
                print(f"❌ Laps collection failed: {e}")
        
        # Intervals
        if "intervals" in data_types:
            try:
                intervals_df = self.collector.collect_intervals(session_key=session_key)
                if intervals_df is not None and not intervals_df.empty:
                    collected_data['intervals'] = intervals_df
                    print(f"✅ Intervals: {len(intervals_df)} records")
                else:
                    print("⚠️ No intervals data")
            except Exception as e:
                print(f"❌ Intervals collection failed: {e}")
        
        # Pit stops
        if "pit_stops" in data_types:
            try:
                pit_df = self.collector.collect_pit(session_key=session_key)
                if pit_df is not None and not pit_df.empty:
                    collected_data['pit_stops'] = pit_df
                    print(f"✅ Pit stops: {len(pit_df)} records")
                else:
                    print("⚠️ No pit stops data")
            except Exception as e:
                print(f"❌ Pit stops collection failed: {e}")
        
        # Weather
        if "weather" in data_types:
            try:
                weather_df = self.collector.collect_weather(session_key=session_key)
                if weather_df is not None and not weather_df.empty:
                    collected_data['weather'] = weather_df
                    print(f"✅ Weather: {len(weather_df)} records")
                else:
                    print("⚠️ No weather data")
            except Exception as e:
                print(f"❌ Weather collection failed: {e}")
        
        # Stints
        if "stints" in data_types:
            try:
                stints_df = self.collector.collect_stints(session_key=session_key)
                if stints_df is not None and not stints_df.empty:
                    collected_data['stints'] = stints_df
                    print(f"✅ Stints: {len(stints_df)} records")
                else:
                    print("⚠️ No stints data")
            except Exception as e:
                print(f"❌ Stints collection failed: {e}")
        
        return collected_data
    
    def save_session_data(self, session_key, session_name, collected_data):
        """Speichere gesammelte Session-Daten"""
        try:
            # Create safe filename
            safe_name = session_name.lower().replace(' ', '_').replace('grand_prix', 'gp')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            
            # Ensure output directory exists
            output_dir = Path(self.config['output_paths']['raw_data'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            saved_files = []
            
            for data_type, df in collected_data.items():
                if df is not None and not df.empty:
                    filename = f"{safe_name}_{session_key}_{data_type}_{timestamp}.csv"
                    filepath = output_dir / filename
                    
                    df.to_csv(filepath, index=False)
                    saved_files.append(str(filepath))
                    print(f"💾 Saved {data_type}: {filepath}")
            
            # Save metadata
            metadata = {
                "session_key": session_key,
                "session_name": session_name,
                "collection_timestamp": datetime.now().isoformat(),
                "data_types": list(collected_data.keys()),
                "files": saved_files
            }
            
            metadata_file = output_dir / f"{safe_name}_{session_key}_metadata_{timestamp}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"📋 Metadata saved: {metadata_file}")
            
            return saved_files
            
        except Exception as e:
            print(f"❌ Error saving data: {e}")
            return []
    
    def collect_recent_race_data(self, year=None, limit=5):
        """Sammle Daten für die letzten Rennen"""
        if year is None:
            year = datetime.now().year
            
        print(f"\n🏁 Collecting recent race data for {year}...")
        
        # Get recent race sessions
        race_sessions = self.get_recent_sessions(year=year, session_type="Race", limit=limit)
        
        if not race_sessions:
            print(f"⚠️ No race sessions found for {year}")
            return
        
        total_files = 0
        
        for session in race_sessions:
            session_key = session['session_key']
            session_name = session.get('session_name', 'Unknown Race')
            
            # Collect data for this session
            collected_data = self.collect_session_data(session_key, session_name)
            
            if collected_data:
                # Save data
                saved_files = self.save_session_data(session_key, session_name, collected_data)
                total_files += len(saved_files)
            else:
                print(f"⚠️ No data collected for {session_name}")
        
        print(f"\n🎉 Collection complete! {total_files} files saved for {len(race_sessions)} sessions.")
    
    def collect_specific_session(self, session_key, data_types=None):
        """Sammle Daten für eine spezifische Session"""
        try:
            # Get session info
            sessions = self.client.get_sessions()
            session_info = None
            
            for session in sessions:
                if session['session_key'] == session_key:
                    session_info = session
                    break
            
            if not session_info:
                print(f"❌ Session {session_key} not found")
                return
            
            session_name = session_info.get('session_name', 'Unknown Session')
            
            # Collect data
            collected_data = self.collect_session_data(session_key, session_name, data_types)
            
            if collected_data:
                # Save data
                saved_files = self.save_session_data(session_key, session_name, collected_data)
                print(f"\n🎉 Collection complete! {len(saved_files)} files saved.")
            else:
                print(f"⚠️ No data collected for session {session_key}")
                
        except Exception as e:
            print(f"❌ Error collecting session data: {e}")

def main():
    """Hauptfunktion für CLI-Nutzung"""
    parser = argparse.ArgumentParser(description="OpenF1 Data Collection Script")
    parser.add_argument("command", choices=["recent", "session", "list"], 
                       help="Command to execute")
    parser.add_argument("--year", type=int, default=None,
                       help="Year for data collection (default: current year)")
    parser.add_argument("--limit", type=int, default=5,
                       help="Number of recent sessions to collect (default: 5)")
    parser.add_argument("--session-key", type=int,
                       help="Specific session key to collect")
    parser.add_argument("--data-types", nargs="+",
                       choices=["drivers", "positions", "laps", "intervals", "pit_stops", "weather", "stints"],
                       help="Specific data types to collect")
    parser.add_argument("--config", default="config/openf1_config.json",
                       help="Path to config file")
    
    args = parser.parse_args()
    
    manager = OpenF1DataCollectionManager(args.config)
    
    if args.command == "recent":
        print("🏎️ Collecting recent race data...")
        manager.collect_recent_race_data(year=args.year, limit=args.limit)
        
    elif args.command == "session":
        if not args.session_key:
            print("❌ --session-key required for session command")
            return
        
        print(f"🏎️ Collecting data for session {args.session_key}...")
        manager.collect_specific_session(args.session_key, args.data_types)
        
    elif args.command == "list":
        print("📅 Available sessions:")
        sessions = manager.get_recent_sessions(year=args.year, limit=args.limit)
        
        for session in sessions:
            session_key = session['session_key']
            session_name = session.get('session_name', 'Unknown')
            session_type = session.get('session_type', 'Unknown')
            date_start = session.get('date_start', 'Unknown')
            
            print(f"  {session_key}: {session_name} ({session_type}) - {date_start}")

if __name__ == "__main__":
    main()