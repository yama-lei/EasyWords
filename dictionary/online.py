# -*- coding: utf-8 -*-
"""
Online Dictionary APIs for EasyWords
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any


class OnlineDictionary(ABC):
    """Base class for online dictionaries"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def lookup(self, word: str) -> Optional[Dict[str, str]]:
        """
        Look up a word
        
        Returns:
            Dict with keys: phonetic, definition, example
            None if not found
        """
        pass


class FreeDictionaryAPI(OnlineDictionary):
    """
    Wrapper for Free Dictionary API
    https://dictionaryapi.dev/
    """
    
    API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"
    
    def __init__(self):
        super().__init__("Free Dictionary API")
    
    def lookup(self, word: str) -> Optional[Dict[str, str]]:
        if not word:
            return None
            
        url = self.API_URL.format(urllib.parse.quote(word))
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if not isinstance(data, list) or not data:
                    return None
                
                entry = data[0]
                result = {
                    'phonetic': '',
                    'definition': '',
                    'example': ''
                }
                
                # Extract Phonetic
                if 'phonetic' in entry:
                    result['phonetic'] = entry['phonetic']
                elif 'phonetics' in entry:
                    for p in entry['phonetics']:
                        if 'text' in p:
                            result['phonetic'] = p['text']
                            break
                
                # Extract Definition and Example
                if 'meanings' in entry:
                    for meaning in entry['meanings']:
                        if 'definitions' in meaning:
                            for definition in meaning['definitions']:
                                if not result['definition'] and 'definition' in definition:
                                    result['definition'] = definition['definition']
                                
                                if not result['example'] and 'example' in definition:
                                    result['example'] = definition['example']
                                
                                if result['definition'] and result['example']:
                                    break
                        if result['definition'] and result['example']:
                            break
                            
                return result
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # Word not found
            print(f"FreeDictionaryAPI HTTP Error: {e}")
        except Exception as e:
            print(f"FreeDictionaryAPI Error: {e}")
            
        return None


class WiktionaryAPI(OnlineDictionary):
    """
    Wrapper for Wiktionary API (using MediaWiki API)
    """
    
    API_URL = "https://en.wiktionary.org/w/api.php?action=query&format=json&prop=extracts&titles={}&redirects=1&explaintext=1&exintro=1"
    
    def __init__(self):
        super().__init__("Wiktionary (English)")
    
    def lookup(self, word: str) -> Optional[Dict[str, str]]:
        if not word:
            return None
            
        url = self.API_URL.format(urllib.parse.quote(word))
        
        try:
            # User-Agent is required by Wikimedia API
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'EasyWordsAnkiAddon/1.0 (mailto:user@example.com)'}
            )
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                pages = data.get('query', {}).get('pages', {})
                if not pages:
                    return None
                
                # Get the first page
                page_id = list(pages.keys())[0]
                if page_id == "-1":
                    return None  # Missing
                
                page = pages[page_id]
                extract = page.get('extract', '')
                
                if not extract:
                    return None
                
                # Parse extract (very basic parsing)
                # Wiktionary extracts are unstructured text. 
                # We'll try to get the first paragraph as definition.
                
                lines = extract.split('\n')
                definition = ""
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('='):
                        definition = line
                        break
                
                return {
                    'phonetic': '', # Wiktionary extract doesn't reliably provide phonetic in plain text
                    'definition': definition,
                    'example': '' # Hard to extract example reliably from plain text summary
                }
                
        except Exception as e:
            print(f"WiktionaryAPI Error: {e}")
            
        return None


def create_online_dictionary(config: Dict[str, Any]) -> Optional[OnlineDictionary]:
    """Factory to create online dictionary instance"""
    type_name = config.get('type')
    
    if type_name == 'free_dictionary':
        return FreeDictionaryAPI()
    elif type_name == 'wiktionary':
        return WiktionaryAPI()
        
    return None


def get_available_online_dicts() -> List[Dict[str, str]]:
    """Get list of supported online dictionary types"""
    return [
        {'type': 'free_dictionary', 'name': 'Free Dictionary API'},
        {'type': 'wiktionary', 'name': 'Wiktionary (English)'}
    ]
