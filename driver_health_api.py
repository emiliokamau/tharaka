"""
🚗 ADVANCED DRIVER MONITORING & HEALTH TRACKING SYSTEM
Kenya Road Safety - Driver Wellness Platform
Features:
  • Camera-based drowsiness detection
  • Driver authentication & accounts
  • Real-time health monitoring
  • Driving hour tracking (Google Maps integration)
  • Fatigue level assessment
  • Smart recommendations
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import math
import base64
from datetime import datetime, timedelta
from functools import wraps
import jwt
from predict_risk import AccidentPredictor
import sqlite3

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'kenya-road-safety-2024-secure-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///drivers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-2024'

# Initialize database
db = SQLAlchemy(app)

# Initialize predictor
predictor = AccidentPredictor()

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
    license_expiry = db.Column(db.DateTime)
    vehicle_type = db.Column(db.String(50))  # Car, Truck, Bus
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_driving_hours = db.Column(db.Float, default=0)
    fatigue_level = db.Column(db.Integer, default=0)  # 0-100
    last_fatigue_assessment = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='inactive')  # active, inactive, on_trip
    health_status = db.Column(db.String(20), default='good')  # good, warning, alert
    
    # Relationships
    sessions = db.relationship('DrivingSession', backref='driver', lazy=True, cascade='all, delete-orphan')
    health_records = db.relationship('HealthRecord', backref='driver', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    average_fatigue = db.Column(db.Integer)  # 0-100
    max_fatigue = db.Column(db.Integer)      # 0-100
    drowsiness_alerts = db.Column(db.Integer, default=0)
    breaks_taken = db.Column(db.Integer, default=0)
    break_durations = db.Column(db.String(500))  # JSON array of break times
    route = db.Column(db.String(500))  # Start -> End
    weather_condition = db.Column(db.String(50))
    road_conditions = db.Column(db.String(50))
    
class HealthRecord(db.Model):
    """Driver health assessment records"""
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    assessment_type = db.Column(db.String(50))  # drowsiness, fatigue, comprehensive
    fatigue_level = db.Column(db.Integer)  # 0-100
    eye_closure_percentage = db.Column(db.Float)  # % of time eyes were closed
    head_position = db.Column(db.String(50))  # normal, tilted, down
    blink_frequency = db.Column(db.Float)  # blinks per minute
    yawn_detected = db.Column(db.Boolean, default=False)
    hours_driven = db.Column(db.Float)
    hours_since_rest = db.Column(db.Float)
    recommendation = db.Column(db.String(500))
    alert_sent = db.Column(db.Boolean, default=False)
    driver_response = db.Column(db.String(100))  # acknowledged, dismissed, took_break

class DailyMetrics(db.Model):
    """Daily driver metrics summary"""
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_driving_hours = db.Column(db.Float, default=0)
    total_distance = db.Column(db.Float, default=0)
    sessions_count = db.Column(db.Integer, default=0)
    average_fatigue = db.Column(db.Integer, default=0)
    max_fatigue = db.Column(db.Integer, default=0)
    total_alerts = db.Column(db.Integer, default=0)
    total_breaks = db.Column(db.Integer, default=0)
    total_break_duration = db.Column(db.Float, default=0)
    incidents = db.Column(db.Integer, default=0)
    overall_health_score = db.Column(db.Integer, default=0)  # 0-100

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Driver registration endpoint"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'full_name', 'phone', 'license_number', 'vehicle_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Check if user already exists
        if Driver.query.filter_by(username=data['username']).first():
            return jsonify({"error": "Username already exists"}), 400
        
        if Driver.query.filter_by(email=data['email']).first():
            return jsonify({"error": "Email already registered"}), 400
        
        if Driver.query.filter_by(license_number=data['license_number']).first():
            return jsonify({"error": "License number already registered"}), 400
        
        # Create new driver
        driver = Driver(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            phone=data['phone'],
            license_number=data['license_number'],
            vehicle_type=data['vehicle_type'],
            license_expiry=datetime.strptime(data.get('license_expiry', '2025-12-31'), '%Y-%m-%d')
        )
        driver.set_password(data['password'])
        
        db.session.add(driver)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Registration successful",
            "driver_id": driver.id,
            "username": driver.username
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Driver login endpoint"""
    try:
        data = request.json
        
        if not data.get('username') or not data.get('password'):
            return jsonify({"error": "Username and password required"}), 400
        
        driver = Driver.query.filter_by(username=data['username']).first()
        
        if not driver or not driver.check_password(data['password']):
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'driver_id': driver.id,
            'username': driver.username,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            "success": True,
            "token": token,
            "driver": {
                "id": driver.id,
                "username": driver.username,
                "full_name": driver.full_name,
                "email": driver.email,
                "vehicle_type": driver.vehicle_type,
                "status": driver.status,
                "health_status": driver.health_status,
                "total_driving_hours": driver.total_driving_hours,
                "fatigue_level": driver.fatigue_level
            }
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def token_required(f):
    """Decorator for protecting routes with JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token required"}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_driver_id = data['driver_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(current_driver_id, *args, **kwargs)
    
    return decorated

# ============================================================================
# DROWSINESS DETECTION ROUTES
# ============================================================================

@app.route('/api/driver/drowsiness-assessment', methods=['POST'])
@token_required
def drowsiness_assessment(driver_id):
    """Process camera frame and assess drowsiness"""
    try:
        data = request.json
        
        # Data from JavaScript facial detection
        eye_closure_pct = data.get('eye_closure_percentage', 0)
        blink_frequency = data.get('blink_frequency', 0)
        head_position = data.get('head_position', 'normal')
        yawn_detected = data.get('yawn_detected', False)
        hours_driven = data.get('hours_driven', 0)
        
        # Calculate fatigue level (0-100)
        fatigue_score = calculate_fatigue_score(
            eye_closure_pct,
            blink_frequency,
            head_position,
            yawn_detected,
            hours_driven
        )
        
        # Determine recommendation
        recommendation, alert_level = generate_recommendation(
            fatigue_score,
            hours_driven,
            head_position,
            yawn_detected
        )
        
        # Create health record
        health_record = HealthRecord(
            driver_id=driver_id,
            assessment_type='drowsiness',
            fatigue_level=fatigue_score,
            eye_closure_percentage=eye_closure_pct,
            blink_frequency=blink_frequency,
            head_position=head_position,
            yawn_detected=yawn_detected,
            hours_driven=hours_driven,
            recommendation=recommendation,
            alert_sent=(alert_level == 'high')
        )
        
        db.session.add(health_record)
        
        # Update driver fatigue level
        driver = Driver.query.get(driver_id)
        driver.fatigue_level = fatigue_score
        driver.last_fatigue_assessment = datetime.utcnow()
        
        # Update health status
        if fatigue_score >= 80:
            driver.health_status = 'alert'
        elif fatigue_score >= 60:
            driver.health_status = 'warning'
        else:
            driver.health_status = 'good'
        
        db.session.commit()
        
        return jsonify({
            "fatigue_level": fatigue_score,
            "alert_level": alert_level,
            "recommendation": recommendation,
            "details": {
                "eye_closure": eye_closure_pct,
                "blink_frequency": blink_frequency,
                "head_position": head_position,
                "yawn_detected": yawn_detected
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def calculate_fatigue_score(eye_closure, blink_freq, head_pos, yawn, hours_driven):
    """
    Calculate fatigue score (0-100) based on facial features
    
    Factors:
    • Eye closure: 0-40 points
    • Blink frequency: 0-25 points (abnormal = high or low)
    • Head position: 0-20 points (tilted/down = high)
    • Yawn detected: +15 points
    • Hours driven: 0-25 points (increases with hours)
    """
    score = 0
    
    # Eye closure (0-40 points)
    # Normal: 5-10%, Heavy drowsiness: >20%
    if eye_closure > 20:
        score += 40
    elif eye_closure > 15:
        score += 30
    elif eye_closure > 10:
        score += 20
    elif eye_closure > 5:
        score += 10
    
    # Blink frequency (0-25 points)
    # Normal: 12-16 blinks/min, Drowsy: <8 or >20
    if blink_freq < 8 or blink_freq > 20:
        score += 25
    elif blink_freq < 10 or blink_freq > 18:
        score += 15
    elif blink_freq < 11 or blink_freq > 17:
        score += 10
    
    # Head position (0-20 points)
    if head_pos == 'down':
        score += 20
    elif head_pos == 'tilted':
        score += 10
    
    # Yawn detection (0-15 points)
    if yawn:
        score += 15
    
    # Hours driven (0-25 points)
    # Risk increases significantly after 4 hours
    if hours_driven > 8:
        score += 25
    elif hours_driven > 6:
        score += 20
    elif hours_driven > 4:
        score += 15
    elif hours_driven > 2:
        score += 10
    
    return min(100, score)

def generate_recommendation(fatigue_score, hours_driven, head_pos, yawn):
    """Generate recommendation and alert level based on fatigue"""
    
    if fatigue_score >= 80:
        return (
            "🚨 CRITICAL: You appear to be extremely drowsy! PULL OVER IMMEDIATELY and rest for at least 15 minutes. Turn off engine and get proper sleep.",
            "high"
        )
    elif fatigue_score >= 60:
        return (
            "⚠️ WARNING: Signs of drowsiness detected! Find a safe place to park and take a 10-15 minute break. Stay hydrated and alert.",
            "medium"
        )
    elif hours_driven > 6:
        return (
            "💡 REMINDER: You've been driving for " + str(round(hours_driven, 1)) + " hours. Take a break now for your safety.",
            "low"
        )
    elif yawn:
        return (
            "👁️ Yawning detected. Consider taking a short break or pulling over for a few minutes.",
            "low"
        )
    elif fatigue_score > 30:
        return (
            "⚡ Stay alert! Maintain focus on the road. Continue monitoring your drowsiness levels.",
            "low"
        )
    else:
        return (
            "✅ You appear to be alert. Continue driving safely and take breaks every 2 hours.",
            "ok"
        )

# ============================================================================
# DRIVING SESSION ROUTES
# ============================================================================

@app.route('/api/driver/start-session', methods=['POST'])
@token_required
def start_session(driver_id):
    """Start a new driving session"""
    try:
        data = request.json
        
        driver = Driver.query.get(driver_id)
        
        session = DrivingSession(
            driver_id=driver_id,
            start_location=data.get('location', 'Unknown'),
            weather_condition=data.get('weather', 'Unknown')
        )
        
        db.session.add(session)
        driver.status = 'on_trip'
        db.session.commit()
        
        return jsonify({
            "success": True,
            "session_id": session.id,
            "start_time": session.start_time.isoformat()
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/driver/end-session/<int:session_id>', methods=['POST'])
@token_required
def end_session(driver_id, session_id):
    """End a driving session"""
    try:
        data = request.json
        
        session = DrivingSession.query.get(session_id)
        if not session or session.driver_id != driver_id:
            return jsonify({"error": "Session not found"}), 404
        
        # Calculate session duration
        session.end_time = datetime.utcnow()
        session.duration_hours = (session.end_time - session.start_time).total_seconds() / 3600
        session.end_location = data.get('location', 'Unknown')
        session.distance_km = data.get('distance', 0)
        session.average_fatigue = data.get('average_fatigue', 0)
        session.max_fatigue = data.get('max_fatigue', 0)
        session.drowsiness_alerts = data.get('alerts', 0)
        session.breaks_taken = data.get('breaks', 0)
        
        # Update driver total hours
        driver = Driver.query.get(driver_id)
        driver.total_driving_hours += session.duration_hours
        driver.status = 'inactive'
        
        # Create daily metrics
        update_daily_metrics(driver_id, session)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "session_summary": {
                "duration_hours": round(session.duration_hours, 2),
                "distance_km": session.distance_km,
                "average_fatigue": session.average_fatigue,
                "alerts_received": session.drowsiness_alerts
            }
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def update_daily_metrics(driver_id, session):
    """Update daily metrics for driver"""
    today = datetime.utcnow().date()
    metrics = DailyMetrics.query.filter_by(driver_id=driver_id, date=today).first()
    
    if not metrics:
        metrics = DailyMetrics(driver_id=driver_id, date=today)
        db.session.add(metrics)
    
    metrics.total_driving_hours += session.duration_hours
    metrics.total_distance += session.distance_km
    metrics.sessions_count += 1
    metrics.average_fatigue = (metrics.average_fatigue + session.average_fatigue) // 2
    metrics.max_fatigue = max(metrics.max_fatigue, session.max_fatigue)

# ============================================================================
# DRIVER PROFILE & HEALTH ROUTES
# ============================================================================

@app.route('/api/driver/profile', methods=['GET'])
@token_required
def get_profile(driver_id):
    """Get driver profile"""
    try:
        driver = Driver.query.get(driver_id)
        if not driver:
            return jsonify({"error": "Driver not found"}), 404
        
        # Get recent health record
        recent_health = HealthRecord.query.filter_by(driver_id=driver_id).order_by(
            HealthRecord.timestamp.desc()
        ).first()
        
        # Get today's metrics
        today = datetime.utcnow().date()
        today_metrics = DailyMetrics.query.filter_by(
            driver_id=driver_id,
            date=today
        ).first()
        
        return jsonify({
            "profile": {
                "id": driver.id,
                "username": driver.username,
                "full_name": driver.full_name,
                "email": driver.email,
                "phone": driver.phone,
                "vehicle_type": driver.vehicle_type,
                "license_number": driver.license_number,
                "registration_date": driver.registration_date.isoformat(),
                "status": driver.status,
                "health_status": driver.health_status
            },
            "health_metrics": {
                "total_driving_hours": round(driver.total_driving_hours, 2),
                "current_fatigue_level": driver.fatigue_level,
                "last_fatigue_assessment": driver.last_fatigue_assessment.isoformat() if driver.last_fatigue_assessment else None,
                "recent_health_record": {
                    "timestamp": recent_health.timestamp.isoformat() if recent_health else None,
                    "fatigue_level": recent_health.fatigue_level if recent_health else 0,
                    "recommendation": recent_health.recommendation if recent_health else None
                } if recent_health else None,
                "today_metrics": {
                    "driving_hours": today_metrics.total_driving_hours if today_metrics else 0,
                    "distance": today_metrics.total_distance if today_metrics else 0,
                    "sessions": today_metrics.sessions_count if today_metrics else 0,
                    "alerts": today_metrics.total_alerts if today_metrics else 0,
                    "breaks_taken": today_metrics.total_breaks if today_metrics else 0
                } if today_metrics else None
            }
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/driver/health-history', methods=['GET'])
@token_required
def get_health_history(driver_id):
    """Get driver health records history"""
    try:
        # Get last 50 health records
        records = HealthRecord.query.filter_by(driver_id=driver_id).order_by(
            HealthRecord.timestamp.desc()
        ).limit(50).all()
        
        return jsonify({
            "count": len(records),
            "records": [{
                "timestamp": r.timestamp.isoformat(),
                "fatigue_level": r.fatigue_level,
                "assessment_type": r.assessment_type,
                "recommendation": r.recommendation,
                "eye_closure": r.eye_closure_percentage,
                "blink_frequency": r.blink_frequency,
                "yawn_detected": r.yawn_detected,
                "hours_driven": r.hours_driven
            } for r in records]
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/driver/driving-sessions', methods=['GET'])
@token_required
def get_driving_sessions(driver_id):
    """Get driving sessions history"""
    try:
        # Get last 20 sessions
        sessions = DrivingSession.query.filter_by(driver_id=driver_id).order_by(
            DrivingSession.start_time.desc()
        ).limit(20).all()
        
        return jsonify({
            "count": len(sessions),
            "sessions": [{
                "id": s.id,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "duration_hours": round(s.duration_hours, 2) if s.duration_hours else 0,
                "distance_km": s.distance_km,
                "start_location": s.start_location,
                "end_location": s.end_location,
                "average_fatigue": s.average_fatigue,
                "max_fatigue": s.max_fatigue,
                "alerts": s.drowsiness_alerts,
                "breaks": s.breaks_taken
            } for s in sessions]
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# ADMIN & MONITORING ROUTES
# ============================================================================

@app.route('/api/admin/active-drivers', methods=['GET'])
def get_active_drivers():
    """Get all currently active drivers (for admin dashboard)"""
    try:
        active_drivers = Driver.query.filter_by(status='on_trip').all()
        
        return jsonify({
            "count": len(active_drivers),
            "drivers": [{
                "id": d.id,
                "username": d.username,
                "full_name": d.full_name,
                "vehicle_type": d.vehicle_type,
                "current_fatigue": d.fatigue_level,
                "health_status": d.health_status,
                "status": d.status
            } for d in active_drivers]
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/health-alerts', methods=['GET'])
def get_health_alerts():
    """Get all recent health alerts"""
    try:
        # Get alerts from last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        alerts = HealthRecord.query.filter(
            HealthRecord.timestamp >= yesterday,
            HealthRecord.alert_sent == True
        ).order_by(HealthRecord.timestamp.desc()).all()
        
        return jsonify({
            "count": len(alerts),
            "alerts": [{
                "id": a.id,
                "driver_id": a.driver_id,
                "driver_name": a.driver.full_name,
                "timestamp": a.timestamp.isoformat(),
                "fatigue_level": a.fatigue_level,
                "recommendation": a.recommendation,
                "response": a.driver_response
            } for a in alerts]
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# GOOGLE MAPS INTEGRATION
# ============================================================================

@app.route('/api/location/track-driving', methods=['POST'])
@token_required
def track_driving_location(driver_id):
    """Track driver location during trip"""
    try:
        data = request.json
        
        # Data from Google Maps API
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        location_name = data.get('location_name')
        time_on_road = data.get('time_on_road')  # minutes
        
        # This would typically be stored in a session tracking table
        # For now, we update the active session
        active_session = DrivingSession.query.filter(
            DrivingSession.driver_id == driver_id,
            DrivingSession.end_time == None
        ).first()
        
        if not active_session:
            return jsonify({"error": "No active session"}), 400
        
        return jsonify({
            "success": True,
            "location_tracked": {
                "latitude": latitude,
                "longitude": longitude,
                "location": location_name,
                "time_on_road": time_on_road
            }
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# STATISTICS & ANALYTICS
# ============================================================================

@app.route('/api/driver/statistics', methods=['GET'])
@token_required
def get_statistics(driver_id):
    """Get driver statistics and analytics"""
    try:
        driver = Driver.query.get(driver_id)
        
        # Get last 7 days metrics
        seven_days_ago = datetime.utcnow().date() - timedelta(days=7)
        week_metrics = DailyMetrics.query.filter(
            DailyMetrics.driver_id == driver_id,
            DailyMetrics.date >= seven_days_ago
        ).all()
        
        # Calculate statistics
        total_hours_week = sum(m.total_driving_hours for m in week_metrics)
        total_distance_week = sum(m.total_distance for m in week_metrics)
        total_alerts_week = sum(m.total_alerts for m in week_metrics)
        avg_fatigue_week = sum(m.average_fatigue for m in week_metrics) / len(week_metrics) if week_metrics else 0
        
        # Get all health records for trend analysis
        health_records = HealthRecord.query.filter_by(driver_id=driver_id).order_by(
            HealthRecord.timestamp.desc()
        ).limit(100).all()
        
        fatigue_trend = [r.fatigue_level for r in reversed(health_records)]
        
        return jsonify({
            "driver_id": driver_id,
            "total_driving_hours": round(driver.total_driving_hours, 2),
            "current_fatigue": driver.fatigue_level,
            "health_status": driver.health_status,
            "last_week": {
                "driving_hours": round(total_hours_week, 2),
                "distance_km": round(total_distance_week, 2),
                "alerts": total_alerts_week,
                "average_fatigue": round(avg_fatigue_week, 1),
                "days_active": len(week_metrics)
            },
            "fatigue_trend": fatigue_trend[-30:],  # Last 30 assessments
            "recommendations": generate_health_recommendations(driver, week_metrics)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_health_recommendations(driver, week_metrics):
    """Generate health recommendations based on driver data"""
    recommendations = []
    
    if driver.fatigue_level >= 70:
        recommendations.append("🚨 Your fatigue level is high. Take a longer break before driving again.")
    
    if driver.total_driving_hours > 40:
        recommendations.append("⏱️ You've driven more than 40 hours this week. Consider resting more.")
    
    if week_metrics and sum(m.total_alerts for m in week_metrics) > 5:
        recommendations.append("⚠️ You've received multiple drowsiness alerts. Get more rest between drives.")
    
    if not recommendations:
        recommendations.append("✅ You're doing great! Continue maintaining your healthy driving habits.")
    
    return recommendations

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """API health check"""
    return jsonify({
        "status": "online",
        "service": "Driver Monitoring & Health Tracking System",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0"
    })

@app.route('/', methods=['GET'])
def index():
    """API info"""
    return jsonify({
        "name": "Kenya Road Safety - Driver Monitoring System",
        "version": "2.0",
        "features": [
            "Driver authentication & accounts",
            "Camera-based drowsiness detection",
            "Real-time health monitoring",
            "Driving session tracking",
            "Health records & analytics",
            "Admin monitoring dashboard"
        ],
        "endpoints": {
            "auth": {
                "/api/auth/register": "POST - Register new driver",
                "/api/auth/login": "POST - Driver login"
            },
            "driver": {
                "/api/driver/profile": "GET - Get driver profile",
                "/api/driver/drowsiness-assessment": "POST - Submit drowsiness assessment",
                "/api/driver/health-history": "GET - Get health records",
                "/api/driver/driving-sessions": "GET - Get driving sessions",
                "/api/driver/statistics": "GET - Get driver statistics",
                "/api/driver/start-session": "POST - Start driving session",
                "/api/driver/end-session/:id": "POST - End driving session"
            },
            "admin": {
                "/api/admin/active-drivers": "GET - Get active drivers",
                "/api/admin/health-alerts": "GET - Get health alerts"
            }
        }
    })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║  🚗 Kenya Road Safety - Driver Monitoring & Health Tracking System  ║
    ║  Version 2.0 - Advanced Driver Wellness Platform                    ║
    ║  Starting on http://localhost:5000                                   ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    Features:
      ✅ Driver authentication & accounts
      ✅ Camera-based drowsiness detection
      ✅ Real-time health monitoring
      ✅ Driving hour tracking
      ✅ Health records database
      ✅ Admin monitoring dashboard
    
    Database: SQLite (drivers.db)
    """)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
