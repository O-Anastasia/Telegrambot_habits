from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import date


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=True)
    habit_1 = db.Column(db.String(300), nullable=True)
    habit_2 = db.Column(db.String(300), nullable=True)
    habit_3 = db.Column(db.String(300), nullable=True)
    date_created_1 = db.Column(db.Date, nullable=True,  default=func.now())
    date_done_1 = db.Column(db.Date, nullable=True, default=func.now())
    date_created_2 = db.Column(db.Date, nullable=True, default=func.now())
    date_done_2 = db.Column(db.Date, nullable=True, default=func.now())
    date_created_3 = db.Column(db.Date, nullable=True, default=func.now())
    date_done_3 = db.Column(db.Date, nullable=True, default=func.now())


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

