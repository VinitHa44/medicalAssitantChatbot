import whisper
from gtts import gTTS
import os
import uuid
from loguru import logger
from config import settings
from pydub import AudioSegment
import tempfile
from typing import Dict


class VoiceService:
    """Handles speech-to-text and text-to-speech"""
    
    def __init__(self):
        # Load Whisper model
        logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL}")
        self.whisper_model = whisper.load_model(settings.WHISPER_MODEL)
        logger.info("✓ Whisper loaded")
        
        # gTTS doesn't need model loading, it's API-based
        logger.info("✓ gTTS ready (Google Text-to-Speech)")
        
        # Ensure output directory exists
        os.makedirs("static/audio", exist_ok=True)
    
    def transcribe_audio(self, audio_path: str) -> Dict[str, str]:
        """
        Convert speech to text using Whisper
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with transcribed text and language
        """
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Transcribe
            result = self.whisper_model.transcribe(
                audio_path,
                language="en",
                fp16=False
            )
            
            transcribed_text = result["text"].strip()
            logger.info(f"✓ Transcribed: {transcribed_text[:100]}...")
            
            return {
                'text': transcribed_text,
                'language': result.get('language', 'en')
            }
            
        except Exception as e:
            logger.error(f"✗ Transcription failed: {e}")
            raise
    
    def text_to_speech(self, text: str, session_id: str = None) -> str:
        """
        Convert text to speech using gTTS
        
        Args:
            text: Text to convert
            session_id: Optional session ID for filename
            
        Returns:
            URL path to generated audio file
        """
        try:
            # Generate unique filename
            filename = f"{session_id or uuid.uuid4()}.mp3"
            output_path = f"static/audio/{filename}"
            
            logger.info(f"Generating speech for text: {text[:100]}...")
            
            # Generate speech with gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
            
            logger.info(f"✓ Audio saved: {output_path}")
            
            # Return URL path
            return f"/static/audio/{filename}"
            
        except Exception as e:
            logger.error(f"✗ TTS failed: {e}")
            raise
    
    @staticmethod
    def convert_audio_format(input_path: str, output_format: str = "wav") -> str:
        """Convert audio to different format"""
        try:
            audio = AudioSegment.from_file(input_path)
            
            output_path = tempfile.NamedTemporaryFile(
                suffix=f".{output_format}",
                delete=False
            ).name
            
            audio.export(output_path, format=output_format)
            logger.info(f"✓ Converted audio to {output_format}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"✗ Audio conversion failed: {e}")
            raise


voice_service = VoiceService()
