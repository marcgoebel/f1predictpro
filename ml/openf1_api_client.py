#!/usr/bin/env python3
"""
OpenF1 API Client

Umfassende Integration der OpenF1 API für Real-time und historische F1-Daten:
- Car Data (Telemetrie)
- Driver Information
- Intervals
- Laps
- Meetings
- Pit Stops
- Position Data
- Race Control Messages
- Sessions
- Stints
- Team Radio
- Weather Data

Dokumentation: https://openf1.org/
"""

import os
import sys
import json
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path

class OpenF1Client:
    """
    Client für die OpenF1 API
    """
    
    def __init__(self, config_file="config/openf1_config.json"):
        self.base_url = "https://api.openf1.org/v1"
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        self.session = requests.Session()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = self.config.get('rate_limit_seconds', 0.5)
        
    def load_config(self):
        """Lade Konfiguration oder erstelle Standard-Konfiguration"""
        default_config = {
            "rate_limit_seconds": 0.5,
            "timeout_seconds": 30,
            "max_retries": 3,
            "retry_delay_seconds": 1,
            "cache_enabled": True,
            "cache_duration_minutes": 60,
            "output_formats": ["json", "csv"],
            "data_sources": {
                "car_data": {
                    "enabled": True,
                    "sample_rate_hz": 3.7,
                    "fields": ["brake", "date", "driver_number", "drs", "n_gear", "rpm", "speed", "throttle"]
                },
                "drivers": {
                    "enabled": True,
                    "fields": ["broadcast_name", "country_code", "driver_number", "first_name", "full_name", "headshot_url", "last_name", "name_acronym", "team_colour", "team_name"]
                },
                "intervals": {
                    "enabled": True,
                    "fields": ["date", "driver_number", "gap_to_leader", "interval"]
                },
                "laps": {
                    "enabled": True,
                    "fields": ["date_start", "driver_number", "duration_sector_1", "duration_sector_2", "duration_sector_3", "lap_duration", "lap_number", "segments_sector_1", "segments_sector_2", "segments_sector_3"]
                },
                "meetings": {
                    "enabled": True,
                    "fields": ["circuit_key", "circuit_short_name", "country_code", "country_name", "date_start", "gmt_offset", "location", "meeting_name", "meeting_official_name", "year"]
                },
                "pit": {
                    "enabled": True,
                    "fields": ["date", "driver_number", "lap_number", "pit_duration"]
                },
                "position": {
                    "enabled": True,
                    "fields": ["date", "driver_number", "position"]
                },
                "race_control": {
                    "enabled": True,
                    "fields": ["category", "date", "flag", "lap_number", "message", "scope"]
                },
                "sessions": {
                    "enabled": True,
                    "fields": ["circuit_key", "circuit_short_name", "country_code", "country_name", "date_end", "date_start", "gmt_offset", "location", "session_name", "session_type", "year"]
                },
                "stints": {
                    "enabled": True,
                    "fields": ["compound", "driver_number", "lap_end", "lap_start", "stint_number", "tyre_age_at_start"]
                },
                "team_radio": {
                    "enabled": True,
                    "fields": ["date", "driver_number", "recording_url"]
                },
                "weather": {
                    "enabled": True,
                    "fields": ["air_temperature", "date", "humidity", "pressure", "rainfall", "track_temperature", "wind_direction", "wind_speed"]
                }
            },
            "output_paths": {
                "cache": "data/cache/openf1",
                "raw_data": "data/raw/openf1",
                "processed_data": "data/processed/openf1"
            }
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge mit defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            return default_config
    
    def setup_logging(self):
        """Setup Logging"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"openf1_client_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _rate_limit(self):
        """Rate limiting für API-Anfragen"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Führe API-Anfrage mit Retry-Logic durch"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.config['max_retries']):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config['timeout_seconds']
                )
                response.raise_for_status()
                
                self.logger.info(f"✅ API-Anfrage erfolgreich: {endpoint}")
                return response.json()
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"⚠️ API-Anfrage fehlgeschlagen (Versuch {attempt + 1}): {e}")
                
                if attempt < self.config['max_retries'] - 1:
                    time.sleep(self.config['retry_delay_seconds'] * (attempt + 1))
                else:
                    self.logger.error(f"❌ API-Anfrage endgültig fehlgeschlagen: {endpoint}")
                    raise
    
    def get_latest_meeting(self) -> Dict:
        """Hole das neueste Meeting"""
        return self._make_request("meetings", {"meeting_key": "latest"})
    
    def get_latest_session(self) -> Dict:
        """Hole die neueste Session"""
        return self._make_request("sessions", {"session_key": "latest"})
    
    def get_meetings(self, year: int = None, country_name: str = None) -> List[Dict]:
        """Hole Meetings mit optionalen Filtern"""
        params = {}
        if year:
            params['year'] = year
        if country_name:
            params['country_name'] = country_name
        
        return self._make_request("meetings", params)
    
    def get_sessions(self, meeting_key: Union[int, str] = None, session_name: str = None) -> List[Dict]:
        """Hole Sessions mit optionalen Filtern"""
        params = {}
        if meeting_key:
            params['meeting_key'] = meeting_key
        if session_name:
            params['session_name'] = session_name
        
        return self._make_request("sessions", params)
    
    def get_drivers(self, session_key: Union[int, str] = None, driver_number: int = None) -> List[Dict]:
        """Hole Fahrer-Informationen"""
        params = {}
        if session_key:
            params['session_key'] = session_key
        if driver_number:
            params['driver_number'] = driver_number
        
        return self._make_request("drivers", params)
    
    def get_car_data(self, session_key: Union[int, str], driver_number: int = None, 
                     speed_min: int = None, speed_max: int = None) -> List[Dict]:
        """Hole Telemetrie-Daten"""
        params = {'session_key': session_key}
        
        if driver_number:
            params['driver_number'] = driver_number
        if speed_min:
            params['speed>='] = speed_min
        if speed_max:
            params['speed<='] = speed_max
        
        return self._make_request("car_data", params)
    
    def get_position_data(self, session_key: Union[int, str], driver_number: int = None) -> List[Dict]:
        """Hole Positions-Daten"""
        params = {'session_key': session_key}
        
        if driver_number:
            params['driver_number'] = driver_number
        
        return self._make_request("position", params)
    
    def get_intervals(self, session_key: Union[int, str], driver_number: int = None) -> List[Dict]:
        """Hole Intervall-Daten"""
        params = {'session_key': session_key}
        
        if driver_number:
            params['driver_number'] = driver_number
        
        return self._make_request("intervals", params)
    
    def get_laps(self, session_key: Union[int, str], driver_number: int = None, 
                 lap_number: int = None) -> List[Dict]:
        """Hole Runden-Daten"""
        params = {'session_key': session_key}
        
        if driver_number:
            params['driver_number'] = driver_number
        if lap_number:
            params['lap_number'] = lap_number
        
        return self._make_request("laps", params)
    
    def get_pit_stops(self, session_key: Union[int, str], driver_number: int = None) -> List[Dict]:
        """Hole Boxenstopp-Daten"""
        params = {'session_key': session_key}
        
        if driver_number:
            params['driver_number'] = driver_number
        
        return self._make_request("pit", params)
    
    def get_stints(self, session_key: Union[int, str], driver_number: int = None) -> List[Dict]:
        """Hole Stint-Daten"""
        params = {'session_key': session_key}
        
        if driver_number:
            params['driver_number'] = driver_number
        
        return self._make_request("stints", params)
    
    def get_team_radio(self, session_key: Union[int, str], driver_number: int = None) -> List[Dict]:
        """Hole Team-Radio-Daten"""
        params = {'session_key': session_key}
        
        if driver_number:
            params['driver_number'] = driver_number
        
        return self._make_request("team_radio", params)
    
    def get_weather(self, session_key: Union[int, str]) -> List[Dict]:
        """Hole Wetter-Daten"""
        params = {'session_key': session_key}
        return self._make_request("weather", params)
    
    def get_race_control(self, session_key: Union[int, str], category: str = None) -> List[Dict]:
        """Hole Race Control Messages"""
        params = {'session_key': session_key}
        
        if category:
            params['category'] = category
        
        return self._make_request("race_control", params)
    
    def save_data_to_csv(self, data: List[Dict], filename: str, output_dir: str = None):
        """Speichere Daten als CSV"""
        if not data:
            self.logger.warning("Keine Daten zum Speichern")
            return
        
        if output_dir is None:
            output_dir = self.config['output_paths']['processed_data']
        
        os.makedirs(output_dir, exist_ok=True)
        
        df = pd.DataFrame(data)
        filepath = os.path.join(output_dir, f"{filename}.csv")
        df.to_csv(filepath, index=False)
        
        self.logger.info(f"💾 Daten gespeichert: {filepath} ({len(df)} Zeilen)")
        return filepath
    
    def save_data_to_json(self, data: List[Dict], filename: str, output_dir: str = None):
        """Speichere Daten als JSON"""
        if not data:
            self.logger.warning("Keine Daten zum Speichern")
            return
        
        if output_dir is None:
            output_dir = self.config['output_paths']['raw_data']
        
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, f"{filename}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"💾 Daten gespeichert: {filepath} ({len(data)} Einträge)")
        return filepath

