# downloads.py
import os
import shutil
import tempfile
from flask import Blueprint, request, jsonify, send_file
from yt_dlp import YoutubeDL

downloads_bp = Blueprint('downloads', __name__)

# This will be set by the main app
DOWNLOAD_FOLDER = None
YDL_OPTS_BASE = {
    'quiet': True,
    'no_warnings': True,
}

@downloads_bp.route('/download', methods=['POST'])
def download():
    data = request.get_json() or {}
    url = data.get('url')
    mode = data.get('mode', 'video')  # 'video', 'audio', or 'playlist'
    format_id = data.get('format_id')

    if not url:
        return jsonify({'error': 'missing url'}), 400

    tmpdir = tempfile.mkdtemp(dir=DOWNLOAD_FOLDER)

    try:
        if mode == 'playlist':
            outtmpl = os.path.join(tmpdir, '%(playlist_index)03d - %(title)s.%(ext)s')
            ydl_opts = {
                **YDL_OPTS_BASE,
                'outtmpl': outtmpl,
                'ignoreerrors': True,
            }
            submode = data.get('submode', 'video')  # 'video' or 'audio'
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

            zip_path = shutil.make_archive(tmpdir, 'zip', tmpdir)
            return send_file(zip_path, as_attachment=True, download_name=os.path.basename(zip_path))

        else:
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
                }
            else:
                ydl_opts = {
                    **YDL_OPTS_BASE,
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                    'outtmpl': outtmpl,
                    'merge_output_format': 'mp4',
                    'noplaylist': True,
                }
                if format_id:
                    ydl_opts['format'] = format_id

            with YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)

            produced_files = [f for f in os.listdir(tmpdir) if not f.startswith('.')]
            if not produced_files:
                return jsonify({'error': 'no file produced'}), 500

            outfile = os.path.join(tmpdir, produced_files[0])
            return send_file(outfile, as_attachment=True, download_name=os.path.basename(outfile))

    except Exception as e:
        return jsonify({'error': 'download failed: ' + str(e)}), 500
    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass
