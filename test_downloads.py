
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the parent directory to the sys.path to allow imports from the app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from downloads import download_file

class TestDownloads(unittest.TestCase):

    @patch('downloads.tempfile.mkdtemp')
    @patch('downloads.YoutubeDL')
    @patch('downloads.send_file')
    @patch('downloads.shutil')
    def test_download_video(self, mock_shutil, mock_send_file, mock_youtube_dl, mock_mkdtemp):
        # Arrange
        mock_mkdtemp.return_value = '/tmp/testdir'
        mock_youtube_dl.return_value.__enter__.return_value.extract_info.return_value = {}
        
        # Mock os.listdir to return a dummy file
        with patch('os.listdir', return_value=['test.mp4']):
            # Act
            download_file('some_url', 'video', None, None)

            # Assert
            mock_youtube_dl.assert_called_once()
            mock_send_file.assert_called_once()

    @patch('downloads.tempfile.mkdtemp')
    @patch('downloads.YoutubeDL')
    @patch('downloads.send_file')
    @patch('downloads.shutil')
    def test_download_audio(self, mock_shutil, mock_send_file, mock_youtube_dl, mock_mkdtemp):
        # Arrange
        mock_mkdtemp.return_value = '/tmp/testdir'
        mock_youtube_dl.return_value.__enter__.return_value.extract_info.return_value = {}
        
        with patch('os.listdir', return_value=['test.mp3']):
            # Act
            download_file('some_url', 'audio', None, None)

            # Assert
            mock_youtube_dl.assert_called_once()
            mock_send_file.assert_called_once()

    @patch('downloads.tempfile.mkdtemp')
    @patch('downloads.YoutubeDL')
    @patch('downloads.send_file')
    @patch('downloads.shutil')
    def test_download_playlist(self, mock_shutil, mock_send_file, mock_youtube_dl, mock_mkdtemp):
        # Arrange
        mock_mkdtemp.return_value = '/tmp/testdir'
        mock_youtube_dl.return_value.__enter__.return_value.extract_info.return_value = {}
        mock_shutil.make_archive.return_value = '/tmp/testdir.zip'

        # Act
        download_file('some_url', 'playlist', None, 'video')

        # Assert
        mock_youtube_dl.assert_called_once()
        mock_shutil.make_archive.assert_called_once()
        mock_send_file.assert_called_once()

    def test_download_no_url(self):
        # Act
        response, status_code = download_file(None, 'video', None, None)

        # Assert
        self.assertEqual(status_code, 400)
        self.assertIn('error', response.get_json())

if __name__ == '__main__':
    unittest.main()
