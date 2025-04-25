import os
import shutil
import random
import string
from pathlib import Path

def generate_random_text(length=100):
    """Generate random text content."""
    return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))

def create_test_files():
    # Create test directory
    test_dir = Path("test_duplicates")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # Create some unique files
    unique_files = [
        "unique_file1.txt",
        "unique_file2.txt",
        "unique_file3.txt"
    ]
    
    # Create some duplicate files (same content, different names)
    duplicate_sets = [
        ["duplicate_set1_a.txt", "duplicate_set1_b.txt", "duplicate_set1_c.txt"],
        ["duplicate_set2_a.txt", "duplicate_set2_b.txt"],
        ["duplicate_set3_a.txt", "duplicate_set3_b.txt", "duplicate_set3_c.txt", "duplicate_set3_d.txt"]
    ]
    
    # Create unique files
    for filename in unique_files:
        content = generate_random_text()
        with open(test_dir / filename, 'w') as f:
            f.write(content)
        print(f"Created unique file: {filename}")
    
    # Create duplicate files
    for duplicate_set in duplicate_sets:
        content = generate_random_text()
        for filename in duplicate_set:
            with open(test_dir / filename, 'w') as f:
                f.write(content)
            print(f"Created duplicate file: {filename}")
    
    # Create some empty files
    empty_files = ["empty1.txt", "empty2.txt"]
    for filename in empty_files:
        with open(test_dir / filename, 'w') as f:
            pass
        print(f"Created empty file: {filename}")
    
    # Create some nested folders with duplicates
    nested_dir = test_dir / "nested_folder"
    nested_dir.mkdir()
    
    # Create duplicates in nested folder
    content = generate_random_text()
    for filename in ["nested_duplicate1.txt", "nested_duplicate2.txt"]:
        with open(nested_dir / filename, 'w') as f:
            f.write(content)
        print(f"Created nested duplicate file: {filename}")
    
    print(f"\nTest files created in: {test_dir.absolute()}")
    print("Structure:")
    print("- 3 unique files")
    print("- 3 sets of duplicate files (9 files total)")
    print("- 2 empty files")
    print("- 1 nested folder with 2 duplicate files")

if __name__ == "__main__":
    create_test_files() 