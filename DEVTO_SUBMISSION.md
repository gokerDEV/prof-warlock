This is a submission for the [Postmark Challenge: Inbox Innovators](https://dev.to/challenges/postmark).

## What I Built 

**Prof. Warlock 🔮** - A magical email-driven service that creates personalized natal chart posters. Instead of filling out web forms, users simply send an email with their birth information and receive a beautiful A3 natal chart poster in return.

This project reimagines email as a powerful application interface, demonstrating how inbound email processing can create delightful user experiences for specialized services. No sign-ups, no complex forms - just the simplicity of email with the power of automated chart generation.

**Key Features:**
- 📧 **Email-First Interface**: Complete interaction through email
- 🎨 **Beautiful A3 Natal Charts**: Professional monochrome design (2480x3508px)
- ⚡ **Instant Processing**: Automated parsing and generation
- 🔒 **Privacy-Focused**: No data storage, immediate processing
- 📍 **Smart Geocoding**: Automatic location coordinate lookup
- 💌 **Intelligent Validation**: Helpful error messages for missing information

## Demo 

**Live Service**: `warlock@[your-domain].com` *(Replace with your actual domain)*

### How to Test:

1. **Send an email** to the service address with this format:
```
To: warlock@yourdomain.com
Subject: Natal Chart Request

First Name: John
Last Name: Doe
Date of Birth: 15-05-1990 08:30
Place of Birth: New York, NY
```

2. **Receive your natal chart** within seconds as a high-quality PNG attachment

3. **Test error handling** by sending incomplete information - you'll get a helpful response with the exact format needed.

### Sample Flow:
![Email Input → Processing → Natal Chart Output]

**Expected Response**: A professional email reply with your personalized natal chart attached as a beautiful A3 poster, including your coordinates and birth details.

### Demo Screenshots:
- Email input interface (any email client)
- Generated natal chart poster (monochrome, professional design)
- Error handling response (helpful formatting guide)

## Code Repository

[**GitHub Repository**](https://github.com/yourusername/prof-warlock)

The complete source code is available with:
- Full FastAPI backend implementation
- Comprehensive test suite (email parsing, chart generation, end-to-end)
- Deployment configuration for Render.com
- Detailed documentation and setup instructions

## How I Built It 

### Implementation Process

I wanted to explore how email could become more than just communication - turning it into a powerful application interface. The challenge was to create something that felt magical while being technically robust.

**Technical Architecture:**
- **Backend**: FastAPI (Python 3.13+) for webhook handling
- **Email Processing**: Postmark Inbound API for receiving emails
- **Chart Generation**: `natal` library for astrological calculations
- **Graphics**: PIL (Pillow) for poster composition and layout
- **Geocoding**: `geopy` for location coordinate lookup
- **Fonts**: Montserrat (Google Fonts) for professional typography
- **Deployment**: Render.com with automatic deployment

### Postmark Integration Experience

Postmark's inbound email processing was incredibly smooth to work with. The webhook payload structure is clean and reliable:

```python
@app.post("/webhook")
async def handle_webhook(request: Request):
    payload = await request.json()
    
    # Extract email data
    from_email = payload.get("From")
    text_body = payload.get("TextBody")
    message_id = payload.get("MessageID")
    
    # Process and respond
    await process_natal_chart_request(from_email, text_body, message_id)
```

### Key Implementation Challenges

1. **Email Parsing**: Created a robust parser that handles various email formats and extracts birth information reliably
2. **Validation Logic**: Built smart validation that provides helpful error messages when information is missing
3. **Chart Generation**: Integrated astrological calculations with custom graphics generation for beautiful output
4. **Error Handling**: Ensured graceful degradation and helpful user feedback for any issues

### Development Highlights

- **Privacy-First**: No data persistence - everything is processed in memory and discarded
- **Robust Testing**: Comprehensive test suite covering email parsing, validation, and chart generation
- **Professional Output**: A3-sized posters (2480x3508px) with careful typography and layout
- **Scalable Architecture**: Stateless design that can handle multiple requests efficiently

### Why This Approach Works

Email as an interface eliminates friction - no apps to download, no accounts to create. Users get the convenience of email with the power of specialized processing. It's particularly perfect for one-time services like natal chart generation.

The project showcases how Postmark's inbound processing can power innovative applications that feel completely natural to users while being technically sophisticated under the hood.

**Result**: A delightful user experience that turns a complex astrological service into something as simple as sending an email. 🌟

---

*Built with ✨ for the Postmark Challenge: Inbox Innovators* 