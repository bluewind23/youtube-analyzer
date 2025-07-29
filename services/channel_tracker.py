"""
Channel Statistics Tracking Service
Collects and stores channel statistics over time for trend analysis
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from flask import current_app
from extensions import db
from models.channel_stats import ChannelStats
from services.youtube_service import get_channels_details_batch

logger = logging.getLogger(__name__)

class ChannelTracker:
    """Service for tracking channel statistics over time"""
    
    def __init__(self):
        self.batch_size = 50  # YouTube API limit per request
        
    def get_channels_to_track(self, hours_since_last_update: int = 24) -> List[str]:
        """
        Get list of channel IDs that need data collection
        
        Args:
            hours_since_last_update: Only return channels not updated in this many hours
            
        Returns:
            List of channel IDs to track
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_since_last_update)
        
        # Get channels that haven't been updated recently
        # This uses a subquery to find the latest record for each channel
        subquery = db.session.query(
            ChannelStats.channel_id,
            db.func.max(ChannelStats.recorded_at).label('latest_record')
        ).group_by(ChannelStats.channel_id).subquery()
        
        stale_channels = db.session.query(subquery.c.channel_id)\
            .filter(subquery.c.latest_record < cutoff_time)\
            .all()
        
        return [channel_id for (channel_id,) in stale_channels]
    
    def collect_channel_data(self, channel_ids: List[str]) -> Dict[str, dict]:
        """
        Collect current statistics for given channels
        
        Args:
            channel_ids: List of channel IDs to collect data for
            
        Returns:
            Dictionary mapping channel_id to channel data
        """
        if not channel_ids:
            return {}
        
        try:
            channel_details = get_channels_details_batch(channel_ids)
            logger.info(f"Collected data for {len(channel_details)} channels")
            return channel_details
        except Exception as e:
            logger.error(f"Failed to collect channel data: {e}")
            return {}
    
    def store_channel_stats(self, channel_details: Dict[str, dict]) -> int:
        """
        Store channel statistics in database
        
        Args:
            channel_details: Dictionary of channel data from YouTube API
            
        Returns:
            Number of records successfully stored
        """
        stored_count = 0
        
        try:
            for channel_id, data in channel_details.items():
                try:
                    # Create channel data structure expected by ChannelStats.record_stats
                    channel_data = {
                        'id': channel_id,
                        'title': data.get('title', ''),
                        'customUrl': data.get('customUrl', ''),
                        'thumbnailUrl': data.get('thumbnailUrl', ''),
                        'subscriberCount': data.get('subscriberCount', 0),
                        'videoCount': data.get('videoCount', 0),
                        'channelViewCount': data.get('channelViewCount', 0)
                    }
                    
                    ChannelStats.record_stats(channel_data)
                    stored_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to store stats for channel {channel_id}: {e}")
                    continue
            
            db.session.commit()
            logger.info(f"Successfully stored stats for {stored_count} channels")
            
        except Exception as e:
            logger.error(f"Failed to commit channel stats: {e}")
            db.session.rollback()
            stored_count = 0
        
        return stored_count
    
    def update_channels_batch(self, channel_ids: Optional[List[str]] = None, 
                            max_channels: int = 100) -> Dict[str, int]:
        """
        Update statistics for a batch of channels
        
        Args:
            channel_ids: Specific channels to update (if None, auto-discovers stale channels)
            max_channels: Maximum number of channels to process in one batch
            
        Returns:
            Dictionary with 'requested', 'collected', 'stored' counts
        """
        if channel_ids is None:
            channel_ids = self.get_channels_to_track()
        
        # Limit batch size
        channel_ids = channel_ids[:max_channels]
        
        if not channel_ids:
            logger.info("No channels need updating")
            return {'requested': 0, 'collected': 0, 'stored': 0}
        
        logger.info(f"Updating statistics for {len(channel_ids)} channels")
        
        # Collect data in batches to respect API limits
        all_channel_data = {}
        for i in range(0, len(channel_ids), self.batch_size):
            batch = channel_ids[i:i + self.batch_size]
            batch_data = self.collect_channel_data(batch)
            all_channel_data.update(batch_data)
        
        # Store the data
        stored_count = self.store_channel_stats(all_channel_data)
        
        result = {
            'requested': len(channel_ids),
            'collected': len(all_channel_data),
            'stored': stored_count
        }
        
        logger.info(f"Channel update complete: {result}")
        return result
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """
        Clean up old channel statistics data
        
        Args:
            days_to_keep: Number of days of data to retain
            
        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        try:
            deleted_count = db.session.query(ChannelStats)\
                .filter(ChannelStats.recorded_at < cutoff_date)\
                .delete()
            
            db.session.commit()
            logger.info(f"Cleaned up {deleted_count} old channel statistics records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            db.session.rollback()
            return 0

# Global instance
channel_tracker = ChannelTracker()