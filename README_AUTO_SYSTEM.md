# 🏎️ F1 Predict Pro - Vollautomatisches System

## 🎯 Überblick

Das vollautomatische F1-System überwacht kontinuierlich den F1-Rennkalender und führt automatisch alle notwendigen Aktionen durch:

- **🔍 Automatisches Abrufen von Rennergebnissen** (FastF1 + Ergast API)
- **📊 Automatische Wettquoten-Updates**
- **🤖 Automatische Vorhersagenerstellung**
- **💰 Automatische Wettempfehlungen**
- **📈 Automatische Post-Race-Auswertung**
- **🧠 Automatisches Model-Retraining**

## 🚀 Schnellstart

### 1. System starten
```bash
python start_auto_system.py
```

### 2. Nur Setup durchführen
```bash
python start_auto_system.py --setup
```

### 3. Systemstatus prüfen
```bash
python start_auto_system.py --status
```

## 🔧 Systemkomponenten

### 1. Auto Race Monitor (`auto_race_monitor.py`)
**Hauptkomponente** - Koordiniert alle anderen Komponenten
- Überwacht F1-Rennkalender
- Holt Wettquoten vor Rennen
- Generiert Vorhersagen
- Erstellt Wettempfehlungen
- Verarbeitet Rennergebnisse nach dem Rennen

### 2. Auto Race Results Fetcher (`auto_race_results_fetcher.py`)
**Neue Komponente** - Holt automatisch Rennergebnisse
- **FastF1 API** (primäre Quelle)
- **Ergast API** (Fallback)
- Speichert Ergebnisse automatisch in `data/incoming_results/`
- Prüft alle 30 Minuten auf neue Ergebnisse

### 3. Auto Race Evaluator (`auto_race_evaluator.py`)
**Bestehende Komponente** - Verarbeitet Rennergebnisse
- Überwacht `data/incoming_results/` Ordner
- Führt Betting-Simulation durch
- Aktualisiert Gewinn/Verlust-Statistiken
- Triggert Model-Retraining nach 5 Rennen

## 📁 Verzeichnisstruktur

```
f1predictpro/
├── start_auto_system.py          # 🚀 Hauptstartskript
├── ml/
│   ├── auto_race_monitor.py       # 🎯 Hauptkoordinator
│   ├── auto_race_results_fetcher.py  # 🔍 Neuer Results Fetcher
│   └── auto_race_evaluator.py     # 📊 Results Processor
├── data/
│   ├── incoming_results/          # 📥 Automatisch abgerufene Ergebnisse
│   ├── processed/                 # 📈 Verarbeitete Daten
│   ├── live/                      # 🔴 Live-Daten (Quoten, Vorhersagen)
│   └── cache/fastf1/              # 💾 FastF1 Cache
├── config/                        # ⚙️ Konfigurationsdateien
└── logs/                          # 📝 System-Logs
```

## ⚙️ Konfiguration

### Auto Monitor Config (`config/auto_monitor_config.json`)
```json
{
  "check_interval_hours": 6,
  "odds_fetch_hours_before_race": [72, 48, 24, 12, 6, 2],
  "prediction_hours_before_race": 24,
  "auto_process_results_hours_after_race": 4,
  "betting_amount": 10,
  "min_expected_value": 0.05,
  "max_bets_per_race": 8
}
```

### Results Fetcher Config (`config/results_fetcher_config.json`)
```json
{
  "check_interval_minutes": 30,
  "data_sources": {
    "fastf1": {
      "enabled": true,
      "priority": 1
    },
    "ergast": {
      "enabled": true,
      "priority": 2,
      "base_url": "https://ergast.com/api/f1"
    }
  },
  "monitoring": {
    "check_hours_after_race": [2, 4, 6, 12, 24],
    "max_days_after_race": 7
  }
}
```

## 🔄 Automatischer Workflow

### Vor dem Rennen
1. **72h vorher**: Erste Wettquoten abrufen
2. **24h vorher**: Vorhersagen generieren
3. **6h vorher**: Finale Wettempfehlungen erstellen

### Nach dem Rennen
1. **2h nach Rennen**: Erste Prüfung auf Ergebnisse
2. **4h nach Rennen**: Intensive Suche nach Ergebnissen
3. **Sobald verfügbar**: Automatische Verarbeitung
4. **Nach 5 Rennen**: Automatisches Model-Retraining

## 📊 Datenquellen

### Rennergebnisse
1. **FastF1** (Primär)
   - Offizielle F1-Telemetriedaten
   - Detaillierte Rennstatistiken
   - Meist 2-4h nach Rennende verfügbar

