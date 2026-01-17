# Troubleshooting Guide

This guide provides solutions to common issues you may encounter while developing, deploying, or running the Geo-Analytics API.

## Table of Contents

- [Application Issues](#application-issues)
- [Database Issues](#database-issues)
- [Performance Issues](#performance-issues)
- [API Issues](#api-issues)
- [Docker Issues](#docker-issues)
- [Authentication Issues](#authentication-issues)
- [Logging and Monitoring](#logging-and-monitoring)

## Application Issues

### Application Won't Start

**Symptoms:** The application fails to start or exits immediately

**Common Causes and Solutions:**

1. **Missing or incorrect environment variables**
   ```bash
   # Check .env file exists
   ls -la .env
   
   # Verify required variables
   grep -E 'APP_|DATABASE_|SECRET' .env
   ```

2. **Port already in use**
   ```bash
   # Check if port 8000 is in use
   lsof -i :8000
   
   # Kill the process using the port
   kill -9 <PID>
   
   # Or use a different port
   APP_PORT=8001 python main.py
   ```

3. **Missing dependencies**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt
   
   # Check for dependency conflicts
   pip check
   ```

### Import Errors

**Symptoms:** `ModuleNotFoundError` or `ImportError`

**Solutions:**

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Verify Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt

# Check PYTHONPATH
echo $PYTHONPATH
```

### Unexpected Crashes

**Symptoms:** Application crashes without clear error message

**Debugging Steps:**

1. **Check logs**
   ```bash
   # Application logs
   tail -f logs/app.log
   
   # System logs (if running as service)
   journalctl -u geo-analytics-api -f
   ```

2. **Enable debug logging**
   ```bash
   # In .env file
   LOG_LEVEL=DEBUG
   APP_DEBUG=true
   ```

3. **Check system resources**
   ```bash
   # Memory usage
   free -h
   
   # Disk space
   df -h
   
   # CPU usage
   top
   ```

## Database Issues

### Connection Refused

**Symptoms:** `Connection refused` or `could not connect to server`

**Solutions:**

1. **Verify database is running**
   ```bash
   # PostgreSQL status
   sudo service postgresql status
   
   # Start if not running
   sudo service postgresql start
   
   # Or with Docker
   docker ps | grep postgres
   ```

2. **Check connection string**
   ```bash
   # Verify DATABASE_URL format
   # postgresql://username:password@host:port/database
   
   # Test connection
   psql $DATABASE_URL
   ```

3. **Firewall issues**
   ```bash
   # Check if port 5432 is accessible
   telnet localhost 5432
   
   # Or using nc
   nc -zv localhost 5432
   ```

### Migration Errors

**Symptoms:** Alembic migrations fail

**Solutions:**

1. **Check migration history**
   ```bash
   alembic current
   alembic history
   ```

2. **Fix corrupted migration state**
   ```bash
   # Stamp database to specific revision
   alembic stamp head
   
   # Or reset to a known good revision
   alembic downgrade <revision_id>
   alembic upgrade head
   ```

3. **Manual migration fixes**
   ```bash
   # Connect to database
   psql geoanalytics_dev
   
   # Check alembic_version table
   SELECT * FROM alembic_version;
   
   # Manually update if needed
   UPDATE alembic_version SET version_num = '<revision_id>';
   ```

### Slow Queries

**Symptoms:** Database queries taking too long

**Debugging:**

```sql
-- Enable query logging in PostgreSQL
ALTER DATABASE geoanalytics_dev SET log_statement = 'all';
ALTER DATABASE geoanalytics_dev SET log_duration = on;

-- Find slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM your_table WHERE ...;
```

**Solutions:**

- Add indexes to frequently queried columns
- Optimize query structure
- Increase database connection pool
- Add query caching with Redis

### Connection Pool Exhausted

**Symptoms:** `TimeoutError` or `QueuePool limit exceeded`

**Solutions:**

```python
# In database configuration
SQLALCHEMY_POOL_SIZE = 20  # Increase pool size
SQLALCHEMY_MAX_OVERFLOW = 10
SQLALCHEMY_POOL_RECYCLE = 3600

# Or in DATABASE_URL
DATABASE_URL = "postgresql://...?pool_size=20&max_overflow=10"
```

## Performance Issues

### High Memory Usage

**Symptoms:** Application consuming excessive memory

**Solutions:**

1. **Profile memory usage**
   ```python
   # Add memory profiler
   from memory_profiler import profile
   
   @profile
   def my_function():
       # function code
       pass
   ```

2. **Check for memory leaks**
   ```bash
   # Install objgraph
   pip install objgraph
   
   # In Python code
   import objgraph
   objgraph.show_most_common_types()
   ```

3. **Limit data loading**
   ```python
   # Use pagination
   items = db.query(Item).limit(100).offset(skip).all()
   
   # Use streaming for large datasets
   for row in db.query(Item).yield_per(1000):
       process(row)
   ```

### High CPU Usage

**Symptoms:** CPU consistently above 80%

**Solutions:**

1. **Profile CPU usage**
   ```python
   import cProfile
   cProfile.run('my_function()')
   ```

2. **Optimize expensive operations**
   - Use async/await for I/O operations
   - Implement caching
   - Move heavy computations to background tasks

3. **Scale horizontally**
   - Add more workers
   - Use load balancer
   - Deploy multiple instances

### Slow Response Times

**Symptoms:** API endpoints responding slowly

**Debugging:**

```python
# Add timing middleware
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

**Solutions:**

- Add database indexes
- Implement caching (Redis)
- Optimize database queries
- Use CDN for static assets
- Enable gzip compression

## API Issues

### 404 Not Found

**Symptoms:** Endpoint returns 404

**Solutions:**

```bash
# Check available routes
curl http://localhost:8000/docs

# Verify route registration
# In main.py
app.include_router(router, prefix="/api")

# Check for typos in URL
```

### 422 Validation Error

**Symptoms:** Request fails with validation error

**Solutions:**

```python
# Check request body matches schema
# Example schema
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: int = Field(gt=0, lt=150)

# Valid request
{
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
}
```

### 500 Internal Server Error

**Symptoms:** Generic server error

**Debugging:**

```bash
# Check application logs
tail -f logs/app.log

# Enable detailed error responses (development only)
APP_DEBUG=true
```

### CORS Errors

**Symptoms:** Browser blocks requests from different origin

**Solutions:**

```python
# In main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Docker Issues

### Container Won't Start

**Symptoms:** Docker container exits immediately

**Solutions:**

```bash
# Check container logs
docker logs <container_id>

# Inspect container
docker inspect <container_id>

# Run interactively to debug
docker run -it <image_name> /bin/bash
```

### Port Binding Errors

**Symptoms:** `port is already allocated`

**Solutions:**

```bash
# Find process using port
lsof -i :8000

# Stop conflicting container
docker ps
docker stop <container_id>

# Use different port
docker run -p 8001:8000 <image_name>
```

### Volume Mount Issues

**Symptoms:** Files not accessible in container

**Solutions:**

```bash
# Check volume mounts
docker inspect -f '{{ .Mounts }}' <container_id>

# Verify permissions
ls -la /path/to/mount

# Fix permissions
chown -R $(id -u):$(id -g) /path/to/mount
```

## Authentication Issues

### Token Expired

**Symptoms:** `401 Unauthorized` with token expiry message

**Solutions:**

```python
# Implement token refresh
@router.post("/token/refresh")
async def refresh_token(refresh_token: str):
    # Verify and issue new token
    pass
```

### Invalid Credentials

**Symptoms:** Login fails with valid credentials

**Solutions:**

```python
# Check password hashing
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Verify password
pwd_context.verify(plain_password, hashed_password)
```

## Logging and Monitoring

### Missing Logs

**Symptoms:** No logs being generated

**Solutions:**

```python
# Configure logging properly
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Log Rotation Not Working

**Solutions:**

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

## Getting Help

If you can't resolve your issue:

1. Check existing GitHub issues
2. Search Stack Overflow
3. Review the logs carefully
4. Create a minimal reproducible example
5. Open a new GitHub issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Relevant logs and error messages

## Useful Commands

```bash
# Check system info
uname -a
python --version
pip list

# Test connectivity
ping google.com
curl -I http://localhost:8000/health

# Resource monitoring
top
htop
df -h
free -m

# Docker debugging
docker ps -a
docker logs -f <container>
docker exec -it <container> /bin/bash

# Database debugging
psql -h localhost -U user -d database
pg_isready
```
