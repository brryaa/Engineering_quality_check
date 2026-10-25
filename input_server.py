import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

BUFFER_FILE = '/tmp/input_buffer.json'

HTML_CONTENT = """<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <title>协作缓冲区 (独立版)</title>
    <style>
        body { font-family: sans-serif; padding: 20px; max-width: 900px; margin: 0 auto; background: #f0f2f5; }
        #editor { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        h3 { margin-top: 0; color: #333; }
        textarea { width: 100%; height: 200px; border: 1px solid #ddd; border-radius: 8px; padding: 15px; box-sizing: border-box; font-size: 16px; transition: border 0.3s; }
        textarea:focus { border-color: #0d6c68; outline: none; }
        .limit-info { text-align: right; font-size: 12px; color: #888; margin-top: 5px; }
        .image-gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; border: 2px dashed #eee; padding: 15px; border-radius: 8px; min-height: 100px; }
        .img-item { position: relative; border-radius: 6px; overflow: hidden; background: #fafafa; border: 1px solid #eee; height: 150px; }
        .img-item img { width: 100%; height: 100%; object-fit: cover; }
        .img-item .remove-btn { position: absolute; top: 5px; right: 5px; background: rgba(255,0,0,0.7); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; font-weight: bold; }
        .hint { color: #666; font-size: 0.9em; margin: 15px 0 5px; }
        .controls { margin-top: 20px; display: flex; align-items: center; gap: 20px; }
        button { background: #0d6c68; color: white; border: none; padding: 12px 30px; border-radius: 25px; cursor: pointer; font-weight: bold; font-size: 16px; box-shadow: 0 4px 10px rgba(13,108,104,0.3); }
        button:hover { background: #084946; }
        .status-bar { font-size: 13px; color: #555; }
    </style>
</head>
<body>
    <div id='editor'>
        <h3>协作缓冲区</h3>
        <p class='hint'>输入文字并粘贴图片 (Ctrl+V)。单张 &lt; 20MB，总计 &lt; 50MB。</p>
        <textarea id='text-input' placeholder='在这里输入文字...' oninput='checkLimits()'></textarea>
        <div id='char-count' class='limit-info'>0 / 5000 字</div>
        <div class='hint'>图片库 (支持多张粘贴):</div>
        <div id='image-gallery' class='image-gallery'></div>
        <div class='controls'>
            <button onclick='saveData()'>保存并同步</button>
            <div id='total-size' class='status-bar'>总计: 0 MB / 50 MB</div>
        </div>
    </div>
    <script>
        let imageList = [];
        function checkLimits() {
            const text = document.getElementById('text-input').value;
            const counter = document.getElementById('char-count');
            counter.innerText = text.length + ' / 5000 字';
            counter.style.color = text.length > 5000 ? 'red' : '#888';
        }
        document.addEventListener('paste', function(e) {
            const items = e.clipboardData.items;
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    const blob = items[i].getAsFile();
                    if (blob.size > 20*1024*1024) { alert('单张超20MB'); continue; }
                    const currentTotal = imageList.reduce((s, m) => s + m.size, 0);
                    if (currentTotal + blob.size > 50*1024*1024) { alert('总计超50MB'); continue; }
                    const reader = new FileReader();
                    reader.onload = (ev) => {
                        imageList.push({data: ev.target.result, size: blob.size});
                        renderGallery();
                    };
                    reader.readAsDataURL(blob);
                }
            }
        });
        function renderGallery() {
            const g = document.getElementById('image-gallery');
            const t = document.getElementById('total-size');
            g.innerHTML = imageList.length ? '' : '暂无图片，点击后按 Ctrl+V 粘贴';
            imageList.forEach((img, i) => {
                const d = document.createElement('div');
                d.className = 'img-item';
                d.innerHTML = '<img src="' + img.data + '"><button class="remove-btn" onclick="removeImg(' + i + ')">×</button>';
                g.appendChild(d);
            });
            t.innerText = '总计: ' + (imageList.reduce((s, m) => s + m.size, 0)/(1024*1024)).toFixed(2) + ' MB / 50 MB';
        }
        function removeImg(i) { imageList.splice(i, 1); renderGallery(); }
        async function saveData() {
            const text = document.getElementById('text-input').value;
            if (text.length > 5000) { alert('太长了！'); return; }
            const res = await fetch('/api/input', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text, images: imageList})
            });
            if (res.ok) alert('同步成功');
            else alert('保存失败，可能文件过大');
        }
        (async function() {
            const r = await fetch('/api/input');
            const d = await r.json();
            if (d.text) document.getElementById('text-input').value = d.text;
            if (d.images) { imageList = d.images; renderGallery(); }
            checkLimits();
        })();
    </script>
</body>
</html>"""

class InputHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/input.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        elif parsed.path == '/api/input':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            content = {'text': '', 'images': []}
            if os.path.exists(BUFFER_FILE):
                try:
                    with open(BUFFER_FILE, 'r') as f:
                        content = json.load(f)
                except:
                    pass
            self.wfile.write(json.dumps(content).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/input':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body.decode('utf-8'))
                except:
                    data = {}
            else:
                data = {}
                
            text = data.get('text', '')
            images = data.get('images', [])
            
            if len(text) > 5000:
                self.send_response(400)
                self.end_headers()
                return
                
            total_size = sum(len(img.get('data', '')) * 0.75 for img in images)
            if total_size > 50 * 1024 * 1024:
                self.send_response(400)
                self.end_headers()
                return

            with open(BUFFER_FILE, 'w') as f:
                json.dump({'text': text, 'images': images}, f)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 8888), InputHandler)
    print("Starting input buffer server on port 8888")
    server.serve_forever()