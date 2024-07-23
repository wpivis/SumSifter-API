import requests

from config import Config

LAS_API_KEY = Config.LAS_API_KEY
LAS_API_ENDPOINT = Config.LAS_API_ENDPOINT

def get_response(messages):

    response = requests.post(
        LAS_API_ENDPOINT,
        headers={
            "LAS-API-Token": LAS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.7,
        },
    )

    r = response.json()

    return r
