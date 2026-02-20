"""
🗄️ DATABASE MODELS & INITIALIZATION
Kenya Road Safety - Database Configuration
Manages all SQLAlchemy models and database operations
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

# ============================================================================
# DATABASE MODELS
# ============================================================================

class Driver(db.Model):
    """Driver profile model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    license_number = db.Column(db.String(50), unique=True)
    vehicle_type = db.Column(db.String(50))
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_driving_hours = db.Column(db.Float, default=0)
    fatigue_level = db.Column(db.Integer, default=0)
    last_fatigue_assessment = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='inactive')
    health_status = db.Column(db.String(20), default='good')
    
    sessions = db.relationship('DrivingSession', backref='driver', lazy=True, cascade='all, delete-orphan')
    health_records = db.relationship('HealthRecord', backref='driver', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'license_number': self.license_number,
            'vehicle_type': self.vehicle_type,
            'total_driving_hours': self.total_driving_hours,
            'fatigue_level': self.fatigue_level,
            'health_status': self.health_status,
            'status': self.status
        }


class DrivingSession(db.Model):
    """Track each driving session"""
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration_hours = db.Column(db.Float)
    start_location = db.Column(db.String(200))
    end_location = db.Column(db.String(200))
    distance_km = db.Column(db.Float)
    average_fatigue = db.Column(db.Integer)
    max_fatigue = db.Column(db.Integer)
    drowsiness_alerts = db.Column(db.Integer, default=0)
    breaks_taken = db.Column(db.Integer, default=0)
    weather_condition = db.Column(db.String(50))
    road_conditions = db.Column(db.String(50))
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_hours': self.duration_hours,
            'distance_km': self.distance_km,
            'start_location': self.start_location,
            'end_location': self.end_location,
            'average_fatigue': self.average_fatigue,
            'max_fatigue': self.max_fatigue,
            'drowsiness_alerts': self.drowsiness_alerts,
            'breaks_taken': self.breaks_taken,
            'weather_condition': self.weather_condition,
            'road_conditions': self.road_conditions
        }


class HealthRecord(db.Model):
    """Driver health assessment records"""
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    assessment_type = db.Column(db.String(50))
    fatigue_level = db.Column(db.Integer)
    eye_closure_percentage = db.Column(db.Float)
    blink_frequency = db.Column(db.Float)
    head_position = db.Column(db.String(50))
    yawn_detected = db.Column(db.Boolean, default=False)
    hours_driven = db.Column(db.Float)
    sleep_hours = db.Column(db.Float)
    tiredness_level = db.Column(db.Integer)
    recommendation = db.Column(db.String(500))
    alert_sent = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'assessment_type': self.assessment_type,
            'fatigue_level': self.fatigue_level,
            'eye_closure_percentage': self.eye_closure_percentage,
            'blink_frequency': self.blink_frequency,
            'head_position': self.head_position,
            'yawn_detected': self.yawn_detected,
            'hours_driven': self.hours_driven,
            'sleep_hours': self.sleep_hours,
            'tiredness_level': self.tiredness_level,
            'recommendation': self.recommendation,
            'alert_sent': self.alert_sent
        }


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db(app):
    """Initialize database with Flask app context"""
    with app.app_context():
        db.create_all()
        print("✅ Database initialized")
