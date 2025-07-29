# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a YouTube video analysis web application built with Flask that allows users to analyze YouTube content through keyword searches and trending video analysis. The application provides insights into video performance metrics, channel statistics, and content trends for Korean YouTube market analysis.

## Development Commands

### Setup and Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Then edit .env with your values

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Running the Application
```bash
# Development server
python app.py  # Runs on http://localhost:8000

# Production with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Database Management
```bash
# Create new migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Downgrade database
flask db downgrade
```

## Code Architecture

### Application Structure
- **Flask Web Framework**: Main application with modular blueprint architecture
- **SQLAlchemy ORM**: Database models with Flask-Migrate for schema management
- **YouTube Data API v3**: Integration with retry logic and quota management
- **Flask-Login**: User authentication system with Google OAuth support
- **Flask-Caching**: Redis/simple cache for API response optimization

### Key Components

#### Core Application (`app.py`)
- Flask app initialization with extensions (SQLAlchemy, Migrate, Login Manager, Cache)
- Blueprint registration for modular routing
- Custom Jinja2 filters (e.g., `human_format` for Korean number formatting)

#### Database Models (`models/`)
- **User**: User accounts with Google OAuth integration
- **ApiKey**: User-owned YouTube API keys with encryption
- **AdminApiKey**: Fallback API keys managed by administrators
- Implements a hybrid key management system (user keys → admin keys)

#### Service Layer (`services/`)
- **youtube_service.py**: Core YouTube API integration with retry logic and error handling
- **youtube_api.py**: Low-level API wrapper functions
- **video_processor.py**: Video data enrichment and processing
- **visitor_stats.py**: Analytics and visitor tracking

#### Routes (`routes/`)
- **main_routes**: Video search, trending videos, CSV export
- **auth_routes**: Login/logout, Google OAuth flow
- **channel_routes**: Channel-specific video listings
- **admin_routes**: Administrative dashboard and API key management

### Authentication & API Key System

The application uses a hybrid API key management approach:
1. **User Keys**: Authenticated users can register their own YouTube API keys
2. **Admin Keys**: Fallback keys for public/unauthenticated access
3. **Smart Rotation**: Automatic key switching on quota exhaustion
4. **Encryption**: API keys are encrypted at rest using Fernet

### Key Features

#### Search & Analysis
- Real-time YouTube video search with filtering (date, duration, channel size)
- Trending video analysis by category for Korean market
- Automatic tag extraction and recommendation
- Performance metrics calculation (views/day, like rate, engagement)

#### Data Export
- CSV export with comprehensive video metrics
- Thumbnail download functionality
- Batch processing for large result sets (up to 250 videos)

#### Caching Strategy
- Response caching for expensive API calls (30-60 minute TTL)
- Channel statistics caching (12 hours)
- Memory-based caching with Redis support

## Configuration

### Environment Variables (.env)
```bash
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app.db  # or MySQL/PostgreSQL URL
ENCRYPTION_KEY=your-fernet-key  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
ADMIN_EMAIL=admin@example.com
```

### Database Configuration
- Default: SQLite for development
- Production: MySQL/PostgreSQL via DATABASE_URL
- Migrations handled by Flask-Migrate with naming conventions

## API Integration Details

### YouTube API Error Handling
- Automatic retry on quota exceeded (up to 3 attempts)
- Key deactivation on permanent failures
- Graceful fallback to alternative keys
- Comprehensive error logging

### Rate Limiting & Optimization
- Batch API requests (50 items per call)
- Intelligent caching to minimize API usage
- Pagination support for large result sets
- Automatic key rotation on quota limits

## Frontend Integration

- Server-side rendered templates with Jinja2
- TailwindCSS for styling (see tailwind.config.js)
- HTMX for dynamic interactions without full page reloads
- Responsive design optimized for mobile and desktop

## Testing & Development

### Local Development Tips
- Use SQLite for quick local setup
- Monitor API quota usage in Google Cloud Console
- Check application logs for API errors and key rotation events
- Use Flask debug mode for detailed error messages

### Common Tasks
```bash
# Check current migrations
flask db current

# Create admin user (implement in flask shell)
flask shell
>>> from models import db, User
>>> admin = User(email='admin@example.com', is_admin=True)
>>> db.session.add(admin)
>>> db.session.commit()

# Run background data collection
python background_jobs.py update-channels --max-channels=200
python background_jobs.py cleanup-old-data --days=90
```

## New Features Added

### Channel Tooltips 🎯
- **Location**: Channel names in video cards and list views
- **Functionality**: Hover tooltips showing subscriber count, video count, and average views
- **Data Source**: Cached from database (24hr TTL) with fallback to real-time API
- **Implementation**: `static/js/channel_tooltip.js` + `/channel-tooltip/<channel_id>` endpoint

### Channel Statistics Tracking 📊
- **Model**: `models/channel_stats.py` - Historical channel data storage
- **Service**: `services/channel_tracker.py` - Data collection and management
- **Background Jobs**: `background_jobs.py` - CLI commands for automation
- **Purpose**: Foundation for future channel analytics features

### Channel Analysis Placeholder 🚧
- **Status**: Temporarily disabled while collecting data
- **User Experience**: "Coming soon" page with feature preview
- **Route**: `/channel/<channel_id>` returns 503 with explanation
- **Future**: Will be enabled once sufficient historical data is collected

## Error Handling & Production Readiness

- ✅ Fixed critical YouTube API call errors
- ✅ Added comprehensive error pages (404, 500, 503)
- ✅ Database migration system ready
- ✅ Background job system for data collection
- ✅ Caching strategy for performance
- ✅ User-friendly tooltips replace broken navigation

## Launch Checklist

Before going live:
1. Set up environment variables in `.env`
2. Configure YouTube API keys in admin panel
3. Run database migrations: `flask db upgrade`
4. Set up background job cron jobs (see PRODUCTION_SETUP.md)
5. Test API functionality with actual keys
6. Configure web server (nginx + gunicorn recommended)