"""
🚗 Voice Chatbot API Backend
Kenya Road Accident Risk Prediction System
Provides real-time safety guidance via voice and text
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import math
from datetime import datetime
from predict_risk import AccidentPredictor

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize predictor
predictor = AccidentPredictor()

# ============================================================================
# DATA SOURCES - Load from training data
# ============================================================================

def load_black_spots():
    """Load black spots from training data"""
    try:
        with open('training_data/black_spots.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "black_spots": [
                {"location": "Nairobi-Mombasa Road", "latitude": -1.3521, "longitude": 36.8219, "risk": "HIGH", "accidents": 156},
                {"location": "Nairobi Outer Ring", "latitude": -1.3000, "longitude": 36.7500, "risk": "HIGH", "accidents": 89},
                {"location": "Nairobi-Nakuru Highway", "latitude": -0.9500, "longitude": 36.6500, "risk": "MEDIUM", "accidents": 67},
                {"location": "Mombasa Road Junction", "latitude": -4.0435, "longitude": 39.6682, "risk": "HIGH", "accidents": 145},
                {"location": "Eldoret-Nakuru Road", "latitude": 0.5136, "longitude": 35.2721, "risk": "MEDIUM", "accidents": 54},
                {"location": "Kisumu-Nakuru Road", "latitude": -0.1022, "longitude": 34.7617, "risk": "MEDIUM", "accidents": 78},
                {"location": "Nairobi CBD", "latitude": -1.2921, "longitude": 36.8219, "risk": "MEDIUM", "accidents": 123},
                {"location": "Thika Road", "latitude": -1.2500, "longitude": 37.0900, "risk": "HIGH", "accidents": 101},
                {"location": "Kiambu Road", "latitude": -1.2000, "longitude": 36.8100, "risk": "MEDIUM", "accidents": 56},
                {"location": "Msa-Dar es Salaam", "latitude": -4.0435, "longitude": 39.6682, "risk": "HIGH", "accidents": 167},
            ]
        }

def load_locations_db():
    """Load locations and their characteristics"""
    try:
        with open('training_data/locations.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "locations": {
                "Nairobi-Mombasa Road": {"traffic": "HIGH", "accidents_yearly": 156, "risk": "HIGH", "description": "Major highway, busy traffic"},
                "Nairobi-Nakuru Highway": {"traffic": "MEDIUM", "accidents_yearly": 67, "risk": "MEDIUM", "description": "Mostly safe, some curves"},
                "Thika Road": {"traffic": "HIGH", "accidents_yearly": 101, "risk": "HIGH", "description": "Industrial area, heavy vehicles"},
                "Nairobi CBD": {"traffic": "HIGH", "accidents_yearly": 123, "risk": "MEDIUM", "description": "Urban area, congestion"},
                "Rural Highway": {"traffic": "LOW", "accidents_yearly": 12, "risk": "LOW", "description": "Safe rural roads"},
                "Kisumu-Nakuru Road": {"traffic": "MEDIUM", "accidents_yearly": 78, "risk": "MEDIUM", "description": "Regional highway"},
                "Eldoret-Nakuru Road": {"traffic": "MEDIUM", "accidents_yearly": 54, "risk": "MEDIUM", "description": "Mountain road, curves"},
            }
        }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates (Haversine formula)"""
    R = 6371  # Earth's radius in km
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def get_nearby_blackspots(latitude, longitude, radius_km=50):
    """Get black spots within radius of driver's location"""
    black_spots = load_black_spots()
    nearby = []
    
    for spot in black_spots.get("black_spots", []):
        distance = calculate_distance(
            latitude, longitude,
            spot["latitude"], spot["longitude"]
        )
        if distance <= radius_km:
            nearby.append({
                **spot,
                "distance_km": round(distance, 1)
            })
    
    # Sort by distance
    nearby.sort(key=lambda x: x["distance_km"])
    return nearby

def get_mock_weather(location):
    """Get mock weather data (in real system, use weather API)"""
    weather_conditions = {
        "Nairobi": {"temp": 24, "condition": "Partly Cloudy", "visibility": "Good", "rain": False},
        "Mombasa": {"temp": 28, "condition": "Sunny", "visibility": "Good", "rain": False},
        "Nakuru": {"temp": 21, "condition": "Cloudy", "visibility": "Good", "rain": False},
        "Eldoret": {"temp": 19, "condition": "Rainy", "visibility": "Moderate", "rain": True},
        "Kisumu": {"temp": 26, "condition": "Partly Cloudy", "visibility": "Good", "rain": False},
    }
    
    # Match location to nearest city
    for city, weather in weather_conditions.items():
        if city.lower() in location.lower():
            return weather
    
    # Default weather
    return {"temp": 24, "condition": "Partly Cloudy", "visibility": "Good", "rain": False}

