from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'editor', 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Vulnerability(db.Model):
    __tablename__ = 'vulnerabilities'
    id = db.Column(db.Integer, primary_key=True)
    repo_name = db.Column(db.String(128), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    severity = db.Column(db.String(64))
    description = db.Column(db.Text)
    extra = db.Column(db.Text)

    def extra_data(self):
        try:
            return json.loads(self.extra or "{}")
        except:
            return {}

    def set_extra(self, data: dict):
        self.extra = json.dumps(data)