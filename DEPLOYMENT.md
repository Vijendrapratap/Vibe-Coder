# VibeDoc Deployment Guide

This guide covers multiple deployment options for VibeDoc, from local development to cloud production environments.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Environment Configuration](#environment-configuration)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- **Python 3.11+** - Core runtime
- **pip** - Package manager
- **SiliconFlow API Key** - Get free at [siliconflow.cn](https://siliconflow.cn)

### Optional

- **Docker** - For containerized deployment
- **Git** - For version control

---

## Local Development

### Step 1: Clone Repository

```bash
git clone https://github.com/YourUsername/VibeDoc-English.git
cd VibeDoc-English
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use your preferred editor
```

Add your API key:

```bash
SILICONFLOW_API_KEY=your_actual_api_key_here
```

### Step 5: Run Application

```bash
python app.py
```

Application will start at:
- **Local**: http://localhost:7860
- **Network**: http://0.0.0.0:7860

---

## Docker Deployment

### Option 1: Docker Run

```bash
# Build image
docker build -t vibedoc:latest .

# Run container
docker run -d \
  --name vibedoc \
  -p 7860:7860 \
  -e SILICONFLOW_API_KEY=your_api_key \
  vibedoc:latest
```

### Option 2: Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  vibedoc:
    build: .
    container_name: vibedoc
    ports:
      - "7860:7860"
    environment:
      - SILICONFLOW_API_KEY=${SILICONFLOW_API_KEY}
      - ENVIRONMENT=production
    restart: unless-stopped
    volumes:
      - ./data:/app/data
```

Run:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Cloud Deployment

### Hugging Face Spaces

1. **Create Space**
   - Go to [huggingface.co/spaces](https://huggingface.co/spaces)
   - Click "Create new Space"
   - Select "Gradio" as SDK

2. **Upload Files**
   ```bash
   git clone https://huggingface.co/spaces/YourUsername/vibedoc
   cd vibedoc
   cp -r /path/to/VibeDoc-English/* .
   git add .
   git commit -m "Initial commit"
   git push
   ```

3. **Configure Secrets**
   - Go to Space Settings → Repository secrets
   - Add `SILICONFLOW_API_KEY` with your API key

4. **Deploy**
   - Space will automatically build and deploy

### Railway

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Initialize**
   ```bash
   railway login
   railway init
   ```

3. **Deploy**
   ```bash
   railway up
   ```

4. **Add Environment Variables**
   ```bash
   railway variables set SILICONFLOW_API_KEY=your_api_key
   ```

### Render

1. **Create Account** at [render.com](https://render.com)

2. **New Web Service**
   - Connect your GitHub repository
   - Select "Python" environment

3. **Configure**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Environment Variables**: Add `SILICONFLOW_API_KEY`

4. **Deploy**
   - Click "Create Web Service"

### Google Cloud Run

1. **Install gcloud CLI**
   ```bash
   # Follow: https://cloud.google.com/sdk/docs/install
   ```

2. **Build and Push**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/vibedoc
   ```

3. **Deploy**
   ```bash
   gcloud run deploy vibedoc \
     --image gcr.io/PROJECT_ID/vibedoc \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars SILICONFLOW_API_KEY=your_api_key
   ```

### AWS (EC2)

1. **Launch EC2 Instance**
   - Ubuntu 22.04 LTS
   - t2.medium or larger
   - Open port 7860 in security group

2. **Connect and Setup**
   ```bash
   ssh ubuntu@your-instance-ip
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python 3.11
   sudo apt install python3.11 python3.11-venv python3-pip -y
   
   # Clone repository
   git clone https://github.com/YourUsername/VibeDoc-English.git
   cd VibeDoc-English
   
   # Setup virtual environment
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   nano .env  # Add API key
   ```

3. **Run as Service**
   Create `/etc/systemd/system/vibedoc.service`:
   
   ```ini
   [Unit]
   Description=VibeDoc Application
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/VibeDoc-English
   Environment="PATH=/home/ubuntu/VibeDoc-English/venv/bin"
   ExecStart=/home/ubuntu/VibeDoc-English/venv/bin/python app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable vibedoc
   sudo systemctl start vibedoc
   sudo systemctl status vibedoc
   ```

4. **Setup Nginx Reverse Proxy** (Optional)
   ```bash
   sudo apt install nginx -y
   ```

   Create `/etc/nginx/sites-available/vibedoc`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:7860;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

   Enable:
   ```bash
   sudo ln -s /etc/nginx/sites-available/vibedoc /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

---

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SILICONFLOW_API_KEY` | API key for AI model | `sk-xxxxxxxxxxxxx` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_TIMEOUT` | 300 | API request timeout (seconds) |
| `MCP_TIMEOUT` | 60 | MCP service timeout (seconds) |
| `ENVIRONMENT` | development | Environment mode |
| `DEBUG` | false | Enable debug logging |
| `PORT` | 7860 | Application port |
| `LOG_LEVEL` | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |

### Example .env File

```bash
# Required
SILICONFLOW_API_KEY=sk-your-actual-key-here

# Optional
API_TIMEOUT=300
MCP_TIMEOUT=60
ENVIRONMENT=production
DEBUG=false
PORT=7860
LOG_LEVEL=INFO
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 7860
lsof -i :7860

# Kill process
kill -9 <PID>

# Or use different port
PORT=7861 python app.py
```

### Module Not Found

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### API Key Not Working

1. Verify key is correct in `.env`
2. Check key is active at [siliconflow.cn](https://siliconflow.cn)
3. Ensure no extra spaces in `.env` file
4. Restart application after changing `.env`

### Permission Denied

```bash
# Linux/macOS
chmod +x app.py

# Docker
docker run --user $(id -u):$(id -g) ...
```

### Out of Memory

- Increase Docker memory limit
- Use smaller batch sizes
- Deploy on instance with more RAM

### Slow Performance

- Check network connection
- Verify API endpoint latency
- Consider using CDN for static assets
- Enable caching

---

## Health Checks

### Basic Check

```bash
curl http://localhost:7860
```

### API Check

```bash
curl -X POST http://localhost:7860/api/health
```

### Docker Health Check

Add to `Dockerfile`:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:7860/ || exit 1
```

---

## Monitoring

### Logs

```bash
# Local
tail -f logs/app.log

# Docker
docker logs -f vibedoc

# Systemd
sudo journalctl -u vibedoc -f
```

### Metrics

Consider integrating:
- **Prometheus** - Metrics collection
- **Grafana** - Visualization
- **Sentry** - Error tracking

---

## Backup

### Configuration

```bash
# Backup .env
cp .env .env.backup

# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz data/
```

### Database (if applicable)

```bash
# Export data
python scripts/export_data.py > backup.json
```

---

## Updates

### Pull Latest Changes

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Docker Update

```bash
docker-compose pull
docker-compose up -d
```

---

## Security Best Practices

1. **Never commit `.env` file** - Use `.env.example` template
2. **Use HTTPS** in production - Setup SSL/TLS certificates
3. **Restrict API access** - Use firewall rules
4. **Regular updates** - Keep dependencies current
5. **Monitor logs** - Watch for suspicious activity
6. **Backup regularly** - Automate backup process

---

## Support

- **Issues**: [GitHub Issues](https://github.com/YourUsername/VibeDoc-English/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YourUsername/VibeDoc-English/discussions)
- **Email**: support@vibedoc.example.com

---

**Last Updated**: November 2025
