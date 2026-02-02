# KOMHunter - Development Setup

## Prerequisites

- Python 3.11+
- Node.js 22+
- npm
- Strava API credentials

## Backend Setup

1. **Create virtual environment**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Strava credentials
   ```

4. **Run the server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

## Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env.local
   # Default API URL is http://localhost:8000
   ```

3. **Run development server**:
   ```bash
   npm run dev
   ```

4. **Build for production**:
   ```bash
   npm run build
   ```

## Docker Setup

Run both services with Docker Compose:

```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

## API Documentation

Once the backend is running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
komhunter/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI endpoints
│   │   ├── services/        # Business logic
│   │   ├── models/          # Pydantic schemas
│   │   └── utils/           # Helpers
│   └── tests/               # pytest tests
├── frontend/
│   └── src/
│       ├── app/             # Next.js pages
│       ├── components/      # React components
│       ├── hooks/           # Custom hooks
│       └── lib/             # Utilities
└── docs/
    ├── ARCHITECTURE.md      # Project architecture
    └── VALIDATION.md        # Validation results
```

## Environment Variables

### Backend (.env)

| Variable | Description |
|----------|-------------|
| `STRAVA_CLIENT_ID` | Strava API client ID |
| `STRAVA_CLIENT_SECRET` | Strava API secret |
| `STRAVA_REDIRECT_URI` | OAuth callback URL |
| `JWT_SECRET_KEY` | Secret for JWT tokens |

### Frontend (.env.local)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |

## Getting Strava Credentials

1. Go to https://www.strava.com/settings/api
2. Create an application
3. Copy Client ID and Client Secret
4. Set Callback Domain to `localhost`
