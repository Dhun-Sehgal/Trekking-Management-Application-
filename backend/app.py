import os
import sys
from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import redis as redis_lib

sys.modules.setdefault("app", sys.modules[__name__])

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")

    _default_db_path = os.path.join(BASE_DIR, "instance", "trekking.db").replace("\\", "/")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{_default_db_path}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 8  # 8 hours

    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
    REDIS_DB = int(os.environ.get("REDIS_DB", 0))
    REDIS_URL = os.environ.get("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/1")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/2")

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@trekking.local")

    GCHAT_WEBHOOK_URL = os.environ.get("GCHAT_WEBHOOK_URL", "")

    DEFAULT_ADMIN_EMAIL = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@trekking.local")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "Admin@123")

    EXPORT_DIR = os.path.join(BASE_DIR, "exports")
    CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", 60))
    FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")


db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
redis_client = None


def get_redis():
    return redis_client


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["EXPORT_DIR"], exist_ok=True)
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if db_uri.startswith("sqlite:///"):
        os.makedirs(os.path.dirname(db_uri.replace("sqlite:///", "")), exist_ok=True)

    global redis_client
    redis_client = redis_lib.from_url(app.config["REDIS_URL"], decode_responses=True)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app, resources={r"/*": {"origins": [app.config["FRONTEND_ORIGIN"], "*"]}}, supports_credentials=False)

    from controller import api_bp
    app.register_blueprint(api_bp)

    @jwt.unauthorized_loader
    def _missing_token(reason):
        return {"error": "Missing or invalid authorization token"}, 401

    @jwt.invalid_token_loader
    def _invalid_token(reason):
        return {"error": "Invalid token"}, 422

    @jwt.expired_token_loader
    def _expired_token(header, payload):
        return {"error": "Token has expired, please log in again"}, 401

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
