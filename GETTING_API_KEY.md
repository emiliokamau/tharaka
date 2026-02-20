# 🔑 Getting Your Gemini API Key - Step by Step

## Quick Guide

1. **Open Google AI Studio**
   - Go to: https://aistudio.google.com/apikey
   - Sign in with your Google account

2. **Create API Key**
   - Click "Get API key" button
   - Click "Create API key" 
   - You can create it in a new project or use an existing one

3. **Copy Your Key**
   - Copy the API key that appears (it looks like: `AIzaSyA...`)
   - **Important**: Store it safely - you won't be able to see it again!

4. **Add to Your Project**
   - Open the `.env` file in this project
   - Replace the line:
     ```
     GEMINI_API_KEY=
     ```
   - With:
     ```
     GEMINI_API_KEY=AIzaSyA...your-actual-key...
     ```

5. **Test Your Setup**
   - Run: `python check_setup.py`
   - If successful, you'll see "✅ ALL CHECKS PASSED"

## Free Tier Information

✅ **Gemini 2.0 Flash Lite is FREE!**
- 1,500 requests per day
- 1 million tokens per minute
- 10 million tokens per day

This is more than enough for scraping the 6-7 URLs in this project!

## Troubleshooting

### Error: "GEMINI_API_KEY not found"
- Make sure your `.env` file exists (not `.env.example`)
- Check that there are no extra spaces in the `.env` file
- Restart your terminal/IDE after adding the key

### Error: "Invalid API key"
- Verify you copied the entire key
- Make sure there are no line breaks in the key
- Try generating a new key

### Error: "Quota exceeded"
- You've hit the free tier limit
- Wait 24 hours for the quota to reset
- Or upgrade to a paid plan (if needed for large-scale scraping)

## Security Best Practices

⚠️ **NEVER commit your API key to Git!**
- The `.env` file is already in `.gitignore`
- Don't share your API key publicly
- Don't hardcode it in your scripts

✅ **Do this**:
```python
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
```

❌ **Don't do this**:
```python
api_key = "AIzaSyA...my-actual-key"  # NEVER!
```

## Next Steps

Once you have your API key configured:
1. Run `python check_setup.py` to verify everything works
2. Run `python scraper.py` to start scraping
3. Check `scraped_data/` for your results!

## Need Help?

- Gemini API Documentation: https://ai.google.dev/docs
- Google AI Studio: https://aistudio.google.com/
- Issues with this scraper: Check the README.md

---

**Ready to scrape? Let's make Kenyan roads safer! 🚗💨**
