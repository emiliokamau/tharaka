"""
Setup guide for getting a new Gemini API key
Your old key was exposed and is now disabled
"""

def instructions():
    print("""
    ⚠️  URGENT: YOUR API KEY WAS LEAKED AND IS NOW DISABLED ⚠️
    
    Your old API key (AIzaSyA52...) is no longer valid.
    Google detected it was exposed and disabled it for security.
    
    ✅ FIX: GET A NEW API KEY
    
    Step 1: Go to https://aistudio.google.com/apikey
    
    Step 2: Click "Create API key" (or "+ Create API key")
    
    Step 3: Select "Create API key in new Google Cloud project"
    
    Step 4: Copy your NEW key (it will look like: AIza...)
    
    Step 5: Edit your .env file:
    
        Open: .env
        Find: GEMINI_API_KEY=
        Replace with: GEMINI_API_KEY=your_new_key_here
        
    Step 6: Save the file
    
    Step 7: Test it:
        python check_setup.py
    
    ✅ After creating the new key, DO THIS:
    
    1. NEVER share your API key publicly
    2. NEVER commit .env to GitHub
    3. NEVER paste it in chat/forums
    4. Keep it only in .env file (which is in .gitignore)
    
    ✅ SECURITY CHECKLIST:
    
    ☑️ Old key is disabled (already done by Google)
    ☑️ New key is created
    ☑️ New key is in .env file
    ☑️ .env is in .gitignore (already done)
    ☑️ Never share the new key
    ☑️ Don't commit .env to version control
    
    Once you have the new key:
    
    1. Update .env with the new key
    2. Run: python check_setup.py
    3. Run: python pdf_extractor.py
    """)

if __name__ == "__main__":
    instructions()