class OpenF1DataCollector:
    """
    High-level Data Collector für OpenF1 API
    """
    
    def __init__(self):
        self.client = OpenF1Client()
        self.logger = self.client.logger
    
    def collect_complete_session_data(self, session_key: Union[int, str], 
                                    save_format: str = "both") -> Dict[str, str]:
        """Sammle alle verfügbaren Daten für eine Session"""
        self.logger.info(f"🔄 Sammle komplette Session-Daten für: {session_key}")
        
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Session Info
        try:
            sessions = self.client.get_sessions(session_key=session_key)
            if sessions:
                session_info = sessions[0]
                session_name = session_info.get('session_name', 'unknown')
                meeting_name = session_info.get('location', 'unknown')
                
                filename_base = f"{meeting_name}_{session_name}_{session_key}_{timestamp}"
                
                if save_format in ["json", "both"]:
                    saved_files['session_info'] = self.client.save_data_to_json(
                        sessions, f"session_info_{filename_base}"
                    )
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Sammeln der Session-Info: {e}")
        
        # Drivers
        try:
            drivers = self.client.get_drivers(session_key=session_key)
            if drivers and save_format in ["csv", "both"]:
                saved_files['drivers'] = self.client.save_data_to_csv(
                    drivers, f"drivers_{filename_base}"
                )
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Sammeln der Fahrer-Daten: {e}")
        
        # Position Data
        try:
            positions = self.client.get_position_data(session_key=session_key)
            if positions and save_format in ["csv", "both"]:
                saved_files['positions'] = self.client.save_data_to_csv(
                    positions, f"positions_{filename_base}"
                )
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Sammeln der Positions-Daten: {e}")
        
        # Laps
        try:
            laps = self.client.get_laps(session_key=session_key)
            if laps and save_format in ["csv", "both"]:
                saved_files['laps'] = self.client.save_data_to_csv(
                    laps, f"laps_{filename_base}"
                )
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Sammeln der Runden-Daten: {e}")
        
        # Intervals
        try:
            intervals = self.client.get_intervals(session_key=session_key)
            if intervals and save_format in ["csv", "both"]:
                saved_files['intervals'] = self.client.save_data_to_csv(
                    intervals, f"intervals_{filename_base}"
                )
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Sammeln der Intervall-Daten: {e}")
        
        # Pit Stops
        try:
            pit_stops = self.client.get_pit_stops(session_key=session_key)
            if pit_stops and save_format in ["csv", "both"]:
                saved_files['pit_stops'] = self.client.save_data_to_csv(
                    pit_stops, f"pit_stops_{filename_base}"
                )
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Sammeln der Boxenstopp-Daten: {e}")
        
        # Stints
        try:
            stints = self.client.get_stints(session_key=session_key)
            if stints and save_format in ["csv", "both"]:
                saved_files['stints'] = self.client.save_data_to_csv(
                    stints, f"stints_{filename_base}"
                )
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Sammeln der Stint-Daten: {e}")
        
        # Weather
        try:
            weather = self.client.get_weather(session_key=session_key)
            if weather and save_format in ["csv", "both"]:
                saved_files['weather'] = self.client.save_data_to_csv(
                    weather, f"weather_{filename_base}"
                )
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Sammeln der Wetter-Daten: {e}")
        
        # Race Control
        try:
            race_control = self.client.get_race_control(session_key=session_key)
            if race_control and save_format in ["csv", "both"]:
                saved_files['race_control'] = self.client.save_data_to_csv(
                    race_control, f"race_control_{filename_base}"
                )
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Sammeln der Race Control-Daten: {e}")
        
        # Team Radio
        try:
            team_radio = self.client.get_team_radio(session_key=session_key)
            if team_radio and save_format in ["csv", "both"]:
                saved_files['team_radio'] = self.client.save_data_to_csv(
                    team_radio, f"team_radio_{filename_base}"
                )
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Sammeln der Team Radio-Daten: {e}")
        
        self.logger.info(f"✅ Session-Datensammlung abgeschlossen: {len(saved_files)} Dateien")
        return saved_files
    
    def collect_telemetry_for_driver(self, session_key: Union[int, str], 
                                   driver_number: int, save_format: str = "csv") -> str:
        """Sammle Telemetrie-Daten für einen spezifischen Fahrer"""
        self.logger.info(f"🏎️ Sammle Telemetrie für Fahrer #{driver_number} in Session {session_key}")
        
        try:
            car_data = self.client.get_car_data(session_key=session_key, driver_number=driver_number)
            
            if car_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"telemetry_driver_{driver_number}_session_{session_key}_{timestamp}"
                
                if save_format == "csv":
                    return self.client.save_data_to_csv(car_data, filename)
                else:
                    return self.client.save_data_to_json(car_data, filename)
            else:
                self.logger.warning(f"Keine Telemetrie-Daten für Fahrer #{driver_number}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Sammeln der Telemetrie: {e}")
            return None
    
    def get_current_season_meetings(self, year: int = None) -> List[Dict]:
        """Hole alle Meetings der aktuellen Saison"""
        if year is None:
            year = datetime.now().year
        
        self.logger.info(f"📅 Lade Meetings für Saison {year}")
        
        try:
            meetings = self.client.get_meetings(year=year)
            self.logger.info(f"✅ {len(meetings)} Meetings gefunden für {year}")
            return meetings
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Laden der Meetings: {e}")
            return []

