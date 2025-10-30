# LangFuse Setup Guide - Stellar Sales System

> **Complete step-by-step instructions for setting up local LangFuse observability**

This guide will walk you through setting up LangFuse on your local machine so you can visualize and debug your pipeline executions.

---

## Table of Contents

1. [What is LangFuse?](#what-is-langfuse)
2. [Prerequisites](#prerequisites)
3. [Step 1: Start LangFuse Server](#step-1-start-langfuse-server)
4. [Step 2: Create Your Account](#step-2-create-your-account)
5. [Step 3: Generate API Keys](#step-3-generate-api-keys)
6. [Step 4: Configure Environment Variables](#step-4-configure-environment-variables)
7. [Step 5: Install Python Package](#step-5-install-python-package)
8. [Step 6: Verify Setup](#step-6-verify-setup)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

---

## What is LangFuse?

LangFuse is an **open-source observability platform** for AI applications. Think of it as a detailed activity monitor for your pipeline.

### What You'll Get:
- **Visual timeline** showing all agents executing in order
- **Performance metrics** (how long each agent takes)
- **Complete data flow** (what inputs/outputs each agent produces)
- **Error tracking** with full details when something goes wrong
- **Cost tracking** for LLM token usage

### Why LangFuse vs LangSmith?
- ✅ **Runs locally** - your data never leaves your machine
- ✅ **Free forever** - no usage limits or quotas
- ✅ **Self-hosted** - complete control and privacy
- ✅ **Easy setup** - just Docker and a few commands

---

## Prerequisites

Before starting, make sure you have:

- ✅ **Docker Desktop** installed and running
  - Download from: https://www.docker.com/products/docker-desktop
  - Verify: Run `docker --version` in terminal
  
- ✅ **Docker Compose** (included with Docker Desktop)
  - Verify: Run `docker-compose --version` in terminal

- ✅ **Stellar Sales System** cloned and set up
  - You should have a `.env` file (copy from `env.example` if not)

- ✅ **At least 2GB free disk space** for LangFuse containers

---

## Step 1: Start LangFuse Server

### 1.1 Open Terminal

Navigate to your project directory:

```bash
cd /path/to/stellar-sales-system
```

### 1.2 Start Docker Containers

Run this command to start LangFuse:

```bash
docker-compose -f docker-compose.langfuse.yml up -d
```

**What this does:**
- `-f docker-compose.langfuse.yml` - Uses the LangFuse configuration file
- `up` - Starts the containers
- `-d` - Runs in background (detached mode)

### 1.3 Verify Containers are Running

Check that both containers started successfully:

```bash
docker ps | grep langfuse
```

You should see 2 containers:
- `stellar_langfuse` (the LangFuse server)
- `stellar_langfuse_db` (PostgreSQL database for LangFuse)

**Example output:**
```
stellar_langfuse      langfuse/langfuse:2   Up 30 seconds   0.0.0.0:3000->3000/tcp
stellar_langfuse_db   postgres:15           Up 31 seconds   5432/tcp
```

### 1.4 Wait for Initialization

The first time you start LangFuse, it needs to:
- Initialize the database
- Create tables
- Set up authentication

**Wait 30-60 seconds** before proceeding to the next step.

### 1.5 Check Logs (Optional)

To see what LangFuse is doing:

```bash
docker logs stellar_langfuse --tail 20
```

You should see messages about database migrations and "Server started" near the end.

---

## Step 2: Create Your Account

### 2.1 Open LangFuse UI

Open your web browser and go to:

```
http://localhost:3000
```

**What you should see:**
- LangFuse welcome page or sign-up form

### 2.2 Create Account

1. Click **"Sign Up"** or **"Create Account"**
2. Fill in the form:
   - **Email**: Use any email (doesn't need to be real for local setup)
     - Example: `admin@localhost.com`
   - **Password**: Choose a secure password
     - **Important**: Remember this password - there's no password recovery for local setup!
   - **Name**: Your name or "Admin"

3. Click **"Create Account"** or **"Sign Up"**

### 2.3 Log In

After account creation, you'll be redirected to the login page:

1. Enter your email and password
2. Click **"Sign In"**

You should now see the LangFuse dashboard!

**First Time Login:**
- You might see a welcome tour - feel free to skip it
- The dashboard will be empty (no traces yet)
- Look for navigation menu on the left side

---

## Step 3: Generate API Keys

API keys allow your Python code to send trace data to LangFuse.

### 3.1 Navigate to Settings

In the LangFuse UI:

1. Look for **Settings** or **⚙️ icon** (usually bottom-left corner)
2. Click on it to open settings menu
3. Find **"API Keys"** section

### 3.2 Create New API Key

1. Click **"Create API Key"** or **"+ New API Key"** button

2. Fill in the form:
   - **Name**: Give it a descriptive name
     - Example: `stellar-sales-system-dev`
   - **Environment**: Leave as default or select "Development"

3. Click **"Create"** or **"Generate"**

### 3.3 Copy Your Keys

⚠️ **IMPORTANT:** You'll see two keys displayed:

1. **Public Key** (starts with `pk-lf-...`)
   - Example: `pk-lf-1234567890abcdef`
   
2. **Secret Key** (starts with `sk-lf-...`)
   - Example: `sk-lf-abcdef1234567890fedcba`

**⚠️ CRITICAL:** The secret key is only shown ONCE!

**Copy both keys immediately:**
- Select and copy the **Public Key** → Paste somewhere safe
- Select and copy the **Secret Key** → Paste somewhere safe

**If you lose them:**
- Delete the old key
- Create a new one
- Update your `.env` file with the new keys

---

## Step 4: Configure Environment Variables

Now we'll add your API keys to the project configuration.

### 4.1 Open Your .env File

Using your code editor or terminal:

```bash
# Using VS Code
code .env

# Using nano
nano .env

# Using vim
vim .env
```

### 4.2 Add LangFuse Configuration

Scroll to the **OBSERVABILITY & MONITORING** section.

Find these lines:

```bash
# LangFuse (Local Self-Hosted Observability - RECOMMENDED)
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
LANGFUSE_HOST=http://localhost:3000
```

Replace the placeholder values with your actual keys:

```bash
# LangFuse (Local Self-Hosted Observability - RECOMMENDED)
LANGFUSE_PUBLIC_KEY=pk-lf-1234567890abcdef
LANGFUSE_SECRET_KEY=sk-lf-abcdef1234567890fedcba
LANGFUSE_HOST=http://localhost:3000
```

### 4.3 Save and Close

- **VS Code**: Press `Ctrl+S` (Windows/Linux) or `Cmd+S` (Mac)
- **nano**: Press `Ctrl+X`, then `Y`, then `Enter`
- **vim**: Press `Esc`, type `:wq`, press `Enter`

### 4.4 Verify .env File

Make sure your keys are correct:

```bash
grep LANGFUSE .env
```

Should show:
```
LANGFUSE_PUBLIC_KEY=pk-lf-1234567890abcdef
LANGFUSE_SECRET_KEY=sk-lf-abcdef1234567890fedcba
LANGFUSE_HOST=http://localhost:3000
```

---

## Step 5: Install Python Package

The `langfuse` Python package lets your code communicate with the LangFuse server.

### 5.1 Activate Virtual Environment

If you use a virtual environment (recommended):

```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

### 5.2 Install LangFuse Package

```bash
pip install langfuse>=2.0.0
```

**Expected output:**
```
Collecting langfuse>=2.0.0
  Downloading langfuse-2.x.x-py3-none-any.whl
Installing collected packages: langfuse
Successfully installed langfuse-2.x.x
```

### 5.3 Verify Installation

```bash
python -c "import langfuse; print(f'LangFuse version: {langfuse.__version__}')"
```

Should print something like:
```
LangFuse version: 2.x.x
```

---

## Step 6: Verify Setup

Let's test that everything works!

### 6.1 Run Connection Test

```bash
python scripts/test_langfuse.py
```

**Expected output:**
```
✅ Langfuse Configuration:
   Host: http://localhost:3000
   Public Key: pk-lf-1234567890...
   Secret Key: sk-lf-abcdef12345...

🔍 Testing connection to Langfuse...
✅ Successfully connected to Langfuse!

📊 View your traces at:
   http://localhost:3000

🎉 Ready to run your pipeline with full observability!
```

### 6.2 Run Simple Trace Test

```bash
python scripts/test_langfuse_simple.py
```

This creates a test trace to verify end-to-end functionality.

**Expected output:**
```
🔍 Testing Langfuse connection...
✅ Langfuse handler initialized
✅ Test LLM call completed
✅ Flushed trace to Langfuse

🎉 SUCCESS! Langfuse is working!
📊 Check your traces at: http://localhost:3000
```

### 6.3 Check LangFuse UI

1. Go to http://localhost:3000
2. Click on **"Traces"** in the left menu
3. You should see your test trace!

**What to look for:**
- Trace name: Something like "FakeListLLM" or "diagnostic-test-trace"
- Status: Should show success (green checkmark)
- Timestamp: Should be just now

**Click on the trace** to see details:
- Timeline view
- Input/output data
- Execution time

---

## Troubleshooting

### Problem: Can't Access http://localhost:3000

**Possible Causes:**

1. **Port 3000 is already in use**
   
   Check what's using port 3000:
   ```bash
   # On macOS/Linux
   lsof -i :3000
   
   # On Windows
   netstat -ano | findstr :3000
   ```
   
   **Solution:** Stop the other service or change LangFuse port:
   - Edit `docker-compose.langfuse.yml`
   - Change `"3000:3000"` to `"3001:3000"`
   - Update `LANGFUSE_HOST` in `.env` to `http://localhost:3001`

2. **Docker containers not running**
   
   Check container status:
   ```bash
   docker ps -a | grep langfuse
   ```
   
   If status shows "Exited", check logs:
   ```bash
   docker logs stellar_langfuse
   ```
   
   **Solution:** Restart containers:
   ```bash
   docker-compose -f docker-compose.langfuse.yml restart
   ```

3. **Firewall blocking connection**
   
   **Solution:** Allow Docker Desktop in your firewall settings

### Problem: "Invalid API credentials" Error

**Symptoms:**
```
❌ Failed to connect to Langfuse: 401 Unauthorized
```

**Possible Causes:**

1. **Keys copied incorrectly**
   - Check for extra spaces or missing characters
   - Public key should start with `pk-lf-`
   - Secret key should start with `sk-lf-`

2. **Keys from wrong project**
   - Make sure you're using keys from your local LangFuse (localhost:3000)
   - Not from cloud.langfuse.com

**Solution:**
1. Delete old API key in LangFuse UI
2. Create new API key
3. Copy both keys carefully
4. Update `.env` file
5. Test again with `python scripts/test_langfuse.py`

### Problem: Traces Not Appearing in UI

**Possible Causes:**

1. **Need to refresh the page**
   - Press `F5` or `Cmd+R` to refresh
   - Traces can take 1-2 seconds to appear

2. **Traces not flushed**
   - Make sure your code calls `langfuse_client.flush()`
   - Our enhanced pipeline does this automatically

3. **Wrong LANGFUSE_HOST**
   - Check that `.env` has `http://localhost:3000`
   - NOT `https://` (local setup uses HTTP)
   - NOT `https://us.cloud.langfuse.com` (that's cloud)

**Solution:**
```bash
# Verify your config
grep LANGFUSE .env

# Should show:
# LANGFUSE_HOST=http://localhost:3000
```

### Problem: Database Connection Errors

**Symptoms:**
```
Error: Could not connect to database
```

**Solution:**

1. Check PostgreSQL container:
   ```bash
   docker logs stellar_langfuse_db --tail 20
   ```

2. Restart both containers:
   ```bash
   docker-compose -f docker-compose.langfuse.yml down
   docker-compose -f docker-compose.langfuse.yml up -d
   ```

3. Wait 60 seconds for initialization

4. Check logs again:
   ```bash
   docker logs stellar_langfuse --tail 20
   ```

### Problem: Out of Disk Space

**Symptoms:**
```
Error: No space left on device
```

**Solution:**

1. Check Docker disk usage:
   ```bash
   docker system df
   ```

2. Clean up unused Docker resources:
   ```bash
   docker system prune -a
   ```
   
   **⚠️ Warning:** This removes unused containers, images, and networks

3. Free up disk space on your machine

### Getting More Help

If you're still stuck:

1. **Check container logs:**
   ```bash
   docker logs stellar_langfuse --tail 50
   docker logs stellar_langfuse_db --tail 50
   ```

2. **Restart everything:**
   ```bash
   docker-compose -f docker-compose.langfuse.yml down
   docker-compose -f docker-compose.langfuse.yml up -d
   ```

3. **Check firewall/antivirus:**
   - Some security software blocks Docker networking
   - Temporarily disable to test

4. **See LANGFUSE_TROUBLESHOOTING.md** for more solutions

---

## Next Steps

✅ **LangFuse is now set up!**

### What to do next:

1. **Read the Usage Guide**
   - See: `docs/LANGFUSE_USAGE_GUIDE.md`
   - Learn how to interpret traces and find bottlenecks

2. **Run Your First Traced Pipeline**
   ```bash
   python orchestrator/pipeline_langfuse_enhanced.py
   ```

3. **View the Results**
   - Go to http://localhost:3000/traces
   - Click on your pipeline trace
   - Explore the timeline and metrics

4. **Learn Advanced Features**
   - Filter traces by transcript ID
   - Compare multiple pipeline runs
   - Set up alerts for errors
   - Export data for analysis

---

## Daily Usage

Once set up, here's your typical workflow:

### Starting Your Day

```bash
# 1. Make sure LangFuse is running
docker ps | grep langfuse

# 2. If not running, start it
docker-compose -f docker-compose.langfuse.yml up -d

# 3. Open LangFuse UI
open http://localhost:3000  # macOS
# or just visit http://localhost:3000 in browser
```

### Running Pipelines

```bash
# Run with full tracing
python orchestrator/pipeline_langfuse_enhanced.py

# Then view in LangFuse UI
```

### Ending Your Day

```bash
# Optional: Stop containers to save resources
docker-compose -f docker-compose.langfuse.yml down

# Data is preserved in Docker volumes
# Next time you start, all traces will still be there
```

---

## Reference

### Important URLs

- **LangFuse UI**: http://localhost:3000
- **Traces**: http://localhost:3000/traces
- **Settings**: http://localhost:3000/settings
- **API Keys**: http://localhost:3000/settings/api-keys

### Important Commands

```bash
# Start LangFuse
docker-compose -f docker-compose.langfuse.yml up -d

# Stop LangFuse
docker-compose -f docker-compose.langfuse.yml down

# Restart LangFuse
docker-compose -f docker-compose.langfuse.yml restart

# View logs
docker logs stellar_langfuse --tail 50

# Check status
docker ps | grep langfuse

# Test connection
python scripts/test_langfuse.py
```

### File Locations

- **Docker Config**: `docker-compose.langfuse.yml`
- **Environment Variables**: `.env`
- **Test Scripts**: `scripts/test_langfuse*.py`
- **Enhanced Pipeline**: `orchestrator/pipeline_langfuse_enhanced.py`
- **Documentation**: `docs/LANGFUSE_*.md`

---

## Summary Checklist

Use this checklist to verify your setup:

- [ ] Docker Desktop installed and running
- [ ] Ran `docker-compose -f docker-compose.langfuse.yml up -d`
- [ ] Both containers running (check with `docker ps`)
- [ ] Opened http://localhost:3000 successfully
- [ ] Created account and logged in
- [ ] Generated API keys (public and secret)
- [ ] Added keys to `.env` file
- [ ] Installed langfuse package (`pip install langfuse>=2.0.0`)
- [ ] Ran `python scripts/test_langfuse.py` successfully
- [ ] Saw test trace in LangFuse UI

**All checked?** You're ready to use LangFuse! 🎉

---

**Need Help?**
- See: `docs/LANGFUSE_TROUBLESHOOTING.md`
- Check: Docker logs for error messages
- Verify: All environment variables are set correctly


