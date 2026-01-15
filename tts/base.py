# -*- coding: utf-8 -*-
"""
Base TTS engine interface
"""

from abc import ABC, abstractmethod
from typing import Optional, List


class TTSEngine(ABC):
    """Base class for TTS engines"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this TTS engine is available"""
        pass
    
    @abstractmethod
    def get_voices(self) -> List[str]:
        """Get list of available voices"""
        pass
    
    @abstractmethod
    def generate(self, text: str, voice: Optional[str] = None, 
                 speed: float = 1.0, output_path: str = None) -> Optional[str]:
        """
        Generate speech audio
        
        Args:
            text: Text to convert to speech
            voice: Voice name (None for default)
            speed: Speech speed (1.0 = normal)
            output_path: Path to save audio file
        
        Returns:
            Path to generated audio file, or None on failure
        """
        pass
    
    def get_default_voice(self) -> Optional[str]:
        """Get the default voice for this engine"""
        voices = self.get_voices()
        return voices[0] if voices else None
