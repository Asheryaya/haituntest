from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assessments = db.relationship('Assessment', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

class Assessment(db.Model):
    __tablename__ = 'assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assessment_type = db.Column(db.String(20), nullable=False)  # 'disc', 'scenario', 'survey'
    status = db.Column(db.String(20), default='in_progress')  # 'in_progress', 'completed'
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    disc_answers = db.relationship('DISCAnswer', backref='assessment', lazy=True)
    scenario_answers = db.relationship('ScenarioAnswer', backref='assessment', lazy=True)
    survey_answers = db.relationship('SurveyAnswer', backref='assessment', lazy=True)
    disc_result = db.relationship('DISCResult', backref='assessment', uselist=False)

class DISCAnswer(db.Model):
    __tablename__ = 'disc_answers'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.String(10), nullable=False)  # 'A', 'B', 'C', 'D'

class ScenarioAnswer(db.Model):
    __tablename__ = 'scenario_answers'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    scenario_number = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.String(10), nullable=False)  # 'A', 'B', 'C', 'D'

class SurveyAnswer(db.Model):
    __tablename__ = 'survey_answers'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.Text, nullable=False)

class DISCResult(db.Model):
    __tablename__ = 'disc_results'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False, unique=True)
    d_score = db.Column(db.Integer, nullable=False)
    i_score = db.Column(db.Integer, nullable=False)
    s_score = db.Column(db.Integer, nullable=False)
    c_score = db.Column(db.Integer, nullable=False)
    primary_type = db.Column(db.String(1), nullable=False)
    secondary_type = db.Column(db.String(1))
