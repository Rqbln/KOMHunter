from strava_auth import authenticate

def get_my_last_activities(limit=10):
    client = authenticate()
    return list(client.get_activities(limit=limit))
