# KOMHunter API - Tests de Validation

## Credentials Strava

| Paramètre | Valeur |
|-----------|--------|
| Client ID | `155189` |
| Client Secret | `7024e6f57e632f4266f2d95027a8a4e3f3a0c63d` |
| Access Token | `44a46852141f5bb8ef14a44046e2d5cd00ca8e38` |
| Refresh Token | `e57b0b86af0ef6ec0e87723b344d51842bc9af4e` |
| Scope | `read,read_all,profile:read_all,activity:read_all` (FULL) |
| Expiration | ~6 heures après création |

**OAuth Flow Complet**: Token obtenu via flow OAuth avec tous les scopes nécessaires.

## Tests des Routes API

### 1. Health Check
```bash
GET /api/health
```
**Résultat**: ✅ Succès
```json
{
    "status": "healthy",
    "app_name": "KOMHunter API",
    "version": "1.0.0"
}
```

### 2. Auth Login
```bash
GET /api/auth/login
```
**Résultat**: ✅ Succès (302 Redirect)
- Redirect vers: `https://www.strava.com/oauth/authorize?...`

### 3. Segments Explore
```bash
POST /api/segments/explore
Content-Type: application/json
Authorization: Bearer <token>

{
    "latitude": 48.8566,
    "longitude": 2.3522,
    "radius_km": 5,
    "activity_type": "riding",
    "max_segments": 3
}
```
**Résultat**: ✅ Succès
- Segments trouvés: 3
- Données incluent: id, name, distance, avg_grade, elev_difference, polyline, difficulty_score

### 4. Segment Details (avec KOM/QOM)
```bash
GET /api/segments/7238082
Authorization: Bearer <token>
```
**Résultat**: ✅ Succès
```json
{
    "id": 7238082,
    "name": "Côte de la Butte Montmartre",
    "distance": 824.062,
    "avg_grade": 6.1,
    "max_grade": 8.5,
    "city": "Paris",
    "country": "France",
    "effort_count": 7636,
    "athlete_count": 3473,
    "polyline": "usjiHksfMuJaKmBhDSTYFwAQkAq@g@e@Om@@e@t@sDf@mJ|AyE",
    "difficulty_score": 12.37,
    "kom": {
        "kom_time": "1:31",
        "qom_time": "1:53",
        "overall_time": "1:31",
        "local_legend_name": "Jean-luc Almansa",
        "local_legend_efforts": "159 efforts in the last 90 days"
    }
}
```

### 5. Geocoding
```bash
GET /api/segments/geocode?query=Boulder,Colorado
```
**Résultat**: ✅ Succès
```json
{
    "latitude": 40.015,
    "longitude": -105.2705,
    "display_name": "Boulder, Boulder County, Colorado, United States",
    "type": "administrative"
}
```

## Routes Strava API Directes

| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /athlete` | ✅ | Profil complet |
| `GET /athlete/activities` | ✅ | Liste des activités |
| `GET /segments/explore` | ✅ | Bounding box search |
| `GET /segments/{id}` | ✅ | Détails segment + KOM/QOM via `xoms` |
| `GET /segments/starred` | ✅ | Segments favoris avec PR |
| `GET /segments/{id}/leaderboard` | ❌ 403 | Limité par Strava (premium API) |

**Note**: Les données KOM/QOM sont disponibles directement dans les détails du segment via le champ `xoms`, pas besoin du leaderboard.

## Calcul de Difficulté

La formule de scoring fonctionne correctement:

```python
# Côte de la Butte Montmartre
distance = 824m
elevation_gain = 49.8m
avg_grade = 6.1%

score = (slope + 1) * speed_factor * distance_factor
      = (6.1 + 1) * 1.61 * 1.08
      = 12.37
```

## Prochaines Étapes

1. ✅ **OAuth Flow Complet**: Token obtenu avec tous les scopes
2. ✅ **Tests avec Données Réelles**: KOM/QOM validés (Côte de Montmartre: KOM 1:31, QOM 1:53)
3. **Rate Limiting**: Respecter 100 req/15min et 1000 req/jour
4. **Caching**: Mettre en cache les résultats de geocoding et segments
5. **Frontend Integration**: Connecter le frontend Next.js à l'API

## Tokens de Test

Pour les tests locaux, utiliser:
```bash
export STRAVA_ACCESS_TOKEN="44a46852141f5bb8ef14a44046e2d5cd00ca8e38"
export STRAVA_REFRESH_TOKEN="e57b0b86af0ef6ec0e87723b344d51842bc9af4e"
```
