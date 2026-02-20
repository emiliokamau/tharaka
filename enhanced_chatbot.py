"""
Enhanced Chatbot Function - Copy this into app.py
This function should replace the chatbot_chat function in app.py
"""

def enhanced_chatbot_response(driver_id):
    """Get the chatbot response logic - call this from the route"""
    from flask import request, jsonify
    from database import Driver
    import random
    
    data = request.get_json()
    user_message = data.get('message', '').lower()
    
    driver = Driver.query.get(driver_id)
    
    # Get driver's current stats
    fatigue = driver.fatigue_level or 0
    total_hours = driver.total_driving_hours or 0
    
    # Priority 1: DROWSINESS - most important for safety
    if any(x in user_message for x in ['drowsy', 'sleepy', 'tired', 'fatigue level', 'how tired', 'how fatigued', 'feeling tired', 'falling asleep']):
        if fatigue >= 80:
            bot_response = f"""CRITICAL ALERT! Your fatigue level is {fatigue}% - EXTREMELY DANGEROUS!

IMMEDIATE ACTION REQUIRED:
1. Pull over to a safe location RIGHT NOW
2. Turn off your engine
3. Take a 15-20 minute nap
4. Get out and stretch
5. If possible, switch drivers

Your safety is more important than your destination!"""
        elif fatigue >= 60:
            bot_response = f"""WARNING! Your fatigue level is {fatigue}% - HIGH RISK!

TAKE ACTION NOW:
1. Find a safe place to pull over within 15 mins
2. Take a 15-20 minute power nap
3. Get fresh air - step out of the car
4. Drink coffee (caffeine takes 30 mins to work)
5. Consider ending your trip

Fatigue is as dangerous as drunk driving!"""
        elif fatigue >= 40:
            bot_response = f"""CAUTION: Your fatigue level is {fatigue}% - Stay alert!

STAY ALERT:
1. Keep windows open for fresh air
2. Sing or talk to stay awake
3. Take a break within the hour
4. Stay hydrated - drink water
5. Avoid heavy meals

You're okay to continue but plan a break soon."""
        else:
            bot_response = f"""GOOD NEWS! Your fatigue level is only {fatigue}% - You're alert!

KEEP IT UP!
1. Continue driving safely
2. Stay aware of your alertness
3. Take regular breaks
4. Monitor your fatigue level

You're doing great!"""
    
    # Priority 2: BLACK SPOTS
    elif any(x in user_message for x in ['black spot', 'dangerous', 'accident area', 'high risk', 'accident black']):
        bot_response = """BLACK SPOT WARNINGS - Kenya's Most Dangerous Roads:

HIGH RISK AREAS:
1. Nairobi-Mombasa Road - 156+ accidents
   - Often congested, watch pedestrians
2. Mombasa Road Junction - 145+ accidents
   - Very high traffic volume
3. Thika Road - 101+ accidents
   - Speed-related crashes common
4. Nairobi Outer Ring - 89+ accidents

MEDIUM RISK:
- Eldoret-Nakuru Road
- Nakuru-Nairobi highway

SAFETY SOLUTIONS:
1. Reduce speed in these areas
2. Increase following distance
3. Use headlights even daytime
4. Stay focused - no distractions
5. Watch for sudden stops"""
    
    # Priority 3: ROUTE RISK
    elif any(x in user_message for x in ['route', 'assess', 'risk level', 'my route', 'trip', 'journey', 'destination']):
        bot_response = """ROUTE RISK ASSESSMENT

To assess your route risk, I need:
1. Your start location
2. Your destination

I can check:
- Black spots along your route
- Current weather conditions
- Road construction areas
- Traffic patterns

SAFETY SOLUTIONS:
1. Plan your route in advance
2. Check weather before departure
3. Identify rest stops along way
4. Have an alternative route ready
5. Share trip with someone

Just tell me your start and end locations!"""
    
    # Priority 4: SAFETY TIPS
    elif any(x in user_message for x in ['safety tip', 'advice', 'how to stay', 'safe driving', 'tip', 'tips', 'recommend']):
        import random
        tips = [
            """BEFORE DRIVING:
1. Get 7-8 hours sleep
2. Check vehicle (tires, brakes)
3. Plan your route
4. Tell someone your destination
5. Don't drink and drive""",
            """DURING DRIVE:
1. Take breaks every 2 hours
2. Never drive 8+ hours straight
3. Stay hydrated
4. Keep windows slightly open
5. Avoid midnight-6am driving""",
            """EMERGENCY SIGNS:
1. Frequent yawning = tired
2. Heavy eyelids = stop NOW
3. Missing exits = fatigue
4. Drifting = pull over!
5. Head nodding = sleep soon!""",
            """PREVENTION:
1. Seatbelt ALWAYS on
2. Speed limits matter
3. No phone usage
4. Watch mirrors often
5. Fresh air helps"""
        ]
        bot_response = f"SAFETY TIPS:\n{random.choice(tips)}"
    
    # Priority 5: WEATHER
    elif any(x in user_message for x in ['weather', 'rain', 'fog', 'condition', 'hot', 'cold']):
        bot_response = """WEATHER ROAD CONDITIONS

DRIVING IN RAIN:
1. Reduce speed by 30%
2. Double following distance
3. Use headlights on low beam
4. Avoid sudden braking
5. Watch for flooding

FOGGY CONDITIONS:
1. Use low beam lights
2. Reduce speed significantly
3. Stay in your lane
4. Use road markings as guide
5. Stop if too dense

HEAT ADVISORY:
1. Stay hydrated
2. Take sun protection
3. Watch for heat exhaustion
4. Never leave children in car"""
    
    # Priority 6: GREETINGS
    elif any(x in user_message for x in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'greetings']):
        bot_response = f"""Hello {driver.full_name}! Welcome to your Road Safety Assistant!

I can help you with:
1. Your fatigue level - ask 'how tired am I'
2. Black spots - ask 'dangerous areas'
3. Route risk - ask 'assess my route'
4. Safety tips - ask 'safety advice'
5. Weather - ask 'weather conditions'

Your current fatigue level: {fatigue}%

Click Quick Actions for instant help!"""
    
    # Priority 7: THANK YOU
    elif 'thank' in user_message:
        bot_response = """You're welcome! Stay safe on the roads!

Remember:
- Fatigue kills - don't push through
- Take regular breaks
- Your family wants you home safe

Anything else I can help with?"""
    
    # Priority 8: Default/Unknown
    else:
        bot_response = """I can help you with:

1. FATIGUE - 'How tired am I?'
2. BLACK SPOTS - 'dangerous areas'
3. ROUTE RISK - 'assess my route'
4. SAFETY TIPS - 'give me advice'
5. WEATHER - 'road conditions'

Or click the Quick Action buttons on the right!

What would you like to know?"""
    
    return jsonify({
        'success': True,
        'response': bot_response,
        'driver_name': driver.full_name,
        'fatigue_level': fatigue
    }), 200
