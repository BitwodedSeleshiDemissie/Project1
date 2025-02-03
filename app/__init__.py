from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()  # Initialize CSRF protection

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'  # Make sure this is a strong secret key
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trip_organizer.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    csrf.init_app(app)  # Enable CSRF protection

    # Import and register routes
    from app import routes
    routes.init_app(app)  # Ensure this is called

    with app.app_context():
        db.create_all()  # Ensure database tables are created

    return app
