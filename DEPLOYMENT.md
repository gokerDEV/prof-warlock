# Deployment Guide for Prof. Warlock 🚀

This guide covers deploying Prof. Warlock using Docker to multiple cloud platforms.

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

## ☁️ Docker Deployment to Google Cloud Run

### Prerequisites
- Google Cloud Platform (GCP) account with billing enabled
- `gcloud` command-line tool installed and configured ([Install Guide](https://cloud.google.com/sdk/docs/install))
- Docker installed locally ([Install Guide](https://docs.docker.com/get-docker/))
- Google Container Registry (GCR) or Artifact Registry API enabled in your GCP project
- GitHub repository with Prof. Warlock code
- Postmark account with inbound processing enabled
- Domain configured for email receiving

### Step 1: Prepare Your Repository

1. **Push your code to GitHub**
```bash
git add .
git commit -m "Prepare for Google Cloud Run Docker deployment"
git push origin main
```

2. **Verify deployment files exist:**
   - ✅ `Dockerfile`
   - ✅ `requirements.txt`
   - (Optional) `.gcloudignore` file (similar to `.gitignore`, but for gcloud deployments)

**Note**: `render.yaml` and `runtime.txt` are specific to other platforms and are not directly used by Google Cloud Run when deploying a Docker container.

### Step 2: Build and Push Docker Image

1. **Enable Artifact Registry API** (recommended) in your GCP project.

2. **Configure Docker authentication:**
```bash
gcloud auth configure-docker
# For Artifact Registry, specify region:
gcloud auth configure-docker [REGION]-docker.pkg.dev
```

3. **Build your Docker image:**
```bash
# For Artifact Registry (Recommended)
docker build -t [REGION]-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME]:latest .
# Example: docker build -t us-central1-docker.pkg.dev/my-gcp-project/prof-warlock-repo/prof-warlock:latest .

# For Google Container Registry (GCR)
# docker build -t gcr.io/[PROJECT_ID]/[IMAGE_NAME]:latest .
```

4. **Push the Docker image:**
```bash
# For Artifact Registry
docker push [REGION]-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME]:latest

# For Google Container Registry (GCR)
# docker push gcr.io/[PROJECT_ID]/[IMAGE_NAME]:latest
```

### Step 3: Deploy to Google Cloud Run

**Deploy the container image to Cloud Run:**
```bash
gcloud run deploy [SERVICE_NAME] \
  --image [IMAGE_URL] \
  --platform managed \
  --region [REGION] \
  --allow-unauthenticated \
  --port 8000
```

- `--allow-unauthenticated` makes your service publicly accessible
- `--port 8000` should match your application's listening port

### Step 4: Configure Environment Variables

Set environment variables during deployment:

```bash
gcloud run deploy [SERVICE_NAME] \
  --image [IMAGE_URL] \
  --platform managed \
  --region [REGION] \
  --allow-unauthenticated \
  --port 8000 \
  --set-env-vars="POSTMARK_API_KEY=your_postmark_api_key,FROM_EMAIL=warlock@yourdomain.com,WEBHOOK_SECRET_TOKEN=your_secure_token,ENVIRONMENT=production,SAVE_INBOUND_EMAILS=false"
```

| Variable               | Value                    | Description                         |
| ---------------------- | ------------------------ | ----------------------------------- |
| `POSTMARK_API_KEY`     | `your_postmark_api_key`  | Your Postmark server API key        |
| `FROM_EMAIL`           | `warlock@yourdomain.com` | Email address for sending responses |
| `WEBHOOK_SECRET_TOKEN` | `your_secure_token`      | Secret token for webhook security   |
| `ENVIRONMENT`          | `production`             | Environment identifier              |
| `SAVE_INBOUND_EMAILS`  | `false`                  | Disable email saving in production  |
| `PORT`                 | `8000`                   | Port the application listens on     |

**Note**: For secrets like API keys, it's recommended to use Google Cloud Secret Manager.

### Step 5: Note Your Service URL

After successful deployment, your service URL will be:
`https://[SERVICE_NAME]-[PROJECT_HASH]-[REGION].a.run.app`

### Step 6: Configure Postmark Webhook

1. **Go to your Postmark server settings**
2. **Navigate to "Inbound" section**
3. **Set Webhook URL to**: `https://[SERVICE_NAME]-[PROJECT_HASH]-[REGION].a.run.app/webhook?token=your_secure_token`
4. **Test the webhook** using Postmark's test feature

## 🔧 Docker Configuration Details

### Dockerfile Features

Our Dockerfile includes:
- **Python 3.13** for latest features and performance
- **Multi-stage optimization** for smaller image size
- **Security hardening** with non-root user
- **Health checks** for monitoring
- **Dynamic port binding** for cloud platform compatibility
- **Cairo dependencies** for natal chart generation

### Build Process

#### Render.com
Render will automatically:
1. **Clone your repository**
2. **Build Docker image** using your Dockerfile
3. **Deploy container** with configured environment variables
4. **Health check** using `/health` endpoint

#### Google Cloud Run
If using pre-built images:
1. **Cloud Run pulls** your Docker image from Artifact Registry/GCR
2. **Deploys container** with configured environment variables and port
3. **Manages scaling** and request handling automatically

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
curl https://your-service-url/

# Detailed health check
curl https://your-service-url/health
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
curl -X POST "https://your-service-url/webhook?token=your_token" \
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

### Platform-Specific Monitoring

#### Render.com
1. **View logs**: Render dashboard > Service > Logs
2. **Monitor performance**: Built-in metrics
3. **Set up alerts**: Configure in dashboard

#### Google Cloud Run
1. **View logs**: Google Cloud Console > Cloud Run > Select service > Logs tab
2. **Monitor performance**: Cloud Run > Service > Metrics tab
3. **Set up alerts**: Configure in Cloud Monitoring

### Common Issues

#### 1. Docker Build Fails
**Error**: Build fails during Docker image creation
**Solution**: 
- Check Dockerfile syntax
- Verify requirements.txt dependencies
- Ensure Python 3.13 compatibility
- Verify Cairo dependencies are installed

#### 2. Environment Variables Not Available
**Error**: `ValueError: POSTMARK_API_KEY environment variable is required`
**Solution**: 
- **Render**: Add missing environment variables in dashboard
- **Cloud Run**: Use `--set-env-vars` or update via Console

#### 3. Port Binding Issues
**Error**: Container can't bind to port or doesn't respond
**Solution**: 
- Verify `PORT` environment variable usage
- Check Dockerfile EXPOSE directive
- Ensure uvicorn binds to `0.0.0.0:$PORT`
- **Cloud Run**: Ensure `--port` matches your app's listening port

#### 4. Health Check Failures
**Error**: Health check endpoint not responding
**Solution**: 
- Verify `/health` endpoint is accessible
- Check if application is fully started
- Review startup logs for errors

#### 5. Cairo Library Issues
**Error**: `OSError: no library called "cairo-2" was found`
**Solution**: 
- Ensure Cairo dependencies are in Dockerfile
- Rebuild and redeploy image

### Debug Mode

For troubleshooting, temporarily enable email saving:

```bash
# Render: In environment variables
SAVE_INBOUND_EMAILS=true

# Cloud Run: Update service
gcloud run services update [SERVICE_NAME] --region [REGION] --update-env-vars SAVE_INBOUND_EMAILS=true
```

## 🔒 Security Considerations

### Production Checklist

- ✅ Use strong webhook secret tokens
- ✅ HTTPS endpoints only (provided by both platforms)
- ✅ Non-root user in Docker container
- ✅ Disable debug email saving
- ✅ Regular security updates
- ✅ Monitor webhook endpoints
- ✅ Minimal Docker image size

### Platform-Specific Security

#### Render.com
- ✅ Environment variables encrypted at rest
- ✅ Automatic HTTPS/TLS
- ✅ DDoS protection

#### Google Cloud Run
- ✅ Use Google Cloud Secret Manager for sensitive data
- ✅ Configure appropriate IAM roles (principle of least privilege)
- ✅ VPC connectivity if needed
- ✅ Binary authorization for image security

### Docker Security

- ✅ Non-root user (appuser:1000)
- ✅ Minimal base image (python:3.13-slim)
- ✅ No unnecessary packages
- ✅ Health checks enabled
- ✅ Proper port exposure

## 📊 Performance Optimization

### Docker Optimization

1. **Multi-stage builds** for smaller final images
2. **Layer caching** - requirements.txt copied first
3. **Minimal dependencies** - only essential packages
4. **Health checks** for proper startup detection

### Platform-Specific Settings

#### Render.com
```dockerfile
# In Dockerfile, you can modify the CMD to add workers
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --workers 2"]
```

#### Google Cloud Run
- **Concurrency**: Adjust max concurrent requests per container instance
- **CPU Allocation**: Choose between request-time or always-allocated CPU
- **Min/Max Instances**: Configure auto-scaling to reduce cold starts

## 🔄 Continuous Deployment

### Render.com
Automatic deployment when you push to your main branch:
1. **Push to GitHub**
2. **Render detects changes**
3. **Builds new Docker image**
4. **Deploys with zero downtime**

### Google Cloud Run
#### Automatic Deployment with Cloud Build
1. **Create `cloudbuild.yaml`** in your repository
2. **Create Cloud Build trigger** for your GitHub repository
3. **Automatic CI/CD** on git push:
   - Clone repository
   - Build Docker image
   - Push to Artifact Registry
   - Deploy to Cloud Run

#### Manual Deployment
```bash
gcloud run deploy [SERVICE_NAME] --image [NEW_IMAGE_URL]
```

---

Need help? Check the [main README](README.md) or open an issue in the repository. 