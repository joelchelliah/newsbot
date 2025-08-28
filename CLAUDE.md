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
- **newsbot.py**: Flask web server with REST endpoints for article display, rating, and triggering news processing
- **config.py**: Environment configuration and validation using dataclasses
- **_types.py**: TypeScript-style type definitions for preferences and article data
- **utils.py**: Shared utilities for template rendering and content extraction
- **templates/**: HTML templates for web article display and email (when enabled)

### Services Layer (/services)
- **AIService**: OpenAI integration for article selection, summarization, and preference learning using embeddings
- **NewsApiService**: News API integration for fetching articles
- **NotificationService**: Unified push notifications (ntfy.sh) and optional email sending

### Data Layer (/stores)
- **PreferencesStore**: Manages user preferences with semantic embeddings (Supabase backend)
- **ArticlesStore**: Full article storage with 30-day retention for web display and rating

### Key Features
- **Web-First Experience**: Mobile-responsive article pages with full content display and interactive rating
- **Push Notifications**: ntfy.sh integration with direct links to web articles  
- **Embedding-based Preference System**: Uses OpenAI embeddings for semantic similarity matching
- **Interactive Rating System**: 3-star rating (1-3) via web interface with localStorage duplicate prevention
- **Template System**: Clean separation of HTML templates and business logic
- **Background Processing**: Non-blocking preference updates with immediate user feedback
- **Preference Scoring**: -5 to 5 scale where negative scores indicate dislikes, positive indicate likes

### Environment Variables Required
**Always Required:**
- `OPENAI_API_KEY`: OpenAI API access
- `NEWS_API_KEY`: NewsAPI.org access  
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`: Supabase database access
- `NEWSBOT_DOMAIN`: Domain for web article links (e.g., https://yourapp.onrender.com)

**Optional:**
- `NTFY_TOPIC`: ntfy.sh topic name for push notifications
- `NEWSBOT_EMAIL_ENABLED`: Set to 'true' to enable email notifications (default: false)
- `FROM_EMAIL`, `TO_EMAIL`, `SMTP_PASS`: Gmail SMTP configuration (only if email enabled)
- `NEWSBOT_DEFAULT_PREFERENCES`: Initial preferences JSON

### API Endpoints
- `POST /trigger`: Main newsbot execution (fetch, select, summarize, store, notify)
- `GET /article/<article_id>`: Display full article with interactive rating interface
- `POST /article/<article_id>/rate/<rating>`: Submit article rating (1-3 stars) via AJAX
- `GET /preferences`: Retrieve current preferences with embeddings

### Dependencies
- Flask web framework with Gunicorn for production
- OpenAI client (>=1.0.0) for AI services and embeddings
- Supabase for preference/summary storage
- newspaper3k for article content extraction
- Zod validation for API responses
- numpy for embedding calculations
