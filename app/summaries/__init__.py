from flask import Blueprint

bp = Blueprint('summaries', __name__)

from app.summaries import routes
