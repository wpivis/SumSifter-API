from flask import Flask
from flask_cors import CORS
from flask_caching import Cache

from config import Config

cache = Cache()

def create_app(config_class=Config):
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    app.config.from_object(config_class)

    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 3600 # timeout in seconds
    cache.init_app(app)

    # Initialize Flask extensions here

    # Register blueprints here
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.summaries import bp as summaries_bp
    app.register_blueprint(summaries_bp, url_prefix='/summaries')

    @app.route('/test/')
    def test_page():
        return 'ok'

    return app
