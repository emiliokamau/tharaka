"""
🚗 UNIFIED DRIVER MONITORING & SAFETY PLATFORM
Kenya Road Safety - Complete Driver Management System
v2.0 - Integrated Dashboard + AI Chatbot + Health Monitoring

Features:
  ✅ User Registration & Authentication (JWT)
  ✅ Driver Health Dashboard (real-time drowsiness detection)
  ✅ AI Voice Chatbot (safety guidance)
  ✅ Driving Session Tracking
  ✅ Health Metrics Monitoring
  ✅ Safety Analytics & Recommendations
  ✅ Black Spot Warnings
  ✅ Risk Prediction

All features accessible from: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import json
import math
import os
from functools import wraps
from predict_risk import AccidentPredictor

# ============================================================================
# INITIALIZE FLASK APP
# ============================================================================

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'kenya-road-safety-2024-secure-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///drivers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-2024'

# Initialize database and predictor
db = SQLAlchemy(app)
predictor = AccidentPredictor()

print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║  🚗 Kenya Road Safety - Unified Driver Monitoring Platform          ║
    ║  Version 2.0 - Dashboard + Chatbot + Health System                  ║
    ║  Starting on http://localhost:5000                                   ║
    ║  All features in one place!                                          ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    Features:
      ✅ Driver Registration & Login
      ✅ Real-time Drowsiness Monitoring
      ✅ AI Safety Chatbot
      ✅ Health Records Tracking
      ✅ Driving Session Management
      ✅ Safety Analytics
      ✅ Black Spot Warnings
      ✅ Risk Prediction
    
    Navigate: Register → Login → Dashboard → Features
    Database: SQLite (drivers.db)
""")

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
    average_fatigue = db.Column(db.Integer)
    max_fatigue = db.Column(db.Integer)
    drowsiness_alerts = db.Column(db.Integer, default=0)
    breaks_taken = db.Column(db.Integer, default=0)
    weather_condition = db.Column(db.String(50))
    road_conditions = db.Column(db.String(50))

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

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def token_required(f):
    """Decorator for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return redirect(url_for('login'))
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_driver_id = data['driver_id']
        except:
            return redirect(url_for('login'))
        return f(current_driver_id, *args, **kwargs)
    return decorated

def generate_token(driver_id):
    """Generate JWT token for driver"""
    return jwt.encode(
        {'driver_id': driver_id, 'exp': datetime.utcnow() + timedelta(days=30)},
        app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )

def load_black_spots():
    """Load black spots from data"""
    return {
        "black_spots": [
            {"location": "Nairobi-Mombasa Road", "latitude": -1.3521, "longitude": 36.8219, "risk": "HIGH", "accidents": 156},
            {"location": "Nairobi Outer Ring", "latitude": -1.3000, "longitude": 36.7500, "risk": "HIGH", "accidents": 89},
            {"location": "Thika Road", "latitude": -1.2500, "longitude": 37.0900, "risk": "HIGH", "accidents": 101},
            {"location": "Mombasa Road Junction", "latitude": -4.0435, "longitude": 39.6682, "risk": "HIGH", "accidents": 145},
            {"location": "Eldoret-Nakuru Road", "latitude": 0.5136, "longitude": 35.2721, "risk": "MEDIUM", "accidents": 54},
        ]
    }

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates"""
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def get_nearby_blackspots(latitude, longitude, radius_km=50):
    """Get black spots within radius"""
    black_spots = load_black_spots()
    nearby = []
    
    for spot in black_spots.get("black_spots", []):
        distance = calculate_distance(latitude, longitude, spot["latitude"], spot["longitude"])
        if distance <= radius_km:
            nearby.append({**spot, "distance_km": round(distance, 1)})
    
    nearby.sort(key=lambda x: x["distance_km"])
    return nearby

# ============================================================================
# FRONTEND ROUTES - Serve HTML Pages
# ============================================================================

@app.route('/')
def index():
    """Landing page - redirect to login/register"""
    token = request.cookies.get('token')
    if token:
        try:
            jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            return redirect(url_for('dashboard'))
        except:
            pass
    return redirect(url_for('login'))

