from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()
db_uri = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
