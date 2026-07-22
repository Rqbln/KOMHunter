> **Note** — This is the original design document for KOMHunter (recovered from the `architecture-only` branch). It is kept for historical reference and describes the first Streamlit prototype, not the current codebase.

## Implementation notes (2026)

The application described below was since rewritten as a **FastAPI backend (`backend/`, port 8000) + Next.js 16 frontend (`frontend/`, Bun, port 3000)**. The core ideas survived — Strava OAuth, segment exploration by bounding box, polyline decoding, Nominatim geocoding, and the difficulty score — but the file layout, auth flow (now JWT sessions with transparent refresh), and UI (Leaflet map, React components) are entirely different, and the root-level Streamlit files are being removed. For the current architecture, commands, and auth contract, see [CLAUDE.md](../CLAUDE.md) and [README-dev.md](README-dev.md).

---

# KOMHunter - Architecture et Logique du Projet

## Vue d'ensemble

**KOMHunter** est une application web Streamlit permettant aux utilisateurs de Strava de découvrir et visualiser les segments sportifs (course à pied ou vélo) dans une zone géographique donnée, avec les informations sur les KOMs (King of the Mountain) actuels.

---

## Architecture des fichiers

```
KOMHunter/
├── app.py                 # Application principale Streamlit (UI + orchestration)
├── strava_auth.py         # Authentification OAuth2 Strava
├── strava_api.py          # Appels directs à l'API REST Strava
├── strava_client.py       # Client simplifié pour récupérer les activités
├── segment_scoring.py     # Calcul de difficulté des segments
├── requirements.txt       # Dépendances Python
├── .env_example           # Template des variables d'environnement
└── token.json             # (généré) Stockage des tokens OAuth
```

---

## Flux d'authentification OAuth2

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTIFICATION STRAVA                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Vérifier si token.json existe                               │
│     │                                                            │
│     ├─► OUI: Charger les tokens                                 │
│     │       │                                                    │
│     │       └─► Token expiré?                                   │
│     │           ├─► OUI: Rafraîchir via refresh_token           │
│     │           │        Sauvegarder nouveau token              │
│     │           └─► NON: Utiliser le token existant             │
│     │                                                            │
│     └─► NON: Flux OAuth complet                                 │
│             1. Générer URL d'autorisation                        │
│             2. Utilisateur autorise l'app sur Strava            │
│             3. Récupérer le code de callback                    │
│             4. Échanger code contre access_token                │
│             5. Sauvegarder dans token.json                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Fichier: `strava_auth.py`

```python
# Variables d'environnement requises:
STRAVA_CLIENT_ID     # ID de l'application Strava
STRAVA_CLIENT_SECRET # Secret de l'application Strava

# Scopes demandés:
- read_all           # Lecture des données générales
- profile:read_all   # Lecture du profil complet
- activity:read_all  # Lecture de toutes les activités
```

---

## Flux principal de l'application

```
┌─────────────────────────────────────────────────────────────────┐
│                     FLUX PRINCIPAL (app.py)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. INITIALISATION                                               │
│     ├─► Configuration page Streamlit                            │
│     ├─► Sidebar: Type sport (Run/Ride), nb segments, rayon     │
│     └─► Input: Recherche de localisation                        │
│                                                                  │
│  2. AUTHENTIFICATION                                             │
│     ├─► Appel authenticate()                                    │
│     ├─► Récupération infos athlète                              │
│     └─► Affichage message de bienvenue                          │
│                                                                  │
│  3. GÉOCODAGE                                                    │
│     ├─► Convertir adresse → coordonnées GPS                     │
│     └─► API: Nominatim (OpenStreetMap)                          │
│                                                                  │
│  4. AFFICHAGE CARTE INITIALE                                     │
│     ├─► Carte Folium centrée sur la localisation               │
│     ├─► Cercle indiquant le rayon de recherche                  │
│     └─► Plugins: Fullscreen, LocateControl                      │
│                                                                  │
│  5. EXPLORATION DES SEGMENTS (au clic)                          │
│     ├─► Appel explore_segments() avec bounding box              │
│     ├─► Pour chaque segment:                                    │
│     │   ├─► get_segment_details() (infos + KOM)                │
│     │   ├─► Décodage polyline pour le tracé                    │
│     │   ├─► Ajout sur la carte (PolyLine + Marker)             │
│     │   └─► Construction données tableau                        │
│     ├─► Affichage carte avec segments                           │
│     └─► Affichage tableau des résultats                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Strava - Endpoints utilisés

### 1. Explorer les segments (`strava_api.py`)

```
GET /api/v3/segments/explore
```

| Paramètre | Description |
|-----------|-------------|
| `bounds` | Bounding box: `sw_lat,sw_lon,ne_lat,ne_lon` |
| `activity_type` | `riding` ou `running` |
| `min_cat` / `max_cat` | Catégorie de difficulté (0-5) |

**Calcul du bounding box:**
```python
delta = radius_km / 111  # 1° latitude ≈ 111km
sw_lat, sw_lon = lat - delta, lon - delta
ne_lat, ne_lon = lat + delta, lon + delta
```

### 2. Détails d'un segment

```
GET /api/v3/segments/{segment_id}
```

**Données retournées:**
- Nom, distance, dénivelé, pente moyenne
- Coordonnées start/end
- Polyline encodée (tracé complet)

### 3. Leaderboard d'un segment

```
GET /api/v3/segments/{segment_id}/leaderboard
```

| Paramètre | Valeur |
|-----------|--------|
| `per_page` | 1 (juste le KOM) |
| `page` | 1 |

**Données KOM extraites:**
- Nom de l'athlète
- Temps (formaté mm:ss ou hh:mm:ss)
- Date de l'effort
- ID de l'athlète

---

## Décodage des Polylines

Les tracés des segments sont encodés en format **Google Polyline**. La fonction `decode_polyline()` convertit cette chaîne en liste de coordonnées `[lat, lng]`.

```
Polyline encodée: "cq|hHkjvv@..."
        ↓
