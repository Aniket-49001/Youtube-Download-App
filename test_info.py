
import unittest
from unittest.mock import patch
import os
import sys
import json

# Add the parent directory to the sys.path to allow imports from the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

class TestInfo(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('info.YoutubeDL')
    def test_get_info_video(self, mock_youtube_dl):
        # Arrange
        mock_youtube_dl.return_value.__enter__.return_value.extract_info.return_value = {
            'id': 'test_id',
            'title': 'test_title',
            'uploader': 'test_uploader',
            'thumbnail': 'test_thumbnail',
            'formats': []
        }

        # Act
        response = self.app.post('/info',
                                 data=json.dumps({'url': 'some_url'}),
                                 content_type='application/json')
        data = response.get_json()

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['type'], 'video')
        self.assertEqual(data['id'], 'test_id')

    @patch('info.YoutubeDL')
    def test_get_info_playlist(self, mock_youtube_dl):
        # Arrange
        mock_youtube_dl.return_value.__enter__.return_value.extract_info.return_value = {
            'id': 'test_id',
            'title': 'test_title',
            'uploader': 'test_uploader',
            'thumbnail': 'test_thumbnail',
            'entries': [
                {
                    'id': 'entry_id',
                    'title': 'entry_title',
                    'duration': 60,
                    'thumbnail': 'entry_thumbnail'
                }
            ]
        }

        # Act
        response = self.app.post('/info',
                                 data=json.dumps({'url': 'some_url'}),
                                 content_type='application/json')
        data = response.get_json()

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['type'], 'playlist')
        self.assertEqual(data['total_videos'], 1)

    def test_get_info_no_url(self):
        # Act
        response = self.app.post('/info',
                                 data=json.dumps({}),
                                 content_type='application/json')

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

if __name__ == '__main__':
    unittest.main()
