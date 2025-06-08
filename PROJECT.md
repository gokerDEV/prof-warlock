---
title: 'Project Document: Prof. Warlock'
description: 'A system to generate and email natal chart posters based on user-submitted birth information via Postmark and Python, adhering to Clean Code Principles.'
---

# Project Document: Prof. Warlock

## 1. Introduction

**Prof. Warlock** is a web service that automatically generates personalized natal chart posters based on user-submitted birth data. Users send their details via email to `warlock@yourdomain.com`. The system then parses the email, generates a natal chart using the `natal` Python library, and returns the result via email.

The application creates beautiful monochrome A3 posters featuring a natal chart, aspect matrix, and distribution analysis, all rendered with custom SVG symbols and an artistic border.

## 2. Project Goals

- Receive user birth information through email
- Extract required fields: `First Name`, `Last Name`, `Date of Birth`, and `Place of Birth`
- Validate data completeness
- Request missing information via email if needed
- Generate comprehensive natal charts using `natal==0.9.3`
- Provide detailed astrological analysis including:
  - Planetary positions and aspects
  - Element distributions
  - Modality distributions
  - Polarity distributions
  - Hemisphere distributions
- Create visually appealing A3 posters with:
  - Main natal chart
  - Aspect matrix
  - Distribution analysis sections
  - Custom SVG symbols
  - Artistic border elements
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
   - Calculates planetary positions using `natal`
   - Generates aspect matrix
   - Analyzes distributions
   - Creates SVG-based visualizations
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
                        ↓
                    Calculate Positions
                        ↓
                    Generate Aspects
                        ↓
                    Analyze Distributions
                        ↓
                    Create Visualization
                        ↓
                    Send Email with Chart
```

## 4. MVP Feature Set

- Email-driven interaction
- Line-by-line field parsing
- Basic validation for completeness
- Automated response for missing data
- Comprehensive chart generation with `natal`
- Distribution analysis (elements, modalities, polarities, hemispheres)
- Aspect matrix visualization
- Custom SVG symbol rendering
- Email delivery with Postmark
- Simple webhook integration

## 5. Technical Details

### 5.1 Input Format

Users must provide birth information in this exact format:

```
First Name: John
Last Name: Doe
Date of Birth: 15-06-1985 08:30
Place of Birth: New York, NY
```

Parsing is performed line-by-line using simple regex.

### 5.2 Parsing & Validation

- Extract values using strict keys
- Ensure all fields are non-empty
- Basic format checks for date and location

### 5.3 Chart Generation

- Use `natal==0.9.3` for calculations
- Accept city, region, country format (assume built-in geolocation)
- Generate comprehensive analysis:
  - Planetary positions
  - House placements
  - Aspect calculations
  - Distribution analysis
- Output a high-quality A3 poster (PNG)

### 5.4 Visualization Components

- **Main Chart**:
  - House divisions
  - Planetary positions
  - Zodiac signs
  - Custom SVG symbols
- **Aspect Matrix**:
  - Planetary relationships
  - Symbol-based representation
- **Distribution Analysis**:
  - Elements section
  - Modalities section
  - Polarities section
  - Hemispheres section
- **Design Elements**:
  - Artistic border
  - Corner decorations
  - Professional typography

### 5.5 Stack Overview

- **Language**: Python 3.13+
- **Libraries**: 
  - FastAPI for API
  - Pillow for image processing
  - CairoSVG for SVG rendering
  - natal for calculations
  - python-postmark for email
- **Platform**: Render
- **Version Control**: Git

### 5.6 Services Structure

- **NatalChartService**: Main chart generation
- **ElementDistributionService**: Element analysis
- **DistributionService**: Modality, polarity, hemisphere analysis
- **AspectMatrixService**: Aspect matrix creation
- **SVGPathService**: Symbol rendering
- **ZodiacService**: Sign calculations

## 6. Clean Code Principles

- **Meaningful Names**: Clear and descriptive
- **Single Responsibility**: Each service handles one aspect
- **Readable Code**: Minimal, meaningful comments
- **Avoid Duplication**: Common utilities shared
- **Keep it Simple**: Clear service boundaries
- **Testable Code**: Comprehensive test suite

## 7. Error Handling

- If parsing fails → send missing info email
- If `natal` fails → log error, notify user
- If SVG rendering fails → fallback to basic symbols
- Assume Postmark delivery is reliable

## 8. Deployment Plan

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: `POSTMARK_API_KEY`, etc.
- **Assets**: SVG files in assets directory

## 9. Project Structure

```
prof_warlock/
├── src/
│   ├── api/
│   │   └── main.py
│   ├── services/
│   │   ├── natal_chart_service.py
│   │   ├── element_distribution_service.py
│   │   ├── distribution_service.py
│   │   ├── aspect_matrix_service.py
│   │   ├── svg_path_service.py
│   │   └── zodiac_service.py
│   └── tests/
│       └── test_suite.py
├── assets/
│   ├── svg_paths/
│   │   └── *.svg
│   └── template.svg
├── requirements.txt
└── README.md
```

## 10. Timeline & Milestones

**Total Duration**: ~1 week

- **Phase 0: Setup** (1 day)
  - Repository setup
  - Service structure
  - Basic API endpoints

- **Phase 1: Core Features** (2 days)
  - Chart calculation
  - Distribution analysis
  - Aspect matrix

- **Phase 2: Visualization** (2 days)
  - SVG symbol rendering
  - Layout implementation
  - Design integration

- **Phase 3: Polish & Launch** (2 days)
  - Testing & refinement
  - Documentation
  - Deployment

## 🆕 Custom Features for GPT Integration

- **AWS S3 Integration**: Images are uploaded to AWS S3 for storage, ensuring scalability and reliability.
- **Enhanced Response Format**: The `/natal-chart` endpoint now returns a structured response with a download link to the generated image, rather than embedding the image directly in the response.
- **Improved Image Handling**: Images are resized to a maximum dimension of 1500px before being uploaded to S3, optimizing for quality and performance.
