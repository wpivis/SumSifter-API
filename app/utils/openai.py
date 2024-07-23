import requests

from config import Config

LAS_API_KEY = Config.LAS_API_KEY
LAS_API_ENDPOINT = Config.LAS_API_ENDPOINT
LAS_GPT_MODEL = Config.LAS_GPT_MODEL

def get_response(messages):

    response = requests.post(
        LAS_API_ENDPOINT,
        headers={
            "LAS-API-Token": LAS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "model": LAS_GPT_MODEL,
            "messages": messages,
            "temperature": 0.7,
        },
    )

    r = response.json()

    return r
