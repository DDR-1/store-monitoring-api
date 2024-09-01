from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class MenuHours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(20))
    dayOfWeek = db.Column(db.Integer)
    start_time_local = db.Column(db.Time)
    end_time_local = db.Column(db.Time)

class StoreStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(20))
    timestamp_utc = db.Column(db.DateTime)
    status = db.Column(db.String(50))

class Timezone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(20))
    timezone_str = db.Column(db.String(50))

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(255), nullable=False, unique=True)
    status = db.Column(db.String(50), nullable=False)
    path = db.Column(db.Text, nullable=False)