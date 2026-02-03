# KOMHunter - Development Setup

## Prérequis

- **Python 3.11+** (backend)
- **Bun** (frontend — [installer Bun](https://bun.sh))
- **Credentials Strava** (voir plus bas)

## Lancer l’application facilement

### Option 1 : Deux terminaux (recommandé en dev)

**Terminal 1 – Backend :**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # puis éditer .env avec tes identifiants Strava
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 – Frontend :**
```bash
cd frontend
bun install
cp .env.example .env.local   # optionnel, défaut: http://localhost:8000
bun run dev
```

Ouvre **http://localhost:3000** dans le navigateur. L’API tourne sur **http://localhost:8000** (docs : http://localhost:8000/docs).

### Option 2 : Makefile (à la racine du repo)

```bash
make install   # installe backend + frontend (une fois)
make dev       # affiche les commandes à lancer dans 2 terminaux
make dev-backend   # lance uniquement le backend
make dev-frontend  # lance uniquement le frontend
```

### Option 3 : Docker

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker-compose up -d
```

App : http://localhost:3000 — API : http://localhost:8000

---

## Backend (détail)

1. **Environnement virtuel :**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Dépendances :**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration :**
   ```bash
   cp .env.example .env
   # Éditer .env avec les identifiants Strava
   ```

4. **Lancer le serveur :**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Tests :**
   ```bash
   pytest tests/ -v
   ```

## Frontend (Bun)

1. **Dépendances :**
   ```bash
   cd frontend
   bun install
   ```
   Après le premier `bun install`, tu peux committer `bun.lockb` pour des builds reproductibles.

2. **Configuration :**
   ```bash
   cp .env.example .env.local
   # NEXT_PUBLIC_API_URL par défaut: http://localhost:8000
   ```

3. **Dev :**
   ```bash
   bun run dev
   ```

4. **Build production :**
   ```bash
   bun run build
   bun run start
   ```

## Docker

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker-compose up -d
docker-compose logs -f
```

## API

Une fois le backend lancé :

- **Swagger :** http://localhost:8000/docs  
- **ReDoc :** http://localhost:8000/redoc  

## Structure du projet

```
komhunter/
├── backend/
│   ├── app/
│   │   ├── api/routes/   # endpoints FastAPI
│   │   ├── services/     # logique métier
│   │   ├── models/       # schémas Pydantic
│   │   └── utils/
│   └── tests/
├── frontend/             # Next.js (Bun)
│   └── src/
│       ├── app/
│       ├── components/
│       ├── hooks/
│       └── lib/
└── docs/
```

## Variables d’environnement

### Backend (`.env`)

| Variable | Description |
|----------|-------------|
| `STRAVA_CLIENT_ID` | Client ID Strava |
| `STRAVA_CLIENT_SECRET` | Client secret Strava |
| `STRAVA_REDIRECT_URI` | URL de callback OAuth |
| `JWT_SECRET_KEY` | Clé secrète JWT |

### Frontend (`.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | URL de l’API backend |

## Obtenir les identifiants Strava

1. Aller sur https://www.strava.com/settings/api  
2. Créer une application  
3. Récupérer Client ID et Client Secret  
4. Définir le domaine de callback sur `localhost`  
