from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
# Use persistent volume for data storage
DATA_DIR = '/app/data' if os.path.exists('/app/data') else '.'
app.config['UPLOAD_FOLDER'] = os.path.join(DATA_DIR, 'uploads')
app.config['DATABASE_PATH'] = os.path.join(DATA_DIR, 'photos.db')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def validate_image(image_path):
    """Basic image validation"""
    try:
        # Check if file is a valid image
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Basic size validation
            if width < 100 or height < 100:
                return False, "Image too small - minimum 100x100 pixels required"
            
            if width > 5000 or height > 5000:
                return False, "Image too large - maximum 5000x5000 pixels allowed"
        
        return True, "Valid image"
        
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

# Initialize database
def init_db():
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    
    # Create photos table
    conn.execute('''CREATE TABLE IF NOT EXISTS photos 
                    (id INTEGER PRIMARY KEY, phone TEXT, filename TEXT, upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Check if upload_time column exists, if not add it
    try:
        conn.execute('SELECT upload_time FROM photos LIMIT 1')
    except sqlite3.OperationalError:
        # Column doesn't exist, add it without default
        conn.execute('ALTER TABLE photos ADD COLUMN upload_time TIMESTAMP')
        # Update existing records with current timestamp
        conn.execute('UPDATE photos SET upload_time = datetime("now") WHERE upload_time IS NULL')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS settings 
                    (key TEXT PRIMARY KEY, value TEXT)''')
    # Default settings
    conn.execute('INSERT OR IGNORE INTO settings VALUES (?, ?)', ('title', 'Photo App'))
    conn.execute('INSERT OR IGNORE INTO settings VALUES (?, ?)', ('logo', ''))
    conn.execute('INSERT OR IGNORE INTO settings VALUES (?, ?)', ('primary_color', '#007bff'))
    conn.execute('INSERT OR IGNORE INTO settings VALUES (?, ?)', ('secondary_color', '#ff6b6b'))
    conn.execute('INSERT OR IGNORE INTO settings VALUES (?, ?)', ('background_color', '#f8f9fa'))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect(url_for('upload'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    settings = get_settings()
    error_message = None
    
    if request.method == 'POST':
        phone = request.form['phone']
        file = request.files['photo']
        
        if file and phone:
            # Validate phone number format
            if not validate_phone(phone):
                error_message = "Invalid phone number. Must start with 05 followed by 8 digits (e.g., 0512345678)"
            # Check if phone number can upload (5-minute restriction)
            elif not can_upload_phone(phone):
                error_message = "This phone number was used recently. Please wait 5 minutes before uploading again."
            else:
                # Check file extension
                allowed_extensions = {'.png', '.jpg', '.jpeg'}
                file_ext = os.path.splitext(file.filename)[1].lower()
                
                if file_ext not in allowed_extensions:
                    error_message = "Only PNG and JPEG files are allowed"
                else:
                    filename = secure_filename(f"{phone}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    # Validate image
                    is_valid, message = validate_image(filepath)
                    
                    if is_valid:
                        # Save to database with timestamp
                        conn = sqlite3.connect(app.config['DATABASE_PATH'])
                        conn.execute('INSERT INTO photos (phone, filename, upload_time) VALUES (?, ?, datetime("now"))', 
                                   (phone, filename))
                        conn.commit()
                        conn.close()
                        
                        return render_template('upload.html', success=True, settings=settings)
                    else:
                        # Remove invalid file
                        os.remove(filepath)
                        error_message = message
    
    return render_template('upload.html', settings=settings, error=error_message)

@app.route('/find', methods=['GET', 'POST'])
def find():
    settings = get_settings()
    photo_data = None
    if request.method == 'POST':
        phone = request.form['phone']
        
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        result = conn.execute('SELECT filename FROM photos WHERE phone = ? ORDER BY id DESC LIMIT 1', (phone,)).fetchone()
        conn.close()
        
        if result:
            photo_data = {'filename': result[0], 'phone': phone}
    
    return render_template('find.html', photo=photo_data, settings=settings)

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

@app.route('/admin')
def admin():
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    settings = dict(conn.execute('SELECT key, value FROM settings').fetchall())
    conn.close()
    return render_template('admin.html', settings=settings)

@app.route('/admin/update', methods=['POST'])
def update_settings():
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    
    # Handle logo file upload
    if 'logo' in request.files and request.files['logo'].filename:
        logo_file = request.files['logo']
        logo_filename = secure_filename(f"logo_{logo_file.filename}")
        logo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))
        conn.execute('UPDATE settings SET value = ? WHERE key = ?', (f'/uploads/{logo_filename}', 'logo'))
    
    # Handle other settings
    for key in ['title', 'primary_color', 'secondary_color', 'background_color']:
        if key in request.form:
            conn.execute('UPDATE settings SET value = ? WHERE key = ?', (request.form[key], key))
    
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

def get_settings():
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    settings = dict(conn.execute('SELECT key, value FROM settings').fetchall())
    conn.close()
    return settings

def cleanup_old_data():
    """Remove photos and data older than 5 minutes"""
    while True:
        try:
            conn = sqlite3.connect(app.config['DATABASE_PATH'])
            # Get photos older than 5 minutes
            cutoff_time = datetime.now() - timedelta(minutes=5)
            old_photos = conn.execute('SELECT filename FROM photos WHERE upload_time < ?', (cutoff_time,)).fetchall()
            
            # Delete old photo files
            for (filename,) in old_photos:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Delete old database records
            conn.execute('DELETE FROM photos WHERE upload_time < ?', (cutoff_time,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        time.sleep(30)  # Check every 30 seconds

def validate_phone(phone):
    """Validate phone number format: 05 + 8 digits"""
    import re
    pattern = r'^05\d{8}$'
    return bool(re.match(pattern, phone))

def can_upload_phone(phone):
    """Check if phone number can upload (not used in last 5 minutes)"""
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    cutoff_time = datetime.now() - timedelta(minutes=5)
    recent_upload = conn.execute('SELECT id FROM photos WHERE phone = ? AND upload_time > ?', (phone, cutoff_time)).fetchone()
    conn.close()
    return recent_upload is None

if __name__ == '__main__':
    init_db()
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
    cleanup_thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True)