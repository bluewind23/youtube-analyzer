#!/usr/bin/env python
"""
Background job runner for channel statistics collection and cache warming

Usage:
    python background_jobs.py update_channels [--max-channels=100]
    python background_jobs.py cleanup_old_data [--days=90]
    python background_jobs.py warm_trending_cache
    python background_jobs.py update_specific_channels <channel_id1> <channel_id2> ...
"""

import sys
import click
from flask.cli import with_appcontext
from app import create_app
from services.channel_tracker import channel_tracker
from services.youtube_service import get_trending_videos
from extensions import cache

# Create Flask app instance
app = create_app()

@click.group()
def cli():
    """Background job management commands"""
    pass

@cli.command()
@click.option('--max-channels', default=100, help='Maximum number of channels to update')
@with_appcontext
def update_channels(max_channels):
    """Update channel statistics for stale channels"""
    click.echo(f"Starting channel statistics update (max: {max_channels})")
    
    try:
        result = channel_tracker.update_channels_batch(max_channels=max_channels)
        
        click.echo(f"✅ Update complete:")
        click.echo(f"   📊 Requested: {result['requested']} channels")
        click.echo(f"   🔍 Collected: {result['collected']} channels")
        click.echo(f"   💾 Stored: {result['stored']} records")
        
        if result['stored'] < result['requested']:
            click.echo(f"⚠️  Some channels failed to update", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Update failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--days', default=90, help='Number of days of data to keep')
@with_appcontext  
def cleanup_old_data(days):
    """Clean up old channel statistics data"""
    click.echo(f"Cleaning up data older than {days} days")
    
    try:
        deleted_count = channel_tracker.cleanup_old_data(days_to_keep=days)
        click.echo(f"✅ Cleanup complete: Deleted {deleted_count} old records")
        
    except Exception as e:
        click.echo(f"❌ Cleanup failed: {e}", err=True)
        sys.exit(1)

@cli.command()
@with_appcontext
def warm_trending_cache():
    """Pre-warm trending videos cache for all categories"""
    click.echo("Starting trending videos cache warming...")
    
    # 주요 카테고리 목록 (YouTube API 카테고리 ID)
    popular_categories = ['0', '1', '2', '10', '15', '17', '19', '20', '22', '23', '24', '25', '26', '27', '28']
    
    success_count = 0
    error_count = 0
    
    for category_id in popular_categories:
        try:
            click.echo(f"Caching category {category_id}...")
            videos, _, service = get_trending_videos(max_results=50, category_id=category_id)
            if videos:
                success_count += 1
                click.echo(f"✅ Category {category_id}: {len(videos)} videos cached")
            else:
                error_count += 1
                click.echo(f"⚠️ Category {category_id}: No videos found")
        except Exception as e:
            error_count += 1
            click.echo(f"❌ Category {category_id} failed: {e}")
    
    click.echo(f"Cache warming complete: {success_count} success, {error_count} errors")

@cli.command()
@click.argument('channel_ids', nargs=-1, required=True)
@with_appcontext
def update_specific_channels(channel_ids):
    """Update statistics for specific channel IDs"""
    channel_list = list(channel_ids)
    click.echo(f"Updating {len(channel_list)} specific channels")
    
    try:
        result = channel_tracker.update_channels_batch(
            channel_ids=channel_list,
            max_channels=len(channel_list)
        )
        
        click.echo(f"✅ Update complete:")
        click.echo(f"   📊 Requested: {result['requested']} channels")
        click.echo(f"   🔍 Collected: {result['collected']} channels") 
        click.echo(f"   💾 Stored: {result['stored']} records")
        
    except Exception as e:
        click.echo(f"❌ Update failed: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    with app.app_context():
        cli()