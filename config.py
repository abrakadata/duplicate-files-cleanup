import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List

# Load environment variables
load_dotenv()

# File System Settings
CHUNK_SIZE = 8192  # 8KB chunks for file reading
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

# Application Directories
APP_NAME = "DuplicateFileCleaner"
APPDATA_DIR = os.path.join(os.environ.get('APPDATA', ''), APP_NAME)

# Directory names (case-insensitive)
LOG_DIR_NAME = "Logs"

# File Paths and Directories
LOG_DIR = os.path.join(APPDATA_DIR, LOG_DIR_NAME)
LOG_FILE = os.path.join(LOG_DIR, 'duplicate_cleaner.log')

# Logging Settings
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 3

# Cloud Storage Settings
CLOUD_PATHS: Dict[str, List[str]] = {
    'onedrive': ['onedrive', 'onedrive for business'],
    'dropbox': ['dropbox'],
    'google_drive': ['google drive', 'my drive'],
    'icloud': ['icloud']
}

CLOUD_WARNINGS: Dict[str, str] = {
    'onedrive': """
- OneDrive files must be downloaded locally (marked as "Always keep on this device") to be scanned
- Deleting files from OneDrive folders will remove them from both your local machine AND OneDrive cloud storage
- Deletions will sync across all devices connected to your OneDrive account""",
    
    'dropbox': """
- Dropbox files must be downloaded locally (set as "Available offline") to be scanned
- Deleting files from Dropbox folders will remove them from both your local machine AND Dropbox cloud storage
- Deletions will sync to all devices connected to your Dropbox account""",
    
    'google_drive': """
- Google Drive files must be downloaded locally (not in "cloud storage only" mode) to be scanned
- Deleting files from Google Drive folders will remove them from both your local machine AND Google Drive cloud storage
- Deletions will sync to all devices using Google Drive Stream/File Stream""",

    'icloud': """
- iCloud files must be downloaded locally to be scanned
- Deleting files from iCloud folders will remove them from both your local machine AND iCloud storage
- Deletions will sync to all devices connected to your iCloud account"""
}

# Hash Algorithm (simplified since only SHA256 is used)
HASH_ALGORITHM = 'SHA256'

# UI Settings
DEFAULT_FILE_TYPES = ".*"
DEFAULT_DIRECTORY = os.path.expanduser("~")
DEFAULT_MIN_FILE_SIZE = 0
DEFAULT_EXCLUDE_DIRS = ""
DEFAULT_SCAN_HIDDEN = False
DEFAULT_FOLLOW_SYMLINKS = False
DEFAULT_HASH_ALGORITHM = HASH_ALGORITHM

# Button Keys
BUTTON_KEYS: Dict[str, str] = {
    'SELECT_PATH': 'select_path_btn',
    'START_SCAN': 'start_scan_btn',
    'RESET_DIR_SELECT': 'reset_dir_select_btn',
    'RESET_MAIN': 'reset_main_btn',
    'DISMISS_CLOUD_WARNING': 'dismiss_cloud_warning_btn',
    'DELETE_SELECTED': 'delete_selected_btn',
    'DELETE_SELECTED_DISABLED': 'delete_selected_disabled_btn',
    'SELECT_ALL': 'select_all_btn',
    'SELECT_NONE': 'select_none_btn'
}

# Sensitive Directories
SENSITIVE_DIRS = {
    str(Path(os.environ['WINDIR'])).lower(),
    str(Path(os.environ['PROGRAMFILES'])).lower(),
    str(Path(os.environ.get('PROGRAMFILES(X86)', ''))).lower(),
    str(Path(os.environ['SYSTEMROOT'])).lower(),
    str(Path(os.environ.get('SYSTEM32', ''))).lower(),
    str(Path(os.environ.get('PROGRAMDATA', ''))).lower()
}

# CSS Styles
CSS_STYLES = """
<style>
    /* Global container adjustments */
    .stApp {
        margin-top: -4rem !important;
    }

    /* Remove top padding from main container */
    .main > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* Sidebar adjustments */
    [data-testid="stSidebar"] {
        padding-top: 1.7rem !important;
    }

    [data-testid="stSidebar"] > div {
        padding-top: 1.7rem !important;
    }

    [data-testid="stSidebarNav"] {
        padding-top: 1.7rem !important;
    }

    /* Sidebar content container */
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.7rem !important;
        margin-top: 0 !important;
    }

    /* Hide the header completely */
    .stApp header {
        display: none !important;
    }

    /* Title specific adjustments */
    h1:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
        line-height: 1.2 !important;
    }

    /* Scan section spacing */
    .scan-buttons-container {
        margin-top: 2rem !important;
    }

    /* Sidebar header adjustments */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* Button adjustments */
    button[kind="primary"], button[kind="secondary"] {
        margin-top: 0.5rem !important;
    }

    /* Keep other styles unchanged */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px !important;
        font-weight: 800 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: auto !important;
        white-space: pre-wrap !important;
        padding: 1rem 2rem !important;
        background-color: transparent !important;
        border: none !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: transparent !important;
        border-bottom: 1.2px solid #ff4b4b !important;
    }

    /* Remove bottom border/line from tab list */
    [data-baseweb="tab-list"] {
        border-bottom: none !important;
    }
    [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Warning container styling */
    .stWarning {
        background-color: #19337e !important;
        border-color: #ffc107 !important;
    }
    
    .stWarning > div {
        background-color: #19337e !important;
    }
    
    .stWarning * {
        color: white !important;
    }
    
    .stWarning svg {
        fill: white !important;
    }

    /* Warning text styling */
    .warning-text {
        line-height: 1.2;
        padding: 0.8rem;
        background-color: transparent;
        border-left: 3px solid #ffc107;
        margin: 0.4rem 0;
    }

    .warning-text h3 {
        font-size: 1.2rem !important;
        margin-bottom: 0.5rem !important;
    }

    .warning-text ul {
        margin: 0.3rem 0 !important;
        padding-left: 1.2rem !important;
    }

    .warning-text li {
        font-size: 0.9rem !important;
        margin: 0.2rem 0 !important;
    }

    /* Footer section spacing */
    .footer-container {
        margin-top: auto !important;
        padding-top: 4rem !important;
    }

    .stMarkdown {
        margin-top: 0 !important;
    }

    hr + div.warning-text {
        margin-top: 0.2rem !important;
    }

    div.warning-text + .stMarkdown {
        margin-top: 0.4rem !important;
    }
</style>
"""

def ensure_directories():
    """Ensure all required directories exist with proper case"""
    # Create base directory if it doesn't exist
    Path(APPDATA_DIR).mkdir(parents=True, exist_ok=True)
    
    # Check for existing directories with different case
    existing_dirs = [d for d in os.listdir(APPDATA_DIR) if os.path.isdir(os.path.join(APPDATA_DIR, d))]
    
    # Handle logs directory
    logs_dir_exists = any(d.lower() == LOG_DIR_NAME.lower() for d in existing_dirs)
    if not logs_dir_exists:
        Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

# Create necessary directories
ensure_directories() 