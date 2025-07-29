from extensions import db

# Import models to ensure they are registered with SQLAlchemy
from .user import User
from .api_key import ApiKey  
from .admin_api_key import AdminApiKey
from .channel_stats import ChannelStats
from .search_history import SearchHistory
from .saved_item import SavedItem
from .feedback import Feedback
from .saved_video import SavedVideo, SavedVideoCategory