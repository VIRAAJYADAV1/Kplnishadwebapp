from flask import Flask, request, render_template_string, send_file, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import yt_dlp
import os
import uuid
import threading
import time
import shutil

app = Flask(__name__)
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["50 per hour"])

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# INLINE HTML TEMPLATE (No separate files needed)
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KPL VidoYT – Fast Online Video Downloader Tool</title>
    <meta name="description" content="KPL VidoYT - Free YouTube video downloader, MP3 converter, 4K HD download, Instagram reels. YouTube SEO tool & Shorts idea generator.">
    <meta name="keywords" content="youtube downloader, yt mp3, video download, youtube seo, shorts ideas, instagram reels download, tiktok download">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root{--bg-primary:#000;--bg-secondary:#0a0a0a;--accent:#006400;--text-primary:#fff;--text-secondary:#ccc;--card-bg:#1a1a1a;}
        [data-theme="light"]{--bg-primary:#f5f5f5;--bg-secondary:#fff;--accent:#228B22;--text-primary:#000;--text-secondary:#333;--card-bg:#f0f0f0;}
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,var(--bg-primary),var(--bg-secondary));color:var(--text-primary);min-height:100vh;}
        .container{max-width:1200px;margin:0 auto;padding:20px;}
        .header{text-align:center;padding:30px;background:var(--card-bg);border-radius:20px;margin-bottom:30px;box-shadow:0 20px 40px rgba(0,0,0,.3);}
        .logo{font-size:3em;font-weight:700;background:linear-gradient(45deg,var(--accent),#32CD32);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px;}
        .theme-toggle{position:fixed;top:20px;right:20px;background:var(--accent);color:#fff;border:none;width:60px;height:60px;border-radius:50%;cursor:pointer;font-size:1.5em;box-shadow:0 10px 20px rgba(0,100,0,.3);}
        .download-section{background:var(--card-bg);padding:30px;border-radius:20px;margin-bottom:30px;box-shadow:0 20px 40px rgba(0,0,0,.3);}
        .url-input{width:100%;padding:20px;font-size:1.1em;border:2px solid var(--accent);border-radius:15px;background:var(--bg-primary);color:var(--text-primary);}
        .format-options{display:flex;gap:15px;flex-wrap:wrap;margin:20px 0;}
        .format-btn,.quality-btn{padding:12px 24px;border:none;border-radius:25px;background:var(--accent);color:#fff;cursor:pointer;font-weight:700;}
        .format-btn.active,.quality-btn.active{background:#32CD32;transform:scale(1.05);}
        .download-btn{width:100%;padding:20px;font-size:1.5em;background:linear-gradient(45deg,var(--accent),#32CD32);color:#fff;border:none;border-radius:15px;cursor:pointer;}
        .progress-container{width:100%;height:8px;background:var(--bg-primary);border-radius:10px;overflow:hidden;margin:20px 0;display:none;}
        .progress-bar{height:100%;background:linear-gradient(90deg,var(--accent),#32CD32);width:0%;transition:width .3s ease;}
        .tools-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;}
        .tool-card{background:rgba(255,255,255,.05);padding:20px;border-radius:15px;text-align:center;border:1px solid var(--accent);}
        .services-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-top:20px;}
        .service-card{background:var(--accent);color:#fff;padding:20px;border-radius:15px;text-align:center;}
        .contact-links{display:flex;justify-content:center;gap:20px;flex-wrap:wrap;margin-top:20px;}
        .contact-links a{color:var(--accent);font-size:1.2em;}
        .trust-badge{background:linear-gradient(45deg,#FFD700,#FFA500);color:#000;padding:15px;border-radius:25px;font-weight:700;text-align:center;margin:20px 0;}
        @media(max-width:768px){.logo{font-size:2em;}.format-options{flex-direction:column;}}
    </style>
</head>
<body data-theme="dark">
    <button class="theme-toggle" onclick="toggleTheme()"><i class="fas fa-moon"></i></button>
    
    <div class="container">
        <div class="header">
            <div class="logo">KPL VidoYT</div>
            <p>Fast Online Video Downloader Tool • 4K HD • MP3</p>
        </div>
        
        <div class="download-section">
            <input type="url" class="url-input" id="videoUrl" placeholder="📎 YouTube/Instagram/TikTok URL paste karo...">
            <div class="format-options">
                <button class="format-btn active" data-format="video">🎥 Video</button>
                <button class="format-btn" data-format="audio">🎵 MP3</button>
            </div>
            <div class="format-options">
                <button class="quality-btn active" data-quality="best">4K</button>
                <button class="quality-btn" data-quality="720p">720p</button>
            </div>
            <div class="progress-container"><div class="progress-bar" id="progressBar"></div></div>
            <button class="download-btn" id="downloadBtn" onclick="startDownload()">🚀 Download Now</button>
        </div>
        
        <div style="background:var(--card-bg);padding:30px;border-radius:20px;margin-bottom:30px;">
            <h2 style="color:var(--accent);text-align:center;">🛠️ Free YouTube Tools</h2>
            <div class="tools-grid">
                <div class="tool-card">
                    <i style="font-size:2em;color:var(--accent);">🔍</i><br>YouTube SEO Tool<br><small>Keywords + Tags</small>
                </div>
                <div class="tool-card">
                    <i style="font-size:2em;color:var(--accent);">🖼️</i><br>Thumbnail Generator<br><small><a href="https://thumbrio-thumbnail.vercel.app" target="_blank">Click Here</a></small>
                </div>
                <div class="tool-card">
                    <i style="font-size:2em;color:var(--accent);">💡</i><br>Shorts Ideas<br><small>Viral content ideas</small>
                </div>
            </div>
        </div>
        
        <div style="background:var(--card-bg);padding:30px;border-radius:20px;">
            <h2 style="color:var(--accent);text-align:center;">🚀 KPL Premium Services</h2>
            <div class="services-grid">
                <div class="service-card"><i class="fab fa-youtube fa-2x"></i><br>YouTube Growth</div>
                <div class="service-card"><i class="fab fa-instagram fa-2x"></i><br>Instagram Automation</div>
                <div class="service-card"><i class="fab fa-whatsapp fa-2x"></i><br>WhatsApp Auto Reply</div>
                <div class="service-card"><i class="fab fa-telegram fa-2x"></i><br>Telegram Bots 24/7</div>
                <div class="service-card"><i class="fas fa-server fa-2x"></i><br>Low Cost RDP</div>
            </div>
        </div>
        
        <div class="trust-badge">
            ⭐⭐⭐⭐⭐ 5-Star by VIRAAJ YADAV @viraaj.technode
            <br><small>✅ 10K+ Users • 100% Safe • No Watermark</small>
        </div>
        
        <div style="background:var(--card-bg);padding:30px;border-radius:20px;text-align:center;">
            <h3>📞 Contact Instantly</h3>
            <div class="contact-links">
                <a href="https://wa.me/918218829942" target="_blank"><i class="fab fa-whatsapp fa-2x"></i><br>+91 82188 29942</a>
                <a href="https://www.instagram.com/kpl_study_3" target="_blank"><i class="fab fa-instagram fa-2x"></i><br>@kpl_study_3</a>
                <a href="https://t.me/Kplboy" target="_blank"><i class="fab fa-telegram fa-2x"></i><br>@Kplboy</a>
            </div>
            <div style="margin-top:20px;padding:15px;background:rgba(0,100,0,.2);border-radius:10px;">
                <strong>🖼️ YouTube Thumbnails:</strong> <a href="https://thumbrio-thumbnail.vercel.app" target="_blank">thumbrio-thumbnail.vercel.app</a>
            </div>
        </div>
    </div>
    
    <script>
        function toggleTheme(){const b=document.body,i=document.querySelector('.theme-toggle i');b.dataset.theme=b.dataset.theme==='dark'?'light':'dark';i.className=b.dataset.theme==='dark'?'fas fa-moon':'fas fa-sun';}
        document.querySelectorAll('.format-btn, .quality-btn').forEach(b=>b.onclick=()=>{document.querySelectorAll('.format-btn, .quality-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');});
        async function startDownload(){const u=document.getElementById('videoUrl').value;if(!u)return alert('URL daalo!');const b=document.getElementById('downloadBtn'),p=document.querySelector('.progress-container'),bar=document.getElementById('progressBar');b.disabled=true;b.textContent='⏳ Processing...';p.style.display='block';try{const f=document.querySelector('.format-btn.active').dataset.format,q=document.querySelector('.quality-btn.active').data||'best',r=await fetch('/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:u,format:f,quality:q})}),d=await r.json();let i=0;const check=async()=>{const s=await fetch(`/status/${d.task_id}`).then(x=>x.json());if(s.ready){bar.style.width='100%';setTimeout(()=>{window.open(`/file/${s.file}`);b.disabled=false;b.textContent='🚀 Download Now';p.style.display='none';},1500);}else{bar.style.width=`${i%90+10}%`;i++;setTimeout(check,800);}};check();}catch(e){alert('Error: '+e);b.disabled=false;b.textContent='🚀 Download Now';p.style.display='none';}}
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(MAIN_TEMPLATE)

@app.route('/download', methods=['POST'])
@limiter.limit("10 per minute")
def download():
    data = request.json
    url = data.get('url')
    quality = data.get('quality', 'best')
    format_type = data.get('format', 'video')
    task_id = str(uuid.uuid4())
    
    def process():
        try:
            ydl_opts = {
                'outtmpl': f'{DOWNLOAD_FOLDER}/{task_id}.%(ext)s',
                'quiet': True,
            }
            if format_type == 'audio':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
                })
            else:
                ydl_opts['format'] = quality
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find downloaded file
            for f in os.listdir(DOWNLOAD_FOLDER):
                if f.startswith(task_id):
                    open(f'/tmp/{task_id}', 'w').write(f)
                    return {'status': 'success', 'file': f}
        except:
            pass
        return {'status': 'error'}
    
    threading.Thread(target=process).start()
    return jsonify({'task_id': task_id})

@app.route('/status/<task_id>')
def status(task_id):
    files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(task_id)]
    return jsonify({'ready': bool(files), 'file': files[0] if files else None})

@app.route('/file/<filename>')
def get_file(filename):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
