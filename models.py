from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    floor = db.Column(db.String(50), nullable=False)

class SustainabilityData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    floor = db.Column(db.String(50), nullable=False)
    energy = db.Column(db.Float, nullable=False)
    water = db.Column(db.Float, nullable=False)
    heat = db.Column(db.Float, nullable=False)
    waste = db.Column(db.Float, nullable=False)

