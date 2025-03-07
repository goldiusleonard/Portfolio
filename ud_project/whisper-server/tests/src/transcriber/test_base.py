import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from transcriber import Transcriber


class TestTranscriber(unittest.TestCase):
    def setUp(self):
        """Set up the Transcriber instance for testing."""
        self.transcriber = Transcriber()

    @patch("transcriber.whisperx.load_model")
    def test_transcriber_initialization(self, mock_load_model):
        """Test that the Transcriber initializes correctly."""
        mock_load_model.return_value = MagicMock()
        transcriber = Transcriber()
        self.assertIsNotNone(transcriber.whisperx_model)
        mock_load_model.assert_called_once()

    @patch("transcriber.whisperx.load_audio")
    @patch("transcriber.Transcriber.transcribe_video")
    def test_transcribe_video_file(self, mock_transcribe_video, mock_load_audio):
        """Test the transcribe_video_file method with a mock video file."""
        mock_video_file = BytesIO(b"mock video data")
        mock_transcribe_video.return_value = ("Transcription text", "en")
        mock_load_audio.return_value = MagicMock(size=1)

        transcript, language = self.transcriber.transcribe_video_file(mock_video_file)

        mock_transcribe_video.assert_called_once()
        self.assertEqual(transcript, "Transcription text")
        self.assertEqual(language, "en")

    @patch("transcriber.whisperx.load_audio")
    def test_transcribe_video_empty_audio(self, mock_load_audio):
        """Test transcribe_video with an empty audio array."""
        mock_load_audio.return_value = MagicMock(size=0)

        transcript, language = self.transcriber.transcribe_video("mock_video.mp4")
        self.assertEqual(transcript, "")
        self.assertEqual(language, "")

    @patch("transcriber.whisperx.load_audio")
    def test_transcribe_video_no_segments(self, mock_load_audio):
        """Test transcribe_video with no segments in the result."""
        mock_audio = MagicMock()
        mock_load_audio.return_value = mock_audio
        self.transcriber.whisperx_model = MagicMock()
        self.transcriber.whisperx_model.transcribe.return_value = {
            "segments": [],
            "language": "en",
        }

        transcript, language = self.transcriber.transcribe_video("mock_video.mp4")
        self.assertEqual(transcript, "")
        self.assertEqual(language, "")

    @patch("transcriber.whisperx.load_audio")
    def test_transcribe_video_unsupported_language(self, mock_load_audio):
        """Test transcribe_video with an unsupported language."""
        mock_audio = MagicMock()
        mock_load_audio.return_value = mock_audio
        self.transcriber.whisperx_model = MagicMock()
        self.transcriber.whisperx_model.transcribe.return_value = {
            "segments": [{"start": 0, "end": 1, "text": "test"}],
            "language": "fr",
        }

        transcript, language = self.transcriber.transcribe_video("mock_video.mp4")
        self.assertEqual(transcript, "")
        self.assertEqual(language, "fr")

    @patch("transcriber.whisperx.load_audio")
    def test_transcribe_video_successful(self, mock_load_audio):
        """Test transcribe_video with a valid transcription."""
        mock_audio = MagicMock()
        mock_load_audio.return_value = mock_audio
        self.transcriber.whisperx_model = MagicMock()
        self.transcriber.whisperx_model.transcribe.return_value = {
            "segments": [
                {"start": 0, "end": 1, "text": "Hello"},
                {"start": 1, "end": 2, "text": "world"},
            ],
            "language": "en",
        }

        transcript, language = self.transcriber.transcribe_video("mock_video.mp4")
        self.assertEqual(transcript, "Hello world")
        self.assertEqual(language, "en")


if __name__ == "__main__":
    unittest.main()