@app.route('/test')
def test():
    """Test route"""
    return jsonify({'status': 'ok', 'message': 'Flask is working'}), 200

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'GET':
        # Simply render the HTML page when the user visits the URL
        return render_template('register.html')
    
    # Logic for POST (when the user clicks the "Submit" button)
    data = request.get_json()
    
    # 1. Validate data exists
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    # 2. Check for required fields
    required_fields = ['full_name', 'username', 'email', 'phone', 'license_number', 'vehicle_type', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'All fields required'}), 400
    
    # 3. Check if user exists
    if Driver.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 409
    
    # 4. Create new driver
    try:
        driver = Driver(
            full_name=data['full_name'],
            username=data['username'],
            email=data['email'],
            phone=data['phone'],
            license_number=data['license_number'],
            vehicle_type=data['vehicle_type']
        )
        driver.set_password(data['password'])
        
        db.session.add(driver)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Account created! Please login'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    driver = Driver.query.filter_by(username=data.get('username')).first()
    
    if not driver or not driver.check_password(data.get('password')):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    token = generate_token(driver.id)
    response = jsonify({'success': True, 'message': 'Login successful', 'token': token, 'driver_id': driver.id})
    response.set_cookie('token', token, httponly=True, max_age=2592000)
    
    return response, 200

@app.route('/logout')
def logout():
    """Logout"""
    response = redirect(url_for('login'))
    response.delete_cookie('token')
    return response

@app.route('/dashboard')
def dashboard():
    """Main dashboard - accessible after login"""
    token = request.cookies.get('token')
    if not token:
        return redirect(url_for('login'))
    
    try:
        data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        driver = Driver.query.get(data['driver_id'])
        if not driver:
            return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', driver=driver)

@app.route('/chatbot')
def chatbot():
    """AI Chatbot page"""
    token = request.cookies.get('token')
    if not token:
        return redirect(url_for('login'))
    
    try:
        data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        driver = Driver.query.get(data['driver_id'])
        if not driver:
            return redirect(url_for('login'))
    except:
        return redirect(url_for('login'))
    
    return render_template('chatbot.html', driver=driver)

# ============================================================================
# API ENDPOINTS - Driver Profile
# ============================================================================

@app.route('/api/driver/profile', methods=['GET'])
@token_required
def get_profile(driver_id):
    """Get driver profile"""
    driver = Driver.query.get(driver_id)
    if not driver:
        return jsonify({'success': False, 'message': 'Driver not found'}), 404
    
    return jsonify({
        'success': True,
        'profile': {
            'id': driver.id,
            'username': driver.username,
            'full_name': driver.full_name,
            'email': driver.email,
            'phone': driver.phone,
            'license_number': driver.license_number,
            'vehicle_type': driver.vehicle_type,
            'total_driving_hours': driver.total_driving_hours,
            'fatigue_level': driver.fatigue_level,
            'health_status': driver.health_status,
            'status': driver.status
        }
    }), 200

@app.route('/api/driver/statistics', methods=['GET'])
@token_required
def get_statistics(driver_id):
    """Get driver statistics"""
    driver = Driver.query.get(driver_id)
    if not driver:
        return jsonify({'success': False, 'message': 'Driver not found'}), 404
    
    sessions = DrivingSession.query.filter_by(driver_id=driver_id).all()
    health_records = HealthRecord.query.filter_by(driver_id=driver_id).all()
    
    total_hours = sum([s.duration_hours or 0 for s in sessions])
    avg_fatigue = sum([s.average_fatigue or 0 for s in sessions]) / len(sessions) if sessions else 0
    total_alerts = sum([s.drowsiness_alerts or 0 for s in sessions])
    
    return jsonify({
        'success': True,
        'statistics': {
            'total_driving_hours': round(total_hours, 1),
            'total_sessions': len(sessions),
            'average_fatigue': round(avg_fatigue, 1),
            'total_alerts': total_alerts,
            'health_records_count': len(health_records)
        }
    }), 200

# ============================================================================
# API ENDPOINTS - Drowsiness Detection
# ============================================================================

