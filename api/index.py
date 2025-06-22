from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from werkzeug.utils import secure_filename
from PIL import Image
import re

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Simple in-memory storage for demo (Vercel is stateless)
uploaded_files = {}
phone_uploads = {}

def validate_image(file):
    """Basic image validation"""
    try:
        img = Image.open(file)
        width, height = img.size
        
        if width < 100 or height < 100:
            return False, "Image too small - minimum 100x100 pixels required"
        
        if width > 5000 or height > 5000:
            return False, "Image too large - maximum 5000x5000 pixels allowed"
        
        return True, "Valid image"
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

def validate_phone(phone):
    """Validate phone number format: 05 + 8 digits"""
    pattern = r'^05\d{8}$'
    return bool(re.match(pattern, phone))

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Photo Upload App</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .form-group { margin: 20px 0; }
            input, button { padding: 10px; margin: 5px; }
            button { background: #007bff; color: white; border: none; cursor: pointer; }
            .error { color: red; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <h1>Photo Upload App</h1>
        <form method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <input type="tel" name="phone" placeholder="05xxxxxxxx" pattern="05[0-9]{8}" maxlength="10" required>
            </div>
            <div class="form-group">
                <input type="file" name="photo" accept=".png,.jpg,.jpeg" required>
            </div>
            <button type="submit">Upload Photo</button>
        </form>
    </body>
    </html>
    '''

@app.route('/', methods=['POST'])
def upload():
    phone = request.form.get('phone')
    file = request.files.get('photo')
    
    if not phone or not file:
        return "Missing phone or file", 400
    
    if not validate_phone(phone):
        return "Invalid phone number. Must start with 05 followed by 8 digits", 400
    
    # Check file extension
    allowed_extensions = {'.png', '.jpg', '.jpeg'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        return "Only PNG and JPEG files are allowed", 400
    
    # Validate image
    is_valid, message = validate_image(file)
    if not is_valid:
        return message, 400
    
    # Store in memory (demo only)
    uploaded_files[phone] = file.filename
    
    return '''
    <h1>Success!</h1>
    <p>Photo uploaded successfully!</p>
    <a href="/">Upload Another</a>
    '''

# Export the Flask app for Vercel
def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    app.run(debug=True)