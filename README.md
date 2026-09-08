# Health Tracker Web

Small static web application. It needs no backend and can be deployed through GitHub Pages.

## Run locally

```bash
python3 scripts/import_whoop.py /path/to/my_whoop_data_2026_09_07 data/health-history.json
python3 -m http.server 8000
```

Open `http://localhost:8000`.

## Publish safely

The generated `data/health-history.json` contains personal health data. It is ignored by Git by default. Use a **private** GitHub repository if you want to sync or publish it with the data. For a public repository, keep this file ignored and let the app show no history until the visitor supplies their own export.

The importer deliberately reads only migraine, anxiety, alcohol, caffeine and menstruation from WHOOP Journal. Google Health is not represented as historical data.
