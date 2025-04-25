import streamlit as st
import os
import hashlib
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from tkinter import filedialog
from dotenv import load_dotenv
import config
from typing import Dict, List, Optional, Tuple, Any, Callable, Set, Union, Literal, DefaultDict
from datetime import datetime
from collections import defaultdict
import time
import tkinter as tk
from dataclasses import dataclass
from enum import Enum, auto
import subprocess

# Custom type hints
FilePath = str | Path
FileSize = int
FileHash = str

# Define OperationType enum
class OperationType(Enum):
    SCAN = auto()
    DELETE = auto()
    NONE = auto()

# Define UIState enum and state management
class UIState(Enum):
    """UI State enumeration."""
    DIRECTORY_SELECT = auto()
    SCANNING = auto()
    RESULTS = auto()
    DELETING = auto()

@dataclass
class FileInfo:
    """Information about a file"""
    size_bytes: int
    is_hidden: bool
    modified: float  # Add modified timestamp field
    hash: Optional[str] = None

# Custom exceptions
class FileOperationError(Exception):
    """Base class for file operation errors"""
    pass

class FileNotFoundError(FileOperationError):
    """Raised when a file is not found"""
    pass

class PermissionError(FileOperationError):
    """Raised when permission is denied"""
    pass

class CloudStorageError(FileOperationError):
    """Raised when there are cloud storage related issues"""
    pass

class ConfigurationError(Exception):
    """Raised when there are configuration issues"""
    pass

class UIStateError(Exception):
    """Raised when there are UI state related issues"""
    pass

# Load environment variables
load_dotenv()

# Constants
DEFAULT_PORT = 8501
DEFAULT_HOST = "localhost"
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
CHUNK_SIZE = 8192  # 8KB chunks for file reading
PASSWORD_MIN_LENGTH = 8
HASH_ITERATIONS = 100000
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 3

# Initialize session state
def init_session_state() -> None:
    """Initialize the session state with default values."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.duplicate_files = []
        st.session_state.selected_files = set()
        st.session_state.processing = False
        st.session_state.current_directory = None
        st.session_state.operation_progress = 0.0
        st.session_state.operation_type = None
        st.session_state.ui_state = UIState.DIRECTORY_SELECT
        st.session_state.file_types = config.DEFAULT_FILE_TYPES
        st.session_state.min_file_size = config.DEFAULT_MIN_FILE_SIZE
        st.session_state.exclude_dirs = config.DEFAULT_EXCLUDE_DIRS
        st.session_state.scan_hidden = config.DEFAULT_SCAN_HIDDEN
        st.session_state.follow_symlinks = config.DEFAULT_FOLLOW_SYMLINKS
        st.session_state.hash_algorithm = config.DEFAULT_HASH_ALGORITHM
        st.session_state.dir_input = config.DEFAULT_DIRECTORY
        st.session_state.space_savings = 0
        st.session_state.last_scan_time = None
        st.session_state.error_message = None
        st.session_state.scan_dir = ""
        st.session_state.initialized = True

# Initialize session state
init_session_state()

# Hash algorithm options with descriptions
HASH_ALGORITHMS = {
    'SHA256': {
        'description': 'Secure hash algorithm',
        'function': lambda data: hashlib.sha256(data).hexdigest()
    }
}

# Create display names for algorithms
ALGO_DISPLAY_NAMES = {
    'SHA256': 'SHA256: Secure hash algorithm'
}

# Constants
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

CLOUD_PATHS: Dict[str, List[str]] = {
    'onedrive': ['onedrive', 'onedrive for business'],
    'dropbox': ['dropbox'],
    'google_drive': ['google drive', 'my drive']
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
- Deletions will sync to all devices using Google Drive Stream/File Stream"""
}

