# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Local development server
python3 newsbot.py

# Manual trigger (test endpoint)
curl -X POST http://localhost:3000/trigger
```

### Testing
```bash
# Run all tests
python3 run_tests.py
```

### Production Deployment
- Deployed to Render.com using `render.yaml` configuration
- Uses Gunicorn as WSGI server: `gunicorn newsbot:app`

## Architecture

### Core Application Structure
- **newsbot.py**: Flask web server with REST endpoints for triggering news processing and managing preferences
- **config.py**: Environment configuration and validation using dataclasses
- **_types.py**: TypeScript-style type definitions for preferences with embeddings

### Services Layer (/services)
- **AIService**: OpenAI integration for article selection, summarization, and preference learning using embeddings
- **NewsApiService**: News API integration for fetching articles
- **EmailService**: SMTP email sending with rating links

### Data Layer (/stores)
- **PreferencesStore**: Manages user preferences with semantic embeddings (Supabase backend)
- **SummariesStore**: Temporary storage for article summaries and rating functionality

### Key Features
- **Embedding-based Preference System**: Uses OpenAI embeddings for semantic similarity matching
- **Rating System**: 3-star rating system (1-3) via email links that updates preferences
- **Preference Scoring**: -5 to 5 scale where negative scores indicate dislikes, positive indicate likes

### Environment Variables Required
- `OPENAI_API_KEY`: OpenAI API access
- `NEWS_API_KEY`: NewsAPI.org access
- `FROM_EMAIL`, `TO_EMAIL`, `SMTP_PASS`: Gmail SMTP configuration
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`: Supabase database access
- `NEWSBOT_DEFAULT_PREFERENCES`: Initial preferences JSON (optional)

### API Endpoints
- `POST /trigger`: Main newsbot execution (fetch, select, summarize, email)
- `GET /preferences`: Retrieve current preferences with embeddings
- `GET /r<rating>/<summary_id>`: Submit article rating (1-3 stars)

### Dependencies
- Flask web framework with Gunicorn for production
- OpenAI client (>=1.0.0) for AI services and embeddings
- Supabase for preference/summary storage
- newspaper3k for article content extraction
- Zod validation for API responses
- numpy for embedding calculations
