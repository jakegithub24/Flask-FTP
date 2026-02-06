from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import os
import hashlib
import shutil
import zipfile
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['STORAGE_FOLDER'] = 'storage'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}

# Create storage folder if it doesn't exist
os.makedirs(app.config['STORAGE_FOLDER'], exist_ok=True)

def get_session_password_hash():
    """Dynamically get the session password hash from environment"""
    password = os.environ.get('SESSION_PASSWORD', 'default')
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_safe_path(folder_path):
    """Get safe path that doesn't allow directory traversal"""
    if not folder_path:
        return app.config['STORAGE_FOLDER']
    
    # Split path into components and sanitize each one
    path_parts = folder_path.split('/')
    safe_parts = [secure_filename(part) for part in path_parts if part]
    
    # Construct the full path
    full_path = os.path.normpath(os.path.join(app.config['STORAGE_FOLDER'], *safe_parts))
    
    # Verify it's within storage folder (prevent directory traversal)
    if not full_path.startswith(os.path.normpath(app.config['STORAGE_FOLDER'])):
        return app.config['STORAGE_FOLDER']
    
    return full_path

def get_breadcrumb(folder_path):
    """Generate breadcrumb navigation"""
    breadcrumb = [{'name': 'Storage', 'path': ''}]
    
    if not folder_path:
        return breadcrumb
    
    parts = folder_path.split('/')
    current_path = ''
    
    for part in parts:
        if part:
            current_path = os.path.join(current_path, part)
            breadcrumb.append({'name': part, 'path': current_path})
    
    return breadcrumb

@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('file_list'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Get the current session password hash from environment
        session_password_hash = get_session_password_hash()
        
        if password_hash == session_password_hash:
            session['logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('file_list'))
        else:
            flash('Invalid password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/files')
@app.route('/files/<path:folder_path>')
@login_required
def file_list(folder_path=''):
    """List files and folders in the given path"""
    files = []
    folders = []
    
    # Get safe directory path
    current_dir = get_safe_path(folder_path)
    
    # Check if path exists and is a directory
    if not os.path.exists(current_dir) or not os.path.isdir(current_dir):
        flash('Folder not found!', 'error')
        return redirect(url_for('file_list'))
    
    try:
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            relative_path = os.path.join(folder_path, item) if folder_path else item
            
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path)
                modified = datetime.fromtimestamp(os.path.getmtime(item_path)).strftime('%Y-%m-%d %H:%M:%S')
                files.append({
                    'name': item,
                    'size': size,
                    'modified': modified,
                    'path': relative_path
                })
            else:
                folders.append({
                    'name': item,
                    'path': relative_path
                })
    except Exception as e:
        flash(f'Error reading directory: {str(e)}', 'error')
    
    # Get breadcrumb navigation
    breadcrumb = get_breadcrumb(folder_path)
    
    return render_template('files.html', files=files, folders=folders, 
                         current_path=folder_path, breadcrumb=breadcrumb)

@app.route('/download/<path:file_path>')
@login_required
def download_file(file_path):
    """Download a file from any subfolder"""
    try:
        # Clean the path - split and sanitize each component
        path_parts = file_path.split('/')
        safe_parts = [secure_filename(part) for part in path_parts if part]
        full_path = os.path.normpath(os.path.join(app.config['STORAGE_FOLDER'], *safe_parts))
        
        # Verify it's within storage folder
        if not full_path.startswith(os.path.normpath(app.config['STORAGE_FOLDER'])):
            flash('Invalid file path!', 'error')
            return redirect(url_for('file_list'))
        
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_file(full_path, as_attachment=True)
        else:
            flash('File not found!', 'error')
            return redirect(url_for('file_list'))
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('file_list'))

@app.route('/download-folder/<path:folder_path>')
@login_required
def download_folder(folder_path):
    """Download a folder as ZIP"""
    try:
        # Get safe folder path
        full_path = get_safe_path(folder_path)
        
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            flash('Folder not found!', 'error')
            return redirect(url_for('file_list'))
        
        # Create ZIP file in temporary location
        folder_name = os.path.basename(full_path)
        zip_path = os.path.join('/tmp', f'{folder_name}.zip')
        
        # Create ZIP file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, full_path)
                    zipf.write(file_path, arcname)
        
        # Send ZIP file
        return send_file(zip_path, as_attachment=True, 
                        download_name=f'{folder_name}.zip')
    except Exception as e:
        flash(f'Error downloading folder: {str(e)}', 'error')
        return redirect(url_for('file_list'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload file to current folder"""
    current_path = request.form.get('current_path', '')
    
    if 'file' not in request.files:
        flash('No file selected!', 'error')
        return redirect(url_for('file_list', folder_path=current_path))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected!', 'error')
        return redirect(url_for('file_list', folder_path=current_path))
    
    if file and allowed_file(file.filename):
        try:
            current_dir = get_safe_path(current_path)
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_dir, filename))
            flash(f'File "{filename}" uploaded successfully!', 'success')
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'error')
    else:
        flash('File type not allowed!', 'error')
    
    return redirect(url_for('file_list', folder_path=current_path))

@app.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    """Create folder in current directory"""
    current_path = request.form.get('current_path', '')
    folder_name = request.form.get('folder_name', '').strip()
    
    if not folder_name:
        flash('Folder name cannot be empty!', 'error')
        return redirect(url_for('file_list', folder_path=current_path))
    
    try:
        current_dir = get_safe_path(current_path)
        folder_path = os.path.join(current_dir, secure_filename(folder_name))
        os.makedirs(folder_path, exist_ok=True)
        flash(f'Folder "{folder_name}" created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating folder: {str(e)}', 'error')
    
    return redirect(url_for('file_list', folder_path=current_path))

@app.route('/delete/<path:file_path>')
@login_required
def delete_file(file_path):
    """Delete file or folder"""
    try:
        # Clean the path - split and sanitize each component
        path_parts = file_path.split('/')
        safe_parts = [secure_filename(part) for part in path_parts if part]
        full_path = os.path.normpath(os.path.join(app.config['STORAGE_FOLDER'], *safe_parts))
        
        # Verify it's within storage folder
        if not full_path.startswith(os.path.normpath(app.config['STORAGE_FOLDER'])):
            flash('Invalid file path!', 'error')
            return redirect(url_for('file_list'))
        
        if os.path.exists(full_path):
            if os.path.isfile(full_path):
                os.remove(full_path)
                flash(f'File deleted successfully!', 'success')
            else:
                # It's a directory
                shutil.rmtree(full_path)
                flash(f'Folder deleted successfully!', 'success')
        else:
            flash('File/Folder not found!', 'error')
    except Exception as e:
        flash(f'Error deleting: {str(e)}', 'error')
    
    # Get parent directory to redirect to
    parent_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else ''
    return redirect(url_for('file_list', folder_path=parent_path))

if __name__ == '__main__':
    app.run(debug=True)
