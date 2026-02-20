from flask import Flask, request, render_template, send_file, jsonify, flash, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import yt_dlp
import os
import uuid
import threading
import time
from datetime import datetime
import shutil

app = Flask(__name__)
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["100 per hour"])

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Admin config
ADMIN_USERS = {
    'VIRAAJ YADAV': {'insta': 'https://www.instagram.com/viraaj.technode?igsh=bWplYXJzNm53cGsw'}
}

# SEO Keywords (hidden meta)
SEO_KEYWORDS = [
    "youtube video downloader", "yt mp3", "youtube shorts download", 
    "free youtube downloader", "4k video download", "instagram reels download",
    "youtube seo tool", "youtube keyword tool", "youtube shorts ideas 2026"
]

@app.route('/')
def index():
    return render_template('index.html', admin=ADMIN_USERS)

@app.route('/download', methods=['POST'])
@limiter.limit("10 per minute")
def download():
    url = request.json.get('url')
    quality = request.json.get('quality', 'best')
    format_type = request.json.get('format', 'video')
    task_id = str(uuid.uuid4())
    
    def process_download():
        try:
            ydl_opts = {
                'outtmpl': f'{DOWNLOAD_FOLDER}/{task_id}.%(ext)s',
                'quiet': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            if format_type == 'audio':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                })
            else:
                ydl_opts['format'] = quality
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
            
            return {'status': 'success', 'file': f'{task_id}.mp4', 'title': title}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    thread = threading.Thread(target=process_download)
    thread.start()
    
    return jsonify({'task_id': task_id})

@app.route('/status/<task_id>')
def status(task_id):
    files = os.listdir(DOWNLOAD_FOLDER)
    for f in files:
        if f.startswith(task_id):
            return jsonify({'ready': True, 'file': f})
    return jsonify({'ready': False})

@app.route('/file/<filename>')
def get_file(filename):
    return send_file(os.path.join(DOWNLOAD_FOLDER, filename), as_attachment=True)

@app.route('/seo')
def seo_tools():
    return render_template('seo.html')

@app.route('/thumbnail')
def thumbnail_tool():
    return render_template('thumbnail.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
