# LangFuse Troubleshooting Guide - Stellar Sales System

> **Solutions to common LangFuse problems and error messages**

This guide helps you resolve issues with your LangFuse setup and usage.

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Docker & Container Issues](#docker--container-issues)
3. [Authentication & API Key Issues](#authentication--api-key-issues)
4. [Traces Not Appearing](#traces-not-appearing)
5. [Performance & Resource Issues](#performance--resource-issues)
6. [Database Problems](#database-problems)
7. [Common Error Messages](#common-error-messages)
8. [Advanced Troubleshooting](#advanced-troubleshooting)

---

## Quick Diagnostics

Run this diagnostic script to check your setup:

```bash
python scripts/diagnose_langfuse.py
```

This tests:
- ✅ Docker container running
- ✅ HTTP connectivity
- ✅ API authentication
- ✅ Python SDK
- ✅ LangChain callback

**Example output:**
```
================================================================================
🔍 LANGFUSE DIAGNOSTIC REPORT
================================================================================

TEST 1: Docker Container Running
✅ Docker container running
   stellar_langfuse	Up 5 minutes

TEST 2: HTTP Connection to Langfuse
✅ Langfuse HTTP endpoint reachable
   Status: 200

TEST 3: API Key Authentication
✅ API authentication successful!

TEST 4: Langfuse Python SDK
✅ Python SDK working!

TEST 5: LangChain Callback Integration
✅ LangChain callback executed!
```

If any test fails, jump to the relevant section below.

---

## Docker & Container Issues

### Problem: "Cannot connect to the Docker daemon"

**Error message:**
```
Error: Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Cause:** Docker Desktop is not running

**Solution:**

1. **Start Docker Desktop**
   - macOS: Open "Docker" from Applications
   - Windows: Start "Docker Desktop" from Start menu
   - Linux: `sudo systemctl start docker`

2. **Verify it's running:**
   ```bash
   docker info
   ```
   
   Should show system information, not an error

3. **Try starting LangFuse again:**
   ```bash
   docker-compose -f docker-compose.langfuse.yml up -d
   ```

### Problem: Port 3000 Already in Use

**Error message:**
```
Error: Bind for 0.0.0.0:3000 failed: port is already allocated
```

**Cause:** Another application is using port 3000

**Solution 1: Find what's using the port**

```bash
# On macOS/Linux
lsof -i :3000

# On Windows
netstat -ano | findstr :3000
```

**Solution 2: Stop the other service**

```bash
# Example: If it's another Node.js app
ps aux | grep node
kill <PID>
```

**Solution 3: Change LangFuse port**

1. Edit `docker-compose.langfuse.yml`:
   ```yaml
   ports:
     - "3001:3000"  # Changed from "3000:3000"
   ```

2. Update `.env`:
   ```bash
   LANGFUSE_HOST=http://localhost:3001
   ```

3. Restart:
   ```bash
   docker-compose -f docker-compose.langfuse.yml down
   docker-compose -f docker-compose.langfuse.yml up -d
   ```

### Problem: Containers Won't Start

**Check logs:**
```bash
docker logs stellar_langfuse --tail 50
docker logs stellar_langfuse_db --tail 50
```

**Common causes:**

1. **Database initialization failed**
   
   **Symptoms in logs:**
   ```
   Error: Database migration failed
   ```
   
   **Solution:**
   ```bash
   # Remove old database volume
   docker-compose -f docker-compose.langfuse.yml down -v
   
   # Start fresh
   docker-compose -f docker-compose.langfuse.yml up -d
   
   # Wait 60 seconds for initialization
   ```

2. **Out of memory**
   
   **Symptoms in logs:**
   ```
   Error: JavaScript heap out of memory
   ```
   
   **Solution:**
   - Close other applications
   - Increase Docker memory limit (Docker Desktop → Settings → Resources)
   - Recommended: 4GB RAM for Docker

3. **Conflicting container names**
   
   **Symptoms:**
   ```
   Error: The container name "/stellar_langfuse" is already in use
   ```
   
   **Solution:**
   ```bash
   # Remove old containers
   docker rm stellar_langfuse stellar_langfuse_db
   
   # Start again
   docker-compose -f docker-compose.langfuse.yml up -d
   ```

### Problem: "Unable to find image" Error

**Error message:**
```
Error: Unable to find image 'langfuse/langfuse:2' locally
```

**Cause:** Docker can't download the image (network issue)

**Solution:**

1. **Check internet connection**

2. **Pull image manually:**
   ```bash
   docker pull langfuse/langfuse:2
   docker pull postgres:15
   ```

3. **Try again:**
   ```bash
   docker-compose -f docker-compose.langfuse.yml up -d
   ```

---

## Authentication & API Key Issues

### Problem: "401 Unauthorized" Error

**Error message:**
```
❌ Failed to connect to Langfuse: 401 Unauthorized
HTTP 401: Invalid credentials
```

**Possible causes:**

1. **Wrong API keys**
   
   **Check your keys:**
   ```bash
   grep LANGFUSE .env
   ```
   
   **Should show:**
   ```
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=http://localhost:3000
   ```
   
   **Solution:**
   - Keys must start with `pk-lf-` and `sk-lf-`
   - No extra spaces
   - No quotes around values
   - Copy keys exactly as shown in LangFuse UI

2. **Keys from wrong LangFuse instance**
   
   **Check LANGFUSE_HOST:**
   ```bash
   grep LANGFUSE_HOST .env
   ```
   
   **Should be:**
   ```
   LANGFUSE_HOST=http://localhost:3000
   ```
   
   **NOT:**
   ```
   LANGFUSE_HOST=https://us.cloud.langfuse.com  ❌ Wrong!
   LANGFUSE_HOST=https://localhost:3000         ❌ Should be http
   ```

3. **API key was deleted**
   
   **Solution:**
   - Go to http://localhost:3000/settings/api-keys
   - Delete old key
   - Create new key
   - Update `.env` file

### Problem: "Public key format invalid" Error

**Error message:**
```
Error: Public key format invalid
```

**Cause:** Typo or corruption in API key

**Solution:**

1. **Regenerate keys:**
   - LangFuse UI → Settings → API Keys
   - Delete existing key
   - Create new key
   - Copy carefully

2. **Update .env:**
   ```bash
   nano .env
   ```
   
   Make sure keys have no:
   - Extra spaces
   - Line breaks
   - Quote marks
   - Special characters

3. **Verify format:**
   ```bash
   python -c "
   from config.settings import settings
   print(f'Public: {settings.LANGFUSE_PUBLIC_KEY}')
   print(f'Secret: {settings.LANGFUSE_SECRET_KEY}')
   print(f'Host: {settings.LANGFUSE_HOST}')
   "
   ```

---

## Traces Not Appearing

### Problem: Pipeline Runs But No Traces

**Symptoms:**
- Pipeline completes successfully
- Console says "Flushed trace to LangFuse"
- But nothing in LangFuse UI

**Diagnostic steps:**

1. **Check API keys are set:**
   ```bash
   python -c "from config.settings import settings; print(settings.LANGFUSE_PUBLIC_KEY)"
   ```
   
   Should print your public key, not None

2. **Check LangFuse is reachable:**
   ```bash
   curl http://localhost:3000/api/public/health
   ```
   
   Should return: `{"status":"OK"}`

3. **Check for errors in Python:**
   ```bash
   python scripts/test_langfuse_simple.py
   ```
   
   Look for connection errors

**Solutions:**

#### Solution 1: Flush not called

**Problem:** Code doesn't call `.flush()`

**Check:** Does your pipeline call `langfuse_client.flush()`?

**Fix:** The enhanced pipeline already does this. If using custom code:
```python
# At the end of your script
langfuse_client.flush()
time.sleep(2)  # Give it time to send data
```

#### Solution 2: Wrong project/session

**Problem:** Traces going to different project

**Solution:**
- LangFuse UI → Top-left dropdown
- Make sure you're viewing the correct project
- Try "All Projects" view

#### Solution 3: Browser cache

**Problem:** UI not refreshing

**Solution:**
- Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- Clear browser cache
- Try incognito/private window

#### Solution 4: Traces are there, just hidden by filter

**Problem:** Filter hiding your traces

**Solution:**
- Click "Clear all filters"
- Check date range includes today
- Check status includes "Success"

### Problem: Only Some Agents Show Up

**Symptoms:**
- Pipeline shows partial data
- Some agents missing from trace

**Cause:** LangGraph automatic tracing only captures LLM calls

**Solution:** This is expected behavior

- LangGraph's `CallbackHandler` auto-captures LLM generations
- For full agent tracing, use our enhanced pipeline:
  ```bash
  python orchestrator/pipeline_langfuse_enhanced.py
  ```

---

## Performance & Resource Issues

### Problem: Pipeline Much Slower with Tracing

**Symptoms:**
- Normal pipeline: 90s
- With LangFuse: 120s
- 30% slowdown

**Causes:**

1. **Network latency** sending data to LangFuse
2. **Large payloads** (full transcript in every span)
3. **Synchronous flush** blocking execution

**Solutions:**

#### Solution 1: Accept the overhead

- 10-20% slowdown is normal
- Only use for debugging, not production

#### Solution 2: Reduce payload size

Edit `core/langfuse_tracer.py`:

```python
def _truncate_data(self, data: Any, max_length: int = 5000):
    # Change to smaller value
    max_length = 1000  # Smaller = faster
```

#### Solution 3: Async flushing

The SDK already uses async, but you can increase buffer:

```python
langfuse_client = Langfuse(
    flush_at=20,  # Send in batches of 20
    flush_interval=10  # Or every 10 seconds
)
```

### Problem: LangFuse UI is Slow

**Symptoms:**
- Pages take 5+ seconds to load
- Timeline doesn't render
- Browser freezing

**Causes:**

1. **Too many traces** (database slow)
2. **Large trace payloads** (huge transcripts)
3. **Low RAM** on machine

**Solutions:**

#### Solution 1: Clean up old traces

```bash
# Access LangFuse database
docker exec -it stellar_langfuse_db psql -U langfuse -d langfuse

# Delete old traces (older than 30 days)
DELETE FROM traces WHERE created_at < NOW() - INTERVAL '30 days';

# Exit
\q
```

#### Solution 2: Increase Docker memory

- Docker Desktop → Settings → Resources
- Increase Memory to 4GB+
- Restart Docker

#### Solution 3: Filter traces

- Don't load "All traces"
- Use date filters (e.g., "Today")
- Use search to find specific traces

### Problem: Out of Disk Space

**Error message:**
```
Error: No space left on device
```

**Check disk usage:**
```bash
docker system df
```

**Shows:**
```
TYPE            TOTAL     ACTIVE    SIZE
Images          25        5         15GB
Containers      10        2         2GB
Volumes         8         2         5GB     ← LangFuse data here
```

**Solution:**

1. **Clean up Docker:**
   ```bash
   # Remove unused containers, images, networks
   docker system prune -a
   
   # When prompted, type: y
   ```

2. **Remove old LangFuse data:**
   ```bash
   # WARNING: This deletes all traces!
   docker-compose -f docker-compose.langfuse.yml down -v
   docker-compose -f docker-compose.langfuse.yml up -d
   ```

3. **Free up disk space:**
   - Empty trash
   - Delete old downloads
   - Use disk cleanup tools

---

## Database Problems

### Problem: "Database connection failed"

**Error in logs:**
```
Error: connect ECONNREFUSED 127.0.0.1:5432
```

**Cause:** PostgreSQL container not running

**Solution:**

1. **Check containers:**
   ```bash
   docker ps -a | grep langfuse_db
   ```

2. **If not running, check logs:**
   ```bash
   docker logs stellar_langfuse_db --tail 50
   ```

3. **Common fixes:**
   
   **If "port already allocated":**
   ```bash
   # Another PostgreSQL is running
   # Stop it or change port in docker-compose.langfuse.yml
   ```
   
   **If "disk full":**
   ```bash
   # Free up space and restart
   docker-compose -f docker-compose.langfuse.yml restart
   ```

### Problem: "Migration failed" Error

**Error message:**
```
Error: Database migration failed
```

**Cause:** Database schema mismatch or corruption

**Solution:**

1. **Reset database (destroys all data):**
   ```bash
   docker-compose -f docker-compose.langfuse.yml down -v
   docker-compose -f docker-compose.langfuse.yml up -d
   ```

2. **Wait for initialization:**
   ```bash
   docker logs stellar_langfuse -f
   # Watch for "Server started" message
   ```

---

## Common Error Messages

### Error: "Module 'langfuse' has no attribute 'Langfuse'"

**Full error:**
```python
AttributeError: module 'langfuse' has no attribute 'Langfuse'
```

**Cause:** Old or broken installation

**Solution:**
```bash
pip uninstall langfuse -y
pip install langfuse>=2.0.0
```

### Error: "Connection refused"

**Full error:**
```
requests.exceptions.ConnectionError: Connection refused
```

**Cause:** LangFuse server not running

**Solution:**
```bash
# Check if running
docker ps | grep langfuse

# If not, start it
docker-compose -f docker-compose.langfuse.yml up -d
```

### Error: "SSL: CERTIFICATE_VERIFY_FAILED"

**Full error:**
```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Cause:** Using HTTPS for local LangFuse

**Solution:**

Check your `.env`:
```bash
# Should be HTTP (not HTTPS) for local
LANGFUSE_HOST=http://localhost:3000  ✅ Correct
LANGFUSE_HOST=https://localhost:3000 ❌ Wrong!
```

### Error: "Trace not found"

**Error message:**
```
404: Trace not found
```

**Causes:**

1. **Trace deleted** - regenerate trace
2. **Wrong project** - check project dropdown in UI
3. **Database reset** - traces were lost

---

## Advanced Troubleshooting

### Enable Debug Logging

Edit `docker-compose.langfuse.yml`:

```yaml
environment:
  NODE_ENV: development  # Uncomment this line
```

Restart:
```bash
docker-compose -f docker-compose.langfuse.yml restart
```

View verbose logs:
```bash
docker logs stellar_langfuse -f
```

### Access LangFuse Database Directly

```bash
# Connect to PostgreSQL
docker exec -it stellar_langfuse_db psql -U langfuse -d langfuse

# List tables
\dt

# Check traces
SELECT id, name, created_at FROM traces ORDER BY created_at DESC LIMIT 10;

# Exit
\q
```

### Check Network Connectivity

```bash
# From host to container
curl http://localhost:3000/api/public/health

# From container to container
docker exec stellar_langfuse curl http://stellar_langfuse_db:5432
```

### Reset Everything

**Nuclear option** - starts completely fresh:

```bash
# Stop and remove everything
docker-compose -f docker-compose.langfuse.yml down -v

# Remove images
docker rmi langfuse/langfuse:2 postgres:15

# Pull fresh images
docker-compose -f docker-compose.langfuse.yml pull

# Start fresh
docker-compose -f docker-compose.langfuse.yml up -d

# Wait 60 seconds
sleep 60

# Create new account and API keys
open http://localhost:3000
```

---

## Getting More Help

### Still Stuck?

1. **Check official docs:**
   - https://langfuse.com/docs

2. **Check our setup guide:**
   - `docs/LANGFUSE_SETUP.md`

3. **Run full diagnostic:**
   ```bash
   python scripts/diagnose_langfuse.py > diagnostic-report.txt
   ```

4. **Collect information:**
   - Docker version: `docker --version`
   - Python version: `python --version`
   - OS: `uname -a` (macOS/Linux) or `ver` (Windows)
   - Error messages from logs
   - Steps you've already tried

### Create Support Ticket

Include this information:

```
### Environment
- OS: macOS 13.5
- Docker: 24.0.6
- Python: 3.11.5
- LangFuse Version: 2.x.x

### Problem
[Describe what's not working]

### Steps to Reproduce
1. ...
2. ...
3. ...

### Error Messages
```
[Paste error logs here]
```

### What I've Tried
- Restarted containers
- Regenerated API keys
- Checked logs (see above)
```

---

## Prevention Checklist

Avoid common issues:

- [ ] Keep Docker Desktop running
- [ ] Use correct LANGFUSE_HOST (http, not https)
- [ ] Keep API keys in `.env` file
- [ ] Don't commit `.env` to git
- [ ] Periodically clean up old traces
- [ ] Monitor disk space
- [ ] Keep Docker images updated

---

## Quick Reference

### Essential Commands

```bash
# Start LangFuse
docker-compose -f docker-compose.langfuse.yml up -d

# Stop LangFuse
docker-compose -f docker-compose.langfuse.yml down

# View logs
docker logs stellar_langfuse --tail 50

# Restart
docker-compose -f docker-compose.langfuse.yml restart

# Reset (destroys data)
docker-compose -f docker-compose.langfuse.yml down -v

# Test connection
python scripts/test_langfuse.py

# Run diagnostics
python scripts/diagnose_langfuse.py
```

### Health Check URLs

- **UI**: http://localhost:3000
- **API Health**: http://localhost:3000/api/public/health
- **Traces**: http://localhost:3000/traces

---

## Summary

**Most Common Issues:**
1. ❌ Docker not running → Start Docker Desktop
2. ❌ Wrong API keys → Regenerate in UI and update `.env`
3. ❌ Port conflict → Change port in `docker-compose.langfuse.yml`
4. ❌ Need to flush → Enhanced pipeline handles this
5. ❌ Wrong host → Use `http://localhost:3000` (http, not https)

**Remember:**
- Check logs first: `docker logs stellar_langfuse`
- Run diagnostics: `python scripts/diagnose_langfuse.py`
- When in doubt, restart: `docker-compose restart`

**Still having issues?** Re-read the setup guide: `docs/LANGFUSE_SETUP.md`


