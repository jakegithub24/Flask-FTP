# Secure FTP-like Server with Ngrok Tunneling

A secure, web-based FTP-like server with automatic ngrok tunneling, featuring a Windows File Explorer-style interface with dark theme and advanced access control.

## Features

- **Secure Authentication**: Session-based password protection with SHA-256 hashing
- **Windows File Explorer UI**: Grid-based file browsing with icon thumbnails
- **Access Privilege System**: Three-tier access control (Upload-only, Download-only, Full Access)
- **Ngrok Integration**: Automatic public URL generation for remote access
- **File Management**: Upload, download, delete files and folders
- **Folder Downloads**: Download entire folders as ZIP files
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Drag & Drop Upload**: Intuitive file upload with visual feedback
- **Real-time Dashboard**: Server-side TUI with live status and ngrok URL display
- **Security-First Design**: Path traversal prevention and secure file handling all supported file types

## Installation

1. Clone or download this repository
```bash
git clone https://github.com/jakegithub24/Flask-FTP.git
```

2. Change to the project directory
```bash
cd Flask-FTP
```

3. Setup python virtual environment
```bash
python3 -m venv myvenv # Create a virtual environment
source myvenv/bin/activate # Activate the virtual environment
```

4. Install dependencies
```bash
pip3 install -r requirements.txt
```

5. Install ngrok:
   - Download from [ngrok.com](https://ngrok.com/download)
   - Add to PATH or place in project directory
   - Sign up for a free account and get your auth token

6. Configure ngrok (one-time setup):
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

## Usage

1. Start the server:
```bash
python main.py
```

2. Follow the interactive prompts:
   - **Set Session Password**: Create a password for client authentication
   - **Choose Access Mode**: Select which operations users can perform:
     - `1` - **Upload Only**: Users can only upload files
     - `2` - **Download Only**: Users can only download files
     - `3` - **Full Access**: Users can upload, download, rename, and delete files
   - The server will start and display the local URL, ngrok URL, and server status

3. Access the server:
   - Use the provided ngrok URL from any device
   - Enter your session password
   - Manage files through the Windows Explorer-style interface

4. Access the Local Dashboard:
   - Open a browser and navigate to `http://localhost:5000`
   - Password: Same as what you set during startup

## Configuration

### Environment Variables
The application uses environment variables set during startup:

- **SESSION_PASSWORD**: SHA-256 hash of the session password (set automatically)
- **ACCESS_PRIVILEGE**: Access control level
  - `upload_only`: Users can only upload files
  - `download_only`: Users can only download files  
  - `upload_download`: Full access (upload, download, delete)

### Customization
- **Storage Location**: Edit `STORAGE_FOLDER` in [app.py](app.py) to change where files are stored
- **Port Number**: Edit `app.run(port=5000)` in [app.py](app.py) to use a different port
- **Session Timeout**: Configure in [app.py](app.py) with Flask session settings

## File Structure

```
Flask-FTP
├── app.py              # Flask application
├── main.py             #  Server TUI and main entry point
├── .gitignore          # Files to ignore (git)
├── README.md           # Project description and usage instructions
├── requirements.txt    # Python dependencies
├── static
│   ├── css
│   │   └── style.css   # CSS file
│   └── js
│       └── script.js   # JavaScript file
├── storage
│   ├── .gitignore      # Files to ignore (git)
│   └── MyFolder
│       └── test.txt
├── templates           # HTML templates
│   ├── base.html
│   ├── files.html
│   └── login.html
└── test_app.py         # pytest file used to test application (development purpose)
```

## Features Implemented:

### Server-side:
- Terminal UI with dark theme using Rich library
- Interactive session setup with privilege selection
- Three-tier access control system:
  - **Upload-only mode**: Restrict users to uploads only
  - **Download-only mode**: Restrict users to downloads only  
  - **Full access mode**: All operations enabled
- Session password protection with SHA-256 hashing
- Automatic ngrok tunneling with URL caching
- Secure file path traversal prevention
- Real-time server status and statistics

### Client-side:
- Windows File Explorer-style grid layout with icons
- Breadcrumb navigation for easy path traversal
- Dark theme with blue accents using Bootstrap 5.3
- Responsive design for desktop and mobile
- Drag & drop file upload with progress indicators
- Single and multiple file upload support
- Folder creation and deletion
- File and folder ZIP download
- Conditional UI based on access privileges
- Smooth animations and transitions
- Session timeout protection with secure logout
- Real-time user feedback with toast notifications

### Security:
- Password hashing with SHA-256 algorithm
- Secure file path handling with `secure_filename()`
- Directory traversal attack prevention
- CSRF protection through session management
- Privilege enforcement on both frontend and backend
- Secure temporary file handling for ZIP downloads
- File operation verification before execution

## Server Controls

### Keyboard Shortcuts (Server TUI):
- `Ctrl+C`: Gracefully shutdown server
- `Enter`: Continue to server dashboard

### Supported File Operations:
- **Upload**: Single or multiple files with drag & drop
- **Download**: Individual files or entire folders as ZIP
- **Delete**: Files and folders (full access mode only)
- **Create Folder**: Create new directories for organization
- **Navigation**: Breadcrumb-based folder navigation

## Requirements
- Python 3.11+
- Flask 3.0.0+ with Flask-Session
- ngrok (free account recommended)
- Modern web browser (Chrome, Firefox, Safari, Edge)

All Python dependencies are listed in `requirements.txt`

## License
AGPL v3.0

## Troubleshooting

### General Issues
1. **Port already in use**: Change the port or kill the process using port 5000
   ```bash
   # Find and kill the process
   lsof -i :5000
   kill -9 <PID>
   ```

2. **Ngrok connection failed**: 
   - Check your internet connection
   - Verify ngrok auth token with `ngrok config add-authtoken YOUR_TOKEN`
   - Try restarting ngrok: `ngrok http 5000`

3. **Module not found errors**: Ensure dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

### Access & Permission Issues
4. **Cannot upload files**: Check if server is in "Upload-only" or "Full Access" mode

5. **Cannot download files**: Verify server is in "Download-only" or "Full Access" mode

6. **Cannot delete files**: Deletion is only available in "Full Access" mode

7. **Folder download fails**: Ensure read permissions on the storage folder

### Browser Issues
8. **Session expires immediately**: Check browser cookie settings, try incognito mode

9. **Files not uploading (drag & drop)**: Use the upload button as fallback, check browser console for JS errors

10. **UI looks broken**: Clear browser cache and hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

## Contribution
Feel free to submit issues and enhancement requests!<br/>
Also feel free to fork the repo and tinker with it. Always open for PRs (new features and bug fixes).

---

Developed with ❤️ by [jakegithub24](https://github.com/jakegithub24)