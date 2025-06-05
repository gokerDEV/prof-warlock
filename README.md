# Prof. Warlock 🔮

**Natal Chart Generator via Email** - A magical email-driven service that creates personalized natal chart posters.

Built for the [Postmark Challenge: Inbox Innovators](https://postmarkapp.com/blog/announcing-the-postmark-challenge-inbox-innovators) - exploring the power of inbound email processing to create unique user experiences.

---

## ✨ What is Prof. Warlock?

Prof. Warlock is an innovative email-first application that generates beautiful natal charts by simply sending an email. No complex web forms, no sign-ups - just send your birth information via email and receive a stunning A3 poster of your natal chart in return.

## 🌟 Features

- **📧 Email-Driven Workflow**: Complete interaction through email
- **🎨 Beautiful A3 Natal Charts**: Monochrome design with custom layout
- **⚡ Instant Processing**: Automated parsing and generation
- **🔒 Privacy-Focused**: No data storage, immediate processing
- **📍 Geocoding Integration**: Automatic location coordinate lookup
- **💌 Smart Validation**: Helpful error messages for missing information

## 🔄 User Flow

### 1. Send Email with Birth Information
Send an email to the configured address with your birth details:

```
To: warlock@yourdomain.com
Subject: Natal Chart Request

First Name: John
Last Name: Doe
Date of Birth: 15-05-1990 08:30
Place of Birth: New York, NY
```

### 2. Automatic Processing
Prof. Warlock automatically:
- ✅ Parses your email content
- ✅ Validates all required fields
- ✅ Geocodes your birth location
- ✅ Generates your natal chart

### 3. Receive Your Chart
Within moments, you'll receive:
- 📧 A reply email with your natal chart attached
- 🖼️ High-quality A3 PNG poster (2480x3508px)
- 🎨 Professional monochrome design
- 📍 Your coordinates and birth details beautifully formatted

### Error Handling
If information is missing, you'll receive a helpful email with the exact format needed:

```
Dear John,

Some information is missing. Please reply using the format:
First Name: ...
Last Name: ...
Date of Birth: DD-MM-YYYY HH:MM
Place of Birth: ...

Best regards,
Prof. Warlock
```

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Postmark account with inbound email processing
- Domain configured for email receiving

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/prof-warlock.git
cd prof-warlock
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your settings
```

Required environment variables:
```env
POSTMARK_API_KEY=your_postmark_api_key
FROM_EMAIL=warlock@yourdomain.com
WEBHOOK_SECRET_TOKEN=your_webhook_secret
ENVIRONMENT=development
SAVE_INBOUND_EMAILS=true
```

5. **Run the application**
```bash
uvicorn src.api.main:app --reload
```

## 🌐 Deployment on Render.com

### Automatic Deployment

1. **Fork this repository**
2. **Connect to Render.com**
   - Go to [Render.com](https://render.com)
   - Connect your GitHub account
   - Select this repository

3. **Configure Environment Variables**
   Set these in your Render service settings:
   ```
   POSTMARK_API_KEY=your_api_key
   FROM_EMAIL=warlock@yourdomain.com  
   WEBHOOK_SECRET_TOKEN=your_secret
   ENVIRONMENT=production
   SAVE_INBOUND_EMAILS=false
   ```

4. **Deploy**
   - Render will automatically use `render.yaml` configuration
   - Your service will be available at: `https://your-service.onrender.com`

### Manual Deployment

If you prefer manual configuration:

```yaml
# render.yaml
services:
  - type: web
    name: prof-warlock
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"
    healthCheckPath: /health
```

## 🔧 Postmark Configuration

### 1. Set up Inbound Email Processing

1. **Create Inbound Server** in Postmark
2. **Configure Webhook URL**: `https://your-domain.com/webhook?token=your_secret_token`
3. **Set up Domain** for receiving emails (e.g., `warlock@yourdomain.com`)

### 2. Webhook Configuration

The service expects Postmark webhook payloads with:
- `From`: Sender email
- `FromName`: Sender name  
- `Subject`: Email subject
- `TextBody`: Email body with birth information
- `MessageID`: For reply threading

## 🧪 Testing

Run the test suite:

```bash
# All tests
python -m pytest

# Specific test
python -m pytest src/tests/test_system.py::test_natal_chart_creation -v

# With output
python -m pytest src/tests/ -v -s
```

Running the tests creates images like `test_results/natal_chart_test.png` and
`test_end_to_end_chart.png` for manual inspection. These files are not tracked in
version control.
