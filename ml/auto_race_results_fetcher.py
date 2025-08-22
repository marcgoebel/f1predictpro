#!/usr/bin/env python3
"""
Automatischer F1 Rennergebnis-Abrufer

Dieses Modul holt automatisch F1-Rennergebnisse von verschiedenen Quellen:
1. FastF1 API (primär)
2. Ergast API (fallback)
3. Offizielle F1 API (falls verfügbar)

Es überwacht kontinuierlich nach neuen Rennergebnissen und speichert sie
automatisch im incoming_results Ordner für die weitere Verarbeitung.
"""

import os
import sys
import json
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Import OpenF1 client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openf1_api_client import OpenF1Client, OpenF1DataCollector

try:
    import fastf1
    FASTF1_AVAILABLE = True
except ImportError:
    FASTF1_AVAILABLE = False
    print("⚠️ FastF1 nicht verfügbar, verwende nur Ergast API")

class AutoRaceResultsFetcher:
    """
    Automatischer Abrufer für F1-Rennergebnisse
    """
    
    def __init__(self, config_file="config/results_fetcher_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        self.processed_races_file = "data/processed/processed_races.json"
        
    def load_config(self):
        """Lade Konfiguration oder erstelle Standard-Konfiguration"""
        default_config = {
            "check_interval_minutes": 30,
            "max_retries": 3,
            "retry_delay_minutes": 5,
            "data_sources": {
                "fastf1": {
                    "enabled": FASTF1_AVAILABLE,
                    "priority": 1,
                    "cache_dir": "data/cache/fastf1"
                },
                "ergast": {
                    "enabled": True,
                    "priority": 2,
                    "base_url": "https://ergast.com/api/f1",
                    "rate_limit_delay": 1
                },
                "f1_official": {
                    "enabled": False,
                    "priority": 3,
                    "base_url": "https://api.formula1.com"
                }
            },
            "output_paths": {
                "incoming_results": "data/incoming_results",
                "race_schedule": "data/live/race_schedule.json"
            },
            "monitoring": {
                "check_hours_after_race": [2, 4, 6, 12, 24],
                "max_days_after_race": 7
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
        
        log_file = os.path.join(log_dir, f"results_fetcher_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_race_schedule(self):
        """Lade aktuellen Rennkalender"""
        schedule_file = self.config['output_paths']['race_schedule']
        
        if os.path.exists(schedule_file):
            with open(schedule_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        self.logger.warning("Kein Rennkalender gefunden, erstelle neuen...")
        return self.fetch_current_schedule()
    
    def fetch_current_schedule(self):
        """Hole aktuellen F1-Kalender"""
        try:
            if FASTF1_AVAILABLE:
                current_year = datetime.now().year
                schedule = fastf1.get_event_schedule(current_year, include_testing=False)
                
                races = []
                for _, race in schedule.iterrows():
                    race_data = {
                        "race_name": race['EventName'],
                        "country": race['Country'],
                        "location": race['Location'],
                        "race_date": race['Session5Date'].isoformat() if pd.notna(race['Session5Date']) else None,
                        "round_number": race['RoundNumber']
                    }
                    races.append(race_data)
                
                # Speichere Kalender
                schedule_file = self.config['output_paths']['race_schedule']
                os.makedirs(os.path.dirname(schedule_file), exist_ok=True)
                with open(schedule_file, 'w', encoding='utf-8') as f:
                    json.dump(races, f, indent=2, ensure_ascii=False)
                
                return races
            else:
                return self.fetch_schedule_from_ergast()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Kalenders: {e}")
            return []
    
    def fetch_schedule_from_ergast(self):
        """Hole Kalender von Ergast API"""
        try:
            current_year = datetime.now().year
            url = f"{self.config['data_sources']['ergast']['base_url']}/{current_year}.json"
            
            response = requests.get(url)
            response.raise_for_status()
            
            data = response.json()
            races = []
            
            for race in data['MRData']['RaceTable']['Races']:
                race_data = {
                    "race_name": race['raceName'],
                    "country": race['Circuit']['Location']['country'],
                    "location": race['Circuit']['Location']['locality'],
                    "race_date": f"{race['date']}T{race.get('time', '14:00:00Z')}",
                    "round_number": int(race['round'])
                }
                races.append(race_data)
            
            return races
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Ergast-Kalenders: {e}")
            return []
    
    def get_processed_races(self):
        """Lade bereits verarbeitete Rennen"""
        if os.path.exists(self.processed_races_file):
            with open(self.processed_races_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both old format (list) and new format (dict)
                if isinstance(data, list):
                    return set(data)
                elif isinstance(data, dict):
                    return set(data.get('processed_files', []))
        return set()
    
    def fetch_race_results_fastf1(self, race_name, round_number, year):
        """Hole Rennergebnisse mit FastF1"""
        try:
            if not FASTF1_AVAILABLE:
                return None
            
            # Setup cache
            cache_dir = self.config['data_sources']['fastf1']['cache_dir']
            os.makedirs(cache_dir, exist_ok=True)
            fastf1.Cache.enable_cache(cache_dir)
            
            # Lade Session
            session = fastf1.get_session(year, round_number, 'R')
            session.load()
            
            # Hole Ergebnisse
            results = session.results
            
            if results is None or results.empty:
                self.logger.warning(f"Keine Ergebnisse für {race_name} (FastF1)")
                return None
            
            # Konvertiere zu unserem Format
            race_results = []
            for _, driver in results.iterrows():
                race_results.append({
                    "Driver": f"{driver['FirstName']} {driver['LastName']}",
                    "Actual_Position": driver['Position'] if pd.notna(driver['Position']) else 20
                })
            
            self.logger.info(f"✅ FastF1: {len(race_results)} Ergebnisse für {race_name}")
            return race_results
            
        except Exception as e:
            self.logger.error(f"FastF1 Fehler für {race_name}: {e}")
            return None
    
    def fetch_race_results_ergast(self, round_number, year):
        """Hole Rennergebnisse von Ergast API"""
        try:
            url = f"{self.config['data_sources']['ergast']['base_url']}/{year}/{round_number}/results.json"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'MRData' in data and 'RaceTable' in data['MRData']:
                races = data['MRData']['RaceTable']['Races']
                
                if races:
                    race = races[0]
                    results = race['Results']
                    
                    # Konvertiere zu DataFrame
                    race_data = []
                    for result in results:
                        driver = result['Driver']
                        constructor = result['Constructor']
                        
                        race_data.append({
                            'position': result['position'],
                            'driver': f"{driver['givenName']} {driver['familyName']}",
                            'constructor': constructor['name'],
                            'points': result.get('points', 0),
                            'status': result['status'],
                            'time': result.get('Time', {}).get('time', 'N/A')
                        })
                    
                    self.logger.info(f"✅ Ergast: {len(race_data)} Ergebnisse gefunden")
                    return pd.DataFrame(race_data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen von Ergast: {e}")
            return None
    
    def fetch_race_results_openf1(self, race_name, round_number, year):
        """Hole Rennergebnisse mit OpenF1 API"""
        try:
            if not self.config['data_sources']['openf1']['enabled']:
                return None
                
            # Initialize OpenF1 client
            openf1_client = OpenF1Client()
            
            # Get session data for the race
            sessions = openf1_client.get_sessions(year=year)
            
            # Find the race session
            race_session = None
            for session in sessions:
                if (session.get('session_type') == 'Race' and 
                    str(session.get('session_name', '')).lower().replace(' ', '_') in race_name.lower().replace(' ', '_')):
                    race_session = session
                    break
            
            if not race_session:
                self.logger.warning(f"OpenF1: Keine Race Session für {race_name} gefunden")
                return None
            
            session_key = race_session['session_key']
            
            # Get final positions
            positions = openf1_client.get_position(session_key=session_key)
            
            if not positions:
                return None
            
            # Get drivers info
            drivers = openf1_client.get_drivers(session_key=session_key)
            driver_map = {d['driver_number']: d for d in drivers}
            
            # Get final lap times
            laps = openf1_client.get_laps(session_key=session_key)
            
            # Process results
            race_data = []
            final_positions = {}
            
            # Get final positions (last recorded position for each driver)
            for pos in positions:
                driver_num = pos['driver_number']
                if driver_num not in final_positions or pos['date'] > final_positions[driver_num]['date']:
                    final_positions[driver_num] = pos
            
            # Create results DataFrame
            for driver_num, pos_data in final_positions.items():
                driver_info = driver_map.get(driver_num, {})
                
                # Get best lap time for this driver
                driver_laps = [lap for lap in laps if lap['driver_number'] == driver_num and lap['lap_duration']]
                best_lap = min(driver_laps, key=lambda x: x['lap_duration']) if driver_laps else None
                
                race_data.append({
                    'position': pos_data['position'],
                    'driver': driver_info.get('full_name', f"Driver {driver_num}"),
                    'constructor': driver_info.get('team_name', 'Unknown'),
                    'driver_number': driver_num,
                    'best_lap': best_lap['lap_duration'] if best_lap else None,
                    'total_laps': len(driver_laps),
                    'session_key': session_key
                })
            
            # Sort by position
            race_data.sort(key=lambda x: int(x['position']))
            
            # Convert to the expected format (list of dicts with Driver and Actual_Position)
            race_results = []
            for result in race_data:
                race_results.append({
                    "Driver": result['driver'],
                    "Actual_Position": result['position']
                })
            
            self.logger.info(f"✅ OpenF1: {len(race_results)} Ergebnisse gefunden")
            return race_results
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen von OpenF1: {e}")
            return None
    
    def save_race_results(self, race_results, race_name, round_number, year):
        """Speichere Rennergebnisse"""
        try:
            # Erstelle Dateiname
            safe_race_name = race_name.lower().replace(' ', '_').replace('grand_prix', 'gp')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"{year}_{safe_race_name}_results_auto_{timestamp}.csv"
            
            # Speichere in incoming_results
            output_dir = self.config['output_paths']['incoming_results']
            os.makedirs(output_dir, exist_ok=True)
            
            filepath = os.path.join(output_dir, filename)
            
            # Erstelle DataFrame und speichere
            df = pd.DataFrame(race_results)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            self.logger.info(f"💾 Ergebnisse gespeichert: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern: {e}")
            return None
    
    def check_for_new_results(self):
        """Prüfe auf neue Rennergebnisse"""
        try:
            races = self.get_race_schedule()
            processed_races = self.get_processed_races()
            from datetime import timezone
            current_time = datetime.now(timezone.utc)
            
            new_results_found = 0
            
            for race in races:
                if not race.get('race_date'):
                    continue
                
                race_time = datetime.fromisoformat(race['race_date'].replace('Z', '+00:00'))
                hours_since_race = (current_time - race_time).total_seconds() / 3600
                
                # Prüfe nur Rennen, die in den letzten Tagen stattgefunden haben
                max_days = self.config['monitoring']['max_days_after_race']
                if hours_since_race < 0 or hours_since_race > (max_days * 24):
                    continue
                
                race_name = race['race_name']
                round_number = race['round_number']
                year = race_time.year
                
                # Erstelle eindeutige ID für dieses Rennen
                race_id = f"{year}_{round_number}_{race_name.lower().replace(' ', '_')}"
                
                if race_id in processed_races:
                    continue
                
                self.logger.info(f"🔍 Prüfe Ergebnisse für: {race_name} (Runde {round_number})")
                
                # Versuche Ergebnisse zu holen (FastF1 zuerst, dann OpenF1, dann Ergast)
                race_results = None
                
                if self.config['data_sources']['fastf1']['enabled']:
                    race_results = self.fetch_race_results_fastf1(race_name, round_number, year)
                
                if not race_results and self.config['data_sources']['openf1']['enabled']:
                    time.sleep(self.config['data_sources']['openf1']['rate_limit_delay'])
                    race_results = self.fetch_race_results_openf1(race_name, round_number, year)
                
                if not race_results and self.config['data_sources']['ergast']['enabled']:
                    time.sleep(self.config['data_sources']['ergast']['rate_limit_delay'])
                    race_results = self.fetch_race_results_ergast(round_number, year)
                
                if race_results:
                    # Speichere Ergebnisse
                    filepath = self.save_race_results(race_results, race_name, round_number, year)
                    
                    if filepath:
                        new_results_found += 1
                        self.logger.info(f"🎉 Neue Ergebnisse gefunden: {race_name}")
                        
                        # Markiere als verarbeitet
                        processed_races.add(race_id)
                        self.save_processed_races(processed_races)
                else:
                    self.logger.info(f"⏳ Noch keine Ergebnisse verfügbar für: {race_name}")
            
            if new_results_found > 0:
                self.logger.info(f"✅ {new_results_found} neue Rennergebnisse gefunden und gespeichert")
            else:
                self.logger.info("ℹ️ Keine neuen Rennergebnisse gefunden")
            
            return new_results_found
            
        except Exception as e:
            self.logger.error(f"Fehler beim Prüfen auf neue Ergebnisse: {e}")
            return 0
    
    def save_processed_races(self, processed_races):
        """Speichere verarbeitete Rennen"""
        try:
            os.makedirs(os.path.dirname(self.processed_races_file), exist_ok=True)
            
            data = {
                "last_updated": datetime.now().isoformat(),
                "processed_files": list(processed_races)
            }
            
            with open(self.processed_races_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der verarbeiteten Rennen: {e}")
    
    def start_continuous_monitoring(self):
        """Starte kontinuierliche Überwachung"""
        self.logger.info("🚀 Starte automatische Rennergebnis-Überwachung")
        
        interval_minutes = self.config['check_interval_minutes']
        self.logger.info(f"⏰ Prüfe alle {interval_minutes} Minuten auf neue Ergebnisse")
        
        try:
            while True:
                self.check_for_new_results()
                
                self.logger.info(f"😴 Warte {interval_minutes} Minuten bis zur nächsten Prüfung...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Überwachung durch Benutzer gestoppt")
        except Exception as e:
            self.logger.error(f"❌ Überwachung gestoppt wegen Fehler: {e}")


def main():
    """Hauptfunktion für CLI-Nutzung"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automatischer F1 Rennergebnis-Abrufer")
    parser.add_argument("command", choices=["start", "check", "setup"], 
                       help="Auszuführender Befehl")
    parser.add_argument("--config", default="config/results_fetcher_config.json",
                       help="Pfad zur Konfigurationsdatei")
    
    args = parser.parse_args()
    
    fetcher = AutoRaceResultsFetcher(args.config)
    
    if args.command == "setup":
        print("🔧 Richte automatischen Rennergebnis-Abrufer ein...")
        
        # Erstelle Verzeichnisse
        directories = [
            "data/incoming_results",
            "data/processed",
            "data/live",
            "data/cache/fastf1",
            "config",
            "logs"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Verzeichnis erstellt: {directory}")
        
        # Initialisiere Kalender
        fetcher.fetch_current_schedule()
        
        print("\n✅ Setup abgeschlossen!")
        print("\nNächste Schritte:")
        print("1. Starte kontinuierliche Überwachung: python auto_race_results_fetcher.py start")
        print("2. Oder einmalige Prüfung: python auto_race_results_fetcher.py check")
        
    elif args.command == "check":
        print("🔍 Einmalige Prüfung auf neue Rennergebnisse...")
        new_results = fetcher.check_for_new_results()
        print(f"\n✅ Prüfung abgeschlossen. {new_results} neue Ergebnisse gefunden.")
        
    elif args.command == "start":
        print("🚀 Starte kontinuierliche Überwachung...")
        fetcher.start_continuous_monitoring()


if __name__ == "__main__":
    main()