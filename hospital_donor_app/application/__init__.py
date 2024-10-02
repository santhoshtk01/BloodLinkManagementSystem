from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import secrets

# Initialize extensions (without binding to the application)
db = SQLAlchemy()
jwt = JWTManager()

# This will store the singleton application instance
app = None
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Configure your database
    app.config['SECRET_KEY'] = secrets.token_hex(32)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yourdatabase.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate with the application and db

    # Register blueprints or other application logic
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
