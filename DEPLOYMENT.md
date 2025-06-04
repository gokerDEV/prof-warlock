# Deployment Guide for Prof. Warlock 🚀

This guide covers deploying Prof. Warlock to Render.com using Docker.

## 🐳 Docker Deployment to Render.com

### Prerequisites
- Render.com account
- GitHub repository with Prof. Warlock code
- Postmark account with inbound processing enabled
- Domain configured for email receiving

### Step 1: Prepare Your Repository

1. **Push your code to GitHub**
```bash
git add .
git commit -m "Prepare for Docker deployment"
git push origin main
```

2. **Verify deployment files exist:**
   - ✅ `Dockerfile`
   - ✅ `render.yaml`
   - ✅ `requirements.txt` 
   - ✅ `runtime.txt`

### Step 2: Create Render Service

1. **Go to [Render.com](https://render.com)**
2. **Connect GitHub** account if not already connected
3. **Create New > Web Service**
4. **Select your repository**
5. **Configure settings:**
   - **Name**: `prof-warlock`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - Render will automatically detect the Dockerfile and use it for deployment

### Step 3: Configure Environment Variables

In your Render service settings, add these environment variables:

| Variable               | Value                    | Description                         |
| ---------------------- | ------------------------ | ----------------------------------- |
| `POSTMARK_API_KEY`     | `your_postmark_api_key`  | Your Postmark server API key        |
| `FROM_EMAIL`           | `warlock@yourdomain.com` | Email address for sending responses |
| `WEBHOOK_SECRET_TOKEN` | `your_secure_token`      | Secret token for webhook security   |
| `ENVIRONMENT`          | `production`             | Environment identifier              |
| `SAVE_INBOUND_EMAILS`  | `false`                  | Disable email saving in production  |

### Step 4: Deploy

1. **Click "Create Web Service"**
2. **Wait for Docker build and deployment** (usually 3-7 minutes)
3. **Your service will be available at**: `https://your-service-name.onrender.com`

### Step 5: Configure Postmark Webhook

1. **Go to your Postmark server settings**
2. **Navigate to "Inbound" section**
3. **Set Webhook URL to**: `https://your-service-name.onrender.com/webhook?token=your_secret_token`
4. **Test the webhook** using Postmark's test feature

## 🔧 Docker Configuration Details

### Dockerfile Features

Our Dockerfile includes:
- **Python 3.13** for latest features and performance
- **Multi-stage optimization** for smaller image size
- **Security hardening** with non-root user
- **Health checks** for monitoring
- **Dynamic port binding** for Render compatibility

### Build Process

Render will automatically:
1. **Clone your repository**
2. **Build Docker image** using your Dockerfile
3. **Deploy container** with configured environment variables
4. **Health check** using `/health` endpoint

### Local Testing

Test your Docker setup locally:

```bash
# Build the image
docker build -t prof-warlock .

# Run with environment variables
docker run -p 8000:8000 \
  -e POSTMARK_API_KEY=your_key \
  -e FROM_EMAIL=warlock@yourdomain.com \
  -e WEBHOOK_SECRET_TOKEN=your_token \
  -e PORT=8000 \
  prof-warlock
```

## 🎯 Post-Deployment Setup

### 1. Verify Health Endpoints

Test that your deployment is working:

```bash
# Basic health check
curl https://your-service.onrender.com/

# Detailed health check
curl https://your-service.onrender.com/health
```

Expected responses:
```json
// GET /
{
  "service": "Prof. Warlock",
  "status": "healthy",
  "version": "1.0.0",
  "message": "Natal chart generation service is running"
}

// GET /health  
{
  "status": "healthy",
  "timestamp": "2025-01-04T...",
  "service": "Prof. Warlock",
  "dependencies": {
    "postmark_api": "configured",
    "geocoding": "available"
  }
}
```

### 2. Test Webhook Endpoint

Test the webhook with a PING:

```bash
curl -X POST "https://your-service.onrender.com/webhook?token=your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "From": "test@example.com",
    "Subject": "ping",
    "TextBody": "ping"
  }'
```

### 3. Configure Domain Email

Set up email receiving on your domain:

1. **Add MX record** pointing to Postmark
2. **Verify domain** in Postmark
3. **Test email delivery** by sending to your configured address

## 🔍 Monitoring & Troubleshooting

### Render.com Monitoring

1. **View logs**: Render dashboard > Service > Logs
2. **Monitor performance**: Built-in metrics
3. **Set up alerts**: Configure in dashboard

### Docker-Specific Logs

Check container logs for Docker-specific issues:
- **Build logs**: Shows pip install and dependency issues
- **Runtime logs**: Shows application startup and errors
- **Health check logs**: Shows endpoint availability

### Common Issues

#### 1. Docker Build Fails
**Error**: Build fails during Docker image creation
**Solution**: 
- Check Dockerfile syntax
- Verify requirements.txt dependencies
- Ensure Python 3.13 compatibility

#### 2. Environment Variables Not Available
**Error**: `ValueError: POSTMARK_API_KEY environment variable is required`
**Solution**: Add missing environment variables in Render dashboard

#### 3. Port Binding Issues
**Error**: Container can't bind to port
**Solution**: 
- Verify `PORT` environment variable usage
- Check Dockerfile EXPOSE directive
- Ensure uvicorn binds to `0.0.0.0:$PORT`

#### 4. Health Check Failures
**Error**: Health check endpoint not responding
**Solution**: 
- Verify `/health` endpoint is accessible
- Check if application is fully started
- Review startup logs for errors

### Debug Mode

For troubleshooting, temporarily enable email saving:

```bash
# In Render environment variables
SAVE_INBOUND_EMAILS=true
```

## 🔒 Security Considerations

### Production Checklist

- ✅ Use strong webhook secret tokens
- ✅ HTTPS endpoints only
- ✅ Non-root user in Docker container
- ✅ Disable debug email saving
- ✅ Regular security updates
- ✅ Monitor webhook endpoints
- ✅ Minimal Docker image size

### Docker Security

- ✅ Non-root user (appuser:1000)
- ✅ Minimal base image (python:3.13-slim)
- ✅ No unnecessary packages
- ✅ Health checks enabled
- ✅ Proper port exposure

## 📊 Performance Optimization

### Docker Optimization

1. **Multi-stage builds** (if needed for larger applications)
2. **Layer caching** - requirements.txt copied first
3. **Minimal dependencies** - only essential packages
4. **Health checks** for proper startup detection

### Production Settings

For high-volume deployments:

```dockerfile
# In Dockerfile, you can modify the CMD to add workers
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --workers 2"]
```

## 🔄 Continuous Deployment

### Automatic Deployment

Render automatically deploys when you push to your main branch:

1. **Push to GitHub**
2. **Render detects changes**
3. **Builds new Docker image**
4. **Deploys with zero downtime**

### Manual Deployment

You can also manually trigger deployments from the Render dashboard.

---

Need help? Check the [main README](README.md) or open an issue in the repository. 