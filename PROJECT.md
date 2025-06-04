---
title: 'Project Document: Prof. Warlock'
description: 'A system to generate and email natal chart posters based on user-submitted birth information via Postmark and Python, adhering to Clean Code Principles.'
---

# Project Document: Prof. Warlock

## 1. Introduction

**Prof. Warlock** is a web service that automatically generates personalized natal chart posters based on user-submitted birth data. Users send their details via email to `warlock@yourdomain.com`. The system then parses the email, generates a natal chart using the `natal` Python library, and returns the result via email.

This project builds upon the earlier `prof-postmark` system, now refactored without OpenAI integration. The application will be deployed on **Render**.

## 2. Project Goals

- Receive user birth information through email
- Extract required fields: `First Name`, `Last Name`, `Date of Birth`, and `Place of Birth`
- Validate data completeness
- Request missing information via email if needed
- Generate natal charts using `natal==0.9.3`
- Email the resulting chart to users
- Deploy on **Render**
- Follow Clean Code principles for maintainability and readability

## 3. System Architecture & Workflow

The service operates via an event-driven flow triggered by **Postmark** webhooks:

1. **Email Submission**: User sends an email to `warlock@yourdomain.com`
2. **Webhook Activation**: Postmark parses and forwards the email (as JSON) to our webhook endpoint
3. **Email Parsing & Validation**:
   - Extracts and validates required fields
4. **Missing Info Handling**:
   - If incomplete, replies via Postmark with a request for missing fields
5. **Chart Generation**:
   - If valid, calls the `natal` library to generate a chart
6. **Email Delivery**:
   - Sends the chart as an attachment using Postmark

### Visual Flow

```
User --> warlock@yourdomain.com
        ↓
    Postmark (Inbound Webhook)
        ↓
  Prof. Warlock (Render App)
      ↓          ↓
Parse Email   [Check for Missing Info]
     ↓              ↓
[Send Info Request] OR [Generate Chart]
     ↓                        ↓
                   Send Email with Chart
```

## 4. MVP Feature Set

- Email-driven interaction
- Line-by-line field parsing
- Basic validation for completeness
- Automated response for missing data
- Chart generation with `natal`
- Email delivery with Postmark
- Simple webhook integration

## 5. Technical Details

### 5.1 Input Format

Users must provide birth information in this exact format:

```
First Name: John
Last Name: Doe
Date of Birth: 15-06-1985
Place of Birth: New York, NY
```

Parsing is performed line-by-line using simple regex.

### 5.2 Parsing & Validation

- Extract values using strict keys
- Ensure all fields are non-empty
- Basic format checks for date and location

### 5.3 Chart Generation

- Use `natal==0.9.3`
- Accept city, region, country format (assume built-in geolocation)
- Output a poster (e.g., PNG)

### 5.4 Email Templates

**Missing Information**
> _"Dear [Name], some information is missing. Please reply using the format: First Name: ..., etc."_

**Chart Delivery**
> _"Dear [Name], your natal chart is ready! (Poster attached)"_

### 5.5 Stack Overview

- **Language**: Python 3.9+
- **Libraries**: Flask, python-postmark, natal, python-dotenv
- **Platform**: Render
- **Version Control**: Git

### 5.6 Base Refactor

- Remove OpenAI code
- Focus webhook logic on strict parsing
- Add `natal` integration
- Configure Postmark templates

## 6. Clean Code Principles

- **Meaningful Names**: Clear and descriptive
- **Single Responsibility**: Small, focused functions
- **Readable Code**: Minimal, meaningful comments
- **Avoid Duplication**: Reuse logic where possible
- **Keep it Simple**: No overengineering
- **AI Code Review**: Manually vet AI-generated logic

## 7. Error Handling

- If parsing fails → send missing info email
- If `natal` fails → log error, notify user
- Assume Postmark delivery is reliable

## 8. Deployment Plan

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Environment Variables**: `POSTMARK_SERVER_TOKEN`, etc.
- **Temporary Files**: Save charts to `/tmp/`, auto-cleaned

## 9. Project Structure

```
prof_warlock/
├── app.py
├── requirements.txt
├── .env
└── README.md
```

## 10. Timeline & Milestones

**Total Duration**: ~2 hours

- **Phase 0: Setup** (10 mins)
  - Repo init, Render app, inbound webhook

- **Phase 1: Parsing & Reply** (20 mins)
  - Email parsing + missing info reply logic

- **Phase 2: Chart Generation** (60 mins)
  - Integrate and test `natal`

- **Phase 3: Email Delivery & Launch** (30 mins)
  - Attach chart and send via Postmark
