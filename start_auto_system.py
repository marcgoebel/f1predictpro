#!/usr/bin/env python3
"""
F1 Predict Pro - Vollautomatisches System

Dieses Skript startet das vollständig automatisierte F1-Vorhersage- und Wettsystem:

🏎️ Funktionen:
- Automatische Überwachung des F1-Rennkalenders
- Automatisches Abrufen von Rennergebnissen (FastF1 + Ergast API)
- Automatisches Holen von Wettquoten
- Automatische Vorhersagenerstellung
- Automatische Wettempfehlungen
- Automatische Post-Race-Auswertung
- Automatisches Model-Retraining

🚀 Verwendung:
  python start_auto_system.py
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Add ml directory to path
ml_dir = os.path.join(os.path.dirname(__file__), 'ml')
sys.path.insert(0, ml_dir)

# Import unserer Module
try:
    from ml.auto_race_monitor import AutoF1RaceMonitor
    from ml.auto_race_results_fetcher import AutoRaceResultsFetcher
    from ml.auto_race_evaluator import AutoRaceEvaluator
    from ml.betting_strategy import generate_betting_recommendations
    from ml.odds_fetcher import fetch_f1_odds
except ImportError as e:
    print(f"❌ Fehler beim Importieren der Module: {e}")
    print("💡 Stelle sicher, dass du im Hauptverzeichnis des Projekts bist")
    print(f"💡 Aktuelles Verzeichnis: {os.getcwd()}")
    print(f"💡 ML Verzeichnis: {ml_dir}")
    sys.exit(1)

class F1AutoSystem:
    """
    Hauptklasse für das vollautomatische F1-System
    """
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialisiere Komponenten
        self.race_monitor = None
        self.results_fetcher = None
        self.race_evaluator = None
        
        # Status-Tracking
        self.system_status = {
            "started_at": None,
            "components_running": {},
            "last_activity": {},
            "errors": []
        }
    
    def setup_logging(self):
        """Setup zentrales Logging"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"auto_system_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def setup_directories(self):
        """Erstelle alle benötigten Verzeichnisse"""
        directories = [
            "data/live",
            "data/processed", 
            "data/incoming_results",
            "data/cache/fastf1",
            "config",
            "logs",
            "models",
            "data/test_results"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            self.logger.debug(f"📁 Verzeichnis sichergestellt: {directory}")
    
    def check_dependencies(self):
        """Prüfe ob alle Abhängigkeiten verfügbar sind"""
        self.logger.info("🔍 Prüfe Systemabhängigkeiten...")
        
        dependencies = {
            "pandas": "pandas",
            "numpy": "numpy", 
            "scikit-learn": "sklearn",
            "fastf1": "fastf1",
            "requests": "requests",
            "schedule": "schedule"
        }
        
        missing = []
        for name, module in dependencies.items():
            try:
                __import__(module)
                self.logger.debug(f"✅ {name} verfügbar")
            except ImportError:
                missing.append(name)
                self.logger.warning(f"⚠️ {name} nicht verfügbar")
        
        if missing:
            self.logger.error(f"❌ Fehlende Abhängigkeiten: {', '.join(missing)}")
            self.logger.info("💡 Installiere mit: pip install -r requirements.txt")
            return False
        
        self.logger.info("✅ Alle Abhängigkeiten verfügbar")
        return True
    
    def initialize_components(self):
        """Initialisiere alle Systemkomponenten"""
        try:
            self.logger.info("🔧 Initialisiere Systemkomponenten...")
            
            # Race Monitor (Hauptkomponente)
            self.race_monitor = AutoF1RaceMonitor()
            self.system_status["components_running"]["race_monitor"] = True
            self.logger.info("✅ Race Monitor initialisiert")
            
            # Results Fetcher (bereits in Race Monitor integriert)
            self.results_fetcher = self.race_monitor.results_fetcher
            self.system_status["components_running"]["results_fetcher"] = True
            self.logger.info("✅ Results Fetcher initialisiert")
            
            # Race Evaluator (bereits in Race Monitor integriert)
            self.race_evaluator = self.race_monitor.race_evaluator
            self.system_status["components_running"]["race_evaluator"] = True
            self.logger.info("✅ Race Evaluator initialisiert")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Komponenteninitialisierung: {e}")
            self.system_status["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "component": "initialization"
            })
            return False
    
    def start_monitoring_thread(self):
        """Starte Race Monitor in separatem Thread"""
        def monitor_worker():
            try:
                self.logger.info("🚀 Starte Race Monitor Thread...")
                self.race_monitor.start_continuous_monitoring()
            except Exception as e:
                self.logger.error(f"❌ Race Monitor Thread Fehler: {e}")
                self.system_status["components_running"]["race_monitor"] = False
                self.system_status["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "component": "race_monitor"
                })
        
        monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        monitor_thread.start()
        return monitor_thread
    
    def start_results_fetcher_thread(self):
        """Starte Results Fetcher in separatem Thread"""
        def fetcher_worker():
            try:
                self.logger.info("🔍 Starte Results Fetcher Thread...")
                self.results_fetcher.start_continuous_monitoring()
            except Exception as e:
                self.logger.error(f"❌ Results Fetcher Thread Fehler: {e}")
                self.system_status["components_running"]["results_fetcher"] = False
                self.system_status["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "component": "results_fetcher"
                })
        
        fetcher_thread = threading.Thread(target=fetcher_worker, daemon=True)
        fetcher_thread.start()
        return fetcher_thread
    
    def monitor_system_health(self):
        """Überwache Systemgesundheit"""
        while True:
            try:
                # Prüfe Thread-Status
                active_components = sum(1 for status in self.system_status["components_running"].values() if status)
                total_components = len(self.system_status["components_running"])
                
                if active_components < total_components:
                    self.logger.warning(f"⚠️ Nur {active_components}/{total_components} Komponenten aktiv")
                
                # Aktualisiere letzte Aktivität
                self.system_status["last_activity"]["health_check"] = datetime.now().isoformat()
                
                # Warte 5 Minuten bis zur nächsten Prüfung
                time.sleep(300)
                
            except Exception as e:
                self.logger.error(f"❌ Fehler bei Gesundheitsprüfung: {e}")
                time.sleep(60)
    
    def print_startup_info(self):
        """Zeige Startup-Informationen"""
        print("\n" + "="*80)
        print("🏎️  F1 PREDICT PRO - VOLLAUTOMATISCHES SYSTEM")
        print("="*80)
        print("\n🚀 SYSTEMSTART...")
        print("\n📋 FUNKTIONEN:")
        print("   • Automatische F1-Rennkalender-Überwachung")
        print("   • Automatisches Abrufen von Rennergebnissen (FastF1 + Ergast)")
        print("   • Automatisches Holen von Wettquoten")
        print("   • Automatische Vorhersagenerstellung")
        print("   • Automatische Wettempfehlungen")
        print("   • Automatische Post-Race-Auswertung")
        print("   • Automatisches Model-Retraining")
        print("\n⚙️  KONFIGURATION:")
        print("   • Prüfintervall: Alle 30 Minuten")
        print("   • Datenquellen: FastF1, Ergast API, Odds API")
        print("   • Logs: logs/auto_system_YYYYMMDD.log")
        print("\n" + "="*80)
    
    def start(self):
        """Starte das vollautomatische System"""
        try:
            self.print_startup_info()
            
            # System-Setup
            self.logger.info("🔧 Starte F1 Predict Pro Auto-System...")
            self.system_status["started_at"] = datetime.now().isoformat()
            
            # Prüfe Abhängigkeiten
            if not self.check_dependencies():
                return False
            
            # Setup Verzeichnisse
            self.setup_directories()
            
            # Initialisiere Komponenten
            if not self.initialize_components():
                return False
            
            # Starte Monitoring (Race Monitor enthält bereits Results Fetcher)
            self.logger.info("🚀 Starte kontinuierliche Überwachung...")
            monitor_thread = self.start_monitoring_thread()
            
            # Starte Gesundheitsüberwachung
            health_thread = threading.Thread(target=self.monitor_system_health, daemon=True)
            health_thread.start()
            
            print("\n✅ SYSTEM ERFOLGREICH GESTARTET!")
            print("\n📊 STATUS:")
            print("   • Race Monitor: 🟢 Aktiv")
            print("   • Results Fetcher: 🟢 Aktiv (integriert)")
            print("   • Race Evaluator: 🟢 Aktiv (integriert)")
            print("\n💡 TIPPS:")
            print("   • Drücke Ctrl+C zum Beenden")
            print("   • Logs werden in logs/ gespeichert")
            print("   • Ergebnisse werden automatisch in data/incoming_results/ gespeichert")
            print("\n🔄 Das System läuft jetzt kontinuierlich und überwacht:")
            print("   • Neue F1-Rennergebnisse")
            print("   • Wettquoten-Updates")
            print("   • Vorhersage-Generierung")
            print("   • Post-Race-Auswertungen")
            print("\n" + "="*80)
            
            # Hauptschleife
            try:
                while True:
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                self.logger.info("🛑 System durch Benutzer gestoppt")
                print("\n🛑 System wird beendet...")
                print("✅ Auf Wiedersehen!")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Kritischer Systemfehler: {e}")
            print(f"\n❌ SYSTEMFEHLER: {e}")
            return False
    
    def get_status(self):
        """Hole aktuellen Systemstatus"""
        return self.system_status


