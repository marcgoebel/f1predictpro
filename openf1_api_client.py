#!/usr/bin/env python3
"""
OpenF1 API Client

Ein Python-Client für die OpenF1 API (https://openf1.org/)
zum Abrufen von F1-Daten in CSV- und JSON-Format.
"""

import requests
import pandas as pd
import json
import time
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

class OpenF1Client:
    """Client für die OpenF1 API"""
    
    def __init__(self, base_url="https://api.openf1.org/v1", rate_limit_seconds=0.5):
        self.base_url = base_url
        self.rate_limit_seconds = rate_limit_seconds
        self.last_request_time = 0
        
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[List[Dict]]:
        """Führe API-Request mit Rate Limiting durch"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - time_since_last)
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            self.last_request_time = time.time()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {e}")
            return None
    
    def get_car_data(self, session_key: int = None, driver_number: int = None, 
                     date_start: str = None, date_end: str = None) -> Optional[List[Dict]]:
        """Hole Car Data (Telemetrie)"""
        params = {}
        if session_key:
            params['session_key'] = session_key
        if driver_number:
            params['driver_number'] = driver_number
        if date_start:
            params['date>='] = date_start
        if date_end:
            params['date<='] = date_end
            
        return self._make_request('car_data', params)
    
    def get_drivers(self, session_key: int = None, driver_number: int = None) -> Optional[List[Dict]]:
        """Hole Fahrer-Informationen"""
        params = {}
        if session_key:
            params['session_key'] = session_key
        if driver_number:
            params['driver_number'] = driver_number
            
        return self._make_request('drivers', params)
    
    def get_intervals(self, session_key: int = None, driver_number: int = None) -> Optional[List[Dict]]:
        """Hole Zeitabstände zwischen Fahrern"""
        params = {}
        if session_key:
            params['session_key'] = session_key
        if driver_number:
            params['driver_number'] = driver_number
            
        return self._make_request('intervals', params)
    
    def get_laps(self, session_key: int = None, driver_number: int = None, 
                 lap_number: int = None) -> Optional[List[Dict]]:
        """Hole Rundenzeiten"""
        params = {}
        if session_key:
            params['session_key'] = session_key
        if driver_number:
            params['driver_number'] = driver_number
        if lap_number:
            params['lap_number'] = lap_number
            
        return self._make_request('laps', params)
    
    def get_meetings(self, year: int = None, country_name: str = None, 
                     meeting_key: int = None) -> Optional[List[Dict]]:
        """Hole Meeting-Informationen (Rennwochenenden)"""
        params = {}
        if year:
            params['year'] = year
        if country_name:
            params['country_name'] = country_name
        if meeting_key:
            params['meeting_key'] = meeting_key
            
        return self._make_request('meetings', params)
    
    def get_pit(self, session_key: int = None, driver_number: int = None) -> Optional[List[Dict]]:
        """Hole Boxenstopp-Daten"""
        params = {}
        if session_key:
            params['session_key'] = session_key
        if driver_number:
            params['driver_number'] = driver_number
            
        return self._make_request('pit', params)
    
    def get_position(self, session_key: int = None, driver_number: int = None, 
                     date_start: str = None, date_end: str = None) -> Optional[List[Dict]]:
        """Hole Positionsdaten"""
        params = {}
        if session_key:
            params['session_key'] = session_key
        if driver_number:
            params['driver_number'] = driver_number
        if date_start:
            params['date>='] = date_start
        if date_end:
            params['date<='] = date_end
            
        return self._make_request('position', params)
    
    def get_race_control(self, session_key: int = None, category: str = None) -> Optional[List[Dict]]:
        """Hole Race Control Messages"""
        params = {}
        if session_key:
            params['session_key'] = session_key
        if category:
            params['category'] = category
            
        return self._make_request('race_control', params)
    
    def get_sessions(self, year: int = None, session_name: str = None, 
                     session_type: str = None, country_name: str = None) -> Optional[List[Dict]]:
        """Hole Session-Informationen"""
        params = {}
        if year:
            params['year'] = year
        if session_name:
            params['session_name'] = session_name
        if session_type:
            params['session_type'] = session_type
        if country_name:
            params['country_name'] = country_name
            
        return self._make_request('sessions', params)
    
    def get_stints(self, session_key: int = None, driver_number: int = None) -> Optional[List[Dict]]:
        """Hole Stint-Daten (Reifenwechsel)"""
        params = {}
        if session_key:
            params['session_key'] = session_key
        if driver_number:
            params['driver_number'] = driver_number
            
        return self._make_request('stints', params)
    
    def get_team_radio(self, session_key: int = None, driver_number: int = None) -> Optional[List[Dict]]:
        """Hole Team Radio Nachrichten"""
        params = {}
        if session_key:
            params['session_key'] = session_key
        if driver_number:
            params['driver_number'] = driver_number
            
        return self._make_request('team_radio', params)
    
    def get_weather(self, session_key: int = None, date_start: str = None, 
                    date_end: str = None) -> Optional[List[Dict]]:
        """Hole Wetterdaten"""
        params = {}
        if session_key:
            params['session_key'] = session_key
        if date_start:
            params['date>='] = date_start
        if date_end:
            params['date<='] = date_end
            
        return self._make_request('weather', params)

class OpenF1DataCollector:
    """Sammelt und verarbeitet OpenF1 Daten"""
    
    def __init__(self, config_file: str = "config/openf1_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.client = OpenF1Client(
            rate_limit_seconds=self.config.get('rate_limit_seconds', 0.5)
        )
        
    def load_config(self) -> Dict[str, Any]:
        """Lade Konfiguration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Standard-Konfiguration"""
        return {
            "rate_limit_seconds": 0.5,
            "timeout_seconds": 30,
            "max_retries": 3,
            "output_formats": ["json", "csv"],
            "output_paths": {
                "cache": "data/cache/openf1",
                "raw_data": "data/raw/openf1",
                "processed_data": "data/processed/openf1"
            }
        }
    
    def collect_drivers(self, session_key: int = None, save_to_file: bool = False, 
                       output_format: str = "csv") -> Optional[pd.DataFrame]:
        """Sammle Fahrer-Daten"""
        data = self.client.get_drivers(session_key=session_key)
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        if save_to_file:
            self._save_dataframe(df, f"drivers_{session_key or 'all'}", output_format)
            
        return df
    
    def collect_laps(self, session_key: int = None, driver_number: int = None, 
                     save_to_file: bool = False, output_format: str = "csv") -> Optional[pd.DataFrame]:
        """Sammle Rundendaten"""
        data = self.client.get_laps(session_key=session_key, driver_number=driver_number)
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        if save_to_file:
            filename = f"laps_{session_key or 'all'}"
            if driver_number:
                filename += f"_driver_{driver_number}"
            self._save_dataframe(df, filename, output_format)
            
        return df
    
    def collect_position(self, session_key: int = None, driver_number: int = None, 
                        save_to_file: bool = False, output_format: str = "csv") -> Optional[pd.DataFrame]:
        """Sammle Positionsdaten"""
        data = self.client.get_position(session_key=session_key, driver_number=driver_number)
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        if save_to_file:
            filename = f"position_{session_key or 'all'}"
            if driver_number:
                filename += f"_driver_{driver_number}"
            self._save_dataframe(df, filename, output_format)
            
        return df
    
    def collect_intervals(self, session_key: int = None, driver_number: int = None, 
                         save_to_file: bool = False, output_format: str = "csv") -> Optional[pd.DataFrame]:
        """Sammle Intervall-Daten"""
        data = self.client.get_intervals(session_key=session_key, driver_number=driver_number)
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        if save_to_file:
            filename = f"intervals_{session_key or 'all'}"
            if driver_number:
                filename += f"_driver_{driver_number}"
            self._save_dataframe(df, filename, output_format)
            
        return df
    
    def collect_pit(self, session_key: int = None, driver_number: int = None, 
                   save_to_file: bool = False, output_format: str = "csv") -> Optional[pd.DataFrame]:
        """Sammle Boxenstopp-Daten"""
        data = self.client.get_pit(session_key=session_key, driver_number=driver_number)
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        if save_to_file:
            filename = f"pit_{session_key or 'all'}"
            if driver_number:
                filename += f"_driver_{driver_number}"
            self._save_dataframe(df, filename, output_format)
            
        return df
    
    def collect_weather(self, session_key: int = None, save_to_file: bool = False, 
                       output_format: str = "csv") -> Optional[pd.DataFrame]:
        """Sammle Wetterdaten"""
        data = self.client.get_weather(session_key=session_key)
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        if save_to_file:
            self._save_dataframe(df, f"weather_{session_key or 'all'}", output_format)
            
        return df
    
    def collect_stints(self, session_key: int = None, driver_number: int = None, 
                      save_to_file: bool = False, output_format: str = "csv") -> Optional[pd.DataFrame]:
        """Sammle Stint-Daten"""
        data = self.client.get_stints(session_key=session_key, driver_number=driver_number)
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        if save_to_file:
            filename = f"stints_{session_key or 'all'}"
            if driver_number:
                filename += f"_driver_{driver_number}"
            self._save_dataframe(df, filename, output_format)
            
        return df
    
    def collect_sessions(self, year: int = None, session_type: str = None, 
                        save_to_file: bool = False, output_format: str = "csv") -> Optional[pd.DataFrame]:
        """Sammle Session-Daten"""
        data = self.client.get_sessions(year=year, session_type=session_type)
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        if save_to_file:
            filename = f"sessions_{year or 'all'}"
            if session_type:
                filename += f"_{session_type.lower()}"
            self._save_dataframe(df, filename, output_format)
            
        return df
    
    def collect_race_control(self, session_key: int = None, save_to_file: bool = False, 
                            output_format: str = "csv") -> Optional[pd.DataFrame]:
        """Sammle Race Control Daten"""
        data = self.client.get_race_control(session_key=session_key)
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        if save_to_file:
            self._save_dataframe(df, f"race_control_{session_key or 'all'}", output_format)
            
        return df
    
    def _save_dataframe(self, df: pd.DataFrame, filename: str, output_format: str):
        """Speichere DataFrame in gewünschtem Format"""
        try:
            # Erstelle Output-Verzeichnis
            output_dir = Path(self.config['output_paths']['raw_data'])
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Timestamp hinzufügen
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            
            if output_format.lower() == "csv":
                filepath = output_dir / f"{filename}_{timestamp}.csv"
                df.to_csv(filepath, index=False)
            elif output_format.lower() == "json":
                filepath = output_dir / f"{filename}_{timestamp}.json"
                df.to_json(filepath, orient='records', indent=2)
            else:
                raise ValueError(f"Unsupported format: {output_format}")
                
            print(f"Data saved to: {filepath}")
            
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def collect_complete_session_data(self, session_key: int, save_to_file: bool = True) -> Dict[str, pd.DataFrame]:
        """Sammle alle verfügbaren Daten für eine Session"""
        print(f"Collecting complete data for session {session_key}...")
        
        collected_data = {}
        
        # Sammle verschiedene Datentypen
        data_collectors = {
            'drivers': lambda: self.collect_drivers(session_key, save_to_file),
            'laps': lambda: self.collect_laps(session_key, save_to_file=save_to_file),
            'position': lambda: self.collect_position(session_key, save_to_file=save_to_file),
            'intervals': lambda: self.collect_intervals(session_key, save_to_file=save_to_file),
            'pit': lambda: self.collect_pit(session_key, save_to_file=save_to_file),
            'weather': lambda: self.collect_weather(session_key, save_to_file=save_to_file),
            'stints': lambda: self.collect_stints(session_key, save_to_file=save_to_file),
            'race_control': lambda: self.collect_race_control(session_key, save_to_file=save_to_file)
        }
        
        for data_type, collector in data_collectors.items():
            try:
                print(f"  Collecting {data_type}...")
                data = collector()
                if data is not None and not data.empty:
                    collected_data[data_type] = data
                    print(f"    ✅ {data_type}: {len(data)} records")
                else:
                    print(f"    ⚠️ {data_type}: No data")
                    
                # Rate limiting
                time.sleep(self.config.get('rate_limit_seconds', 0.5))
                
            except Exception as e:
                print(f"    ❌ {data_type}: Error - {e}")
        
        return collected_data

# Beispiel-Nutzung
if __name__ == "__main__":
    # Initialisiere Client
    client = OpenF1Client()
    
    # Hole aktuelle Sessions
    print("Fetching 2024 sessions...")
    sessions = client.get_sessions(year=2024)
    
    if sessions:
        print(f"Found {len(sessions)} sessions")
        
        # Zeige letzte 5 Sessions
        for session in sessions[-5:]:
            print(f"- {session.get('session_name')} ({session.get('session_type')})")
    
    # Initialisiere Data Collector
    collector = OpenF1DataCollector()
    
    # Sammle Daten für eine spezifische Session (falls verfügbar)
    if sessions:
        latest_session = sessions[-1]
        session_key = latest_session['session_key']
        
        print(f"\nCollecting data for session {session_key}...")
        data = collector.collect_complete_session_data(session_key, save_to_file=False)
        
        print(f"\nCollected {len(data)} data types:")
        for data_type, df in data.items():
            print(f"- {data_type}: {len(df)} records")