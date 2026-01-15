# -*- coding: utf-8 -*-
"""
TTS manager for coordinating different TTS engines
"""

import os
import hashlib
from typing import Optional, Dict, List, Any, Callable
from aqt import mw

from ..config import config
from .base import TTSEngine
from .sapi5 import SAPI5Engine
from .edge_tts import EdgeTTSEngine


# Available engines
_engines: Dict[str, TTSEngine] = {
    'sapi5': SAPI5Engine(),
    'edge_tts': EdgeTTSEngine()
}


def get_available_engines() -> Dict[str, TTSEngine]:
    """Get dictionary of available TTS engines"""
    return {name: engine for name, engine in _engines.items() if engine.is_available()}


def get_current_engine() -> Optional[TTSEngine]:
    """Get the currently configured TTS engine"""
    engine_name = config.get_tts_engine()
    engine = _engines.get(engine_name)
    
    if engine and engine.is_available():
        return engine
    
    # Fallback to first available engine
    available = get_available_engines()
    if available:
        return list(available.values())[0]
    
    return None


def generate_audio(text: str, voice: Optional[str] = None, 
                   speed: Optional[float] = None) -> Optional[str]:
    """
    Generate audio for text using the configured TTS engine
    
    Args:
        text: Text to convert to speech
        voice: Voice name (None for default)
        speed: Speech speed (None for configured default)
    
    Returns:
        Filename of generated audio (relative to media folder), or None on failure
    """
    engine = get_current_engine()
    if not engine:
        print("No TTS engine available")
        return None
    
    if not text:
        return None
    
    # Get voice and speed from config if not provided
    if voice is None:
        voice = config.get_tts_voice()
    
    if speed is None:
        speed = config.get_tts_speed()
    
    # Generate filename
    filename = _generate_filename(text, engine.name, voice, speed)
    
    # Check if audio already exists (cache)
    media_dir = mw.col.media.dir()
    output_path = os.path.join(media_dir, filename)
    
    if config.is_cache_audio() and os.path.exists(output_path):
        return filename
    
    # Generate audio
    result = engine.generate(text, voice, speed, output_path)
    
    if result and os.path.exists(result):
        return filename
    
    return None


def generate_audio_batch(items: List[Dict]) -> List[Optional[str]]:
    """
    Generate audio for multiple items.
    
    Args:
        items: List of dicts with keys: text, voice (optional), speed (optional)
    
    Returns:
        List of filenames (relative to media dir) or None for failures,
        in the same order as items.
    """
    engine = get_current_engine()
    if not engine:
        return [None] * len(items)
        
    # Pre-process items
    processed_items = []
    to_generate = []
    
    media_dir = mw.col.media.dir()
    
    default_voice = config.get_tts_voice()
    default_speed = config.get_tts_speed()
    
    for i, item in enumerate(items):
        text = item.get('text')
        if not text:
            processed_items.append({'index': i, 'filename': None})
            continue
            
        voice = item.get('voice', default_voice)
        speed = item.get('speed', default_speed)
        
        filename = _generate_filename(text, engine.name, voice, speed)
        output_path = os.path.join(media_dir, filename)
        
        if config.is_cache_audio() and os.path.exists(output_path):
            processed_items.append({'index': i, 'filename': filename})
        else:
            to_generate.append({
                'index': i,
                'text': text,
                'voice': voice,
                'speed': speed,
                'output_path': output_path,
                'filename': filename
            })
            
    # Generate batch if supported
    if to_generate:
        if hasattr(engine, 'generate_batch'):
            engine.generate_batch(to_generate)
        else:
            # Fallback to sequential
            for item in to_generate:
                engine.generate(item['text'], item['voice'], item['speed'], item['output_path'])
                
        # Update results
        for item in to_generate:
            if os.path.exists(item['output_path']):
                processed_items.append({'index': item['index'], 'filename': item['filename']})
            else:
                processed_items.append({'index': item['index'], 'filename': None})
                
    # Sort back to original order
    processed_items.sort(key=lambda x: x['index'])
    return [item['filename'] for item in processed_items]


def generate_audio_in_background(note: Any, field_name: str, text: str, 
                                callback: Optional[Callable[[bool, Optional[str]], None]] = None) -> None:
    """
    Generate audio in background and update note field.
    
    Args:
        note: The note to update
        field_name: The field to put the audio tag in
        text: Text to generate audio for
        callback: Optional callback to run after update (success: bool, filename: str)
    """
    from aqt.operations import QueryOp
    
    def _op(col):
        # This runs in background thread
        return generate_audio(text)
    
    def _success(filename):
        # This runs in main thread
        success = False
        if filename:
            try:
                # Update note field
                note[field_name] = f"[sound:{filename}]"
                success = True
            except Exception as e:
                print(f"Error updating note in background callback: {e}")
        
        if callback:
            callback(success, filename)

    op = QueryOp(
        parent=mw,
        op=lambda col: _op(col),
        success=_success
    )
    # We run without progress dialog to avoid interrupting typing
    op.run_in_background()


def _generate_filename(text: str, engine: str, voice: str, speed: float) -> str:
    """
    Generate a unique filename for the audio
    
    Format: easywords_[hash].mp3
    """
    # Create hash from text, engine, voice, and speed
    content = f"{text}_{engine}_{voice}_{speed}"
    hash_obj = hashlib.md5(content.encode('utf-8'))
    hash_str = hash_obj.hexdigest()[:12]
    
    return f"easywords_{hash_str}.mp3"


def get_voices_for_engine(engine_name: str) -> List[str]:
    """Get list of voices for a specific engine"""
    engine = _engines.get(engine_name)  
    if engine and engine.is_available():
        return engine.get_voices()
    return []


def get_current_voices() -> List[str]:
    """Get list of voices for the current engine"""
    engine = get_current_engine()
    if engine:
        return engine.get_voices()
    return []
