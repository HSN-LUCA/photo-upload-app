from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import os
from werkzeug.utils import secure_filename

application = Flask(__name__)
application.config['UPLOAD_FOLDER'] = 'uploads'
application.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(application.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    conn = sqlite3.connect('photos.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS photos 
                    (id INTEGER PRIMARY KEY, phone TEXT, filename TEXT)''')
    conn.commit()
    conn.close()

@application.route('/')
def index():
    return redirect(url_for('upload'))

@application.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        phone = request.form['phone']
        file = request.files['photo']
        
        if file and phone:
            filename = secure_filename(f"{phone}_{file.filename}")
            file.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
            
            conn = sqlite3.connect('photos.db')
            conn.execute('INSERT INTO photos (phone, filename) VALUES (?, ?)', (phone, filename))
            conn.commit()
            conn.close()
            
            return render_template('upload.html', success=True)
    
    return render_template('upload.html')

@application.route('/find', methods=['GET', 'POST'])
def find():
    photo_data = None
    if request.method == 'POST':
        phone = request.form['phone']
        
        conn = sqlite3.connect('photos.db')
        result = conn.execute('SELECT filename FROM photos WHERE phone = ? ORDER BY id DESC LIMIT 1', (phone,)).fetchone()
        conn.close()
        
        if result:
            photo_data = {'filename': result[0], 'phone': phone}
    
    return render_template('find.html', photo=photo_data)

@application.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(application.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    init_db()
    application.run(debug=True)