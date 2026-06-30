# Q-Rescue AI Frontend

Streamlit frontend and visualisation dashboard for the Q-Rescue AI group project.

## Features

- Secure demo login and session handling
- Disaster scenario input
- Simulation results and resource recommendations
- Classical and quantum optimisation comparison charts
- Disaster map visualisation
- Hospital and ambulance live tracking
- Individual ambulance route tracking with optional live refresh
- Responsive dark emergency-control-centre interface

## Technology

- Python
- Streamlit
- Pandas
- Plotly
- Folium

## Run locally

Python 3.10 or newer is recommended.

### Windows

```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run Home.py
```

You can also double-click `run_app.bat`.

### macOS or Linux

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run Home.py
```

The dashboard will normally open at `http://localhost:8501`.

## Demo accounts

| Username | Password |
| --- | --- |
| `admin` | `QRescue123` |
| `operator` | `Operator123` |
| `responder` | `Responder123` |

These accounts are for frontend demonstration only and must be replaced with backend authentication before production use.

## Project structure

```text
Q-Rescue-Frontend/
|-- assets/                 # Interface images
|-- data/                   # Sample frontend data
|-- pages/                  # Streamlit dashboard pages
|-- Home.py                 # Application entry point
|-- adapters.py             # Temporary UI-to-backend domain mapping
|-- auth.py                 # Demo authentication and sessions
|-- ambulance_data.py       # Ambulance route sample data
|-- ui_theme.py             # Shared interface styling
|-- utils.py                # Frontend simulation helpers
|-- requirements.txt        # Python dependencies
|-- run_app.bat             # Windows launcher
`-- run_app.sh              # macOS/Linux launcher
```

## Backend integration

The current calculations and tracking updates use demonstration data so the frontend can run independently.

- `adapters.py` maps frontend demo fields to backend-style domain structures: `Severity`, `DisasterCategory`, `Location`, and `Ambulance`.
- The disaster severity input uses the backend scale: `1=Low`, `2=Medium`, `3=High`, `4=Critical`.
- Disaster categories use the backend set: `generic`, `flood`, `industrial_accident`, and `city_wide_emergency`.
- Sample data is Sheffield-based to match the project context.
- Recent simulation results are saved to a lightweight JSON file in the repository `cache/` directory. This is temporary demo persistence and should be replaced by backend API/database storage when the services layer is connected.

Backend services can later replace the data returned by `utils.py` and `ambulance_data.py` without changing the page layout.

## Contribution

This folder contains the frontend contribution only. Add it to the group repository under a directory such as `frontend/`, then create a feature branch and pull request for review.
