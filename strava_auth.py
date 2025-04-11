import os
import json
from dotenv import load_dotenv
from stravalib import Client
import datetime 

load_dotenv()

def authenticate():
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")

    if os.path.exists("token.json"):
        with open("token.json") as f:
            token_data = json.load(f)

        client = Client(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_expires=token_data["expires_at"]
        )

        # 🛠️ Correction ici :
        if client.token_expires < datetime.datetime.now().timestamp():
            refreshed = client.refresh_access_token(
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=token_data["refresh_token"]
            )
            with open("token.json", "w") as f:
                json.dump(refreshed, f)
    else:
        client = Client()
        url = client.authorization_url(
            client_id=client_id,
            redirect_uri="http://localhost",
            scope=["read_all", "profile:read_all", "activity:read_all"]
        )
        print("Go to this URL and authorize the app:", url)
        code = input("Paste the code from the URL here: ")
        token_response = client.exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            code=code
        )
        with open("token.json", "w") as f:
            json.dump(token_response, f)
        client.access_token = token_response["access_token"]

    return client
