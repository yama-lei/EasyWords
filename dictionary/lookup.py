# -*- coding: utf-8 -*-
"""
Dictionary lookup interface for EasyWords
"""

from typing import Optional, Dict, List
from ..config import config
from .mdx_parser import create_parser, MDXParser


# Cache of loaded parsers
_parsers: Dict[str, MDXParser] = {}

# Simple in-memory cache for online lookups
# Format: {word: result_dict}
_online_cache: Dict[str, Optional[Dict]] = {}


def get_parsers() -> List[MDXParser]:
    """Get list of loaded dictionary parsers"""
    global _parsers
    
    mdx_paths = config.get_mdx_paths()
    if not mdx_paths:
        return []
    
    # Load new dictionaries
    for path in mdx_paths:
        if path not in _parsers:
            parser = create_parser(path)
            if parser.load():
                _parsers[path] = parser
    
    # Remove parsers for paths no longer in config
    paths_to_remove = [p for p in _parsers.keys() if p not in mdx_paths]
    for path in paths_to_remove:
        _parsers[path].close()
        del _parsers[path]
    
    return list(_parsers.values())


def lookup_word(word: str) -> Optional[Dict]:
    """
    Look up a word in configured dictionaries.
    
    Returns:
        Dict with keys: phonetic, definition, example
        None if word not found in any dictionary
    """
    if not word:
        return None

    mode = config.get_dictionary_mode()

    # Local only
    if mode == "local":
        parsers = get_parsers()
        for parser in parsers:
            result = parser.lookup(word)
            if result:
                return result
        return get_fallback_result(word)

    # Online only
    if mode == "online":
        online_result = lookup_word_online(word)
        if online_result:
            return online_result
        return get_fallback_result(word)

    # Auto: local first, then online
    parsers = get_parsers()
    for parser in parsers:
        result = parser.lookup(word)
        if result:
            return result

    online_result = lookup_word_online(word)
    if online_result:
        return online_result
    
    # Not found in any dictionary
    return get_fallback_result(word)


def lookup_word_online(word: str) -> Optional[Dict]:
    """
    Look up a word in configured online dictionaries
    
    Returns:
        Dict with keys: phonetic, definition, example
        None if word not found in any online dictionary
    """
    if not word:
        return None
    
    # Check cache first
    if word in _online_cache:
        return _online_cache[word]
    
    from .online import create_online_dictionary
    import logging
    
    logger = logging.getLogger(__name__)
    
    online_dicts = config.get_online_dictionaries()
    
    # If no online dicts configured, add defaults if list is empty
    # This ensures users have something to start with
    if not online_dicts:
        # We don't save this to config automatically, just use temporarily
        # Or should we? Better to respect empty config.
        # But for Phase 3 requirements "Implement at least 3 mainstream dictionary API access",
        # let's assume we want them available. 
        # Actually, let's rely on user configuration via OnlineDictDialog.
        pass
    
    for dict_config in online_dicts:
        if not dict_config.get('enabled', False):
            continue
        
        try:
            online_dict = create_online_dictionary(dict_config)
            if online_dict:
                result = online_dict.lookup(word)
                if result:
                    logger.info(f"Found word '{word}' in online dictionary: {dict_config.get('name')}")
                    _online_cache[word] = result
                    return result
        except Exception as e:
            logger.error(f"Error looking up word in {dict_config.get('name', 'unknown')}: {e}")
            continue
    
    # Cache negative result to avoid repeated failed lookups
    _online_cache[word] = None
    return None


def get_fallback_result(word: str) -> Dict:
    """
    Get a fallback result when no dictionary is available
    
    This is useful for testing and when dictionaries are not yet configured.
    """
    return {
        'phonetic': '',  # Empty, will be filled by user
        'definition': '',  # Empty, will be filled by user
        'example': ''  # Empty, will be filled by user
    }


def reload_dictionaries():
    """Reload all dictionaries (useful after config changes)"""
    global _parsers, _online_cache
    
    for parser in _parsers.values():
        parser.close()
    
    _parsers.clear()
    _online_cache.clear()


def has_dictionaries() -> bool:
    """Check if any dictionaries are configured"""
    return len(config.get_mdx_paths()) > 0 or len(config.get_online_dictionaries()) > 0


def get_dictionary_fields() -> Dict[str, Dict[str, str]]:
    """
    Get available fields from all configured dictionaries
    
    Returns:
        Dict mapping dictionary path to available fields
        Format: {
            "path/to/dict.mdx": {
                "Phonetic": "description",
                "Definition": "description"
            }
        }
    """
    result = {}
    parsers = get_parsers()
    
    for parser in parsers:
        fields = parser.get_available_fields()
        if fields:
            result[parser.mdx_path] = fields
    
    return result
