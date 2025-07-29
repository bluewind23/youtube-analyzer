# Production Setup Guide

## Prerequisites

1. **Python Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Variables** 
   Create `.env` file:
   ```bash
   SECRET_KEY=your-very-secure-secret-key-here
   DATABASE_URL=sqlite:///app.db  # or MySQL/PostgreSQL URL
   ENCRYPTION_KEY=your-fernet-encryption-key  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   GOOGLE_OAUTH_CLIENT_ID=your-google-oauth-client-id
   GOOGLE_OAUTH_CLIENT_SECRET=your-google-oauth-client-secret
   ADMIN_EMAIL=admin@yourdomain.com
   ```

3. **Database Setup**
   ```bash
   flask db upgrade
   ```

## Launch Steps

### 1. Start the Web Application

For **development**:
```bash
python app.py
```

For **production** (recommended):
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 2. Set Up Admin User

```bash
flask shell
>>> from models import db, User
>>> admin = User(email='admin@yourdomain.com', is_admin=True)
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()
```

### 3. Configure YouTube API Keys

1. Log in as admin at `/login`
2. Go to admin panel
3. Add YouTube Data API v3 keys as fallback keys

### 4. Set Up Background Data Collection

Add to crontab for automatic data collection:
```bash
# Update channel statistics every 6 hours
0 */6 * * * cd /path/to/app && /path/to/venv/bin/python background_jobs.py update-channels --max-channels=200

# Clean up old data weekly
0 2 * * 0 cd /path/to/app && /path/to/venv/bin/python background_jobs.py cleanup-old-data --days=90
```

Or run manually:
```bash
# Update channel statistics
python background_jobs.py update-channels --max-channels=200

# Clean old data (keep 90 days)
python background_jobs.py cleanup-old-data --days=90

# Update specific channels
python background_jobs.py update-specific-channels UC_channel_id_1 UC_channel_id_2
```

## Production Optimizations

### 1. Database
- Use PostgreSQL or MySQL for production
- Set up database connection pooling
- Configure regular backups

### 2. Caching
- Set up Redis for better caching performance
- Update `config.py`:
  ```python
  CACHE_TYPE = 'RedisCache'
  CACHE_REDIS_URL = 'redis://localhost:6379/0'
  ```

### 3. Web Server
- Use nginx as reverse proxy
- Configure SSL/TLS certificates
- Set up rate limiting

### 4. Monitoring
- Monitor API quota usage in Google Cloud Console
- Set up application logging
- Monitor database performance

## Security Checklist

- [ ] Change default secret keys
- [ ] Set up HTTPS
- [ ] Configure firewall rules
- [ ] Enable database encryption
- [ ] Set up API rate limiting
- [ ] Monitor for suspicious activity
- [ ] Regular security updates

## Features Status

### ✅ Ready for Launch
- Video search and analysis
- Trending video tracking
- Channel tooltips with basic stats
- User authentication with Google OAuth
- API key management
- CSV export functionality
- Background data collection system

### 🚧 Coming Soon (Channel Analysis)
- Subscriber growth trends
- Video upload patterns
- View count analytics
- Popular content analysis

## Troubleshooting

### Common Issues

1. **YouTube API Quota Exceeded**
   - Add more API keys in admin panel
   - Keys automatically rotate when quota exceeded

2. **Database Errors**
   - Check database permissions
   - Ensure migrations are applied: `flask db upgrade`

3. **Background Jobs Failing**
   - Check API key availability
   - Monitor logs for specific errors
   - Verify database connection

### Performance Tips

1. **Reduce API Usage**
   - Increase cache timeout for stable data
   - Batch API requests when possible
   - Use background jobs for data collection

2. **Database Optimization**
   - Regular VACUUM/OPTIMIZE for SQLite
   - Add indexes for frequently queried columns
   - Archive old data periodically

## Support

Check logs in `/var/log/` or application logs for detailed error information.
Monitor YouTube API quota in Google Cloud Console.