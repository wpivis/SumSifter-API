import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    LAS_API_ENDPOINT = os.environ.get('LAS_API_ENDPOINT', default="")
    LAS_API_KEY = os.environ.get('LAS_API_KEY')
    FAKE_RESPONSE = os.environ.get('FAKE_RESPONSE', default='False') == 'True'
