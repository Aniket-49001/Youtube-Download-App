import unittest
from unittest.mock import patch, MagicMock
import json
import queue
from app import app, tasks, task_queue

class AppTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        # Clear tasks and queue before each test
        tasks.clear()
        while not task_queue.empty():
            task_queue.get()

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'YouTube Downloader', response.data)

    @patch('yt_dlp.YoutubeDL')
    def test_info_route_video(self, mock_youtube_dl):
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = {
            'id': 'test_id',
            'title': 'test_title',
            'uploader': 'test_uploader',
            'thumbnail': 'test_thumbnail',
            'formats': [
                {'format_id': '1', 'height': 720, 'vcodec': 'avc1', 'acodec': 'mp4a', 'ext': 'mp4', 'filesize': 1000},
                {'format_id': '2', 'height': 1080, 'vcodec': 'avc1', 'acodec': 'mp4a', 'ext': 'mp4', 'filesize': 2000},
            ]
        }
        mock_youtube_dl.return_value.__enter__.return_value = mock_ydl_instance

        response = self.app.post('/info',
                                 data=json.dumps({'url': 'https://www.youtube.com/watch?v=test_id'}),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['type'], 'video')
        self.assertEqual(data['title'], 'test_title')
        self.assertEqual(len(data['formats']), 2)

    @patch('yt_dlp.YoutubeDL')
    def test_info_route_playlist(self, mock_youtube_dl):
        mock_ydl_instance = MagicMock()
        mock_ydl_instance.extract_info.return_value = {
            'id': 'playlist_id',
            'title': 'playlist_title',
            'uploader': 'playlist_uploader',
            'thumbnail': 'playlist_thumbnail',
            'entries': [
                {'id': 'video1', 'title': 'video1_title'},
                {'id': 'video2', 'title': 'video2_title'},
            ]
        }
        mock_youtube_dl.return_value.__enter__.return_value = mock_ydl_instance

        response = self.app.post('/info',
                                 data=json.dumps({'url': 'https://www.youtube.com/playlist?list=playlist_id'}),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['type'], 'playlist')
        self.assertEqual(data['title'], 'playlist_title')
        self.assertEqual(data['total_videos'], 2)

    def test_download_route(self):
        url = 'https://www.youtube.com/watch?v=test_id'
        response = self.app.post('/download',
                                 data=json.dumps({'url': url, 'mode': 'video', 'format_id': '1'}),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('task_id', data)
        task_id = data['task_id']
        self.assertIn(task_id, tasks)
        self.assertEqual(tasks[task_id]['url'], url)
        self.assertEqual(tasks[task_id]['mode'], 'video')
        self.assertEqual(tasks[task_id]['format_id'], '1')
        self.assertFalse(task_queue.empty())
        self.assertEqual(task_queue.get(), task_id)

    def test_status_route(self):
        task_id = 'test_task_id'
        tasks[task_id] = {'status': 'pending'}
        response = self.app.get(f'/status/{task_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'pending')

if __name__ == '__main__':
    unittest.main()