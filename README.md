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
Date of Birth: 15-05-1990
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
Date of Birth: ...
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

### Test Coverage

- ✅ Email parsing and validation
- ✅ User information extraction
- ✅ Natal chart generation
- ✅ Health check endpoints
- ✅ Webhook ping/pong
- ✅ End-to-end workflow with real data

## 📁 Project Structure

```
prof-warlock/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI application
│   │   └── webhook_handler.py   # Webhook processing logic
│   ├── core/
│   │   ├── configuration.py     # Environment configuration
│   │   └── domain_models.py     # Data models
│   └── services/
│       ├── email_parser.py      # Email content parsing
│       ├── email_service.py     # Email sending logic
│       ├── natal_chart_service.py # Chart generation
│       └── validation_service.py # Input validation
├── assets/fonts/static/         # Montserrat fonts
├── tests/                       # Test suite
├── requirements.txt             # Python dependencies
├── render.yaml                  # Render.com deployment config
├── Procfile                     # Process configuration
└── README.md                    # This file
```

## 🎯 About the Postmark Challenge

This project was created for the [Postmark Challenge: Inbox Innovators](https://postmarkapp.com/blog/announcing-the-postmark-challenge-inbox-innovators), which challenged developers to build innovative applications using Postmark's inbound email processing capabilities.

**Challenge Goals:**
- 💡 Reimagine email as an interactive application interface
- 🔧 Showcase the power of inbound email processing
- 🚀 Build something unique and useful

Prof. Warlock demonstrates how email can become a powerful user interface for specialized services, eliminating the need for traditional web forms while providing a delightful user experience.

## 🛠️ Technical Stack

- **Backend**: FastAPI (Python)
- **Email Processing**: Postmark Inbound API
- **Astrology**: `natal` library for chart generation
- **Graphics**: PIL (Pillow) for poster composition
- **Geocoding**: `geopy` for location lookup
- **Fonts**: Montserrat (Google Fonts)
- **Deployment**: Render.com

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Acknowledgments

- [Postmark](https://postmarkapp.com) for excellent inbound email processing
- [DEV.to](https://dev.to) for hosting the Inbox Innovators challenge
- The `natal` library for astrological calculations
- Google Fonts for the beautiful Montserrat typeface

---

Made with ✨ for the Postmark Challenge: Inbox Innovators
