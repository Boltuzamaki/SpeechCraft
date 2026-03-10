from app.auth.email_auth import email_auth
from app.auth.google_auth import google_auth
from app.config.config import config
from app.extensions import db, login_manager, migrate
from flask import Flask
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app(config_name="default"):
    """
    Application factory function.
    """
    app = Flask(__name__)

    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Apply middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    from app.main.routes import main as main_blueprint

    app.register_blueprint(main_blueprint)

    app.register_blueprint(email_auth, url_prefix="/auth")
    app.register_blueprint(google_auth, url_prefix="/auth")

    # Register context processor
    @app.context_processor
    def inject_user():
        return dict(user=current_user)

    with app.app_context():
        try:
            db.create_all()
        except Exception:
            pass 

    return app
