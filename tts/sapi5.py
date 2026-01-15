# -*- coding: utf-8 -*-
"""
Windows SAPI5 TTS engine implementation
"""

import os
import sys
from typing import Optional, List
from .base import TTSEngine


class SAPI5Engine(TTSEngine):
    """Windows SAPI5 TTS engine"""
    
    def __init__(self):
        super().__init__("sapi5")
        self._speaker = None
        self._voices_cache = None
    
    def is_available(self) -> bool:
        """Check if SAPI5 is available (Windows only)"""
        if sys.platform != "win32":
            return False
        
        try:
            import win32com.client
            return True
        except ImportError:
            return False
    
    def _get_speaker(self):
        """Get or create the SAPI speaker object"""
        if self._speaker is None:
            try:
                import win32com.client
                self._speaker = win32com.client.Dispatch("SAPI.SpVoice")
            except Exception as e:
                print(f"Failed to initialize SAPI5: {e}")
                return None
        return self._speaker
    
    def get_voices(self) -> List[str]:
        """Get list of available SAPI5 voices"""
        if self._voices_cache is not None:
            return self._voices_cache
        
        speaker = self._get_speaker()
        if not speaker:
            return []
        
        try:
            voices = []
            for voice in speaker.GetVoices():
                voices.append(voice.GetDescription())
            self._voices_cache = voices
            return voices
        except Exception as e:
            print(f"Failed to get SAPI5 voices: {e}")
            return []
    
    def _set_voice(self, voice_name: Optional[str]):
        """Set the voice by name"""
        if not voice_name:
            return
        
        speaker = self._get_speaker()
        if not speaker:
            return
        
        try:
            for voice in speaker.GetVoices():
                if voice.GetDescription() == voice_name:
                    speaker.Voice = voice
                    break
        except Exception as e:
            print(f"Failed to set voice: {e}")
    
    def generate(self, text: str, voice: Optional[str] = None,
                 speed: float = 1.0, output_path: str = None) -> Optional[str]:
        """Generate speech using SAPI5"""
        if not self.is_available():
            return None
        
        speaker = self._get_speaker()
        if not speaker:
            return None
        
        try:
            # Set voice if specified
            if voice:
                self._set_voice(voice)
            
            # Set speech rate (-10 to 10, 0 is normal)
            # Convert our speed (0.5 to 2.0) to SAPI rate
            rate = int((speed - 1.0) * 10)
            rate = max(-10, min(10, rate))
            speaker.Rate = rate
            
            # Generate audio to file
            if output_path:
                # Save to WAV file
                import win32com.client
                filestream = win32com.client.Dispatch("SAPI.SpFileStream")
                filestream.Open(output_path, 3)  # 3 = SSFMCreateForWrite
                speaker.AudioOutputStream = filestream
                speaker.Speak(text)
                filestream.Close()
                speaker.AudioOutputStream = None
                
                # Convert WAV to MP3 if needed
                if output_path.endswith('.mp3'):
                    wav_path = output_path.replace('.mp3', '.wav')
                    self._convert_to_mp3(wav_path, output_path)
                    if os.path.exists(wav_path):
                        os.remove(wav_path)
                
                return output_path
            else:
                # Speak directly (not saving to file)
                speaker.Speak(text)
                return None
                
        except Exception as e:
            print(f"SAPI5 generation error: {e}")
            return None
    
    def _convert_to_mp3(self, wav_path: str, mp3_path: str) -> bool:
        """Convert WAV to MP3 (optional, requires pydub)"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_wav(wav_path)
            audio.export(mp3_path, format="mp3")
            return True
        except ImportError:
            # pydub not available, just rename to mp3 (Anki can play WAV anyway)
            if os.path.exists(wav_path):
                import shutil
                shutil.move(wav_path, mp3_path)
            return False
        except Exception as e:
            print(f"WAV to MP3 conversion error: {e}")
            return False
