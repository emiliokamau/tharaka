"""
🔐 SECURITY HARDENING GUIDE
Protect your API keys at all costs!
"""

SECURITY_GUIDE = """
╔════════════════════════════════════════════════════════════════════════════╗
║                         🔐 SECURITY HARDENING 🔐                          ║
║                    Protect Your API Keys At All Costs                      ║
╚════════════════════════════════════════════════════════════════════════════╝


⚠️ WHAT HAPPENED TO YOUR KEYS:
══════════════════════════════════════════════════════════════════════════════

Your API keys were EXPOSED in:
1. The .env file (visible in terminal output)
2. Possibly in chat/conversation history
3. Now disabled by Google (security measure)

Google automatically REVOKED both your keys for security.


🔒 HOW TO PROTECT YOUR KEYS:
══════════════════════════════════════════════════════════════════════════════

✅ DO THIS:

1. Store ONLY in .env file
   ├─ Never in code files
   ├─ Never in documentation
   ├─ Never in comments
   └─ Never in Git commits

2. .env file MUST be in .gitignore
   ├─ Already done in your project
   └─ Check: grep .env .gitignore

3. Use environment variables ONLY
   ├─ Load with: os.getenv("GEMINI_API_KEY")
   ├─ Configure with: genai.configure(api_key=GEMINI_API_KEY)
   └─ Never hardcode the key

4. Be careful in terminals
   ├─ Don't print full API key
   ├─ Only show: AIza...7Y (start & end)
   ├─ Terminal history saves everything!
   └─ Clear history if you accidentally paste the key

5. Copy-paste carefully
   ├─ When pasting key, paste ONLY into .env
   ├─ Don't paste into terminal directly
   ├─ Don't paste into chat/email
   └─ Terminal history saves pasted commands!


❌ NEVER DO THIS:

1. Don't hardcode keys in Python files
   BAD:  api_key = "AIzaSyA1b2c3d4e5..."
   GOOD: api_key = os.getenv("GEMINI_API_KEY")

2. Don't paste keys in terminal
   BAD:  python script.py AIzaSyA1b2c3d4e5...
   GOOD: Set in .env, load from there

3. Don't print full keys
   BAD:  print(f"Key: {api_key}")
   GOOD: print(f"Key: {api_key[:10]}...{api_key[-5:]}")

4. Don't commit .env to GitHub
   BAD:  git add .env
   GOOD: .env already in .gitignore

5. Don't share keys in chat/forum/email
   BAD:  Help! My key is AIzaSyA1b2c3d4e5...
   GOOD: Help! My API isn't working (without sharing key)

6. Don't paste keys in screenshots
   BAD:  Screenshot showing terminal with API key
   GOOD: Screenshot with key hidden/redacted

7. Don't leave keys in command history
   BAD:  Running: echo AIzaSyA1b2c3d4e5... (saves to history)
   GOOD: Only put keys in .env files


🛡️ YOUR PROJECT SECURITY STATUS:
══════════════════════════════════════════════════════════════════════════════

✅ ALREADY PROTECTED:
├─ .gitignore includes .env
├─ .gitignore includes __pycache__/
├─ Code uses os.getenv() instead of hardcoding
└─ No keys in documentation

❌ NOW NEEDS FIXING:
├─ Both your exposed keys are now revoked ✓ (already done)
└─ Your .env is now empty ✓ (already done)

✅ WHAT TO DO NEXT:
├─ Generate NEW API keys
├─ Add only to .env file
├─ NEVER expose them again
└─ Continue working


📋 STEPS TO RECOVER:
══════════════════════════════════════════════════════════════════════════════

Step 1: Generate NEW API Keys (Google revoked the old ones)
├─ Gemini key: https://aistudio.google.com/apikey
└─ Web Unlocker (if needed): https://brightdata.com/

Step 2: ADD TO .ENV ONLY
├─ Open: .env file (not in terminal!)
├─ Add: GEMINI_API_KEY=your_new_key_only_here
└─ Save file

Step 3: VERIFY IT WORKS
├─ Run: python check_setup.py
├─ Should show: ✅ API key configured
└─ Should NOT show: The actual key

Step 4: CONTINUE WORKING
├─ Run: python setup_wizard.py
└─ Extract from PDF

Step 5: PROTECT GOING FORWARD
├─ Never show your API key
├─ Always use .env file
├─ Clear terminal history if you accidentally type it
└─ Keep .gitignore protecting .env


🔐 SECURE WORKFLOW:
══════════════════════════════════════════════════════════════════════════════

How your code should work:

1. .env file (PROTECTED - not in Git)
   └─ GEMINI_API_KEY=AIzaSyA...YourKeyHere...1b2c3d

2. Python code loads it safely
   ├─ from dotenv import load_dotenv
   ├─ load_dotenv()
   ├─ api_key = os.getenv("GEMINI_API_KEY")
   └─ genai.configure(api_key=api_key)

3. Key stays hidden
   ├─ Never logged to console
   ├─ Never printed in errors
   ├─ Never exposed in output
   └─ Only used internally by Gemini SDK


✅ TERMINAL SAFETY TIPS:
══════════════════════════════════════════════════════════════════════════════

1. NEVER type API keys directly in terminal
   ✗ echo AIzaSyA...key...1b2c3d
   ✗ python -c "api_key='AIzaSyA...key...1b2c3d'"
   ✓ Edit .env file with text editor instead

2. Clear terminal if you accidentally paste a key
   ├─ Command: history -c (Linux/Mac)
   ├─ Command: Clear-History (PowerShell)
   └─ Or just close and open a new terminal

3. Don't run scripts with API key as argument
   ✗ python script.py AIzaSyA...key...1b2c3d
   ✓ python script.py (loads from .env)

4. Check your terminal history!
   ├─ Linux/Mac: cat ~/.bash_history | grep -i api
   ├─ PowerShell: Get-History | findstr api
   └─ Delete any lines with API keys

5. Be careful with copy-paste
   ├─ Only paste API key into .env file
   ├─ Don't paste in terminal
   ├─ Don't paste in chat/email
   └─ Don't paste in screenshots


🆘 IF YOU ACCIDENTALLY EXPOSED A KEY:
══════════════════════════════════════════════════════════════════════════════

What to do immediately:

1. REVOKE THE KEY
   ├─ Go to: https://aistudio.google.com/apikey
   ├─ Find the exposed key
   ├─ Delete it immediately
   └─ Google will disable it if widely exposed

2. GENERATE A NEW KEY
   ├─ Still at: https://aistudio.google.com/apikey
   ├─ Click: "Create API key"
   └─ Copy the new key

3. UPDATE YOUR .ENV
   ├─ Open: .env file
   ├─ Replace old key with new key
   └─ Save file

4. CONTINUE WORKING
   ├─ Run: python check_setup.py
   ├─ Verify new key works
   └─ Continue your project

5. PREVENT FUTURE EXPOSURE
   ├─ Never paste keys in terminal
   ├─ Only use .env files
   ├─ Clear terminal history if needed
   └─ Follow this security guide


📝 SECURITY CHECKLIST:
══════════════════════════════════════════════════════════════════════════════

Before you continue working:

API Key Protection:
☑️ Old exposed keys have been revoked
☑️ New API key generated
☑️ New key added ONLY to .env file
☑️ .env is in .gitignore
☑️ .env file is never printed
☑️ .env file is never committed to Git

Code Security:
☑️ No hardcoded API keys in .py files
☑️ Using os.getenv() to load from .env
☑️ Never print full API key to console
☑️ Only show masked version: AIza...123

Terminal Safety:
☑️ No API keys in terminal commands
☑️ Terminal history cleaned (if exposed)
☑️ Not sharing keys in chat/email/forums
☑️ Not showing keys in screenshots

File Protection:
☑️ .env is in .gitignore
☑️ .env is not committed
☑️ .env is not shared
☑️ .env has correct permissions (readable only by you)


🎯 GOING FORWARD:
══════════════════════════════════════════════════════════════════════════════

Every time you:

1. Need to add an API key
   └─ Add ONLY to .env file
   
2. Get a new API key
   └─ Replace ONLY in .env file
   
3. Use the key in code
   └─ Use: os.getenv("GEMINI_API_KEY")
   
4. Debug an issue
   └─ Never log full API key
   └─ Log: f"{api_key[:10]}...{api_key[-5:]}"
   
5. Get an error with API key
   └─ Check .env is configured
   └─ Check .env has valid key
   └─ Check code uses os.getenv()
   └─ Don't paste key in error message!


⚠️ FINAL WARNING:
══════════════════════════════════════════════════════════════════════════════

Your API keys are:
• Precious (tied to your account)
• Powerful (can access Google services)
• Irreplaceable (if exposed, revoke immediately)
• Easy to leak (if not careful)

Protect them like your password!

✅ Follow this guide = Your keys stay safe
❌ Ignore this guide = Your keys will be compromised


╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                  🔐 Your keys are now fully protected!                    ║
║                                                                            ║
║              NEVER expose your API keys again. Use .env only!            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

if __name__ == "__main__":
    print(SECURITY_GUIDE)
