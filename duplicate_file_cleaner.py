import os
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import sys
from send2trash import send2trash

# Set up logging directory in AppData
LOG_DIR = os.path.join(os.environ.get('APPDATA', ''), 'DuplicateFileCleaner')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, 'duplicate_cleaner.log')

# Custom logging filter to only log when needed
class DeletionFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.should_log = False

    def filter(self, record):
        return self.should_log

# Set up logging with size limit
deletion_filter = DeletionFilter()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=10485760,  # 10MB
            backupCount=3  # Keep 3 backup files
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()
logger.addFilter(deletion_filter)

class DuplicateFileCleaner:
    # File size limits (in bytes)
    MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB
    MIN_FILE_SIZE = 1  # 1 byte

    # Default allowed extensions (common file types)
    DEFAULT_ALLOWED_EXTENSIONS = {
        # Documents
        '.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt',
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
        # Audio
        '.mp3', '.wav', '.flac', '.m4a', '.ogg',
        # Video
        '.mp4', '.avi', '.mkv', '.mov', '.wmv',
        # Archives
        '.zip', '.rar', '.7z', '.tar', '.gz',
        # Data
        '.csv', '.xlsx', '.xls',
        # Other
        '.log', '.json', '.xml'
    }

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Duplicate File Cleaner")
        self.window.geometry("800x600")
        self.setup_ui()
        self.files_hashes = {}
        self.duplicates = []
        self.allowed_extensions = self.DEFAULT_ALLOWED_EXTENSIONS.copy()
        
        # Protected directories (converted to lowercase for case-insensitive comparison)
        self.sensitive_dirs = {
            str(Path(os.environ['WINDIR'])).lower(),
            str(Path(os.environ['PROGRAMFILES'])).lower(),
            str(Path(os.environ.get('PROGRAMFILES(X86)', ''))).lower(),
            str(Path(os.environ['SYSTEMROOT'])).lower(),
            str(Path(os.environ.get('SYSTEM32', ''))).lower(),
            str(Path(os.environ.get('PROGRAMDATA', ''))).lower()
        }

    def setup_ui(self):
        """Set up the user interface."""
        # Configure grid weights
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky='nsew')
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Directory selection frame
        dir_frame = ttk.LabelFrame(main_frame, text="Directory Selection", padding="5")
        dir_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        dir_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Button(dir_frame, text="Select Folder", command=self.select_directory).grid(row=0, column=0, padx=5)
        self.dir_label = ttk.Label(dir_frame, text="No folder selected")
        self.dir_label.grid(row=0, column=1, padx=5, sticky='w')

        # File type selection frame
        type_frame = ttk.LabelFrame(main_frame, text="File Type Filters", padding="5")
        type_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        
        # File categories in a grid
        file_categories = {
            "Documents": ['.txt', '.doc', '.docx', '.pdf'],
            "Images": ['.jpg', '.jpeg', '.png', '.gif'],
            "Audio": ['.mp3', '.wav', '.flac'],
            "Video": ['.mp4', '.avi', '.mkv'],
            "Archives": ['.zip', '.rar', '.7z']
        }
        
        self.type_vars = {}
        for i, (category, extensions) in enumerate(file_categories.items()):
            var = tk.BooleanVar(value=True)
            self.type_vars[category] = (var, extensions)
            ttk.Checkbutton(type_frame, text=category, variable=var,
                          command=self.update_allowed_extensions).grid(row=i//3, column=i%3, padx=10, pady=2, sticky='w')

        # Size limits frame
        size_frame = ttk.LabelFrame(main_frame, text="Size Limits (MB)", padding="5")
        size_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Label(size_frame, text="Min:").grid(row=0, column=0, padx=5)
        self.min_size = ttk.Entry(size_frame, width=10)
        self.min_size.insert(0, "0")
        self.min_size.grid(row=0, column=1, padx=5)
        
        ttk.Label(size_frame, text="Max:").grid(row=0, column=2, padx=5)
        self.max_size = ttk.Entry(size_frame, width=10)
        self.max_size.insert(0, "1024")
        self.max_size.grid(row=0, column=3, padx=5)

        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress = ttk.Progressbar(progress_frame, length=600, mode='determinate')
        self.progress.grid(row=0, column=0, sticky='ew')

        # Results frame with reduced height
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="5")
        results_frame.grid(row=4, column=0, sticky='nsew', padx=5, pady=5)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)
        
        # Reduced height of text widget from 15 to 10
        self.result_text = tk.Text(results_frame, height=10, width=90)
        self.result_text.grid(row=0, column=0, sticky='nsew')
        
        # Scrollbar for results
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.result_text.yview)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.result_text['yscrollcommand'] = scrollbar.set

        # Button frame with padding
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, sticky='ew', padx=5, pady=(10, 5))  # Added top padding
        button_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Button(button_frame, text="Scan for Duplicates", command=self.scan_duplicates).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Delete Duplicates", command=self.confirm_deletion).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.window.quit).grid(row=0, column=2, padx=5)

        # Set a minimum window size
        self.window.minsize(700, 500)

    def update_allowed_extensions(self):
        """Update the set of allowed file extensions based on checkbox selections."""
        self.allowed_extensions = set()
        for category, (var, extensions) in self.type_vars.items():
            if var.get():
                self.allowed_extensions.update(extensions)

    def is_sensitive_directory(self, path):
        """Check if the path is in a sensitive system directory."""
        try:
            path = str(Path(path).resolve()).lower()
            return any(path.startswith(sensitive_dir) for sensitive_dir in self.sensitive_dirs)
        except Exception:
            return True  # If we can't resolve the path, treat it as sensitive

    def is_safe_file(self, file_path):
        """Check if the file is safe to process based on various criteria."""
        try:
            # Check file extension
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.allowed_extensions:
                logging.info(f"Skipping file with unsupported extension: {file_path}")
                return False

            # Check file size
            size = os.path.getsize(file_path)
            min_size_mb = float(self.min_size.get()) * 1024 * 1024  # Convert MB to bytes
            max_size_mb = float(self.max_size.get()) * 1024 * 1024  # Convert MB to bytes
            
            if not (min_size_mb <= size <= max_size_mb):
                logging.info(f"Skipping file outside size limits: {file_path}")
                return False

            # Check if file is in system directory
            if self.is_sensitive_directory(file_path):
                logging.info(f"Skipping file in system directory: {file_path}")
                return False

            return True
        except Exception as e:
            logging.error(f"Error checking file safety for {file_path}: {str(e)}")
            return False

    def get_file_hash(self, file_path):
        """Generate MD5 hash for the given file using chunks for large files."""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):  # Read in 8kb chunks
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logging.error(f"Error hashing file {file_path}: {str(e)}")
            return None

    def select_directory(self):
        """Open directory selection dialog."""
        directory = filedialog.askdirectory()
        if directory:
            if self.is_sensitive_directory(directory):
                messagebox.showerror("Error", "Cannot scan system directories for security reasons.")
                return
            self.directory = directory
            self.dir_label.config(text=directory)
            logging.info(f"Selected directory: {directory}")

    def scan_duplicates(self):
        """Scan for duplicate files in the selected directory."""
        if not hasattr(self, 'directory'):
            messagebox.showwarning("Warning", "Please select a directory first!")
            return

        if self.is_sensitive_directory(self.directory):
            messagebox.showerror("Error", "Cannot scan system directories for security reasons.")
            return

        try:
            # Validate size inputs
            float(self.min_size.get())
            float(self.max_size.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for size limits.")
            return

        # Clear previous results
        self.files_hashes.clear()
        self.duplicates.clear()
        self.result_text.delete(1.0, tk.END)
        self.progress['value'] = 0
        self.window.update()

        self.result_text.insert(tk.END, "Scanning for duplicates...\n")
        self.window.update()

        try:
            # Count total files for progress bar
            total_files = sum(len(files) for _, _, files in os.walk(self.directory))
            processed_files = 0

            for root, _, files in os.walk(self.directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if not self.is_safe_file(file_path):
                            continue

                        file_hash = self.get_file_hash(file_path)
                        if not file_hash:
                            continue

                        if file_hash in self.files_hashes:
                            self.duplicates.append((file_path, self.files_hashes[file_hash]))
                            self.result_text.insert(tk.END, 
                                f"Found duplicate:\n  Original: {self.files_hashes[file_hash]}\n  Duplicate: {file_path}\n\n")
                        else:
                            self.files_hashes[file_hash] = file_path

                        # Update progress
                        processed_files += 1
                        self.progress['value'] = (processed_files / total_files) * 100
                        self.window.update()

                    except Exception as e:
                        logging.error(f"Error processing file {file_path}: {str(e)}")

            if not self.duplicates:
                self.result_text.insert(tk.END, "No duplicate files found.\n")
            else:
                self.result_text.insert(tk.END, f"\nFound {len(self.duplicates)} duplicate files.\n")

        except Exception as e:
            logging.error(f"Error during scan: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during scanning: {str(e)}")

        self.progress['value'] = 0
        self.window.update()

    def confirm_deletion(self):
        """Confirm and delete duplicate files."""
        if not self.duplicates:
            messagebox.showinfo("Info", "No duplicates to delete!")
            return

        # Extra confirmation for large number of files
        if len(self.duplicates) > 10:
            if not messagebox.askyesno("Warning", 
                f"You are about to move {len(self.duplicates)} files to the Recycle Bin.\n"
                "This is a large number of files. Are you absolutely sure?"):
                return

        # Show detailed confirmation
        confirmation_msg = (
            f"Are you sure you want to move these {len(self.duplicates)} duplicate files "
            "to the Recycle Bin?\n\n"
            "Files will be moved to the Recycle Bin and can be restored if needed.\n"
            "Original files will remain untouched."
        )
        
        if messagebox.askyesno("Confirm Deletion", confirmation_msg):
            self.delete_duplicate_files()

    def delete_duplicate_files(self):
        """Move duplicate files to the Recycle Bin."""
        deleted_count = 0
        
        # Enable logging only if we're going to delete files
        deletion_filter.should_log = True
        
        try:
            for duplicate_path, original_path in self.duplicates:
                try:
                    # Recheck if file is safe before deletion
                    if not self.is_safe_file(duplicate_path):
                        self.result_text.insert(tk.END, f"Skipping file for safety: {duplicate_path}\n")
                        continue

                    if not os.path.exists(duplicate_path):
                        logging.warning(f"File not found: {duplicate_path}")
                        self.result_text.insert(tk.END, f"File not found: {duplicate_path}\n")
                        continue

                    # Normalize the path for Windows
                    normalized_path = str(Path(duplicate_path).resolve())
                    send2trash(normalized_path)
                    deleted_count += 1
                    logging.info(f"Moved to Recycle Bin: {normalized_path}")
                    self.result_text.insert(tk.END, f"Moved to Recycle Bin: {duplicate_path}\n")
                except Exception as e:
                    logging.error(f"Error moving file to Recycle Bin {duplicate_path}: {str(e)}")
                    self.result_text.insert(tk.END, f"Error moving to Recycle Bin {duplicate_path}: {str(e)}\n")

            if deleted_count > 0:
                self.result_text.insert(tk.END, f"\nSuccessfully moved {deleted_count} duplicate files to Recycle Bin.\n")
                logging.info(f"Operation completed. {deleted_count} files moved to Recycle Bin.")
            else:
                self.result_text.insert(tk.END, "\nNo files were moved to the Recycle Bin.\n")
        finally:
            # Disable logging after operation is complete
            deletion_filter.should_log = False
            
        self.duplicates.clear()

    def run(self):
        """Start the application."""
        self.window.mainloop()

if __name__ == "__main__":
    app = DuplicateFileCleaner()
    app.run() 