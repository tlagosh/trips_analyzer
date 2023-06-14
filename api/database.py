from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
db_uri = 'postgresql://postgres:cordiA24@localhost:5432/trip_analyzer'