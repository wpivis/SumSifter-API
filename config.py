import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