def main():
    """Demo der OpenF1 API Integration"""
    print("🏎️ OpenF1 API Integration Demo")
    print("=" * 50)
    
    # Client initialisieren
    collector = OpenF1DataCollector()
    
    try:
        # Neueste Session abrufen
        print("\n🔍 Lade neueste Session...")
        latest_session = collector.client.get_latest_session()
        
        if latest_session:
            session_key = latest_session[0]['session_key']
            session_name = latest_session[0]['session_name']
            location = latest_session[0]['location']
            
            print(f"📍 Neueste Session: {session_name} in {location} (Key: {session_key})")
            
            # Fahrer abrufen
            print("\n👥 Lade Fahrer...")
            drivers = collector.client.get_drivers(session_key=session_key)
            
            if drivers:
                print(f"✅ {len(drivers)} Fahrer gefunden:")
                for driver in drivers[:5]:  # Zeige nur erste 5
                    print(f"  #{driver['driver_number']}: {driver['full_name']} ({driver['team_name']})")
                
                # Beispiel: Sammle Daten für ersten Fahrer
                first_driver = drivers[0]
                driver_number = first_driver['driver_number']
                
                print(f"\n🏎️ Sammle Beispiel-Telemetrie für {first_driver['full_name']}...")
                telemetry_file = collector.collect_telemetry_for_driver(
                    session_key=session_key, 
                    driver_number=driver_number
                )
                
                if telemetry_file:
                    print(f"💾 Telemetrie gespeichert: {telemetry_file}")
            
            # Sammle komplette Session-Daten (nur ein kleiner Test)
            print(f"\n📊 Sammle Session-Übersicht für {session_name}...")
            saved_files = collector.collect_complete_session_data(
                session_key=session_key, 
                save_format="csv"
            )
            
            print(f"✅ {len(saved_files)} Dateien erstellt:")
            for data_type, filepath in saved_files.items():
                print(f"  {data_type}: {filepath}")
        
        # Aktuelle Saison-Meetings
        print("\n📅 Lade aktuelle Saison...")
        meetings = collector.get_current_season_meetings()
        
        if meetings:
            print(f"✅ {len(meetings)} Meetings in der aktuellen Saison:")
            for meeting in meetings[-5:]:  # Zeige letzte 5
                print(f"  {meeting['meeting_name']} - {meeting['location']} ({meeting['date_start']})")
        
        print("\n🎉 OpenF1 API Integration erfolgreich getestet!")
        
    except Exception as e:
        print(f"❌ Fehler beim Testen der OpenF1 API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()