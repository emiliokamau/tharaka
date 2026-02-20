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
from datetime import datetime, timedelta
import jwt
import json
import math
import os
from functools import wraps
from predict_risk import AccidentPredictor
from database import db, Driver, DrivingSession, HealthRecord, init_db

# ============================================================================
# INITIALIZE FLASK APP
# ============================================================================

app = Flask(__name__)
CORS(app)

# Configuration
import os
from dotenv import load_dotenv

load_dotenv()

# Use PostgreSQL in production (Render), SQLite locally
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Render provides postgres:// or postgresql:// prefix
    # Convert to psycopg2 format if needed
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///drivers.db'

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'kenya-road-safety-2024-secure-key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-2024')

# Initialize database with app
db.init_app(app)
predictor = AccidentPredictor()

print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║  KENYA ROAD SAFETY - Unified Driver Monitoring Platform             ║
    ║  Version 2.0 - Dashboard + Chatbot + Health System                  ║
    ║  Starting on http://localhost:5000                                   ║
    ║  All features in one place!                                          ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    Features:
      [OK] Driver Registration & Login
      [OK] Real-time Drowsiness Monitoring
      [OK] AI Safety Chatbot
      [OK] Health Records Tracking
      [OK] Driving Session Management
      [OK] Safety Analytics
      [OK] Black Spot Warnings
      [OK] Risk Prediction
    
    Navigate: Register → Login → Dashboard → Features
    Database: SQLite (drivers.db)
    Database Models: Imported from database.py
