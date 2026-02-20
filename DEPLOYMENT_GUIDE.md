# Kenya Road Safety Platform - Deployment Guide

## Quick Start Command for Render

**Start Command:**
```bash
gunicorn app:app --workers 4 --timeout 120
```

This command is already saved in the `Procfile` - Render will use it automatically.

---

## Database Migration: SQLite to PostgreSQL

### Why PostgreSQL?
- SQLite doesn't work on Render's ephemeral filesystem
- PostgreSQL is free with Render's free tier
- Better concurrent access handling

### Migration Steps

#### Step 1: Export SQLite Data
```bash
# Install sqlite3 if needed, then export your data
sqlite3 instance/drivers.db ".dump" > dump.sql
```

#### Step 2: Create PostgreSQL on Render
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Create New → PostgreSQL
3. Note the `Internal Database URL`

#### Step 3: Import Data to PostgreSQL
```bash
# Connect to Render's PostgreSQL
psql $DATABASE_URL -f dump.sql
```

#### Step 4: Environment Variables (Render Dashboard)
Add these in your Web Service settings:
- `DATABASE_URL` = (PostgreSQL connection string from Step 2)
- `SECRET_KEY` = (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
- `JWT_SECRET_KEY` = (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
- `GEMINI_API_KEY` = (your API key from Google AI Studio)

---

## Deploy to Render

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for production deployment"
   git push origin main
   ```

2. **Create Render Web Service**
   - Go to Render Dashboard → New → Web Service
   - Connect your GitHub repository
   - Settings:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn app:app --workers 4 --timeout 120`
   - Add Environment Variables (see above)

3. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

---

## Deploy Frontend to Vercel (Optional)

Since your Flask app serves HTML templates directly, you have two options:

### Option A: Keep All on Render (Recommended for simplicity)
- Your Flask app already serves templates
- No Vercel needed
- Just point your domain to Render

### Option B: Vercel for Static Assets
If you want faster frontend:
1. Create `vercel.json` in root:
   ```json
   {
     "rewrites": [
       { "source": "/(.*)", "destination": "https://your-render-app.onrender.com/$1" }
     ]
   }
   ```
2. Deploy to Vercel
3. Vercel acts as CDN, forwards API calls to Render

---

## Files Modified for Deployment

| File | Change |
|------|--------|
| `requirements.txt` | Added Flask, SQLAlchemy, Gunicorn, psycopg2 |
| `Procfile` | Added Gunicorn start command |
| `app.py` | Added environment variable support for DATABASE_URL |
| `.env.example` | Added production environment variables |

---

## Troubleshooting

### Database Connection Error
- Ensure `DATABASE_URL` is set in Render dashboard
- Format: `postgresql://user:pass@host:5432/dbname`

### Import Error
- Make sure all packages installed: `pip install -r requirements.txt`

### Static Files Not Loading
- Flask looks for templates in `/templates` folder
- Ensure folder structure is preserved
