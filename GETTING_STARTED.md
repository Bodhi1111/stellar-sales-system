# 🚀 Getting Started: Transform Your Stellar Sales System

**Welcome!** You're about to transform your sales transcript processor into a DemoDesk-style platform. This guide will get you started in the next 30 minutes.

---

## 📦 What You're Building

**Current**: Upload transcript file → Process → View results in Baserow  
**Target**: Live meeting → Real-time AI suggestions → Automatic CRM update → Analytics dashboard

---

## ⚡ Quick Start (30 Minutes)

### Step 1: Read the Guides (10 minutes)

You have 3 documents to guide you:

1. **`/workspace/docs/DEMODESK_TRANSFORMATION_GUIDE.md`** (MAIN GUIDE)
   - 📖 150+ pages of detailed implementation
   - 🏗️ Architecture design
   - 📝 Code examples for every feature
   - 🎓 Learning resources

2. **`/workspace/DEMODESK_QUICKSTART.md`** (THIS ONE!)
   - ⚡ Fast-track guide
   - 🎯 3 quick wins to build momentum
   - 📅 12-week sprint plan
   - ✅ Daily checklists

3. **`/workspace/README.md`** (EXISTING)
   - 📚 Current system documentation
   - 🏛️ Your existing architecture
   - 🧪 How to run tests

**Action**: Skim the quick-start, then deep-dive the main guide.

---

### Step 2: Run Database Migration (5 minutes)

This adds user accounts, organizations, and team features to your database.

```bash
cd /workspace

# Make sure PostgreSQL is running
docker ps | grep postgres

# Run migration
python scripts/migrate_to_demodesk_architecture.py
```

**Expected Output**:
```
🚀 STELLAR SALES SYSTEM → DEMODESK MIGRATION
====================================
📄 Executing SQL file: add_user_tables.sql
✅ Successfully executed add_user_tables.sql

🔍 Verifying tables...
📊 Existing tables:
   ✅ organizations
   ✅ users
   ✅ meeting_sessions
   ✅ suggestions
   ✅ team_metrics
   ✅ audit_logs
   ✅ invitations
   📋 transcripts

✅ All 7 new tables created successfully!

👤 Checking demo user...
✅ Demo user exists:
   Email: admin@demo.com
   Password: password123 (CHANGE THIS!)

🎉 MIGRATION COMPLETE!
```

**If it fails**:
- Check PostgreSQL: `docker-compose up -d postgres`
- Check `.env` file has correct credentials
- Try manual: `psql -U postgres -d stellar_sales -f sql/add_user_tables.sql`

---

### Step 3: Test Your API (5 minutes)

```bash
# Start FastAPI server
cd /workspace
source venv/bin/activate
uvicorn api.app:app --reload

# In another terminal, test the endpoint
curl http://localhost:8000/

# Expected: {"status": "ok", "message": "Welcome to the Stellar Sales System API!"}
```

---

### Step 4: Set Up Frontend (10 minutes)

```bash
# Create frontend directory
cd /workspace
mkdir -p frontend
cd frontend

# Initialize Next.js
npx create-next-app@latest . --typescript --tailwind --app --use-npm

# Answer prompts:
# ✔ Would you like to use TypeScript? Yes
# ✔ Would you like to use ESLint? Yes
# ✔ Would you like to use Tailwind CSS? Yes
# ✔ Would you like to use `src/` directory? No
# ✔ Would you like to use App Router? Yes
# ✔ Would you like to customize the default import alias? No

# Install dependencies
npm install axios @tanstack/react-query zustand date-fns

# Start dev server
npm run dev

# Open browser to http://localhost:3000
```

**Expected**: You see the Next.js welcome page.

---

## 🎯 Your First 3 Wins (This Week!)

### Win #1: WebSocket Echo Server (Tuesday, 2 hours)

Create a simple WebSocket server to understand real-time communication.

**File**: `/workspace/test_websocket.py`

```python
from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ Client connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        print(f"❌ Connection closed: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Test It**:

```bash
# Terminal 1: Start server
python test_websocket.py

# Terminal 2: Connect with websocat (install: brew install websocat)
websocat ws://localhost:8001/ws

# Type messages and see them echoed back!
```

**Success Metric**: ✅ Messages are echoed back instantly

---

### Win #2: Display Transcripts in React (Thursday, 3 hours)

Build your first React page that fetches data from your API.

**File**: `/workspace/frontend/app/transcripts/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';

