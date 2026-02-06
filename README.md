# Secure FTP-like Server with Ngrok Tunneling

A secure, web-based FTP-like server with automatic ngrok tunneling, featuring a beautiful dark-themed UI with blue accents.

## Features

- **Secure Authentication**: Session-based password protection
- **Ngrok Integration**: Automatic public URL generation
- **Beautiful UI**: Dark theme with blue accents and smooth animations
- **File Management**: Upload, download, delete files and folders
- **Responsive Design**: Works on desktop and mobile
- **Real-time Dashboard**: Server-side TUI with live updates
- **Drag & Drop**: Easy file upload with Dropzone.js

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

2. Follow the prompts:
   - Set a session password when prompted
   - The server will start and generate a public URL

3. Access the server:
   - Use the provided ngrok URL from any device
   - Enter the session password
   - Manage your files through the web interface

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
- Terminal UI with dark blue theme using Rich library
- Session password protection
- Automatic ngrok tunneling
- Real-time dashboard
- Secure shutdown handling

### Client-side:
- Dark theme with blue accents using Bootstrap 5.3
- Smooth animations and transitions
- Drag & drop file upload
- Responsive design
- Real-time file management
- Session timeout protection
- Visual feedback with toasts and alerts

### Security:
- Password hashing with SHA-256
- Secure file handling
- Session management with authentication
- Auto-expiring sessions
- File type restrictions
- Size limits

## Keyboard Shortcuts (Server TUI)
- `Ctrl+C`: Shutdown server
- `Enter`: Continue to dashboard

## Requirements
- Python 3.11.14+
- Flask and dependencies (see requirements.txt)
- ngrok (free account)
- Modern web browser

## License
AGPL v3.0

## Troubleshooting

1. **Port already in use**: Change the port in `main.py` and `app.py`
2. **Ngrok connection failed**: Check your internet connection and ngrok auth token
3. **File upload fails**: Check file size and type restrictions
4. **Session issues**: Clear browser cookies or use incognito mode

## Contributing
Feel free to submit issues and enhancement requests!
Also feel free to fork the repo and tinker with it. Always open for PRs (new features and bug fixes).

---

Developed with ❤️ by (jakegithub24)[https://github.com/jakegithub24]
