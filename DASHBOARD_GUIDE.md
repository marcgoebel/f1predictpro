# 🏎️ F1 PredictPro - Dashboard Guide

## 📱 Verfügbare Dashboards

Das F1 PredictPro System verfügt über **zwei spezialisierte Dashboards**, die unterschiedliche Aspekte der F1-Vorhersagen abdecken:

### 💰 Betting Dashboard (Port 8501)
**Datei:** `dashboard/app.py`  
**URL:** http://localhost:8501

**Fokus:** Wett-Empfehlungen und Live-Betting

**Features:**
- 🏁 **Live Dashboard** - Aktuelle Rennvorhersagen
- 📊 **Driver Analysis** - Detaillierte Fahreranalyse
- 💰 **Betting Recommendations** - KI-generierte Wett-Empfehlungen
- 📈 **Probabilities** - Positionswahrscheinlichkeiten
- 📥 **Export-Funktionen** - CSV/PDF Export
- 🔄 **Auto-Refresh** - Live-Updates alle 30 Sekunden

**Zielgruppe:** Nutzer, die aktiv wetten und Live-Empfehlungen benötigen

---

### 📊 Analytics Dashboard (Port 8502)
**Datei:** `dashboard/analytics_dashboard.py`  
**URL:** http://localhost:8502

**Fokus:** Datenanalyse und Performance-Metriken

**Features:**
- 🏠 **Analytics-Übersicht** - System-Metriken und KPIs
- 📈 **Performance-Trends** - Historische Leistungsanalyse
- 🎯 **Modell-Genauigkeit** - ML-Modell Performance
- 📊 **Odds-Analytics** - Detaillierte Quoten-Analyse
- 🏁 **Renn-Statistiken** - Umfassende Rennanalysen
- 🧠 **ML-Performance** - Machine Learning Insights
- 📉 **Fehleranalyse** - Vorhersagefehler-Identifikation
- 🔮 **Vorhersage-Qualität** - Kalibrierung und Zuverlässigkeit

**Zielgruppe:** Datenanalysten, Entwickler und Nutzer, die tiefere Einblicke in die Systemperformance benötigen

---

## 🚀 Dashboard-Verwaltung

### Beide Dashboards starten
```bash
python start_dashboards.py
```

Dieser Befehl startet automatisch:
- Betting Dashboard auf Port 8501
- Analytics Dashboard auf Port 8502

### Einzelne Dashboards starten

**Nur Betting Dashboard:**
```bash
streamlit run dashboard/app.py --server.port 8501
```

**Nur Analytics Dashboard:**
```bash
streamlit run dashboard/analytics_dashboard.py --server.port 8502
```

### Dashboards stoppen
- **Alle Dashboards:** `Ctrl+C` im Terminal mit `start_dashboards.py`
- **Einzelne Dashboards:** `Ctrl+C` im jeweiligen Terminal

---

## 🔧 Technische Details

### Dashboard-Architektur

```
dashboard/
├── app.py                    # Betting Dashboard (Original)
├── analytics_dashboard.py    # Analytics Dashboard (Neu)
└── supabase_dashboard.py     # Legacy Dashboard (Backup)
```

### Datenquellen

**Betting Dashboard:**
- Lokale CSV-Dateien (`data/live/`)
- Live-Vorhersagen
- Odds-Manager
- Betting-Strategien

**Analytics Dashboard:**
- Supabase-Datenbank
- Historische Daten
- Performance-Metriken
- ML-Modell-Logs

### Port-Zuordnung

| Dashboard | Port | Zweck |
|-----------|------|-------|
| Betting | 8501 | Live-Wetten und Empfehlungen |
| Analytics | 8502 | Datenanalyse und Insights |
| Legacy | 8503+ | Backup/Test-Instanzen |

---

## 📋 Nutzungsempfehlungen

### Für Wett-Interessierte
1. **Hauptsächlich Betting Dashboard nutzen** (Port 8501)
2. Regelmäßig Wett-Empfehlungen überprüfen
3. Auto-Refresh aktivieren für Live-Updates
4. Export-Funktionen für Dokumentation nutzen

### Für Datenanalysten
1. **Hauptsächlich Analytics Dashboard nutzen** (Port 8502)
2. Performance-Trends überwachen
3. Modell-Genauigkeit analysieren
4. Odds-Analytics für Markteinblicke

### Für Entwickler
1. **Beide Dashboards parallel nutzen**
2. Analytics Dashboard für System-Monitoring
3. Betting Dashboard für Feature-Tests
4. Logs und Metriken regelmäßig überprüfen

---

## 🛠️ Wartung und Updates

### Dashboard-Updates
- Betting Dashboard: Fokus auf neue Betting-Features
- Analytics Dashboard: Fokus auf erweiterte Analysen
- Beide Dashboards teilen sich die gleichen Datenquellen

### Backup-Strategie
- `supabase_dashboard.py` als Legacy-Backup
- Regelmäßige Exports der Dashboard-Konfigurationen
- Datenbank-Backups für Analytics-Daten

### Performance-Optimierung
- Caching für beide Dashboards aktiviert
- Separate Ports vermeiden Konflikte
- Automatisches Restart bei Fehlern

---

## 🆘 Troubleshooting

### Häufige Probleme

**Dashboard startet nicht:**
```bash
# Prüfe ob Port bereits belegt ist
netstat -an | findstr :8501
netstat -an | findstr :8502
```

**Datenbank-Verbindungsfehler:**
- Supabase-Credentials überprüfen
- Internet-Verbindung testen
- Analytics Dashboard neu starten

**Odds-Manager Fehler:**
- Odds-Konfiguration überprüfen (`config/odds_config.json`)
- Betting Dashboard neu starten
- Fallback auf Testdaten aktiviert

### Support
Bei Problemen:
1. Terminal-Logs überprüfen
2. Browser-Konsole checken
3. Dashboard-spezifische Fehlermeldungen beachten
4. Gegebenenfalls einzelne Dashboards testen

---

*Erstellt: Januar 2025 | Version: 2.0*