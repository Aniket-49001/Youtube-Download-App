# app.py
import os
import tempfile
import shutil
import uuid
import threading
import queue
from flask import Flask, request, jsonify, send_file, render_template, after_this_request
from yt_dlp import YoutubeDL

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DOWNLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'Downloads', 'YouTube Downloader')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# In-memory task storage and queue
tasks = {}
task_queue = queue.Queue()

# Default options shared across operations
YDL_OPTS_BASE = {
    'quiet': True,
    'no_warnings': True,
}
COOKIES_FILE = os.path.join(BASE_DIR, 'cookies.txt')
if os.path.exists(COOKIES_FILE):
    YDL_OPTS_BASE['cookiefile'] = COOKIES_FILE

def get_simple_error(error_str):
    """Parses a yt-dlp error string and returns a simplified version."""
    if 'Private video' in error_str:
        return 'This is a private video.'
    if 'Video unavailable' in error_str:
        return 'This video is unavailable.'
    if 'removed for violating' in error_str:
        return 'This video was removed.'
    if 'not available in your country' in error_str:
        return 'This video is not available in your country.'
    if 'age-restricted' in error_str:
        return 'This video is age-restricted.'
    if 'Login required' in error_str:
        return 'This video requires login.'
    if 'payment to watch' in error_str:
        return 'This is a paid video.'
    if 'Premiere' in error_str:
        return 'This video is a premiere.'
    if 'Live event' in error_str:
        return 'This is a live event.'
    if 'HTTP Error 404' in error_str:
        return 'Video not found.'
    if 'HTTP Error 403' in error_str:
        return 'Access denied to video.'
    if 'HTTP Error 429' in error_str:
        return 'Too many requests. Please try again later.'
    if 'no file produced' in error_str:
        return 'Download failed.'
    
    return 'An error occurred while processing your request.'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/info', methods=['POST'])
def info():
    data = request.get_json() or {}
    url = data.get('url')
    if not url:
        return jsonify({'error': 'missing url'}), 400

    try:
        ffmpeg_location = os.path.join(BASE_DIR, 'bin')
        with YoutubeDL({**YDL_OPTS_BASE, 'skip_download': True, 'ffmpeg_location': ffmpeg_location}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        simple_error = get_simple_error(str(e))
        return jsonify({'error': simple_error}), 400

    is_playlist = 'entries' in info

    if is_playlist:
        entries = []
        for e in list(info.get('entries', []))[:10]:
            if not e:
                continue
            entries.append({
                'id': e.get('id'),
                'title': e.get('title'),
                'duration': e.get('duration'),
                'thumbnail': e.get('thumbnail'),
            })
        return jsonify({
            'type': 'playlist',
            'id': info.get('id'),
            'title': info.get('title'),
            'uploader': info.get('uploader'),
            'thumbnail': info.get('thumbnail'),
            'total_videos': len(info.get('entries', [])),
            'entries_sample': entries,
        })

    formats = []
    for f in info.get('formats', []):
        formats.append({
            'format_id': f.get('format_id'),
            'ext': f.get('ext'),
            'acodec': f.get('acodec'),
            'vcodec': f.get('vcodec'),
            'filesize': f.get('filesize') or f.get('filesize_approx'),
            'height': f.get('height'),
            'abr': f.get('abr'),
        })

    return jsonify({
        'type': 'video',
        'id': info.get('id'),
        'title': info.get('title'),
        'uploader': info.get('uploader'),
        'thumbnail': info.get('thumbnail'),
        'formats': formats,
    })

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json() or {}
    url = data.get('url')
    if not url:
        return jsonify({'error': 'missing url'}), 400

    task_id = str(uuid.uuid4())
    task = {
        'task_id': task_id,
        'url': url,
        'mode': data.get('mode', 'video'),
        'format_id': data.get('format_id'),
        'submode': data.get('submode', 'video'),
        'status': 'pending',
        'result': None,
        'error': None,
    }
    tasks[task_id] = task
    task_queue.put(task_id)

    return jsonify({'task_id': task_id})

@app.route('/status/<task_id>')
def status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'task not found'}), 404
    return jsonify({
        'status': task['status'],
        'error': task['error'],
    })

@app.route('/file/<task_id>')
def file(task_id):
    task = tasks.get(task_id)
    if not task or task['status'] != 'completed':
        return jsonify({'error': 'file not available'}), 404

    filepath = task['result']
    filename = os.path.basename(filepath)

    @after_this_request
    def cleanup(response):
        try:
            if task_id in tasks:
                del tasks[task_id]
            
            if os.path.exists(filepath):
                 # if it's a zip file, the result is the zip file itself, and we need to remove the original folder
                if filename.endswith('.zip'):
                    folder_to_remove = os.path.dirname(filepath)
                    shutil.rmtree(folder_to_remove)
                os.remove(filepath)

        except Exception as e:
            app.logger.error(f"Error cleaning up task {task_id}: {e}")
        return response

    return send_file(filepath, as_attachment=True, download_name=filename)


def worker():
    while True:
        task_id = task_queue.get()
        task = tasks[task_id]
        task['status'] = 'processing'
        
        tmpdir = None
        try:
            tmpdir = tempfile.mkdtemp(dir=DOWNLOAD_FOLDER)
            
            url = task['url']
            mode = task['mode']
            format_id = task['format_id']

            ffmpeg_location = os.path.join(BASE_DIR, 'bin')

            if mode == 'playlist':
                outtmpl = os.path.join(tmpdir, '%(playlist_index)03d - %(title)s.%(ext)s')
                ydl_opts = {
                    **YDL_OPTS_BASE,
                    'outtmpl': outtmpl,
                    'ignoreerrors': True,
                    'ffmpeg_location': ffmpeg_location,
                }
                submode = task['submode']
                if submode == 'audio':
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    })
                else:
                    ydl_opts.update({
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                        'merge_output_format': 'mp4',
                    })

                with YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)
                
                zip_basename = os.path.join(DOWNLOAD_FOLDER, f"playlist-{os.path.basename(tmpdir)}")
                zip_path = shutil.make_archive(zip_basename, 'zip', root_dir=tmpdir)
                shutil.rmtree(tmpdir)

                task['status'] = 'completed'
                task['result'] = zip_path

            else: # single video/audio
                outtmpl = os.path.join(tmpdir, '%(id)s.%(ext)s')
                if mode == 'audio':
                    ydl_opts = {
                        **YDL_OPTS_BASE,
                        'format': 'bestaudio/best',
                        'outtmpl': outtmpl,
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'noplaylist': True,
                        'ffmpeg_location': ffmpeg_location,
                    }
                else: # video
                    ydl_opts = {
                        **YDL_OPTS_BASE,
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                        'outtmpl': outtmpl,
                        'merge_output_format': 'mp4',
                        'noplaylist': True,
                        'ffmpeg_location': ffmpeg_location,
                    }
                    if format_id:
                        ydl_opts['format'] = format_id

                with YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)

                produced_files = [f for f in os.listdir(tmpdir) if not f.startswith('.')]
                if not produced_files:
                    raise Exception('no file produced')

                outfile = os.path.join(tmpdir, produced_files[0])
                
                # Move file out of tmpdir so we can clean it
                final_path = os.path.join(DOWNLOAD_FOLDER, produced_files[0])
                shutil.move(outfile, final_path)
                shutil.rmtree(tmpdir)

                task['status'] = 'completed'
                task['result'] = final_path

        except Exception as e:
            if tmpdir and os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)
            task['status'] = 'failed'
            task['error'] = get_simple_error(str(e))
        finally:
            task_queue.task_done()

# Start the worker thread
threading.Thread(target=worker, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