Coordonnées: [[48.701, 2.134], [48.702, 2.135], ...]
```

**Algorithme:**
1. Parcourir la chaîne caractère par caractère
2. Décoder les deltas latitude/longitude
3. Accumuler les coordonnées
4. Diviser par 1e-5 pour obtenir les degrés

---

## Calcul de difficulté des segments

### Fichier: `segment_scoring.py`

```python
def compute_difficulty(distance_m, elevation_gain, kom_speed_kmh):
    """
    Score de difficulté (plus bas = plus facile)
    
    Formule: (pente + 1) × (30 / vitesse_KOM)
    
    - pente = dénivelé / distance
    - 30 = vitesse de référence (ajustable)
    """
```

> **Note:** Cette fonction est définie mais non utilisée dans la version actuelle de l'UI.

---

## Interface utilisateur (Streamlit)

### Sidebar (Paramètres)

| Élément | Type | Valeurs |
|---------|------|---------|
| Sport type | Selectbox | Run, Ride |
| Nb segments | Slider | 1-10 (défaut: 10) |
| Rayon recherche | Slider | 1-50 km (défaut: 10) |
| Localisation | Text input | Adresse (défaut: Paris) |

### Zone principale

1. **Carte Folium interactive**
   - Cercle bleu = zone de recherche
   - Lignes rouges = segments trouvés
   - Marqueurs verts = départ des segments
   - Popup = détails au clic

2. **Tableau des résultats**
   - ID (lien vers Strava)
   - Nom du segment
   - Distance
   - Pente moyenne
   - Nom du KOM
   - Temps du KOM

---

## Géocodage (Nominatim)

```python
def geocode_location(location_query):
    """
    Convertit une adresse en coordonnées GPS
    via l'API Nominatim (OpenStreetMap)
    
    Fallback: Paris (48.7016, 2.1341)
    """
```

**Endpoint:** `https://nominatim.openstreetmap.org/search`

---

## Dépendances principales

| Package | Rôle |
|---------|------|
| `streamlit` | Framework web UI |
| `stravalib` | Client Python Strava (OAuth + API) |
| `folium` | Cartes interactives |
| `streamlit_folium` | Intégration Folium/Streamlit |
| `pandas` | Manipulation des données |
| `requests` | Appels HTTP directs |
| `polyline` | Décodage des polylines |
| `python-dotenv` | Chargement .env |

---

## Diagramme de séquence complet

```
┌─────────┐    ┌─────────┐    ┌──────────┐    ┌────────┐    ┌──────────┐
│  User   │    │  app.py │    │strava_   │    │strava_ │    │ Strava   │
│         │    │         │    │auth.py   │    │api.py  │    │ API      │
└────┬────┘    └────┬────┘    └────┬─────┘    └───┬────┘    └────┬─────┘
     │              │              │              │              │
     │ Ouvre app    │              │              │              │
     │─────────────►│              │              │              │
     │              │              │              │              │
     │              │ authenticate()              │              │
     │              │─────────────►│              │              │
     │              │              │              │              │
     │              │              │ token.json?  │              │
     │              │              │──────────────│              │
     │              │              │              │              │
     │              │◄─────────────│              │              │
     │              │   client     │              │              │
     │              │              │              │              │
     │              │ get_athlete()│              │              │
     │              │──────────────│──────────────│─────────────►│
     │              │              │              │              │
     │◄─────────────│ "Hello, X"  │              │              │
     │              │              │              │              │
     │ Recherche loc│              │              │              │
     │─────────────►│              │              │              │
     │              │              │              │              │
     │              │ geocode      │              │              │
     │              │──────────────│──────────────│───► Nominatim│
     │              │              │              │              │
     │◄─────────────│ Carte init   │              │              │
     │              │              │              │              │
     │ Clic Explorer│              │              │              │
     │─────────────►│              │              │              │
     │              │              │              │              │
     │              │ explore_segments()          │              │
     │              │──────────────│──────────────│─────────────►│
     │              │              │              │◄─────────────│
     │              │              │              │   segments   │
     │              │              │              │              │
     │              │ [loop] get_segment_details()│              │
     │              │──────────────│──────────────│─────────────►│
     │              │              │              │◄─────────────│
     │              │              │              │ details+KOM  │
     │              │              │              │              │
     │◄─────────────│ Carte + Tab  │              │              │
     │              │              │              │              │
```

---

## Configuration requise

1. **Créer une application Strava:**
   - https://www.strava.com/settings/api
   - Récupérer Client ID et Client Secret

2. **Configurer l'environnement:**
   ```bash
   cp .env_example .env
   # Éditer .env avec vos credentials
   ```

3. **Installer les dépendances:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Lancer l'application:**
   ```bash
   streamlit run app.py
   ```

5. **Première authentification:**
   - L'app génère une URL d'autorisation
   - Autoriser sur Strava
   - Coller le code retourné
   - Le token est sauvegardé pour les sessions futures

---

## Points d'extension possibles

1. **Scoring de difficulté** - Activer `compute_difficulty()` pour classer les segments par facilité
2. **Filtres avancés** - Filtrer par dénivelé, distance, nombre d'efforts
3. **Comparaison PR** - Comparer ses temps personnels avec le KOM
4. **Export** - Exporter la liste des segments en CSV/GPX
5. **Historique** - Sauvegarder les recherches précédentes
