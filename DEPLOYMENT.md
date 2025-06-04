# Deployment Guide for Prof. Warlock 🚀

This guide covers deploying Prof. Warlock to production environments, with a focus on Render.com.

## 🌐 Render.com Deployment (Recommended)

### Prerequisites
- Render.com account
- GitHub repository with Prof. Warlock code
- Postmark account with inbound processing enabled
- Domain configured for email receiving

### Step 1: Prepare Your Repository

1. **Push your code to GitHub**
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

2. **Verify deployment files exist:**
   - ✅ `render.yaml`
   - ✅ `requirements.txt` 
   - ✅ `Procfile`
   - ✅ `runtime.txt`

### Step 2: Create Render Service

1. **Go to [Render.com](https://render.com)**
2. **Connect GitHub** account if not already connected
3. **Create New > Web Service**
4. **Select your repository**
5. **Configure settings:**
   - **Name**: `prof-warlock`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

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
2. **Wait for deployment** (usually 2-5 minutes)
3. **Your service will be available at**: `https://your-service-name.onrender.com`

### Step 5: Configure Postmark Webhook

1. **Go to your Postmark server settings**
2. **Navigate to "Inbound" section**
3. **Set Webhook URL to**: `https://your-service-name.onrender.com/webhook?token=your_secret_token`
4. **Test the webhook** using Postmark's test feature

## 🔧 Alternative Deployment Options

### Heroku

1. **Create Heroku app**
```bash
heroku create prof-warlock-app
```

2. **Set environment variables**
```bash
heroku config:set POSTMARK_API_KEY=your_key
heroku config:set FROM_EMAIL=warlock@yourdomain.com
heroku config:set WEBHOOK_SECRET_TOKEN=your_token
heroku config:set ENVIRONMENT=production
heroku config:set SAVE_INBOUND_EMAILS=false
```

3. **Deploy**
```bash
git push heroku main
```

### Railway

1. **Connect GitHub repository**
2. **Set environment variables in dashboard**
3. **Deploy automatically**

### Docker Deployment

1. **Create Dockerfile**
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Build and run**
```bash
docker build -t prof-warlock .
docker run -p 8000:8000 --env-file .env prof-warlock
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

### Common Issues

#### 1. Environment Variables Not Set
**Error**: `ValueError: POSTMARK_API_KEY environment variable is required`
**Solution**: Add missing environment variables in Render dashboard

#### 2. Webhook Authentication Fails
**Error**: 401 Unauthorized
**Solution**: Verify webhook URL includes correct token parameter

#### 3. Email Not Processing
**Error**: No response to emails
**Solution**: 
- Check webhook URL in Postmark
- Verify domain MX records
- Check service logs for errors

#### 4. Dependency Installation Fails
**Error**: Build fails during pip install
**Solution**: 
- Verify `requirements.txt` format
- Check Python version in `runtime.txt`

### Debug Mode

For troubleshooting, temporarily enable email saving:

```bash
# In Render environment variables
SAVE_INBOUND_EMAILS=true
```

This will save incoming webhook payloads for analysis.

## 🔒 Security Considerations

### Production Checklist

- ✅ Use strong webhook secret tokens
- ✅ HTTPS endpoints only
- ✅ Disable debug email saving
- ✅ Regular security updates
- ✅ Monitor webhook endpoints
- ✅ Implement rate limiting if needed

### Environment Variables Security

- ✅ Never commit `.env` files
- ✅ Use platform secret management
- ✅ Rotate tokens regularly
- ✅ Minimum required permissions

## 📊 Performance Optimization

### Production Settings

For high-volume deployments:

1. **Increase worker processes**
```bash
# In start command
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --workers 4
```

2. **Enable logging**
```python
# In configuration
LOGGING_LEVEL=INFO
```

3. **Consider caching**
- Geocoding results
- Font loading
- Template rendering

## 🔄 Continuous Deployment

### GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        # Render automatically deploys on git push
        run: echo "Deployment handled by Render"
```

---

Need help? Check the [main README](README.md) or open an issue in the repository. 