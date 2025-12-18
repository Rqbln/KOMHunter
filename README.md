<div align="center">

# 🏆 KOM Hunter

**Intelligent Strava segment explorer to find and conquer the easiest KOM/QOM opportunities**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.44.1-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Strava API](https://img.shields.io/badge/Strava-API-FC4C02?logo=strava&logoColor=white)](https://www.strava.com/api)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20Python-lightgrey)]()

</div>

---

## 📋 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Architecture](#-architecture)
- [Technologies Used](#-technologies-used)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 About

**KOM Hunter** is a powerful Python application that helps runners and cyclists identify and visualize the easiest Strava segments (KOM/QOM) to target in any selected area. The tool combines:

- 🔍 **Intelligent Segment Discovery** : Search segments by location and radius
- 🧮 **Difficulty Scoring** : Custom algorithm to calculate segment difficulty
- 🗺️ **Interactive Mapping** : Visualize segments on an interactive map with detailed popups
- 📊 **Smart Filtering** : Filter by sport type (running/cycling) and customize search parameters

The system analyzes segment data (distance, elevation gain, KOM pace/speed) to calculate a difficulty index, helping athletes prioritize which segments offer the best opportunities for achieving KOM/QOM status.

---

## ✨ Features

### 🔍 Advanced Segment Search
- ✅ Search segments by location (city, address, coordinates)
- ✅ Adjustable search radius (1-50 km)
- ✅ Real-time geocoding with OpenStreetMap
- ✅ Filter by sport type (Running/Cycling)

### 🧮 Intelligent Difficulty Scoring
- ✅ Custom difficulty index calculation
- ✅ Considers distance, elevation gain, and KOM speed
- ✅ Lower score = easier segment to target
- ✅ Customizable scoring formula

### 🗺️ Interactive Visualization
- ✅ Interactive map with Folium
- ✅ Segment polylines with detailed popups
- ✅ Start/end markers for each segment
- ✅ Search radius visualization
- ✅ Fullscreen and location controls

### 📊 Rich Segment Information
- ✅ Segment name, distance, and grade
- ✅ Current KOM holder and time
- ✅ Direct links to Strava segments
- ✅ Detailed segment data table
- ✅ Real-time progress tracking

### 🔐 Secure Authentication
- ✅ OAuth 2.0 with Strava API
- ✅ Automatic token refresh
- ✅ Secure credential management with `.env`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    KOM Hunter Ecosystem                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐  │
│  │   Streamlit  │◄─────►│  Strava API  │◄─────►│  Python  │  │
│  │     UI       │      │   OAuth 2.0  │      │  Client  │  │
│  └──────┬───────┘      └──────┬───────┘      └─────┬────┘  │
│         │                      │                    │        │
│         │                      │                    │        │
│         └──────────────────────┼────────────────────┘        │
│                                │                              │
│                         ┌──────▼──────┐                      │
│                         │   Folium    │                      │
│                         │  (Mapping)  │                      │
│                         └─────────────┘                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → Location search and parameters
2. **Geocoding** → OpenStreetMap Nominatim API converts location to coordinates
3. **Strava API** → Fetches segments in the area
4. **Segment Analysis** → Calculates difficulty scores
5. **Visualization** → Displays segments on interactive map
6. **User Interaction** → Click segments for detailed information

---

## 🛠️ Technologies Used

### Core Technologies
| Technology | Version | Usage |
|------------|---------|-------|
| [Python](https://www.python.org/) | 3.10+ | Main programming language |
| [Streamlit](https://streamlit.io/) | 1.44.1 | Web application framework |
| [StravaLib](https://github.com/stravalib/stravalib) | 2.3 | Strava API client library |
| [Folium](https://python-visualization.github.io/folium/) | 0.19.5 | Interactive map rendering |
| [Pandas](https://pandas.pydata.org/) | 2.2.3 | Data manipulation and analysis |

### Supporting Libraries
| Technology | Version | Usage |
|------------|---------|-------|
| [Requests](https://requests.readthedocs.io/) | 2.32.3 | HTTP library for API calls |
| [Python-dotenv](https://github.com/theskumar/python-dotenv) | 1.1.0 | Environment variable management |
| [Streamlit-folium](https://github.com/randyzwitch/streamlit-folium) | 0.24.0 | Folium integration for Streamlit |
| [Polyline](https://github.com/frederickjansen/polyline) | 2.0.0 | Polyline encoding/decoding |

### Services
- 🔥 **Strava API** : Segment data, leaderboards, authentication
- 🌐 **OpenStreetMap Nominatim** : Geocoding and location search

---

## 📦 Prerequisites

### Required
- **Python 3.10+** installed on your system
- **Strava Account** with API access
- **Internet Connection** for API calls and map rendering

### Optional
- **Git** for cloning the repository
- **Virtual Environment** (recommended) for dependency isolation

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/KOMHunter.git
cd KOMHunter
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Strava API Credentials

1. **Create a Strava Application** :
   - Go to [Strava API Settings](https://www.strava.com/settings/api)
   - Click "Create App"
   - Fill in the required information:
     - **Application Name** : KOM Hunter (or your choice)
     - **Category** : Web
     - **Website** : `http://localhost`
     - **Authorization Callback Domain** : `localhost`
   - Click "Create"

2. **Get Your Credentials** :
   - Copy your **Client ID**
   - Copy your **Client Secret**

3. **Create `.env` File** :
   Create a new `.env` file in the project root:
   ```bash
   touch .env
   ```

4. **Edit `.env` File** :
   ```env
   STRAVA_CLIENT_ID=your_client_id_here
   STRAVA_CLIENT_SECRET=your_client_secret_here
   ```
   
   **Note** : The `STRAVA_REFRESH_TOKEN` is generated automatically during the first authentication and stored in `token.json`. You don't need to set it manually in `.env`.

### 5. Initial Authentication

On first run, the application will guide you through the OAuth flow:

1. Run the application (see [Usage](#-usage))
2. The terminal will display an authorization URL
3. Open the URL in your browser
4. Authorize the application
5. Copy the authorization code from the redirect URL
6. Paste it in the terminal
7. A `token.json` file will be created automatically

---

## ⚙️ Configuration

### Environment Variables

The `.env` file should contain:

```env
# Strava API Credentials
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret

# Note: STRAVA_REFRESH_TOKEN is generated automatically during first authentication
# and stored in token.json. You don't need to set it manually in .env
```

### Token Management

The application automatically handles token refresh. The `token.json` file stores:
- `access_token` : Current access token
- `refresh_token` : Refresh token for obtaining new access tokens
- `expires_at` : Token expiration timestamp

**Note** : Never commit `token.json` or `.env` to version control!

---

## 💻 Usage

### Start the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

### Using the Interface

1. **Authenticate** :
   - The app will automatically authenticate with Strava
   - Your name will appear in the sidebar if successful

2. **Configure Search Parameters** :
   - **Sport Type** : Select "Run" or "Ride"
   - **Search Radius** : Adjust the slider (1-50 km)
   - **Location** : Enter a city, address, or location name
   - **Max Segments** : Choose how many segments to display (1-10)

3. **Explore Segments** :
   - Click the "🔍 Explorer les segments" button
   - Wait for the search to complete (progress bar will show status)
   - Segments will appear on the map as red polylines
   - Click on segments to see detailed information

4. **View Segment Details** :
   - Hover over segment markers for quick info
   - Click markers for detailed popups
   - View the results table below the map
   - Click segment IDs to open them on Strava

### Example Workflow

```bash
# 1. Start the application
streamlit run app.py

# 2. In the browser:
#    - Select "Ride" as sport type
#    - Set radius to 15 km
#    - Enter "Paris, France" as location
#    - Click "Explorer les segments"

# 3. Review the map and table
#    - Identify segments with low difficulty scores
#    - Click on interesting segments for details
#    - Plan your next ride to target these segments!
```

---

## 🧠 How the Difficulty Index Works

The difficulty index is calculated using a custom formula that considers multiple factors:

```python
score = (slope + 1) * (30 / kom_speed_kmh)
```

Where:
- **slope** = `elevation_gain / distance_km`
- **kom_speed_kmh** = Current KOM speed in km/h

### Interpretation

- **Lower score** = Easier segment to target
- **Higher score** = More challenging segment

### Customization

You can modify the scoring algorithm in `segment_scoring.py`:

```python
def compute_difficulty(distance_m, elevation_gain, kom_speed_kmh):
    """
    Customize this function to adjust the difficulty calculation.
    """
    # Your custom formula here
    return score
```

---

## 📁 Project Structure

```
KOMHunter/
│
├── 📄 app.py                    # Main Streamlit application
├── 📄 strava_client.py           # Strava API client wrapper
├── 📄 strava_auth.py             # OAuth authentication handler
├── 📄 strava_api.py             # Strava API endpoints and utilities
├── 📄 segment_scoring.py         # Difficulty scoring algorithm
├── 📄 requirements.txt           # Python dependencies
├── 📄 LICENSE                    # MIT License
├── 📄 README.md                  # This file
├── 📄 .env.example               # Example environment variables
└── 📄 token.json                 # OAuth tokens (generated, not in repo)
```

### Key Files

| File | Description |
|------|-------------|
| `app.py` | Main Streamlit UI and application logic |
| `strava_auth.py` | Handles OAuth 2.0 authentication flow |
| `strava_api.py` | Segment exploration and detail fetching |
| `strava_client.py` | Wrapper for Strava API client |
| `segment_scoring.py` | Difficulty index calculation |

---

## 📚 API Documentation

### Strava API Endpoints Used

#### Segment Exploration
```
GET /api/v3/segments/explore
```
- **Purpose** : Discover segments in a geographic area
- **Parameters** :
  - `bounds` : Bounding box coordinates
  - `activity_type` : "riding" or "running"
  - `min_cat` / `max_cat` : Category filters

#### Segment Details
```
GET /api/v3/segments/{id}
```
- **Purpose** : Get detailed information about a specific segment
- **Returns** : Segment metadata, coordinates, elevation profile

#### Segment Leaderboard
```
GET /api/v3/segments/{id}/leaderboard
```
- **Purpose** : Get KOM/QOM information
- **Parameters** :
  - `per_page` : Number of results (default: 1 for KOM)
  - `page` : Page number

### Geocoding API

The application uses **OpenStreetMap Nominatim** for location search:

```
GET https://nominatim.openstreetmap.org/search
```

**Parameters** :
- `q` : Location query string
- `format` : Response format (json)
- `limit` : Maximum results

**Note** : Please respect rate limits and use appropriate User-Agent headers.

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Guidelines

- Follow existing code style and conventions
- Add comments for complex logic
- Test your changes before submitting
- Update documentation if necessary
- Ensure `.env` and `token.json` are in `.gitignore`

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/KOMHunter.git
cd KOMHunter

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt

# Make your changes and test
streamlit run app.py
```

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more details.

```
MIT License

Copyright (c) 2025 Rqbln

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🙏 Acknowledgments

- [Strava](https://www.strava.com/) for providing the API and platform
- [Streamlit](https://streamlit.io/) for the amazing web framework
- [Folium](https://python-visualization.github.io/folium/) for interactive mapping
- [OpenStreetMap](https://www.openstreetmap.org/) for geocoding services
- The open-source community

---

## 🔗 Useful Links

- [Strava API Documentation](https://developers.strava.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Folium Documentation](https://python-visualization.github.io/folium/)
- [StravaLib Documentation](https://pythonhosted.org/stravalib/)

---

<div align="center">

**Made with ❤️ for KOM hunters everywhere**

[⬆ Back to top](#-kom-hunter)

</div>
