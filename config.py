# -*- coding: utf-8 -*-
"""
Configuration management for EasyWords add-on
"""

from typing import Dict, Any, List
import aqt


class Config:
    """Configuration manager for EasyWords add-on"""
    
    def __init__(self, addon_name: str = "easyWords"):
        self.addon_name = addon_name
        self._config_cache = None
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from Anki"""
        if self._config_cache is None:
            self._config_cache = aqt.mw.addonManager.getConfig(self.addon_name)
        return self._config_cache or {}
    
    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to Anki"""
        aqt.mw.addonManager.writeConfig(self.addon_name, config)
        self._config_cache = config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        config = self.load()
        return config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        config = self.load()
        config[key] = value
        self.save(config)
    
    def get_mdx_paths(self) -> List[str]:
        """Get list of MDX dictionary paths"""
        return self.get('mdx_paths', [])
    
    def add_mdx_path(self, path: str) -> None:
        """Add a new MDX dictionary path"""
        paths = self.get_mdx_paths()
        if path not in paths:
            paths.append(path)
            self.set('mdx_paths', paths)
    
    def remove_mdx_path(self, path: str) -> None:
        """Remove an MDX dictionary path"""
        paths = self.get_mdx_paths()
        if path in paths:
            paths.remove(path)
            self.set('mdx_paths', paths)
    
    def get_tts_engine(self) -> str:
        """Get current TTS engine"""
        return self.get('tts_engine', 'sapi5')
    
    def set_tts_engine(self, engine: str) -> None:
        """Set TTS engine"""
        self.set('tts_engine', engine)
    
    def get_tts_voice(self) -> str:
        """Get TTS voice"""
        return self.get('tts_voice', '')
    
    def set_tts_voice(self, voice: str) -> None:
        """Set TTS voice"""
        self.set('tts_voice', voice)
    
    def get_tts_speed(self) -> float:
        """Get TTS speed"""
        return self.get('tts_speed', 1.0)
    
    def set_tts_speed(self, speed: float) -> None:
        """Set TTS speed"""
        self.set('tts_speed', speed)
    
    def is_auto_fill_on_add(self) -> bool:
        """Check if auto-fill is enabled when adding cards"""
        return self.get('auto_fill_on_add', True)
    
    def is_auto_play_on_review(self) -> bool:
        """Check if auto-play is enabled during review"""
        return self.get('auto_play_on_review', True)
    
    def is_cache_audio(self) -> bool:
        """Check if audio caching is enabled"""
        return self.get('cache_audio', True)
    
    def is_auto_create_note_type(self) -> bool:
        """Check if note type should be created automatically"""
        return self.get('auto_create_note_type', False)
    
    def is_auto_generate_audio_on_add(self) -> bool:
        """Check if audio should be generated automatically when adding cards"""
        return self.get('auto_generate_audio_on_add', True)

    def get_dictionary_mode(self) -> str:
        """
        Get dictionary lookup mode.
        
        Returns:
            "local"  - only use MDX dictionaries
            "online" - only use online dictionaries
            "auto"   - try local first, then online (default)
        """
        mode = self.get("dictionary_mode", "auto")
        if mode not in ("local", "online", "auto"):
            return "auto"
        return mode

    def set_dictionary_mode(self, mode: str) -> None:
        """Set dictionary lookup mode"""
        if mode not in ("local", "online", "auto"):
            mode = "auto"
        self.set("dictionary_mode", mode)
    
    def get_openai_api_key(self) -> str:
        """Get OpenAI API Key"""
        return self.get('openai_api_key', '')
    
    def set_openai_api_key(self, key: str) -> None:
        """Set OpenAI API Key"""
        self.set('openai_api_key', key)
    
    def get_openai_model(self) -> str:
        """Get OpenAI Model"""
        return self.get('openai_model', 'gpt-3.5-turbo')
    
    def set_openai_model(self, model: str) -> None:
        """Set OpenAI Model"""
        self.set('openai_model', model)
    
    def get_base_url(self) -> str:
        """Get OpenAI API Base URL"""
        default_url = "https://api.openai.com/v1/chat/completions"
        return self.get('base_url', default_url)
    
    def set_base_url(self, url: str) -> None:
        """Set OpenAI API Base URL"""
        self.set('base_url', url)
    def get_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Get all field mappings
        
        Returns:
            Dict mapping note type name to field mappings
            Format: {
                "Note Type Name": {
                    "Word": "target_field_name",
                    "Phonetic": "target_field_name",
                    ...
                }
            }
        """
        return self.get('field_mappings', {})
    
    def get_field_mapping(self, note_type_name: str) -> Dict[str, str]:
        """
        Get field mapping for a specific note type
        
        Args:
            note_type_name: Name of the note type
        
        Returns:
            Dict mapping source field to target field (only enabled fields)
            Empty dict if no mapping configured
        """
        mappings = self.get_field_mappings()
        raw_mapping = mappings.get(note_type_name, {})
        
        # Normalize mapping format and filter enabled fields
        normalized = {}
        for source_field, target_value in raw_mapping.items():
            if isinstance(target_value, dict):
                # Enhanced format: {"target": "field_name", "enabled": true}
                if target_value.get('enabled', True):
                    normalized[source_field] = target_value['target']
            elif isinstance(target_value, str):
                # Simple format (legacy): "field_name"
                normalized[source_field] = target_value
        
        return normalized
    
    def get_field_mapping_full(self, note_type_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get full field mapping configuration including enabled/disabled status
        
        Args:
            note_type_name: Name of the note type
        
        Returns:
            Dict mapping source field to config dict with 'target' and 'enabled' keys
        """
        mappings = self.get_field_mappings()
        raw_mapping = mappings.get(note_type_name, {})
        
        # Normalize to enhanced format
        normalized = {}
        for source_field, target_value in raw_mapping.items():
            if isinstance(target_value, dict):
                normalized[source_field] = target_value
            elif isinstance(target_value, str):
                # Convert legacy format
                normalized[source_field] = {
                    'target': target_value,
                    'enabled': True
                }
        
        return normalized
    
    def set_field_mapping(self, note_type_name: str, mapping: Dict[str, str]) -> None:
        """
        Set field mapping for a specific note type
        
        Args:
            note_type_name: Name of the note type
            mapping: Dict mapping source field to target field
        """
        mappings = self.get_field_mappings()
        mappings[note_type_name] = mapping
        self.set('field_mappings', mappings)
    
    def has_field_mapping(self, note_type_name: str) -> bool:
        """Check if a note type has configured field mapping"""
        mappings = self.get_field_mappings()
        return note_type_name in mappings and bool(mappings[note_type_name])
    
    def get_online_dictionaries(self) -> List[Dict[str, Any]]:
        """
        Get online dictionary configurations
        
        Returns:
            List of dictionary configs
        """
        return self.get('online_dictionaries', [])
    
    def set_online_dictionaries(self, dictionaries: List[Dict[str, Any]]) -> None:
        """Set online dictionary configurations"""
        self.set('online_dictionaries', dictionaries)
    
    def add_online_dictionary(self, dictionary: Dict[str, Any]) -> None:
        """Add an online dictionary configuration"""
        dictionaries = self.get_online_dictionaries()
        dictionaries.append(dictionary)
        self.set_online_dictionaries(dictionaries)
    
    def remove_online_dictionary(self, index: int) -> None:
        """Remove an online dictionary by index"""
        dictionaries = self.get_online_dictionaries()
        if 0 <= index < len(dictionaries):
            dictionaries.pop(index)
            self.set_online_dictionaries(dictionaries)


# Global config instance
config = Config()