def main():
    """Hauptfunktion"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="F1 Predict Pro - Vollautomatisches System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python start_auto_system.py              # Starte das vollautomatische System
  python start_auto_system.py --setup      # Nur Setup durchführen
  python start_auto_system.py --status     # Zeige Systemstatus

Das System überwacht kontinuierlich:
• F1-Rennkalender
• Neue Rennergebnisse (FastF1 + Ergast API)
• Wettquoten-Updates
• Automatische Vorhersagen und Wettempfehlungen
        """
    )
    
    parser.add_argument("--setup", action="store_true",
                       help="Nur Setup durchführen, System nicht starten")
    parser.add_argument("--status", action="store_true",
                       help="Zeige aktuellen Systemstatus")
    
    args = parser.parse_args()
    
    system = F1AutoSystem()
    
    if args.setup:
        print("🔧 Führe System-Setup durch...")
        system.setup_directories()
        if system.check_dependencies():
            print("✅ Setup erfolgreich abgeschlossen!")
            print("\n💡 Starte das System mit: python start_auto_system.py")
        else:
            print("❌ Setup fehlgeschlagen - prüfe Abhängigkeiten")
            return 1
    
    elif args.status:
        print("📊 Systemstatus wird implementiert...")
        # TODO: Status-Anzeige implementieren
        return 0
    
    else:
        # Starte das vollautomatische System
        success = system.start()
        return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)