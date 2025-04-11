# Strava KOM Hunter 🏃‍♂️🚴‍♀️

**Strava KOM Hunter** is a Python-powered tool that helps runners and cyclists identify and visualize the easiest Strava segments (KOM/QOM) to target in a selected area.  
It uses segment data (distance, elevation gain, KOM pace/speed) to calculate a difficulty index and displays the best opportunities on an interactive map.

## 🔧 Features

- 🔍 Search for segments by location and radius
- 🧮 Calculate a custom "difficulty index" for each segment
- 🗺️ Display segments on a map with interactive popups
- 📊 Filter by sport type (running / cycling)
- 💾 Optional export to CSV or GPX

## 📦 Tech Stack

- `Python 3.10+`
- [stravalib](https://github.com/stravalib/stravalib) — Strava API client
- `Streamlit` — for the interactive UI
- `folium` + `streamlit-folium` — for rendering maps
- `pandas`, `pydantic`, `dotenv` — for data handling and configs

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/kom-hunter.git
cd kom-hunter
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your `.env`
Create a `.env` file based on `.env.example`:
```env
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_REFRESH_TOKEN=your_refresh_token
```

👉 You can get these values by [creating a Strava app](https://www.strava.com/settings/api).

### 4. Run the app
```bash
streamlit run app.py
```

## 🧠 How the Difficulty Index Works

Each segment is scored based on a formula like:
```
index = (elevation_gain / distance_km) * (30 / kom_speed_kmh)
```

You can customize this logic in `segment_scoring.py`.

## 📂 Project Structure

```
kom-hunter/
├── app.py                 # Streamlit UI
├── strava_client.py       # Handles API auth and segment fetching
├── segment_scoring.py     # Logic for computing difficulty
├── .env.example           # Example env config
├── requirements.txt
└── README.md
```

## 🙌 Contributions

Feel free to fork, tweak, and submit pull requests!  
This project is for personal and community use, especially for all KOM hunters out there 😎
