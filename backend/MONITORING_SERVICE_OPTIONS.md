# Website Monitoring Service - Alternative Startup Methods

This document explains different approaches to start the WebsiteMonitorService to avoid the known uvicorn + Playwright + Windows event loop conflicts.

## The Problem

The original FastAPI lifespan approach fails on Windows due to:

- Playwright trying to create subprocesses in the uvicorn event loop
- Windows event loop policy conflicts
- `NotImplementedError` when creating subprocess transport

## Solution Options

### Option 1: Separate Process (Recommended) ⭐

Run the monitoring service as a completely independent process.

**Advantages:**

- ✅ Completely isolated from FastAPI
- ✅ Can restart independently
- ✅ Better resource management
- ✅ Works on all platforms
- ✅ No event loop conflicts

**Usage:**

1. **Start the daemon directly:**

   ```bash
   # Linux/Mac
   cd backend
   python -m app.logic.monitoring_daemon

   # Windows
   cd backend
   python -m app.logic.monitoring_daemon
   ```

2. **Use the helper scripts:**

   ```bash
   # Linux/Mac
   chmod +x scripts/start-monitoring-daemon.sh
   ./scripts/start-monitoring-daemon.sh

   # Windows
   scripts\start-monitoring-daemon.bat
   ```

3. **Docker Compose:**

   ```bash
   # Add monitoring service to your stack
   docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up
   ```

4. **As a system service (Linux):**

   ```bash
   # Create systemd service (example)
   sudo tee /etc/systemd/system/webpage-monitoring.service > /dev/null <<EOF
   [Unit]
   Description=Webpage Change Monitoring Service
   After=network.target

   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/your/backend
   ExecStart=/path/to/your/.venv/bin/python -m app.logic.monitoring_daemon
   Restart=always

   [Install]
   WantedBy=multi-user.target
   EOF

   sudo systemctl enable webpage-monitoring
   sudo systemctl start webpage-monitoring
   ```

### Option 2: Threaded Approach ⚡

Run the monitoring service in a separate thread with its own event loop (integrated with FastAPI).

**Advantages:**

- ✅ Integrated with FastAPI lifecycle
- ✅ Automatic startup/shutdown
- ✅ Uses separate event loop
- ✅ Good for development

**Usage:**

1. **Set environment variable:**

   ```bash
   export ENABLE_MONITORING=true
   ```

2. **Start FastAPI normally:**
   ```bash
   uvicorn app.main:app --reload
   ```

The service will automatically start/stop with FastAPI.

### Option 3: Manual API Control 🎛️

Control the monitoring service via API endpoints.

**Advantages:**

- ✅ Full control via API
- ✅ Can start/stop on demand
- ✅ Good for debugging
- ✅ Integrated monitoring

**API Endpoints:**

```bash
# Check status
curl http://localhost:8000/api/v1/monitoring/status

# Start monitoring
curl -X POST http://localhost:8000/api/v1/monitoring/start

# Stop monitoring
curl -X POST http://localhost:8000/api/v1/monitoring/stop

# Restart monitoring
curl -X POST http://localhost:8000/api/v1/monitoring/restart
```

## Configuration

### Environment Variables

- `ENABLE_MONITORING=true` - Enable automatic startup (Options 2)
- `DATABASE_URL` - Database connection string
- `MONITORING_INTERVAL=60` - Check interval in seconds

### Database Setup

Ensure your database is running and migrations are applied:

```bash
# Apply migrations
alembic upgrade head
```

## Troubleshooting

### Common Issues:

1. **Windows Event Loop Issues:**

   ```
   psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode
   ```
   **Solution:** The monitoring services now use `WindowsSelectorEventLoopPolicy()` which is compatible with both psycopg (PostgreSQL) and Playwright on Windows. This issue is automatically handled.

2. **Database Connection Errors:**

   - Ensure PostgreSQL is running
   - Check DATABASE_URL environment variable
   - Verify database exists and migrations are applied

3. **Playwright Installation:**

   ```bash
   # Install Playwright browsers
   playwright install chromium
   
   # If you get permission errors on Windows:
   playwright install chromium --force
   ```

4. **Permission Errors (Linux/Mac):**

   ```bash
   # Make scripts executable
   chmod +x scripts/start-monitoring-daemon.sh
   ```

5. **Port Conflicts:**
   - Ensure FastAPI and monitoring don't compete for resources
   - Check logs for specific error messages

6. **Windows Subprocess Errors:**
   If you still get subprocess creation errors, ensure:
   - Windows Defender isn't blocking the process
   - Your antivirus allows subprocess creation
   - Run with appropriate permissions

### Monitoring Logs

The monitoring service logs to:

- Console output (when run directly)
- `logs/app.log` (application logs)
- `logs/errors.log` (error logs)

## Recommended Setup

### Development:

- Use **Option 2 (Threaded)** for development
- Set `ENABLE_MONITORING=true` in your `.env`
- Monitor via API endpoints

### Production:

- Use **Option 1 (Separate Process)**
- Set up as system service or Docker container
- Use process manager (systemd, supervisor, etc.)
- Monitor via health checks

## Migration from Old Approach

If you were using the old FastAPI lifespan approach:

1. Remove `ENABLE_MONITORING=true` from your FastAPI environment
2. Choose one of the new approaches above
3. Update your deployment scripts accordingly

The new approaches are more robust and avoid the Windows event loop issues entirely.