@app.route('/api/drowsiness/assess', methods=['POST'])
@token_required
def assess_drowsiness(driver_id):
    """Assess drowsiness from facial data"""
    data = request.get_json()
    
    eye_closure = data.get('eye_closure_percentage', 0)
    blink_freq = data.get('blink_frequency', 15)
    head_pos = data.get('head_position', 'normal')
    yawn = data.get('yawn_detected', False)
    hours_driven = data.get('hours_driven', 0)
    
    # Calculate fatigue score
    fatigue_score = 0
    fatigue_score += eye_closure * 0.4  # Eye closure: 0-40 points
    
    if blink_freq < 8 or blink_freq > 20:
        fatigue_score += 25
    else:
        fatigue_score += (abs(blink_freq - 15) / 15) * 10
    
    if head_pos == 'down':
        fatigue_score += 20
    elif head_pos == 'tilted':
        fatigue_score += 10
    
    if yawn:
        fatigue_score += 15
    
    if hours_driven > 6:
        fatigue_score += 15
    
    fatigue_score = min(100, max(0, fatigue_score))
    
    # Determine alert level
    if fatigue_score >= 80:
        alert_level = 'critical'
        recommendation = '🚨 CRITICAL: Pull over IMMEDIATELY and rest 15 minutes!'
    elif fatigue_score >= 60:
        alert_level = 'warning'
        recommendation = '⚠️ WARNING: Take a break soon'
    elif fatigue_score >= 30:
        alert_level = 'info'
        recommendation = '✅ You appear alert. Continue safe driving'
    else:
        alert_level = 'safe'
        recommendation = '✅ Great! You are alert. Keep up good driving'
    
    # Save to database
    driver = Driver.query.get(driver_id)
    driver.fatigue_level = int(fatigue_score)
    driver.last_fatigue_assessment = datetime.utcnow()
    
    record = HealthRecord(
        driver_id=driver_id,
        assessment_type='drowsiness',
        fatigue_level=int(fatigue_score),
        eye_closure_percentage=eye_closure,
        blink_frequency=blink_freq,
        head_position=head_pos,
        yawn_detected=yawn,
        hours_driven=hours_driven,
        recommendation=recommendation,
        alert_sent=(alert_level in ['critical', 'warning'])
    )
    
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'fatigue_level': round(fatigue_score, 1),
        'alert_level': alert_level,
        'recommendation': recommendation,
        'details': {
            'eye_closure': eye_closure,
            'blink_frequency': blink_freq,
            'head_position': head_pos,
            'yawn_detected': yawn
        }
    }), 200

# ============================================================================
# API ENDPOINTS - Sessions
# ============================================================================

@app.route('/api/session/start', methods=['POST'])
@token_required
def start_session(driver_id):
    """Start driving session"""
    data = request.get_json()
    
    session = DrivingSession(
        driver_id=driver_id,
        start_location=data.get('start_location', 'Unknown'),
        weather_condition=data.get('weather', 'Unknown'),
        road_conditions=data.get('road_conditions', 'Normal')
    )
    
    db.session.add(session)
    db.session.commit()
    
    driver = Driver.query.get(driver_id)
    driver.status = 'on_trip'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'session': {
            'id': session.id,
            'driver_id': session.driver_id,
            'start_time': session.start_time.isoformat(),
            'start_location': session.start_location
        }
    }), 201

@app.route('/api/session/end/<int:session_id>', methods=['POST'])
@token_required
def end_session(driver_id, session_id):
    """End driving session"""
    data = request.get_json()
    
    session = DrivingSession.query.get(session_id)
    if not session or session.driver_id != driver_id:
        return jsonify({'success': False, 'message': 'Session not found'}), 404
    
    session.end_time = datetime.utcnow()
    session.end_location = data.get('end_location', 'Unknown')
    session.distance_km = data.get('distance_km', 0)
    session.average_fatigue = data.get('average_fatigue', 0)
    session.max_fatigue = data.get('max_fatigue', 0)
    session.drowsiness_alerts = data.get('drowsiness_alerts', 0)
    session.breaks_taken = data.get('breaks_taken', 0)
    
    if session.start_time and session.end_time:
        duration = (session.end_time - session.start_time).total_seconds() / 3600
        session.duration_hours = round(duration, 2)
    
    db.session.commit()
    
    driver = Driver.query.get(driver_id)
    driver.status = 'inactive'
    driver.total_driving_hours += session.duration_hours or 0
    db.session.commit()
    
    return jsonify({
        'success': True,
        'session': {
            'id': session.id,
            'duration_hours': session.duration_hours,
            'distance_km': session.distance_km,
            'average_fatigue': session.average_fatigue,
            'alerts': session.drowsiness_alerts
        }
    }), 200

@app.route('/api/session/history', methods=['GET'])
@token_required
def get_sessions(driver_id):
    """Get session history"""
    sessions = DrivingSession.query.filter_by(driver_id=driver_id).order_by(DrivingSession.start_time.desc()).limit(20).all()
    
    return jsonify({
        'success': True,
        'total': len(sessions),
        'sessions': [{
            'id': s.id,
            'start_time': s.start_time.isoformat(),
            'end_time': s.end_time.isoformat() if s.end_time else None,
            'duration_hours': s.duration_hours,
            'distance_km': s.distance_km,
            'start_location': s.start_location,
            'end_location': s.end_location,
            'average_fatigue': s.average_fatigue,
            'max_fatigue': s.max_fatigue,
            'alerts': s.drowsiness_alerts
        } for s in sessions]
    }), 200

# ============================================================================
# API ENDPOINTS - Health Records
# ============================================================================