def get_safety_recommendations(latitude=None, longitude=None, destination=None):
    """Generate safety recommendations based on location and time"""
    recommendations = []
    
    # Time-based recommendations
    hour = datetime.now().hour
    if hour >= 18 or hour <= 6:
        recommendations.append("🌙 Night driving: Use headlights, reduce speed, stay alert")
    else:
        recommendations.append("☀️ Daytime driving: Maintain safe speed and distance")
    
    # Location-based recommendations
    if latitude and longitude:
        nearby_spots = get_nearby_blackspots(latitude, longitude, 50)
        if nearby_spots:
            high_risk_spots = [s for s in nearby_spots if s["risk"] == "HIGH"]
            if high_risk_spots:
                spot_names = ", ".join([s["location"] for s in high_risk_spots[:2]])
                recommendations.append(f"⚠️ High-risk areas nearby ({spot_names}): Reduce speed and stay vigilant")
    
    # General recommendations
    recommendations.append("✅ Maintain safe following distance (3+ seconds)")
    recommendations.append("✅ Avoid phone while driving")
    recommendations.append("✅ Take breaks every 2 hours on long journeys")
    
    return recommendations

def parse_user_query(query):
    """Parse user query to extract intent and entities"""
    query_lower = query.lower()
    
    intent = "general"
    if any(word in query_lower for word in ["weather", "rain", "condition", "visibility"]):
        intent = "weather"
    elif any(word in query_lower for word in ["black spot", "danger", "risk", "accident", "unsafe"]):
        intent = "blackspots"
    elif any(word in query_lower for word in ["to", "heading", "going", "drive", "route"]):
        intent = "route_info"
    elif any(word in query_lower for word in ["safe", "safety", "recommendation", "advice"]):
        intent = "safety"
    elif any(word in query_lower for word in ["speed", "limit", "how fast"]):
        intent = "speed"
    
    return intent

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chatbot endpoint - processes user messages"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        user_location = data.get('location', None)  # {lat, lon}
        
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
        
        # Parse user intent
        intent = parse_user_query(user_message)
        
        # Generate response based on intent
        if intent == "weather":
            response = handle_weather_query(user_message, user_location)
        elif intent == "blackspots":
            response = handle_blackspots_query(user_message, user_location)
        elif intent == "route_info":
            response = handle_route_query(user_message, user_location)
        elif intent == "safety":
            response = handle_safety_query(user_message, user_location)
        elif intent == "speed":
            response = handle_speed_query(user_message)
        else:
            response = handle_general_query(user_message, user_location)
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": str(e), "response": "Sorry, I encountered an error. Please try again."}), 500