# Page config
st.set_page_config(
    page_title="Duplicate Files Cleanup Utility",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS to adjust spacing and add styles
st.markdown(config.CSS_STYLES, unsafe_allow_html=True)

# Set up logging
if not os.path.exists(config.LOG_DIR):
    os.makedirs(config.LOG_DIR)

# Custom logging filter to only log when needed
class DeletionFilter(logging.Filter):
    """Filter for deletion related log messages"""
    
    def __init__(self) -> None:
        """Initialize the deletion filter"""
        super().__init__()
        self.deletion_messages: List[str] = []

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and store deletion related messages"""
        if "deleted" in record.msg.lower():
            self.deletion_messages.append(record.msg)
        return True

# Set up logging with size limit
deletion_filter = DeletionFilter()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()
logger.addFilter(deletion_filter)

class FileOperations:
    """Class for handling file operations"""
    
    @staticmethod
    def is_safe_file(file_path: FilePath) -> bool:
        """
        Check if a file is safe to delete.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if the file is safe to delete, False otherwise
            
        Raises:
            FileOperationError: If there are issues checking the file
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Check if file is in a system directory
            system_paths = {
                os.environ.get('WINDIR', ''),
                os.environ.get('PROGRAMFILES', ''),
                os.environ.get('PROGRAMFILES(X86)', ''),
                os.environ.get('PROGRAMDATA', ''),
                os.environ.get('SYSTEMROOT', '')
            }
            
            return not any(str(path).lower().startswith(str(sys_path).lower()) 
                         for sys_path in system_paths if sys_path)
                         
        except Exception as e:
            raise FileOperationError(f"Error checking file safety: {str(e)}")

    @staticmethod
    def safe_delete_file(file_path: FilePath) -> bool:
        """
        Safely delete a file after performing safety checks.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            bool: True if file was deleted successfully
            
        Raises:
            FileOperationError: If there are issues deleting the file
        """
        try:
            if not FileOperations.is_safe_file(file_path):
                raise FileOperationError(f"File {file_path} failed safety checks")
                
            if FileOperations.is_cloud_storage_file(file_path):
                raise CloudStorageError(f"File {file_path} appears to be a cloud storage file")
                
            os.remove(file_path)
            return True
            
        except Exception as e:
            raise FileOperationError(f"Error deleting file: {str(e)}")

    @staticmethod
    def is_cloud_storage_file(file_path: FilePath) -> bool:
        """
        Check if a file is from a cloud storage provider.
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if file appears to be from cloud storage
        """
        cloud_indicators = {
            'OneDrive',
            'Dropbox',
            'Google Drive',
            'iCloud',
            'Box'
        }
        
        path_str = str(file_path).lower()
        return any(indicator.lower() in path_str for indicator in cloud_indicators)

    @staticmethod
    def get_file_info(file_path: FilePath) -> FileInfo:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileInfo: Information about the file
            
        Raises:
            FileOperationError: If there are issues getting file information
        """
        try:
            path = Path(file_path)
            stats = path.stat()
            
            return FileInfo(
                size_bytes=stats.st_size,
                is_hidden=bool(path.name.startswith('.') or 
                             bool(stats.st_file_attributes & 0x2) if os.name == 'nt' else False),
                modified=stats.st_ctime,
                hash=None  # Hash is computed separately when needed
            )
            
        except Exception as e:
            raise FileOperationError(f"Error getting file info: {str(e)}")

    @staticmethod
    def compute_file_hash(file_path: FilePath, chunk_size: int = 8192) -> FileHash:
        """
        Compute the SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file
            chunk_size: Size of chunks to read, defaults to 8KB
            
        Returns:
            str: Hex digest of the file hash
            
        Raises:
            FileOperationError: If there are issues computing the hash
        """
        try:
            hasher = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
                    
            return hasher.hexdigest()
            
        except Exception as e:
            raise FileOperationError(f"Error computing file hash: {str(e)}")

class CloudStorage:
    """Handles cloud storage detection and warnings"""
    
    @staticmethod
    def detect(path: FilePath) -> Optional[str]:
        """Detect if a path is within a cloud storage directory"""
        try:
            path_normalized = os.path.normpath(path.lower())
            for provider, indicators in config.CLOUD_PATHS.items():
                if any(indicator.lower() in path_normalized for indicator in indicators):
                    return provider
            return None
        except Exception as e:
            logger.error(f"Error detecting cloud storage for {path}: {str(e)}")
            return None

    @staticmethod
    def get_warning(path: FilePath) -> Optional[str]:
        """Get cloud storage warning if applicable"""
        cloud_service = CloudStorage.detect(path)
        if cloud_service:
            return config.CLOUD_WARNINGS.get(cloud_service.lower(), f"Warning: This path is in {cloud_service}")
        return None

    @staticmethod
    def is_sensitive_directory(path: FilePath) -> bool:
        """Check if the path is in a sensitive system directory."""
        try:
            path = str(Path(path).resolve()).lower()
            return any(path.startswith(sensitive_dir) for sensitive_dir in config.SENSITIVE_DIRS)
        except Exception:
            return True  # If we can't resolve the path, treat it as sensitive

def init_ui_state() -> None:
    """Initialize UI state with default values."""
    if not st.session_state.initialized:
        init_session_state()

def set_ui_state(new_state: UIState) -> None:
    """Set UI state with validation."""
    if not isinstance(new_state, UIState):
        raise UIStateError(f"Invalid UI state: {new_state}")
    st.session_state.ui_state = new_state

def get_ui_state() -> UIState:
    """Get current UI state."""
    return st.session_state.ui_state

def find_duplicates(directory: FilePath) -> None:
    """
    Find duplicate files in the given directory.
    
    Args:
        directory: Directory to scan for duplicates
    """
    st.session_state.processing = True
    st.session_state.operation_type = OperationType.SCAN
    st.session_state.operation_progress = 0
    st.session_state.duplicate_files = []
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize file tracking
        files_by_size: DefaultDict[FileSize, List[FilePath]] = defaultdict(list)
        files_by_hash: DefaultDict[FileHash, List[FilePath]] = defaultdict(list)
        total_files = 0
        processed_files = 0
        
        # First pass: Group files by size
        for root, _, files in os.walk(directory):
            if st.session_state.processing is False:  # Only break if processing is explicitly set to False
                break
                
            status_text.text(f"Scanning directory: {root}")
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    # Skip files that don't meet criteria
                    if not FileOperations.is_safe_file(filepath):
                        continue
                        
                    file_info = FileOperations.get_file_info(filepath)
                    if file_info and file_info.size_bytes > 0:  # Skip empty files
                        files_by_size[file_info.size_bytes].append(filepath)
                        total_files += 1
                except FileOperationError as e:
                    logger.warning(f"Skipping file due to error: {str(e)}")
                    continue
        
        # Second pass: Calculate hashes for files of the same size
        for size, size_group in files_by_size.items():
            if len(size_group) < 2:  # Skip unique files
                continue
                
            if st.session_state.processing is False:  # Only break if processing is explicitly set to False
                break
                
            for filepath in size_group:
                try:
                    file_hash = FileOperations.compute_file_hash(filepath)
                    files_by_hash[file_hash].append(filepath)
                    processed_files += 1
                    progress = min(processed_files / total_files, 1.0) if total_files > 0 else 0
                    st.session_state.operation_progress = progress
                    progress_bar.progress(progress)
                    status_text.text(f"Processing file: {filepath}")
                except FileOperationError as e:
                    logger.warning(f"Skipping file due to error: {str(e)}")
                    continue
        
        # Collect duplicate groups
        st.session_state.duplicate_files = [
            sorted(group) for group in files_by_hash.values() 
            if len(group) > 1
        ]
            
    except Exception as e:
        logger.error(f"An error occurred while scanning: {str(e)}")
        st.error(f"An error occurred while scanning: {str(e)}")
    finally:
        st.session_state.processing = False
        st.session_state.operation_type = OperationType.NONE
        progress_bar.empty()
        status_text.empty()
        
        if st.session_state.duplicate_files:
            st.success(f"Found {len(st.session_state.duplicate_files)} groups of duplicate files!")
            set_ui_state(UIState.RESULTS)
        else:
            st.info("No duplicate files found.")
            set_ui_state(UIState.DIRECTORY_SELECT)

def delete_selected_files():
    """Delete the selected files and return the number of files successfully deleted"""
    deleted_count = 0
    errors = []
    
    st.session_state.operation_type = OperationType.DELETE
    
    # Calculate and store total size before deletion
    total_size = 0
    for file_path in st.session_state.selected_files:
        try:
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
        except (OSError, IOError):
            continue
    
    # Store the space savings
    st.session_state.space_savings = total_size
    
    # Proceed with deletion
    for file_path in st.session_state.selected_files.copy():
        try:
            os.remove(file_path)
            st.session_state.selected_files.remove(file_path)
            deleted_count += 1
        except Exception as e:
            errors.append(f"Error deleting {file_path}: {str(e)}")
    
    st.session_state.operation_type = OperationType.NONE
    return deleted_count, errors

def get_safe_file_size(file_path: FilePath) -> Optional[int]:
    """Get file size safely with proper error handling.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes or None if file cannot be accessed
    """
    try:
        return os.path.getsize(file_path)
    except (OSError, IOError):
        return None

def select_directory() -> Optional[str]:
    """Open Windows folder picker dialog and return selected path."""
    try:
        # PowerShell command to open folder picker
        ps_command = '''
        Add-Type -AssemblyName System.Windows.Forms
        $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
        $folderBrowser.Description = "Select a folder to scan for duplicates"
        $folderBrowser.RootFolder = "MyComputer"
        if ($folderBrowser.ShowDialog() -eq "OK") {
            $folderBrowser.SelectedPath
        }
        '''
        
        # Run PowerShell command and get output
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True
        )
        
        selected_path = result.stdout.strip()
        if selected_path and os.path.isdir(selected_path):
            st.session_state.scan_dir = selected_path
            st.rerun()
            
    except Exception as e:
        logger.error(f"Error in directory selection: {e}")
        st.error("Failed to open folder selection dialog")

# Title and description
st.title("🔍 Duplicate Files Cleanup Utility")

# Main content area with larger tabs
tab1, tab2 = st.tabs(["🔍  SCAN", "📋  RESULTS"])

# Sidebar for displaying selected path
with st.sidebar:
    st.header("Configuration")
    
    # Add scan configuration options
    st.subheader("Scan Settings")
    min_file_size = st.slider("Minimum file size (KB)", 0, 1000, 0)
    file_types = st.text_input("File types to scan (comma-separated, e.g., .txt,.pdf)", value=".*")
    exclude_dirs = st.text_input("Directories to exclude (comma-separated)", value="")
    
    # Add scan options
    st.subheader("Scan Options")
    scan_hidden = st.checkbox("Scan hidden files", value=False)
    follow_symlinks = st.checkbox("Follow symbolic links", value=False)

with tab1:
    # Main heading for the scan tab
    st.markdown("### Scan for Duplicates")
    
    # Show selected directory and scan button if directory is selected
    if st.session_state.scan_dir:
        st.text_input(
            "Selected directory",
            value=st.session_state.scan_dir,
            disabled=True,
            key="dir_display"
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Change folder", type="primary", key=BUTTON_KEYS['SELECT_PATH']):
                select_directory()
        with col2:
            if st.button("Reset"):
                st.session_state.scan_dir = ""
                st.rerun()
        with col3:
            if st.button("Start Scan", type="primary", key=BUTTON_KEYS['START_SCAN']):
                # Check for cloud storage using CloudStorage class
                cloud_service = CloudStorage.detect(st.session_state.scan_dir)
                if cloud_service:
                    warning_container = st.empty()
                    warning_text = CloudStorage.get_warning(st.session_state.scan_dir)
                    warning_container.warning(f"⚠️ You've selected a {cloud_service.replace('_', ' ').title()} folder. Please note:{warning_text}")
                    
                    col1, col2, col3 = st.columns([6, 2, 6])
                    with col2:
                        if st.button("Dismiss", key=BUTTON_KEYS['DISMISS_CLOUD_WARNING']):
                            warning_container.empty()
                            st.rerun()
                    st.stop()
                
                # Store configuration in session state
                st.session_state.min_file_size = min_file_size
                st.session_state.file_types = file_types
                st.session_state.exclude_dirs = exclude_dirs
                st.session_state.scan_hidden = scan_hidden
                st.session_state.follow_symlinks = follow_symlinks
                
                with st.spinner("Scanning for duplicates..."):
                    try:
                        find_duplicates(st.session_state.scan_dir)
                    except Exception as e:
                        st.error(f"Error during scan: {str(e)}")
    else:
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Select folder", type="primary", key=BUTTON_KEYS['SELECT_PATH']):
                select_directory()
        with col2:
            st.empty()
        with col3:
            st.empty()

# Display results
with tab2:
    st.header("Scan Results")
    
    if st.session_state.duplicate_files:
        # Initialize selected files if not already done
        if not st.session_state.initialized:
            init_ui_state()
            
        # Filter out non-existent files from selected files and recalculate space savings
        st.session_state.selected_files = {f for f in st.session_state.selected_files if os.path.exists(f)}
        current_selected_size = sum(get_safe_file_size(file) for file in st.session_state.selected_files)
        
        # Update space savings with current selection
        st.session_state.space_savings = current_selected_size
            
        total_groups = len(st.session_state.duplicate_files)
        total_duplicates = sum(len(group) - 1 for group in st.session_state.duplicate_files)
        
        st.markdown(f"""
        ### Summary
        - Found {total_groups} groups of duplicate files
        - Total duplicate files: {total_duplicates}
        - Selected for deletion: {len(st.session_state.selected_files)} files
        - Potential space savings: {st.session_state.space_savings / (1024*1024):.2f} MB
        """)
        
        # Add buttons for selection and deletion
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
        with col1:
            if st.button("Select All", key=BUTTON_KEYS['SELECT_ALL']):
                init_ui_state()
                # Select all files and calculate total size
                total_size = 0
                for group in st.session_state.duplicate_files:
                    for file in group:  # Include all files
                        if os.path.exists(file):
                            st.session_state.selected_files.add(file)
                            try:
                                total_size += os.path.getsize(file)
                            except (OSError, IOError):
                                continue
                st.session_state.space_savings = total_size
                st.rerun()
        with col2:
            if st.button("Select None", key=BUTTON_KEYS['SELECT_NONE']):
                init_ui_state()
                st.rerun()
        with col3:
            if len(st.session_state.selected_files) > 0:
                if st.button("Delete Selected", type="primary"):
                    if st.session_state.get('confirm_delete', False):
                        deleted_count, errors = delete_selected_files()
                        if deleted_count > 0:
                            st.success(f"Successfully deleted {deleted_count} files!")
                        if errors:
                            st.error("Errors occurred during deletion:\n" + "\n".join(errors))
                        # Reset confirmation state
                        st.session_state.confirm_delete = False
                        # Refresh the page
                        st.rerun()
                    else:
                        st.session_state.confirm_delete = True
                        st.warning(f"⚠️ Are you sure you want to delete {len(st.session_state.selected_files)} files? Click 'Delete Selected' again to confirm.")
            else:
                st.button("Delete Selected", key=BUTTON_KEYS['DELETE_SELECTED_DISABLED'], disabled=True, help="Select files to delete first")
        
        # Display duplicate groups with checkboxes
        valid_groups = []
        for group in st.session_state.duplicate_files:
            # Only include groups where at least two files still exist
            existing_files = [f for f in group if os.path.exists(f)]
            if len(existing_files) > 1:
                valid_groups.append(existing_files)
        
        for i, group in enumerate(valid_groups, 1):
            # Get file times for the group
            file_times = [(f, FileOperations.get_file_info(f)['modified']) for f in group]
            # Sort by timestamp (oldest first)
            file_times.sort(key=lambda x: x[1])
            
            with st.expander(f"Group {i} - {len(group)} files - {get_safe_file_size(group[0]) / 1024:.1f} KB each"):
                st.markdown("**Files in this group:**")
                
                # Display each file with its timestamp and size
                for file_path, timestamp in file_times:
                    file_size = get_safe_file_size(file_path) / 1024  # Convert to KB
                    is_selected = file_path in st.session_state.selected_files
                    
                    # Format the timestamp
                    time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                    
                    # Create a checkbox for each file
                    if st.checkbox(
                        f"{file_path}\n📅 {time_str} | 💾 {file_size:.1f} KB",
                        value=is_selected,
                        key=f"check_{hash(file_path)}",
                        help="Select for deletion"
                    ):
                        st.session_state.selected_files.add(file_path)
                    else:
                        st.session_state.selected_files.discard(file_path)
                
                st.markdown("---")
    else:
        st.info("Run a scan to see results here")

# Footer with warning
st.markdown("---")
st.markdown("""
<div class="warning-text">
<h3>⚠️ Important Notes about Cloud Storage</h3>

For all cloud storage services (OneDrive, Dropbox, Google Drive):
- Files must be downloaded locally before they can be scanned for duplicates
- Deleting files from cloud storage folders affects both local and cloud copies
- Changes will sync across all your connected devices
- Consider moving files to a local folder before deletion to prevent unintended synchronization
</div>
""", unsafe_allow_html=True)

st.markdown("""
### About
This utility helps you find and manage duplicate files in your system.
""") 