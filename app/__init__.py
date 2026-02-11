import os
from flask import Flask


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    from app.routes.search import bp as search_bp
    app.register_blueprint(search_bp)

    return app
