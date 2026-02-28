from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

GATEWAY_URL = os.environ.get('GATEWAY_URL', 'http://gateway:8080')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    try:
        response = requests.post(
            f'{GATEWAY_URL}/login',
            auth=(email, password)
        )
        
        if response.status_code == 200:
            session['token'] = response.text
            session['email'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'token' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html', email=session.get('email'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'token' not in session:
        return redirect(url_for('index'))
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('dashboard'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        files = {'file': (file.filename, file.stream, file.content_type)}
        headers = {'Authorization': f'Bearer {session["token"]}'}
        
        response = requests.post(
            f'{GATEWAY_URL}/upload',
            files=files,
            headers=headers
        )
        
        if response.status_code == 200:
            flash('Video uploaded successfully! Check your email for the file ID.', 'success')
        else:
            flash(f'Upload failed: {response.text}', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/download', methods=['POST'])
def download():
    if 'token' not in session:
        return redirect(url_for('index'))
    
    file_id = request.form.get('file_id')
    
    if not file_id:
        flash('Please enter a file ID', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        response = requests.get(
            f'{GATEWAY_URL}/download',
            params={'fid': file_id},
            headers=headers,
            stream=True
        )
        
        if response.status_code == 200:
            return send_file(
                response.raw,
                as_attachment=True,
                download_name=f'{file_id}.mp3',
                mimetype='audio/mpeg'
            )
        else:
            flash(f'Download failed: {response.text}', 'error')
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
