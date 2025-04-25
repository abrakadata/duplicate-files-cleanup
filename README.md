# Duplicate Files Cleanup Utility

A user-friendly web interface for managing duplicate files, powered by [fclones](https://github.com/pkolaczk/fclones) by [Piotr Kołaczkowski](https://github.com/pkolaczk).

## Features

- Easy-to-use web interface
- Secure file hashing using SHA256
- Configurable scanning options
- Real-time progress tracking
- Advanced filtering options
- Cloud storage awareness
- Secure authentication system

## Prerequisites

1. Install fclones (created by Piotr Kołaczkowski):
   ```bash
   # For Windows (using scoop)
   scoop install fclones

   # For Linux
   cargo install fclones

   # For macOS
   brew install fclones
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Streamlit interface:
   ```bash
   streamlit run fclones_ui.py
   ```

2. Open your web browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

3. Log in with your credentials:
   - Default credentials: username: 'admin', password: 'admin'
   - You can reset to default credentials if needed

4. Configure your scan:
   - Select directory to scan
   - Set file size limits
   - Configure advanced options
   - Choose file types to include/exclude

5. Click "Start Scan" to begin

## Security Features

- Secure authentication system with password hashing
- SHA256 file hashing for reliable duplicate detection
- Cloud storage awareness to prevent accidental deletions
- Safe file operations with proper error handling
- Session management for secure access

## Development

To modify the interface:

1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make changes to `fclones_ui.py`

3. Test changes:
   ```bash
   streamlit run fclones_ui.py
   ```

## Best Practices

We maintain a comprehensive set of best practices in [BEST_PRACTICES.md](BEST_PRACTICES.md). This document covers:

- Code Quality Guidelines
- Data Handling Standards
- Configuration Management
- Git and Command Line Usage
- Environment-specific Considerations

Please review these guidelines before contributing to the project.

## Recent Changes

- Added best practices documentation
- Simplified hash algorithm to use only SHA256 for better security and consistency
- Improved session state management
- Enhanced error handling and logging
- Streamlined UI for better user experience
- Added cloud storage awareness
- Implemented secure authentication system

## Credits

This utility is built on top of [fclones](https://github.com/pkolaczk/fclones), a high-performance duplicate file finder created by [Piotr Kołaczkowski](https://github.com/pkolaczk). The original fclones project is licensed under the MIT License.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 