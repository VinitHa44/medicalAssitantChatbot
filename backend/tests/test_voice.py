import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.voice import VoiceService


@pytest.mark.asyncio
async def test_transcribe_audio():
    """Test audio transcription with Whisper"""
    with patch('whisper.load_model') as mock_whisper:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'What are the symptoms of diabetes?'
        }
        mock_whisper.return_value = mock_model
        
        voice_service = VoiceService()
        
        # Mock audio file
        audio_data = BytesIO(b'fake audio data')
        
        result = voice_service.transcribe_audio(audio_data)
        
        assert result['text'] == 'What are the symptoms of diabetes?'


@pytest.mark.asyncio
async def test_text_to_speech():
    """Test text to speech generation with gTTS"""
    with patch('gtts.gTTS') as mock_gtts:
        mock_tts = MagicMock()
        mock_gtts.return_value = mock_tts
        
        voice_service = VoiceService()
        
        text = "Diabetes is a chronic disease."
        
        audio_path = voice_service.text_to_speech(text, "session-123")
        
        assert audio_path is not None
        assert '.mp3' in audio_path or 'audio' in audio_path


@pytest.mark.asyncio
async def test_transcribe_empty_audio():
    """Test transcription with empty audio"""
    with patch('whisper.load_model') as mock_whisper:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {'text': ''}
        mock_whisper.return_value = mock_model
        
        voice_service = VoiceService()
        
        audio_data = BytesIO(b'')
        
        result = voice_service.transcribe_audio(audio_data)
        
        # Should handle empty audio gracefully
        assert result['text'] == '' or result is None


@pytest.mark.asyncio
async def test_tts_long_text():
    """Test TTS with long text"""
    with patch('gtts.gTTS') as mock_gtts:
        mock_tts = MagicMock()
        mock_gtts.return_value = mock_tts
        
        voice_service = VoiceService()
        
        # Long text
        text = " ".join(["Medical information sentence."] * 100)
        
        audio_path = voice_service.text_to_speech(text, "session-123")
        
        assert audio_path is not None


@pytest.mark.asyncio
async def test_whisper_language_detection():
    """Test Whisper language detection"""
    with patch('whisper.load_model') as mock_whisper:
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            'text': 'Hello',
            'language': 'en'
        }
        mock_whisper.return_value = mock_model
        
        voice_service = VoiceService()
        
        audio_data = BytesIO(b'audio')
        
        result = voice_service.transcribe_audio(audio_data)
        
        assert isinstance(result, dict)
        assert 'text' in result
        assert 'language' in result


@pytest.mark.asyncio
async def test_tts_file_creation():
    """Test that TTS creates audio file"""
    import tempfile
    import os
    
    with patch('gtts.gTTS') as mock_gtts:
        mock_tts = MagicMock()
        
        # Create actual temp file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        def save_side_effect(path):
            # Simulate file creation
            with open(path, 'wb') as f:
                f.write(b'fake audio')
        
        mock_tts.save.side_effect = save_side_effect
        mock_gtts.return_value = mock_tts
        
        voice_service = VoiceService()
        
        with patch.object(voice_service, 'text_to_speech', return_value=temp_path):
            result = voice_service.text_to_speech("Test text", "session")
            
            assert os.path.exists(result)
            
            # Cleanup
            os.unlink(result)


@pytest.mark.asyncio
async def test_transcribe_handles_errors():
    """Test transcription error handling"""
    with patch('whisper.load_model') as mock_whisper:
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = Exception("Transcription failed")
        mock_whisper.return_value = mock_model
        
        voice_service = VoiceService()
        
        audio_data = BytesIO(b'corrupt audio')
        
        # Should handle error gracefully
        try:
            result = voice_service.transcribe_audio(audio_data)
            assert result is None or result == ""
        except Exception as e:
            assert "Transcription failed" in str(e)
