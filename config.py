import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Credentials
    REINVENT_EMAIL = os.getenv('REINVENT_EMAIL')
    REINVENT_PASSWORD = os.getenv('REINVENT_PASSWORD')
    
    # URLs
    LOGIN_URL = "https://registration.awsevents.com/flow/awsevents/reinvent2025/event-catalog/page/eventCatalog"
    
    # Interest Keywords (case-insensitive)
    INTEREST_KEYWORDS = [
        'AI', 'Kiro', 'Architect', 'Lakehouse', 
        'ETL', 'Trino', 'DevOps'
    ]
    
    # Venue filtering - only include these venues
    ALLOWED_VENUES = [
        'Caesars Forum',
        'Venetian',
        'Wynn'
    ]
    
    # Excluded Venues (legacy, now using ALLOWED_VENUES)
    EXCLUDED_VENUES = [
        'MGM Grand',
        'Mandalay Bay'
    ]
    
    # Schedule Settings
    CONFERENCE_DATES = [
        '2025-12-01', '2025-12-02', '2025-12-03', 
        '2025-12-04', '2025-12-05'
    ]
    
    LUNCH_BREAK_START = '11:00'
    LUNCH_BREAK_END = '13:00'
    BUFFER_MINUTES = 30
    MIN_BACKUP_SESSIONS = 2
    
    # WebDriver Settings
    CHROME_HEADLESS = os.getenv('CHROME_HEADLESS', 'true').lower() == 'true'
    CHROME_TIMEOUT = int(os.getenv('CHROME_TIMEOUT', '30'))
    
    # Output Settings
    OUTPUT_DIR = 'data'
    OUTPUT_FORMAT = os.getenv('OUTPUT_FORMAT', 'markdown')
    MAX_SESSIONS_PER_DAY = int(os.getenv('MAX_SESSIONS_PER_DAY', '8'))