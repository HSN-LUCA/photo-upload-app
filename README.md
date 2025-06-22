# Photo Upload App

A Flask-based photo upload application with face detection and automatic cleanup.

## Features

- 📸 **Face Detection**: Only accepts photos with human faces
- ⏰ **10-Minute Restrictions**: Phone numbers can't upload again for 10 minutes
- 🗑️ **Auto Cleanup**: Photos and data automatically deleted after 10 minutes
- 🎨 **Admin Panel**: Customize colors, logo, and app title
- 🔒 **File Validation**: Only PNG and JPEG files accepted
- 🌐 **Cloud Ready**: Deployed on Fly.io

## Live Demo

🚀 **Live App**: https://photo-app-new.fly.dev
🔧 **Admin Panel**: https://photo-app-new.fly.dev/admin

## Local Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run App**:
   ```bash
   python app.py
   ```

3. **Access**:
   - App: http://localhost:8080
   - Admin: http://localhost:8080/admin

## Technologies Used

- **Backend**: Python, Flask
- **Database**: SQLite
- **Face Detection**: MediaPipe
- **Frontend**: HTML, CSS, JavaScript
- **Hosting**: Fly.io
- **File Processing**: Pillow (PIL)

## Deployment

Deployed using Fly.io with Docker containerization.

## Privacy & Security

- Photos automatically deleted after 10 minutes
- Face detection prevents inappropriate uploads
- Phone number restrictions prevent spam
- HTTPS enabled by default