@app.route('/api/location-info', methods=['POST'])
def location_info():
    """Get info about a specific location"""
    try:
        data = request.json
        location = data.get('location', '')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        locations_db = load_locations_db()
        
        # Find matching location
        location_info_data = None
        for loc_name, loc_data in locations_db.get("locations", {}).items():
            if location.lower() in loc_name.lower() or loc_name.lower() in location.lower():
                location_info_data = {
                    "location": loc_name,
                    **loc_data,
                    "weather": get_mock_weather(loc_name)
                }
                break
        
        if not location_info_data:
            location_info_data = {
                "location": location,
                "traffic": "UNKNOWN",
                "accidents_yearly": 0,
                "risk": "UNKNOWN",
                "description": "Location not in database",
                "weather": get_mock_weather(location)
            }
        
        # Add nearby black spots if coordinates provided
        if latitude and longitude:
            location_info_data["nearby_blackspots"] = get_nearby_blackspots(latitude, longitude)
        
        return jsonify(location_info_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/blackspots', methods=['POST'])
def blackspots():
    """Get black spots near user location"""
    try:
        data = request.json
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius = data.get('radius', 50)
        
        if not latitude or not longitude:
            return jsonify({"error": "Location coordinates required"}), 400
        
        nearby = get_nearby_blackspots(latitude, longitude, radius)
        
        return jsonify({
            "center": {"latitude": latitude, "longitude": longitude},
            "radius_km": radius,
            "count": len(nearby),
            "blackspots": nearby
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict-route-risk', methods=['POST'])
def predict_route_risk():
    """Predict risk level for a route"""
    try:
        data = request.json
        location = data.get('location', '')
        
        locations_db = load_locations_db()
        
        # Find location in database
        location_data = None
        for loc_name, loc_info in locations_db.get("locations", {}).items():
            if location.lower() in loc_name.lower() or loc_name.lower() in location.lower():
                location_data = loc_info
                location = loc_name
                break
        
        if not location_data:
            return jsonify({
                "location": location,
                "risk": "UNKNOWN",
                "confidence": 0,
                "message": "Location not found in database"
            })
        
        # Predict risk using model
        accident_count = location_data.get("accidents_yearly", 0)
        result = predictor.predict_risk(
            location=location,
            accident_count=accident_count,
            regions_affected=1,
            risk_factors=3,
            black_spots_count=1
        )
        
        return jsonify({
            "location": location,
            "risk": result.get("risk_level", "UNKNOWN"),
            "confidence": result.get("confidence", 0),
            "probability": result.get("probability", 0),
            "recommendation": result.get("recommendation", "Drive safely"),
            "accidents_yearly": accident_count
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommendations', methods=['POST'])
def recommendations():
    """Get safety recommendations"""
    try:
        data = request.json
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        destination = data.get('destination')
        
        safety_recs = get_safety_recommendations(latitude, longitude, destination)
        
        return jsonify({
            "recommendations": safety_recs,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# QUERY HANDLERS
# ============================================================================

def handle_weather_query(query, location_data):
    """Handle weather-related queries"""
    weather = get_mock_weather("Kenya")
    
    response = f"🌤️ Weather Update:\n"
    response += f"Temperature: {weather['temp']}°C\n"
    response += f"Condition: {weather['condition']}\n"
    response += f"Visibility: {weather['visibility']}\n"
    
    if weather['rain']:
        response += "⚠️ Rain detected - Reduce speed and increase following distance"
    else:
        response += "✅ No rain - Good driving conditions"
    
    return {
        "response": response,
        "intent": "weather",
        "data": weather
    }

def handle_blackspots_query(query, location_data):
    """Handle black spots queries"""
    if not location_data or 'latitude' not in location_data or 'longitude' not in location_data:
        return {
            "response": "I need your location to find nearby black spots. Please enable location sharing.",
            "intent": "blackspots"
        }
    
    nearby = get_nearby_blackspots(location_data['latitude'], location_data['longitude'])
    
    if not nearby:
        response = "✅ Good news! No high-risk black spots found nearby."
    else:
        response = f"⚠️ Found {len(nearby)} black spots near you:\n\n"
        for i, spot in enumerate(nearby[:3], 1):
            response += f"{i}. {spot['location']} ({spot['distance_km']}km away)\n"
            response += f"   Risk: {spot['risk']} | Accidents/year: {spot['accidents']}\n"
    
    return {
        "response": response,
        "intent": "blackspots",
        "data": nearby[:3]
    }

def handle_route_query(query, location_data):
    """Handle route information queries"""
    # Extract destination from query
    destinations = ["mombasa", "nakuru", "kisumu", "eldoret", "thika", "nairobi"]
    destination = None
    
    for dest in destinations:
        if dest in query.lower():
            destination = dest.title()
            break
    
    if not destination:
        return {
            "response": "Where are you heading? Please mention your destination.",
            "intent": "route_info"
        }
    
    response = f"📍 Route to {destination}:\n"
    response += "⏱️ Estimated time: Depends on current traffic\n"
    response += "🚗 Road condition: Use location-based info\n"
    response += "⚠️ Check nearby black spots for your safety\n"
    response += "✅ Drive safely and maintain speed limits"
    
    return {
        "response": response,
        "intent": "route_info",
        "destination": destination
    }

def handle_safety_query(query, location_data):
    """Handle safety recommendation queries"""
    recommendations = get_safety_recommendations(
        location_data.get('latitude') if location_data else None,
        location_data.get('longitude') if location_data else None
    )
    
    response = "🛡️ Safety Recommendations:\n"
    for i, rec in enumerate(recommendations, 1):
        response += f"{i}. {rec}\n"
    
    return {
        "response": response,
        "intent": "safety",
        "recommendations": recommendations
    }

def handle_speed_query(query):
    """Handle speed limit queries"""
    response = "🚗 Speed Limits in Kenya:\n"
    response += "• Urban areas (towns): 50 km/h\n"
    response += "• Open roads: 80 km/h\n"
    response += "• Highways: 100 km/h\n"
    response += "• Motorways: 120 km/h\n"
    response += "\n⚠️ Adjust for weather, traffic, and road conditions"
    
    return {
        "response": response,
        "intent": "speed"
    }

def handle_general_query(query, location_data):
    """Handle general queries"""
    response = "👋 Hello! I'm your road safety assistant. I can help with:\n"
    response += "• 🌤️ Weather conditions\n"
    response += "• ⚠️ Black spots and dangerous areas\n"
    response += "• 🛡️ Safety recommendations\n"
    response += "• 📍 Route information\n"
    response += "• 🚗 Speed limit information\n"
    response += "\nWhat would you like to know?"
    
    return {
        "response": response,
        "intent": "general"
    }

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """API health check"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    })

@app.route('/', methods=['GET'])
def index():
    """API info"""
    return jsonify({
        "name": "Kenya Road Safety Chatbot API",
        "version": "1.0",
        "endpoints": {
            "/api/chat": "POST - Main chatbot endpoint",
            "/api/location-info": "POST - Get location information",
            "/api/blackspots": "POST - Get nearby black spots",
            "/api/predict-route-risk": "POST - Predict route risk",
            "/api/recommendations": "POST - Get safety recommendations",
            "/api/health": "GET - Health check"
        }
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  🚗 Kenya Road Safety Chatbot API                             ║
    ║  Starting on http://localhost:5000                             ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)
