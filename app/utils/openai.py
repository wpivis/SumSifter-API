import requests

from config import Config


# OpenAI configuration from your config file
OPENAI_API_KEY = Config.OPENAI_API_KEY
OPENAI_API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-3.5-turbo"  # You can change this to your specific OpenAI model

def get_response(messages):
    response = requests.post(
        OPENAI_API_ENDPOINT,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "messages": messages,
            "temperature": 0.7,
        },
    )

    r = response.json()
    
    return r


# LAS_API_KEY = Config.LAS_API_KEY
# LAS_API_ENDPOINT = Config.LAS_API_ENDPOINT
# LAS_GPT_MODEL = Config.LAS_GPT_MODEL

# def get_response(messages):

#     response = requests.post(
#         LAS_API_ENDPOINT,
#         headers={
#             "LAS-API-Token": LAS_API_KEY,
#             "Content-Type": "application/json",
#         },
#         json={
#             "model": LAS_GPT_MODEL,
#             "messages": messages,
#             "temperature": 0.7,
#         },
#     )

#     r = response.json()

#     return r