export default function TranscriptsPage() {
  const [transcripts, setTranscripts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/transcripts')
      .then(res => res.json())
      .then(data => {
        setTranscripts(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching transcripts:', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-8 text-center">Loading transcripts...</div>;
  }

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-4xl font-bold mb-6">Sales Transcripts</h1>
      
      <div className="grid gap-4">
        {transcripts.map((transcript: any) => (
          <div
            key={transcript.id}
            className="border rounded-lg p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-2xl font-semibold mb-2">
                  {transcript.crm_data?.client_name || 'Unknown Client'}
                </h3>
                <p className="text-gray-600">{transcript.filename}</p>
              </div>
              
              <span className={`px-4 py-2 rounded-full text-sm font-medium ${
                transcript.crm_data?.outcome === 'Won' 
                  ? 'bg-green-100 text-green-800'
                  : transcript.crm_data?.outcome === 'Lost'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {transcript.crm_data?.outcome || 'Pending'}
              </span>
            </div>
            
            <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Deal Amount:</span>
                <span className="ml-2 font-bold text-green-600">
                  ${transcript.crm_data?.deal?.toLocaleString() || 0}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Meeting Date:</span>
                <span className="ml-2">
                  {transcript.crm_data?.meeting_date || 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Duration:</span>
                <span className="ml-2">
                  {transcript.crm_data?.duration_minutes || 0} min
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Add API Endpoint**: `/workspace/api/app.py`

```python
from core.database.postgres import PostgresManager
from core.database.models import Transcript

postgres_manager = PostgresManager(settings)

@app.get("/api/transcripts")
async def list_transcripts():
    """
    Get list of all transcripts with CRM data.
    """
    session = postgres_manager.get_session()
    try:
        transcripts = session.query(Transcript).order_by(
            Transcript.created_at.desc()
        ).limit(50).all()
        
        return [{
            "id": t.id,
            "external_id": t.external_id,
            "filename": t.filename,
            "crm_data": t.crm_data,
            "created_at": t.created_at.isoformat(),
        } for t in transcripts]
    finally:
        session.close()
```

**Test It**:

```bash
# Terminal 1: Start FastAPI
cd /workspace
uvicorn api.app:app --reload

# Terminal 2: Start Next.js
cd /workspace/frontend
npm run dev

# Open browser to http://localhost:3000/transcripts
```

**Success Metric**: ✅ You see a list of your transcripts in a beautiful UI

---

### Win #3: Zoom OAuth (Saturday, 2 hours)

Connect your Zoom account to auto-download recordings.

**Steps**:

1. **Register Zoom App**:
   - Go to https://marketplace.zoom.us/develop/create
   - Choose "OAuth" app type
   - Set redirect URL: `http://localhost:8000/auth/zoom/callback`
   - Add scopes: `recording:read`, `meeting:read`
   - Save **Client ID** and **Client Secret**

2. **Add to `.env`**:
```env
ZOOM_CLIENT_ID=your_client_id_here
ZOOM_CLIENT_SECRET=your_client_secret_here
```

3. **Add OAuth Endpoint**: `/workspace/api/auth.py` (NEW FILE)

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import httpx
from config.settings import settings

router = APIRouter(prefix="/auth/zoom", tags=["auth"])

@router.get("/login")
async def zoom_oauth_login():
    """Redirect to Zoom OAuth page."""
    auth_url = (
        f"https://zoom.us/oauth/authorize"
        f"?response_type=code"
        f"&client_id={settings.ZOOM_CLIENT_ID}"
        f"&redirect_uri=http://localhost:8000/auth/zoom/callback"
    )
    return RedirectResponse(auth_url)

@router.get("/callback")
async def zoom_oauth_callback(code: str):
    """Exchange code for access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://zoom.us/oauth/token",
            auth=(settings.ZOOM_CLIENT_ID, settings.ZOOM_CLIENT_SECRET),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "http://localhost:8000/auth/zoom/callback"
            }
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get token")
    
    token_data = response.json()
    return {"message": "Zoom connected!", "access_token": token_data["access_token"]}
```

4. **Include Router in Main App**: `/workspace/api/app.py`

```python
from api.auth import router as auth_router

app.include_router(auth_router)
```

5. **Test It**:
```bash
# Start server
uvicorn api.app:app --reload

# Visit in browser
http://localhost:8000/auth/zoom/login

# You'll be redirected to Zoom, authorize, then redirected back
```

**Success Metric**: ✅ You see `{"message": "Zoom connected!", "access_token": "..."}`

---

## 📅 Next Week's Plan

### Monday (3 hours)
- [ ] Read main guide (`DEMODESK_TRANSFORMATION_GUIDE.md`)
- [ ] Plan your 12-week roadmap
- [ ] Set up project management (Trello, Notion, etc.)

### Tuesday (3 hours)
- [ ] Complete Win #1 (WebSocket echo server)
- [ ] Watch FastAPI WebSocket tutorial

### Wednesday (3 hours)
- [ ] Add WebSocket to main app
- [ ] Test with real transcript streaming

### Thursday (3 hours)
- [ ] Complete Win #2 (React transcript list)
- [ ] Style with Tailwind CSS

### Friday (3 hours)
- [ ] Write tests for new endpoints
- [ ] Deploy to local Docker

### Saturday (2 hours)
- [ ] Complete Win #3 (Zoom OAuth)
- [ ] Test with real Zoom meeting

### Sunday
- 🏖️ Rest! Review your progress, celebrate wins

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'X'"
```bash
# Activate your virtual environment
cd /workspace
source venv/bin/activate

# Install missing package
pip install X
```

### "Port 8000 already in use"
```bash
# Find process using port
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use a different port
uvicorn api.app:app --reload --port 8001
```

### "Database connection failed"
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# If not, start it
docker-compose up -d postgres

# Test connection
psql -U postgres -d stellar_sales -c "SELECT 1;"
```

### "Next.js page not found"
```bash
# Make sure you're in the right directory
cd /workspace/frontend

# Check file structure
ls -la app/transcripts/

# Restart dev server
npm run dev
```

### "CORS error in browser console"
Add to `/workspace/api/app.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📚 Essential Reading

**Before You Code**:
1. ✅ This file (you're here!)
2. ✅ `/workspace/DEMODESK_QUICKSTART.md` (quick reference)
3. ✅ `/workspace/docs/DEMODESK_TRANSFORMATION_GUIDE.md` (deep dive)

**As You Code**:
1. 📖 [FastAPI Docs](https://fastapi.tiangolo.com/)
2. 📖 [Next.js Docs](https://nextjs.org/docs)
3. 📖 [React Query Docs](https://tanstack.com/query/latest)

**When Stuck**:
1. 🔍 Google the exact error message
2. 💬 Ask in Discord/Reddit (links in main guide)
3. 🤖 Ask Claude/ChatGPT with code examples

---

## ✅ Success Checklist (End of Week 1)

- [ ] Database migration completed (7 new tables)
- [ ] Demo user can log in
- [ ] WebSocket echo server working
- [ ] React dashboard displays transcripts
- [ ] Zoom OAuth flow completed
- [ ] All services running (FastAPI, Next.js, PostgreSQL)
- [ ] No errors in console

**If all checked**: 🎉 You're ready for Week 2!

---

## 🚀 What's Next?

### Week 2-4: Real-Time Streaming
- Build streaming parser agent
- Add WebSocket to ingestion pipeline
- Test with live transcript data

### Week 5-8: UI Polish
- Add login/signup pages
- Build transcript detail page
- Implement JWT authentication

### Week 9-12: Live Assistant
- Zoom Bot SDK integration
- Real-time suggestion engine
- In-meeting overlay UI

**Full plan**: See `/workspace/docs/DEMODESK_TRANSFORMATION_GUIDE.md`

---

## 💬 Need Help?

1. **Check the guides**: 90% of questions are answered there
2. **Search existing code**: Your codebase has great examples
3. **Ask AI**: Claude/ChatGPT for specific code questions
4. **Community**: Discord servers (links in main guide)

---

## 🎓 Final Advice

**Start Small**: Don't try to build everything at once. Complete the 3 quick wins first.

**Test Often**: Run your code after every change. Catch bugs early.

**Document**: Write comments as you code. Future you will thank you.

**Have Fun**: You're building something awesome! Enjoy the journey. 🚀

---

**Ready?** Start with the database migration above, then tackle Win #1! 🎯

**Questions?** Read the full guide: `/workspace/docs/DEMODESK_TRANSFORMATION_GUIDE.md`

**Good luck!** 🚀

---

**Created**: October 23, 2025  
**Version**: 1.0  
**For**: Stellar Growth & Automation