2. **Ergast API** (Fallback)
   - Historische F1-Datenbank
   - Zuverlässige Grunddaten
   - Meist 1-2h nach Rennende verfügbar

### Wettquoten
- **The Odds API** (Hauptquelle)
- **Stake.com Scraping** (Backup)

## 🚨 Monitoring & Logs

### Log-Dateien
- `logs/auto_system_YYYYMMDD.log` - Hauptsystem
- `logs/auto_monitor_YYYYMMDD.log` - Race Monitor
- `logs/results_fetcher_YYYYMMDD.log` - Results Fetcher
- `logs/auto_evaluator_YYYYMMDD.log` - Race Evaluator

### Wichtige Log-Nachrichten
```
🔍 Prüfe Ergebnisse für: British Grand Prix (Runde 12)
✅ FastF1: 20 Ergebnisse für British Grand Prix
💾 Ergebnisse gespeichert: data/incoming_results/2025_british_gp_results_auto_20250706_1845.csv
🎉 Neue Ergebnisse gefunden: British Grand Prix
📊 Verarbeite neue Rennergebnisse...
🤖 Model-Retraining ausgelöst nach 5 verarbeiteten Rennen
```

## 🛠️ Fehlerbehebung

### Häufige Probleme

#### 1. Keine Rennergebnisse gefunden
```bash
⏳ Noch keine Ergebnisse verfügbar für: British Grand Prix
```
**Lösung**: Warten - Ergebnisse werden automatisch abgerufen, sobald verfügbar

#### 2. FastF1 Fehler
```bash
❌ FastF1 Fehler für British Grand Prix: Session not available
```
**Lösung**: System verwendet automatisch Ergast API als Fallback

#### 3. API Rate Limits
```bash
⚠️ API Rate Limit erreicht, warte 60 Sekunden...
```
**Lösung**: System wartet automatisch und versucht erneut

### Manuelle Eingriffe

#### Einzelne Prüfung auf neue Ergebnisse
```bash
python ml/auto_race_results_fetcher.py check
```

#### Manuelle Verarbeitung von Ergebnissen
```bash
python ml/auto_race_evaluator.py
```

#### Manuelle Vorhersage für nächstes Rennen
```bash
python ml/predict_live_race.py
```

## 📈 Performance & Statistiken

### Automatische Metriken
- **Abruf-Erfolgsrate**: % der automatisch abgerufenen Rennergebnisse
- **Verarbeitungszeit**: Durchschnittliche Zeit von Ergebnis bis Verarbeitung
- **Vorhersagegenauigkeit**: Kontinuierliche Überwachung der Model-Performance
- **Betting-ROI**: Automatische Berechnung der Gewinn/Verlust-Entwicklung

### Status-Dashboard (geplant)
```
🏎️ F1 PREDICT PRO - SYSTEM STATUS

📊 Letzte 24h:
   • Neue Ergebnisse: 1 (British GP)
   • Verarbeitete Rennen: 1
   • Generierte Vorhersagen: 1
   • Betting ROI: +€15.50

🔄 Nächste Aktionen:
   • Belgian GP Vorhersage: in 18h
   • Quoten-Update: in 6h
   • Model-Retraining: nach 4 weiteren Rennen
```

## 🔮 Zukunftige Erweiterungen

### Geplante Features
1. **Real-time Notifications**
   - Webhook-Integration
   - Email-Benachrichtigungen
   - Discord/Slack-Bot

2. **Erweiterte Datenquellen**
   - Offizielle F1 API (falls verfügbar)
   - Zusätzliche Wettanbieter
   - Social Media Sentiment

3. **Machine Learning Verbesserungen**
   - Online Learning (kontinuierliches Training)
   - Ensemble-Modelle
   - Deep Learning Integration

4. **Web-Dashboard**
   - Live-Status-Anzeige
   - Interaktive Konfiguration
   - Historische Analyse

## 🤝 Beitragen

Das System ist modular aufgebaut und kann einfach erweitert werden:

1. **Neue Datenquellen** in `auto_race_results_fetcher.py` hinzufügen
2. **Zusätzliche Monitoring-Features** in `auto_race_monitor.py` implementieren
3. **Erweiterte Auswertungen** in `auto_race_evaluator.py` einbauen

## 📞 Support

Bei Problemen oder Fragen:
1. Prüfe die Log-Dateien in `logs/`
2. Überprüfe die Konfigurationsdateien in `config/`
3. Teste einzelne Komponenten manuell

---

**🎉 Das System läuft jetzt vollautomatisch und holt sich alle F1-Daten selbstständig, sobald sie verfügbar sind!**