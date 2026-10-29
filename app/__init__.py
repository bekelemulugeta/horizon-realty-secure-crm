from flask import Flask
from config import Config
from app.models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Blueprints
    from app.routes.auth import auth_bp
    from app.routes.sales import sales_bp
    from app.routes.admin import admin_bp
    from app.routes.public import public_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)

    return app
