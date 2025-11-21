
import os

from flask import Blueprint, request, jsonify

from yt_dlp import YoutubeDL



info_bp = Blueprint('info_bp', __name__)



# Get the absolute path to the 'bin' directory

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))

BIN_DIR = os.path.join(BASE_DIR, 'bin')



# Default options shared across operations

YDL_OPTS_BASE = {

    'quiet': True,

    'no_warnings': True,

    'ffmpeg_location': BIN_DIR,

}



@info_bp.route('/info', methods=['POST'])

def get_info():

    data = request.get_json() or {}

    url = data.get('url')

    if not url:

        return jsonify({'error': 'missing url'}), 400



    try:

        with YoutubeDL({**YDL_OPTS_BASE, 'skip_download': True, 'force_generic_extractor': True}) as ydl:

            info = ydl.extract_info(url, download=False)

    except Exception as e:

        return jsonify({'error': str(e)}), 400



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
