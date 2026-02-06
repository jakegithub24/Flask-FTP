"""
Comprehensive Test Suite for Flask FTP Application
Tests authentication, file management, upload/download, and error handling
"""

import pytest
import os
import json
import hashlib
from io import BytesIO
from app import app
import tempfile
import shutil


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    # Create temporary storage directory for tests
    app.config['TESTING'] = True
    app.config['STORAGE_FOLDER'] = tempfile.mkdtemp()
    
    with app.test_client() as client:
        yield client
    
    # Cleanup temporary directory
    if os.path.exists(app.config['STORAGE_FOLDER']):
        shutil.rmtree(app.config['STORAGE_FOLDER'])


@pytest.fixture
def test_password():
    """Set up test password in environment"""
    return 'testpassword123'


@pytest.fixture
def app_with_password(test_password):
    """Create app with a test password"""
    os.environ['SESSION_PASSWORD'] = test_password
    from importlib import reload
    import app as app_module
    app_module = reload(app_module)
    
    app_module.app.config['TESTING'] = True
    app_module.app.config['STORAGE_FOLDER'] = tempfile.mkdtemp()
    
    with app_module.app.test_client() as client:
        yield client, app_module.app.config['STORAGE_FOLDER']
    
    # Cleanup
    if os.path.exists(app_module.app.config['STORAGE_FOLDER']):
        shutil.rmtree(app_module.app.config['STORAGE_FOLDER'])


# ============================================
# Test 1: Basic App and Routes Existence
# ============================================

class TestAppBasics:
    """Test basic application initialization"""
    
    def test_app_creation(self):
        """Test that Flask app is created successfully"""
        assert app is not None
        assert app.config['TESTING'] == False  # Default
    
    def test_app_secret_key(self):
        """Test that app has a secret key"""
        assert app.secret_key is not None
    
    def test_storage_folder_exists(self):
        """Test that storage folder is created"""
        assert os.path.exists(app.config['STORAGE_FOLDER'])
    
    def test_max_file_size_config(self):
        """Test that max content length is configured"""
        assert app.config['MAX_CONTENT_LENGTH'] == 100 * 1024 * 1024


# ============================================
# Test 2: Authentication and Login Routes
# ============================================

class TestAuthentication:
    """Test user authentication and login functionality"""
    
    def test_login_page_get(self, client):
        """Test GET request to login page"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'password' in response.data.lower()
    
    def test_login_with_correct_password(self, app_with_password):
        """Test login with correct password"""
        client, storage_folder = app_with_password
        test_password = 'testpassword123'
        
        response = client.post('/login', data={'password': test_password})
        assert response.status_code == 302  # Redirect on success
        
        # Verify session is set
        response = client.get('/files', follow_redirects=True)
        assert response.status_code == 200
    
    def test_login_with_wrong_password(self, app_with_password):
        """Test login with incorrect password"""
        client, storage_folder = app_with_password
        
        response = client.post('/login', data={'password': 'wrongpassword'}, follow_redirects=True)
        assert response.status_code == 200
        assert b'invalid' in response.data.lower() or b'error' in response.data.lower()
    
    def test_login_empty_password(self, client):
        """Test login with empty password"""
        response = client.post('/login', data={'password': ''}, follow_redirects=True)
        assert response.status_code == 200
    
    def test_logout(self, client):
        """Test logout functionality"""
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'logged out' in response.data.lower() or b'login' in response.data.lower()
    
    def test_index_redirect_to_login(self, client):
        """Test that index redirects to login when not authenticated"""
        response = client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'password' in response.data.lower()
    
    def test_index_redirect_to_filelist_when_logged_in(self, app_with_password):
        """Test that index redirects to file list when authenticated"""
        client, storage_folder = app_with_password
        
        # Login first
        client.post('/login', data={'password': 'testpassword123'})
        
        # Now test index redirect
        response = client.get('/', follow_redirects=False)
        assert response.status_code == 302


# ============================================
# Test 3: File List Route
# ============================================

class TestFileList:
    """Test file listing functionality"""
    
    def test_file_list_requires_login(self, client):
        """Test that /files route requires authentication"""
        response = client.get('/files', follow_redirects=False)
        assert response.status_code == 302  # Redirect to login
    
    def test_file_list_empty_storage(self, app_with_password):
        """Test file list with empty storage"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Access file list
        response = client.get('/files')
        assert response.status_code == 200
    
    def test_file_list_with_files(self, app_with_password):
        """Test file list with existing files"""
        client, storage_folder = app_with_password
        
        # Create test file
        test_file_path = os.path.join(storage_folder, 'test.txt')
        with open(test_file_path, 'w') as f:
            f.write('test content')
        
        # Login and access file list
        client.post('/login', data={'password': 'testpassword123'})
        response = client.get('/files')
        
        assert response.status_code == 200
        assert b'test.txt' in response.data
    
    def test_file_list_with_folders(self, app_with_password):
        """Test file list displays folders"""
        client, storage_folder = app_with_password
        
        # Create test folder
        test_folder = os.path.join(storage_folder, 'testfolder')
        os.makedirs(test_folder, exist_ok=True)
        
        # Login and access file list
        client.post('/login', data={'password': 'testpassword123'})
        response = client.get('/files')
        
        assert response.status_code == 200
        assert b'testfolder' in response.data
    
    def test_folder_navigation(self, app_with_password):
        """Test navigating into a folder"""
        client, storage_folder = app_with_password
        
        # Create nested folder structure
        test_folder = os.path.join(storage_folder, 'parent', 'child')
        os.makedirs(test_folder, exist_ok=True)
        
        # Create a file in the child folder
        test_file = os.path.join(test_folder, 'nested.txt')
        with open(test_file, 'w') as f:
            f.write('nested file')
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Navigate to parent folder
        response = client.get('/files/parent', follow_redirects=True)
        assert response.status_code == 200
        assert b'child' in response.data
        
        # Navigate to child folder
        response = client.get('/files/parent/child', follow_redirects=True)
        assert response.status_code == 200
        assert b'nested.txt' in response.data


# ============================================
# Test 4: File Upload
# ============================================

class TestFileUpload:
    """Test file upload functionality"""
    
    def test_upload_requires_login(self, client):
        """Test that upload requires authentication"""
        response = client.post('/upload', follow_redirects=False)
        assert response.status_code == 302  # Redirect to login
    
    def test_upload_valid_file(self, app_with_password):
        """Test uploading a valid file"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Upload file with allowed extension
        data = {
            'file': (BytesIO(b'test file content'), 'testfile.txt'),
            'current_path': ''
        }
        response = client.post('/upload', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'uploaded successfully' in response.data.lower()
        assert os.path.exists(os.path.join(storage_folder, 'testfile.txt'))
    
    def test_upload_to_subfolder(self, app_with_password):
        """Test uploading a file to a subfolder"""
        client, storage_folder = app_with_password
        
        # Create subfolder
        subfolder = os.path.join(storage_folder, 'uploads')
        os.makedirs(subfolder, exist_ok=True)
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Upload file to subfolder
        data = {
            'file': (BytesIO(b'nested file'), 'nested.txt'),
            'current_path': 'uploads'
        }
        response = client.post('/upload', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        assert os.path.exists(os.path.join(subfolder, 'nested.txt'))
    
    def test_upload_multiple_files(self, app_with_password):
        """Test uploading multiple files"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Upload multiple files
        files = ['file1.txt', 'file2.pdf', 'image.jpg']
        for filename in files:
            data = {
                'file': (BytesIO(b'test content'), filename),
                'current_path': ''
            }
            response = client.post('/upload', data=data, follow_redirects=True)
            assert response.status_code == 200
            assert os.path.exists(os.path.join(storage_folder, filename))
    
    def test_upload_invalid_file_type(self, app_with_password):
        """Test uploading file with disallowed extension"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Try to upload .exe file (not allowed)
        data = {
            'file': (BytesIO(b'malicious'), 'malware.exe'),
            'current_path': ''
        }
        response = client.post('/upload', data=data, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'not allowed' in response.data.lower()
        assert not os.path.exists(os.path.join(storage_folder, 'malware.exe'))
    
    def test_upload_no_file(self, app_with_password):
        """Test upload with no file selected"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Post without file
        response = client.post('/upload', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'no file' in response.data.lower()
    
    def test_upload_allowed_extensions(self, app_with_password):
        """Test all allowed file extensions"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Test allowed extensions
        allowed_files = ['doc.txt', 'image.pdf', 'photo.png', 'pic.jpg', 'anim.gif',
                        'archive.zip', 'document.doc', 'sheet.xls', 'slide.ppt']
        
        for filename in allowed_files:
            data = {
                'file': (BytesIO(b'content'), filename),
                'current_path': ''
            }
            response = client.post('/upload', data=data, follow_redirects=True)
            assert response.status_code == 200


# ============================================
# Test 5: File Download
# ============================================

class TestFileDownload:
    """Test file download functionality"""
    
    def test_download_requires_login(self, client):
        """Test that download requires authentication"""
        response = client.get('/download/testfile.txt', follow_redirects=False)
        assert response.status_code == 302  # Redirect to login
    
    def test_download_existing_file(self, app_with_password):
        """Test downloading an existing file"""
        client, storage_folder = app_with_password
        
        # Create test file
        test_file_path = os.path.join(storage_folder, 'download_test.txt')
        test_content = b'test file content for download'
        with open(test_file_path, 'wb') as f:
            f.write(test_content)
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Download file
        response = client.get('/download/download_test.txt')
        assert response.status_code == 200
        assert test_content in response.data
    
    def test_download_nonexistent_file(self, app_with_password):
        """Test downloading a file that doesn't exist"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Try to download non-existent file
        response = client.get('/download/nonexistent.txt', follow_redirects=True)
        assert response.status_code == 200
        assert b'not found' in response.data.lower()
    
    def test_download_with_special_characters(self, app_with_password):
        """Test downloading file with special characters in name"""
        client, storage_folder = app_with_password
        
        # Create file with special characters
        test_file_path = os.path.join(storage_folder, 'test-file_123.txt')
        with open(test_file_path, 'w') as f:
            f.write('special chars test')
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Download file
        response = client.get('/download/test-file_123.txt')
        assert response.status_code == 200
    
    def test_download_file_from_subfolder(self, app_with_password):
        """Test downloading a file from a nested folder"""
        client, storage_folder = app_with_password
        
        # Create nested folder and file
        nested_folder = os.path.join(storage_folder, 'parent', 'child')
        os.makedirs(nested_folder, exist_ok=True)
        
        test_file = os.path.join(nested_folder, 'nested.txt')
        test_content = b'nested file content'
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Download nested file
        response = client.get('/download/parent/child/nested.txt')
        assert response.status_code == 200
        assert test_content in response.data


class TestDownloadFolder:
    """Test folder download as ZIP functionality"""
    
    def test_download_folder_requires_login(self, client):
        """Test that folder download requires authentication"""
        response = client.get('/download-folder/testfolder', follow_redirects=False)
        assert response.status_code == 302  # Redirect to login
    
    def test_download_folder_as_zip(self, app_with_password):
        """Test downloading a folder as ZIP"""
        client, storage_folder = app_with_password
        
        # Create folder with files
        test_folder = os.path.join(storage_folder, 'zip_test')
        os.makedirs(test_folder, exist_ok=True)
        
        # Create multiple files
        for i in range(3):
            test_file = os.path.join(test_folder, f'file{i}.txt')
            with open(test_file, 'w') as f:
                f.write(f'file content {i}')
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Download folder as ZIP
        response = client.get('/download-folder/zip_test')
        assert response.status_code == 200
        assert b'PK' in response.data[:4]  # ZIP file signature
    
    def test_download_empty_folder_as_zip(self, app_with_password):
        """Test downloading an empty folder as ZIP"""
        client, storage_folder = app_with_password
        
        # Create empty folder
        test_folder = os.path.join(storage_folder, 'empty_folder')
        os.makedirs(test_folder, exist_ok=True)
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Download empty folder as ZIP
        response = client.get('/download-folder/empty_folder')
        assert response.status_code == 200
        assert b'PK' in response.data[:4]  # ZIP file signature
    
    def test_download_nested_folder_as_zip(self, app_with_password):
        """Test downloading a nested folder as ZIP"""
        client, storage_folder = app_with_password
        
        # Create nested folder structure
        nested_folder = os.path.join(storage_folder, 'parent', 'nested_zip')
        os.makedirs(nested_folder, exist_ok=True)
        
        test_file = os.path.join(nested_folder, 'inside.txt')
        with open(test_file, 'w') as f:
            f.write('nested content')
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Download nested folder as ZIP
        response = client.get('/download-folder/parent/nested_zip')
        assert response.status_code == 200
        assert b'PK' in response.data[:4]  # ZIP file signature


# ============================================
# Test 6: Create Folder
# ============================================

class TestCreateFolder:
    """Test folder creation functionality"""
    
    def test_create_folder_requires_login(self, client):
        """Test that folder creation requires authentication"""
        response = client.post('/create_folder', follow_redirects=False)
        assert response.status_code == 302  # Redirect to login
    
    def test_create_folder_success(self, app_with_password):
        """Test successful folder creation"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Create folder
        response = client.post('/create_folder', 
                              data={'folder_name': 'newfolder', 'current_path': ''},
                              follow_redirects=True)
        
        assert response.status_code == 200
        assert b'created successfully' in response.data.lower()
        assert os.path.exists(os.path.join(storage_folder, 'newfolder'))
    
    def test_create_folder_in_subfolder(self, app_with_password):
        """Test creating folder in a subfolder"""
        client, storage_folder = app_with_password
        
        # Create parent folder
        parent_folder = os.path.join(storage_folder, 'parent')
        os.makedirs(parent_folder, exist_ok=True)
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Create subfolder inside parent
        response = client.post('/create_folder',
                              data={'folder_name': 'child', 'current_path': 'parent'},
                              follow_redirects=True)
        
        assert response.status_code == 200
        assert os.path.exists(os.path.join(parent_folder, 'child'))
    
    def test_create_multiple_folders(self, app_with_password):
        """Test creating multiple folders"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        folders = ['folder1', 'folder2', 'folder3']
        for folder_name in folders:
            response = client.post('/create_folder',
                                  data={'folder_name': folder_name, 'current_path': ''},
                                  follow_redirects=True)
            assert response.status_code == 200
            assert os.path.exists(os.path.join(storage_folder, folder_name))
    
    def test_create_folder_empty_name(self, app_with_password):
        """Test creating folder with empty name"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Try to create folder with empty name
        response = client.post('/create_folder',
                              data={'folder_name': '', 'current_path': ''},
                              follow_redirects=True)
        
        assert response.status_code == 200
        assert b'cannot be empty' in response.data.lower()
    
    def test_create_folder_with_special_characters(self, app_with_password):
        """Test creating folder with special characters"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Create folder with special characters (secure_filename handles this)
        response = client.post('/create_folder',
                              data={'folder_name': 'my-folder_2024', 'current_path': ''},
                              follow_redirects=True)
        
        assert response.status_code == 200


# ============================================
# Test 7: Delete File/Folder
# ============================================

class TestDeleteFileFolder:
    """Test file and folder deletion functionality"""
    
    def test_delete_requires_login(self, client):
        """Test that delete requires authentication"""
        response = client.get('/delete/testfile.txt', follow_redirects=False)
        assert response.status_code == 302  # Redirect to login
    
    def test_delete_file_success(self, app_with_password):
        """Test successful file deletion"""
        client, storage_folder = app_with_password
        
        # Create test file
        test_file_path = os.path.join(storage_folder, 'delete_me.txt')
        with open(test_file_path, 'w') as f:
            f.write('delete this')
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Delete file
        response = client.get('/delete/delete_me.txt', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'deleted successfully' in response.data.lower()
        assert not os.path.exists(test_file_path)
    
    def test_delete_folder_success(self, app_with_password):
        """Test successful folder deletion"""
        client, storage_folder = app_with_password
        
        # Create test folder
        test_folder = os.path.join(storage_folder, 'delete_folder')
        os.makedirs(test_folder, exist_ok=True)
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Delete folder
        response = client.get('/delete/delete_folder', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'deleted successfully' in response.data.lower()
        assert not os.path.exists(test_folder)
    
    def test_delete_nonexistent_file(self, app_with_password):
        """Test deleting a file that doesn't exist"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Try to delete non-existent file
        response = client.get('/delete/nonexistent.txt', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'not found' in response.data.lower()
    
    def test_delete_folder_with_files(self, app_with_password):
        """Test deleting folder containing files"""
        client, storage_folder = app_with_password
        
        # Create folder with files
        test_folder = os.path.join(storage_folder, 'folder_with_files')
        os.makedirs(test_folder, exist_ok=True)
        
        test_file = os.path.join(test_folder, 'file.txt')
        with open(test_file, 'w') as f:
            f.write('content')
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Delete folder
        response = client.get('/delete/folder_with_files', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'deleted successfully' in response.data.lower()
        assert not os.path.exists(test_folder)
    
    def test_delete_file_from_subfolder(self, app_with_password):
        """Test deleting a file from a nested folder"""
        client, storage_folder = app_with_password
        
        # Create nested folder and file
        nested_folder = os.path.join(storage_folder, 'parent', 'child')
        os.makedirs(nested_folder, exist_ok=True)
        
        test_file = os.path.join(nested_folder, 'nested.txt')
        with open(test_file, 'w') as f:
            f.write('nested content')
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Delete nested file
        response = client.get('/delete/parent/child/nested.txt', follow_redirects=True)
        
        assert response.status_code == 200
        assert not os.path.exists(test_file)


# ============================================
# Test 8: Security Tests
# ============================================

class TestSecurity:
    """Test security features"""
    
    def test_path_traversal_prevention(self, app_with_password):
        """Test that path traversal attacks are prevented"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Try path traversal attack
        response = client.get('/download/../../../etc/passwd', follow_redirects=True)
        assert response.status_code == 200
        assert b'not found' in response.data.lower()
    
    def test_allowed_file_extensions(self, client):
        """Test that file extension validation works"""
        from app import allowed_file
        
        # Test allowed extensions
        assert allowed_file('document.txt') == True
        assert allowed_file('image.pdf') == True
        assert allowed_file('photo.png') == True
        assert allowed_file('pic.jpg') == True
        assert allowed_file('archive.zip') == True
        
        # Test disallowed extensions
        assert allowed_file('malware.exe') == False
        assert allowed_file('script.sh') == False
        assert allowed_file('virus.bat') == False
        assert allowed_file('file.py') == False
    
    def test_secure_filename_handling(self, app_with_password):
        """Test that file names are sanitized"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Try to upload file with path traversal in name
        data = {
            'file': (BytesIO(b'content'), '../../../etc/passwd.txt')
        }
        response = client.post('/upload', data=data, follow_redirects=True)
        
        # Should only allow the filename part
        unsafe_path = os.path.join(storage_folder, '..', '..', '..', 'etc', 'passwd.txt')
        assert not os.path.exists(unsafe_path)


# ============================================
# Test 9: Session Management
# ============================================

class TestSessionManagement:
    """Test session handling"""
    
    def test_session_persistence_across_requests(self, app_with_password):
        """Test that session persists across multiple requests"""
        client, storage_folder = app_with_password
        
        # Login
        response1 = client.post('/login', data={'password': 'testpassword123'})
        
        # Access protected route
        response2 = client.get('/files')
        assert response2.status_code == 200
        
        # Access another protected route
        response3 = client.post('/create_folder', 
                               data={'folder_name': 'test'},
                               follow_redirects=True)
        assert response3.status_code == 200
    
    def test_logout_clears_session(self, app_with_password):
        """Test that logout clears the session"""
        client, storage_folder = app_with_password
        
        # Login
        client.post('/login', data={'password': 'testpassword123'})
        
        # Logout
        client.get('/logout')
        
        # Try to access protected route
        response = client.get('/files', follow_redirects=False)
        assert response.status_code == 302  # Redirect to login


# ============================================
# Test 10: Error Handling
# ============================================

class TestErrorHandling:
    """Test error handling"""
    
    def test_nonexistent_route(self, client):
        """Test accessing non-existent route"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
    
    def test_invalid_request_method(self, client):
        """Test invalid HTTP method"""
        response = client.put('/login')
        assert response.status_code in [405, 404]  # Method not allowed or not found


if __name__ == '__main__':
    # Run tests with pytest
    # Command: pytest test_app.py -v
    pytest.main([__file__, '-v'])