""")

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
        recommendation = '[OK] You appear alert. Continue safe driving'
    else:
        alert_level = 'safe'
        recommendation = '[OK] Great! You are alert. Keep up good driving'
    
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
    
    # Get driver's current fatigue level
    fatigue = driver.fatigue_level or 0
    
    # Enhanced responses for all topics
    responses = {
        # Drowsiness related
        'drowsy': f'I notice you might be getting drowsy. Your current fatigue level is {fatigue}%. Please take a break immediately. Your safety is our priority. Would you like information on nearby rest stops?',
        'tired': f'If you\'re feeling tired, I recommend pulling over to rest. You\'ve been driving for {round(driver.total_driving_hours, 1)} hours. Driving while fatigued is dangerous.',
        'sleepy': f'Don\'t fight drowsiness! Your fatigue level is {fatigue}%. Pull over in a safe location and take a 15-20 minute nap.',
        'sleep': f'For optimal driving alertness, aim for 7-8 hours of sleep before a long trip. Naps of 20 minutes can help combat fatigue.',
        'drowsiness': f'Drowsiness management is crucial. Your current fatigue level is {fatigue}%. Take breaks every 2 hours, stay hydrated, and avoid driving between midnight and 6am.',
        'fatigue': f'Your current fatigue level is {fatigue}%. ' + ('This is high - please take a break soon!' if fatigue >= 60 else 'You appear alert. Keep up the good driving!'),
        
        # Black spots
        'black spot': 'There are several high-risk areas on Kenyan roads. Major black spots include Nairobi-Mombasa Road, Thika Road, Mombasa Road Junction, and Nairobi Outer Ring. Stay alert and reduce speed in these zones. Would you like details about dangerous roads near your location?',
        'dangerous': 'High-risk areas include: Nairobi-Mombasa Road (156 accidents), Mombasa Road Junction (145 accidents), Thika Road (101 accidents), and Eldoret-Nakuru Road (54 accidents). Drive cautiously in these areas.',
        'accident': 'Road accidents in Kenya are often caused by speeding, fatigue, and distraction. The most dangerous roads are the Nairobi-Mombasa highway and major urban roads. Always wear seatbelts and follow traffic rules.',
        
        # Route risk
        'route': 'I can help assess your route risk. Please provide your start and end locations, or enable location services for automated risk assessment along your journey.',
        'risk': 'Route risk assessment analyzes road conditions, weather, black spots, and traffic patterns to determine safety levels. Would you like me to assess your planned route?',
        
        # Road safety
        'safety': 'Road safety is our top priority! Key tips: 1) Always wear seatbelts, 2) Follow speed limits, 3) Avoid distractions, 4) Take regular breaks, 5) Never drive under the influence, 6) Use headlights at night.',
        'speed': 'Speed limits in Kenya: Urban areas 50km/h, highways 100km/h, school zones 30km/h. Exceeding speed limits significantly increases accident risk.',
        'seatbelt': 'Always wear your seatbelt - it reduces the risk of fatal injury by 45% for front-seat passengers. It\'s not just safe, it\'s the law!',
        
        # Alerts
        'alert': f'You have received an alert. Your current fatigue level is {fatigue}%. ' + ('Please take immediate action - consider stopping for a break.' if fatigue >= 60 else 'Continue safe driving but stay aware of your alertness.'),
        'warning': 'Alerts are triggered when: drowsiness is detected, fatigue level exceeds 60%, or you\'ve been driving for more than 4 hours continuously. Always respond to safety warnings.',
        
        # Weather
        'weather': 'Current weather conditions may vary. In rainy weather, reduce speed, increase following distance, and use headlights. Check local weather updates before and during your trip.',
        'rain': 'When driving in rain: reduce speed, use headlights, increase following distance, avoid sudden braking, and watch for flooding on roads.',
        
        # General help
        'help': 'I can help you with: drowsiness detection, black spot warnings, route risk assessment, safety information, weather updates, and health tracking. What do you need?',
        'hello': f'Hello {driver.full_name}! How can I assist with your safe driving today?',
        'hi': f'Hi {driver.full_name}! Ready to help with road safety information.',
    }
    
    # Find matching response
    bot_response = 'I\'m here to help with your safety while driving. Ask me about drowsiness alerts, black spots, safety tips, weather, or your health status. You can also click the Quick Actions buttons.',
    
    for keyword, response in responses.items():
        if keyword in user_message:
            bot_response = response
            break
    
    # Special handling for questions
    if '?' in user_message:
        if 'fatigue' in user_message or 'tired' in user_message:
            bot_response = f'Your current fatigue level is {fatigue}%. ' + ('This is HIGH - please take a break soon!' if fatigue >= 60 else 'You appear to be doing well. Keep driving safely!')
        elif 'black spot' in user_message:
            bot_response = 'Major black spots in Kenya include: Nairobi-Mombasa Road (HIGH risk, 156 accidents), Thika Road (HIGH risk, 101 accidents), Mombasa Road Junction (HIGH risk, 145 accidents). Stay extra cautious in these areas.'
        elif 'safety tip' in user_message:
            import random
            tips = [
                'Take a 15-minute break every 2 hours of driving.',
                'Never drive if you feel sleepy - even a short nap can help.',
                'Keep a safe distance from other vehicles.',
                'Check your mirrors every 5-10 seconds.',
                'Stay hydrated - dehydration can cause fatigue.',
                'Avoid heavy meals before driving.',
                'Use the 20-minute nap rule to combat drowsiness.'
            ]
            bot_response = f'Here\'s a safety tip: {random.choice(tips)}'
    
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
# FRONTEND ROUTES - Voice Communication
# ============================================================================

@app.route('/voice')
def voice_communication():
    """Driver Voice Communication page"""
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
    
    return render_template('voice_driver.html', driver=driver)

# ============================================================================
# API ENDPOINTS - Voice Communication
# ============================================================================

@app.route('/api/voice/command', methods=['POST'])
@token_required
def voice_command(driver_id):
    """Process voice command from driver"""
    data = request.get_json()
    command = data.get('command', '').lower()
    
    driver = Driver.query.get(driver_id)
    
    # Get current session
    current_session = DrivingSession.query.filter_by(
        driver_id=driver_id,
        end_time=None
    ).first()
    
    # Process commands
    response = ''
    action = None
    session_id = None
    
    # Fatigue level query
    if 'fatigue' in command or 'tired' in command or 'sleepy' in command:
        fatigue = driver.fatigue_level or 0
        if fatigue >= 70:
            response = f'Your fatigue level is {fatigue} percent. This is high! Please take a break immediately for your safety.'
        elif fatigue >= 40:
            response = f'Your fatigue level is {fatigue} percent. You should stay alert and consider taking a break soon.'
        else:
            response = f'Your fatigue level is {fatigue} percent. You are doing well! Keep up safe driving.'
    
    # Weather query
    elif 'weather' in command or 'rain' in command:
        response = 'Current weather conditions may vary. Drive carefully in rain and reduce speed. Check local weather updates for your area.'
    
    # Black spots
    elif 'black spot' in command or 'dangerous' in command or 'accident' in command:
        response = 'There are several high-risk areas on Kenyan roads. Stay alert, especially on Nairobi-Mombasa Road, Thika Road, and Mombasa Road Junction. Would you like me to check black spots near your location?'
    
    # Start session
    elif 'start' in command and ('session' in command or 'trip' in command or 'drive' in command):
        if current_session:
            response = 'You already have an active driving session. Say "end session" to finish it.'
        else:
            session = DrivingSession(
                driver_id=driver_id,
                start_location='Unknown',
                weather_condition='Unknown',
                road_conditions='Normal'
            )
            db.session.add(session)
            db.session.commit()
            
            driver.status = 'on_trip'
            db.session.commit()
            
            session_id = session.id
            action = 'start_session'
            response = 'Driving session started! Remember to drive safely. I will monitor your fatigue levels throughout your trip.'
    
    # End session
    elif 'end' in command and ('session' in command or 'trip' in command):
        if not current_session:
            response = 'You have no active driving session to end.'
        else:
            current_session.end_time = datetime.utcnow()
            duration = (current_session.end_time - current_session.start_time).total_seconds() / 3600
            current_session.duration_hours = round(duration, 2)
            
            driver.status = 'inactive'
            driver.total_driving_hours += current_session.duration_hours
            
            db.session.commit()
            
            response = f'Driving session ended. You drove for {round(duration, 1)} hours. Stay safe!'
            action = 'end_session'
    
    # Driving time
    elif 'how long' in command or 'driving time' in command or 'hours driven' in command:
        if current_session:
            duration = (datetime.utcnow() - current_session.start_time).total_seconds() / 3600
            response = f'You have been driving for {round(duration, 1)} hours in your current session.'
        else:
            response = f'You have driven for a total of {round(driver.total_driving_hours, 1)} hours overall.'
    
    # Safety tips
    elif 'safety' in command or 'tip' in command or 'advice' in command:
        tips = [
            'Always wear your seatbelt, even for short trips.',
            'Take a 15-minute break every 2 hours of driving.',
            'Never drive if you feel sleepy - pull over and rest.',
            'Maintain safe following distance from other vehicles.',
            'Check mirrors frequently to stay aware of surroundings.'
        ]
        import random
        tip = random.choice(tips)
        response = f'Here is a safety tip: {tip}'
    
    # Emergency
    elif 'emergency' in command or 'help' in command or 'save me' in command:
        response = 'Initiating emergency protocol. Your emergency contacts will be notified.'
        action = 'emergency'
    
    # Music
    elif 'music' in command or 'play' in command:
        response = 'I cannot play music directly, but you can use your phone or car stereo. Stay focused on the road!'
    
    # Greetings
    elif 'hello' in command or 'hi' in command or 'hey' in command:
        response = f'Hello {driver.full_name}! I am your driving assistant. Ask me about your fatigue level, weather, black spots, or say "start session" to begin driving.'
    
    # Thank you
    elif 'thank' in command:
        response = 'You are welcome! Stay safe on the road!'
    
    # Don't understand
    else:
        response = 'I did not understand that. Try asking about your fatigue level, weather, black spots, or say "help" for more options.'
    
    return jsonify({
        'success': True,
        'response': response,
        'action': action,
        'session_id': session_id
    }), 200

@app.route('/api/voice/emergency', methods=['POST'])
@token_required
def voice_emergency(driver_id):
    """Handle emergency voice command"""
    driver = Driver.query.get(driver_id)
    
    # Get current session info
    current_session = DrivingSession.query.filter_by(
        driver_id=driver_id,
        end_time=None
    ).first()
    
    # Log emergency
    record = HealthRecord(
        driver_id=driver_id,
        assessment_type='emergency',
        fatigue_level=driver.fatigue_level or 0,
        recommendation='EMERGENCY: Driver requested emergency assistance',
        alert_sent=True
    )
    
    db.session.add(record)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Emergency protocol activated',
        'driver_name': driver.full_name,
        'location': 'Unknown - enable location for precise coordinates'
    }), 200

@app.route('/api/voice/status', methods=['GET'])
@token_required
def voice_status(driver_id):
    """Get current driver status for voice system"""
    driver = Driver.query.get(driver_id)
    
    current_session = DrivingSession.query.filter_by(
        driver_id=driver_id,
        end_time=None
    ).first()
    
    return jsonify({
        'success': True,
        'status': {
            'driver_name': driver.full_name,
            'fatigue_level': driver.fatigue_level or 0,
            'health_status': driver.health_status,
            'total_driving_hours': driver.total_driving_hours,
            'current_session': {
                'id': current_session.id,
                'start_time': current_session.start_time.isoformat() if current_session else None
            } if current_session else None
        }
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
# MAIN
# ============================================================================

if __name__ == '__main__':
    init_db(app)
    app.run(debug=True, host='0.0.0.0', port=5000)
