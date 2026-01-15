# -*- coding: utf-8 -*-
"""
Microsoft Edge TTS engine implementation
"""

import asyncio
import os
from typing import Optional, List, Dict
from .base import TTSEngine


class EdgeTTSEngine(TTSEngine):
    """Microsoft Edge TTS engine (requires internet)"""
    
    def __init__(self):
        super().__init__("edge_tts")
        self._voices_cache = None
    
    def is_available(self) -> bool:
        """Check if edge-tts library is available"""
        try:
            import edge_tts
            return True
        except ImportError:
            return False
    
    def get_voices(self) -> List[str]:
        """Get list of available Edge TTS voices"""
        if self._voices_cache is not None:
            return self._voices_cache
        
        if not self.is_available():
            return []
        
        try:
            import edge_tts
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            voices = loop.run_until_complete(edge_tts.list_voices())
            loop.close()
            
            # Extract English voices
            voice_names = []
            for voice in voices:
                if 'en-' in voice['Locale'].lower():
                    voice_names.append(f"{voice['ShortName']} ({voice['Locale']})")
            
            self._voices_cache = voice_names
            return voice_names
            
        except Exception as e:
            print(f"Failed to get Edge TTS voices: {e}")
            return []
    
    def _prepare_voice_rate(self, voice: Optional[str], speed: float) -> tuple[str, str]:
        """Prepare voice name and rate string"""
        # Parse voice name if in format "ShortName (Locale)"
        voice_name = voice
        if voice and '(' in voice:
            voice_name = voice.split('(')[0].strip()
        
        # Default to en-US voice if not specified
        if not voice_name:
            voice_name = "en-US-AriaNeural"
        
        # Convert speed to rate string
        # speed 1.0 = +0%, 0.5 = -50%, 2.0 = +100%
        rate_percent = int((speed - 1.0) * 100)
        rate_str = f"{rate_percent:+d}%"
        
        return voice_name, rate_str

    def generate(self, text: str, voice: Optional[str] = None,
                 speed: float = 1.0, output_path: str = None) -> Optional[str]:
        """Generate speech using Edge TTS"""
        if not self.is_available() or not output_path:
            return None
        
        try:
            import edge_tts
            
            voice_name, rate_str = self._prepare_voice_rate(voice, speed)
            
            # Run async generation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
            loop.run_until_complete(communicate.save(output_path))
            loop.close()
            
            return output_path
            
        except Exception as e:
            print(f"Edge TTS generation error: {e}")
            return None

    def generate_batch(self, items: List[Dict]) -> List[Optional[str]]:
        """
        Generate multiple audio files in parallel.
        items: List of dicts with keys: text, voice, speed, output_path
        """
        if not self.is_available():
            return [None] * len(items)
            
        import edge_tts
        
        async def _run_batch():
            tasks = []
            for item in items:
                text = item.get('text')
                output_path = item.get('output_path')
                
                if not text or not output_path:
                    # Return None for invalid items
                    async def _dummy(): return None
                    tasks.append(_dummy())
                    continue
                    
                voice_name, rate_str = self._prepare_voice_rate(
                    item.get('voice'), item.get('speed', 1.0)
                )
                
                communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
                tasks.append(communicate.save(output_path))
            
            # Execute all tasks concurrently
            await asyncio.gather(*tasks, return_exceptions=True)

        # Run the batch in a single event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_batch())
        finally:
            loop.close()
            
        # Verify results
        results = []
        for item in items:
            path = item.get('output_path')
            if path and os.path.exists(path):
                results.append(path)
            else:
                results.append(None)
        return results
    
    def get_default_voice(self) -> Optional[str]:
        """Get default English voice"""
        voices = self.get_voices()
        if not voices:
            return "en-US-AriaNeural"
        
        # Prefer en-US voices
        for voice in voices:
            if 'en-US' in voice:
                return voice
        
        # Otherwise return first English voice
        return voices[0] if voices else "en-US-AriaNeural"
