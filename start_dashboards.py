#!/usr/bin/env python3
"""
Dashboard Starter - Startet beide F1 Dashboards gleichzeitig
Betting Dashboard (app.py) und Supabase Dashboard (supabase_dashboard.py)
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def start_dashboard(script_name, port, dashboard_type):
    """Start a Streamlit dashboard on specified port"""
    try:
        print(f"[INFO] Starte {dashboard_type} auf Port {port}...")
        
        # Change to dashboard directory
        dashboard_dir = Path(__file__).parent / "dashboard"
        
        # Start Streamlit with specific port
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_dir / script_name),
            "--server.port", str(port),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        print(f"[OK] {dashboard_type} gestartet auf http://localhost:{port}")
        return process
        
    except Exception as e:
        print(f"[ERROR] Fehler beim Starten von {dashboard_type}: {e}")
        return None

def main():
    print("F1 PredictPro - Dashboard Starter")
    print("=" * 50)
    
    # Check if dashboard directory exists
    dashboard_dir = Path(__file__).parent / "dashboard"
    if not dashboard_dir.exists():
        print("[ERROR] Dashboard-Verzeichnis nicht gefunden!")
        return
    
    # Check if dashboard files exist
    betting_dashboard = dashboard_dir / "app.py"
    supabase_dashboard = dashboard_dir / "supabase_dashboard.py"
    
    if not betting_dashboard.exists():
        print("[ERROR] Betting Dashboard (app.py) nicht gefunden!")
        return
    
    if not supabase_dashboard.exists():
        print("[ERROR] Supabase Dashboard (supabase_dashboard.py) nicht gefunden!")
        return
    
    print("[INFO] Starte beide Dashboards...")
    print()
    
    # Start both dashboards
    processes = []
    
    # Start Betting Dashboard on port 8503
    betting_process = start_dashboard("app.py", 8503, "Betting Dashboard")
    if betting_process:
        processes.append((betting_process, "Betting Dashboard"))
    
    # Wait a moment before starting second dashboard
    time.sleep(2)
    
    # Start Supabase Dashboard on port 8502
    supabase_process = start_dashboard("supabase_dashboard.py", 8502, "Supabase Dashboard")
    if supabase_process:
        processes.append((supabase_process, "Supabase Dashboard"))
    
    if not processes:
        print("[ERROR] Keine Dashboards konnten gestartet werden!")
        return
    
    print()
    print("[OK] Dashboards erfolgreich gestartet!")
    print("=" * 50)
    print("Verfügbare Dashboards:")
    print()
    print("Betting Dashboard:    http://localhost:8503")
    print("   └─ Wett-Empfehlungen, Live-Odds, Betting-Strategien")
    print()
    print("Supabase Dashboard:   http://localhost:8502")
    print("   └─ Datenbank-Management, Supabase-Integration")
    print()
    print("[INFO] Drücke Ctrl+C um beide Dashboards zu stoppen")
    print("=" * 50)
    
    try:
        # Keep the script running and monitor processes
        while True:
            time.sleep(5)
            
            # Check if processes are still running
            for process, name in processes:
                if process.poll() is not None:
                    print(f"[WARNING] {name} wurde beendet (Exit Code: {process.returncode})")
                    
                    # Try to restart if it crashed
                    if process.returncode != 0:
                        print(f"[INFO] Versuche {name} neu zu starten...")
                        if "Betting" in name:
                            new_process = start_dashboard("app.py", 8501, "Betting Dashboard")
                        else:
                            new_process = start_dashboard("supabase_dashboard.py", 8502, "Supabase Dashboard")
                        
                        if new_process:
                            # Replace the old process in the list
                            processes = [(p, n) if n != name else (new_process, name) for p, n in processes]
    
    except KeyboardInterrupt:
        print("\n[INFO] Stoppe alle Dashboards...")
        
        # Terminate all processes
        for process, name in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"[OK] {name} gestoppt")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"[FORCE] {name} forciert gestoppt")
            except Exception as e:
                print(f"[WARNING] Fehler beim Stoppen von {name}: {e}")
        
        print("[INFO] Alle Dashboards gestoppt. Auf Wiedersehen!")

if __name__ == "__main__":
    main()