@app.route('/api/health/record', methods=['POST'])
@token_required
def record_health(driver_id):
    """Log health record"""
    data = request.get_json()
    
    record = HealthRecord(
        driver_id=driver_id,
        assessment_type=data.get('record_type', 'health_update'),
        sleep_hours=data.get('sleep_hours'),
        tiredness_level=data.get('tiredness_level'),
        fatigue_level=data.get('fatigue_level', 0),
        recommendation=data.get('recommendation', '')
    )
    
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'record': {
            'id': record.id,
            'timestamp': record.timestamp.isoformat(),
            'sleep_hours': record.sleep_hours,
            'tiredness_level': record.tiredness_level
        }
    }), 201

@app.route('/api/health/history', methods=['GET'])
@token_required
def get_health_history(driver_id):
    """Get health history"""
    limit = request.args.get('limit', 50, type=int)
    records = HealthRecord.query.filter_by(driver_id=driver_id).order_by(HealthRecord.timestamp.desc()).limit(limit).all()
    
    return jsonify({
        'success': True,
        'total': len(records),
        'records': [{
            'id': r.id,
            'timestamp': r.timestamp.isoformat(),
            'assessment_type': r.assessment_type,
            'sleep_hours': r.sleep_hours,
            'tiredness_level': r.tiredness_level,
            'fatigue_level': r.fatigue_level,
            'recommendation': r.recommendation
        } for r in records]
    }), 200

# ============================================================================
# API ENDPOINTS - Chatbot
# ============================================================================

@app.route('/api/chatbot/chat', methods=['POST'])
@token_required
def chatbot_chat(driver_id):
    """Chat with AI chatbot"""
    data = request.get_json()
    user_message = data.get('message', '').lower()
    
    driver = Driver.query.get(driver_id)
    
    # Chatbot responses
    responses = {
        'drowsy': 'I notice you might be getting drowsy. Please take a break immediately. Your safety is our priority. Would you like information on nearby rest stops?',
        'tired': 'If you\'re feeling tired, I recommend pulling over to rest. Driving while fatigued is dangerous. How long have you been driving?',
        'black spot': f'There are several high-risk areas nearby. Stay alert and reduce speed in these zones. Would you like details about dangerous roads near you?',
        'safety': 'Road safety is our top priority! Always wear seatbelts, follow speed limits, and avoid distractions. What else can I help with?',
        'alert': 'You have received an alert. Please check your dashboard for details about your current drowsiness level.',
        'help': 'I can help you with: drowsiness detection, safety information, black spot warnings, health tracking, and more. What do you need?',
    }
    
    # Find matching response
    bot_response = 'I\'m here to help with your safety while driving. Ask me about drowsiness alerts, black spots, safety tips, or your health status.'
    
    for keyword, response in responses.items():
        if keyword in user_message:
            bot_response = response
            break
    
    return jsonify({
        'success': True,
        'response': bot_response,
        'driver_name': driver.full_name
    }), 200

@app.route('/api/chatbot/location-info', methods=['GET'])
@token_required
def location_info(driver_id):
    """Get location-based safety info"""
    lat = request.args.get('latitude', type=float)
    lon = request.args.get('longitude', type=float)
    
    if not lat or not lon:
        return jsonify({'success': False, 'message': 'Location required'}), 400
    
    nearby_spots = get_nearby_blackspots(lat, lon, 50)
    
    return jsonify({
        'success': True,
        'nearby_blackspots': nearby_spots,
        'message': f'Found {len(nearby_spots)} high-risk areas nearby. Drive safely!'
    }), 200

@app.route('/api/chatbot/risk-prediction', methods=['POST'])
@token_required
def predict_route_risk(driver_id):
    """Predict risk for a route"""
    data = request.get_json()
    
    # Get risk prediction
    risk_score = predictor.predict_route_risk(
        start_lat=data.get('start_latitude'),
        start_lon=data.get('start_longitude'),
        end_lat=data.get('end_latitude'),
        end_lon=data.get('end_longitude')
    )
    
    if risk_score >= 0.7:
        risk_level = 'HIGH'
        advice = '🔴 HIGH RISK: Drive cautiously, avoid this route if possible'
    elif risk_score >= 0.4:
        risk_level = 'MEDIUM'
        advice = '🟡 MEDIUM RISK: Stay alert and maintain safe speed'
    else:
        risk_level = 'LOW'
        advice = '🟢 LOW RISK: Route appears safe. Safe driving!'
    
    return jsonify({
        'success': True,
        'risk_score': round(risk_score, 2),
        'risk_level': risk_level,
        'advice': advice
    }), 200

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        print("✅ Database initialized")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
