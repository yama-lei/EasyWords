# -*- coding: utf-8 -*-
"""
Online dictionary support for EasyWords
"""

from typing import Optional, Dict, List
import logging
import json

logger = logging.getLogger(__name__)


class OnlineDictionary:
    """Base class for online dictionary APIs"""
    
    def __init__(self, name: str, api_url: str, api_key: str = ""):
        self.name = name
        self.api_url = api_url
        self.api_key = api_key
    
    def lookup(self, word: str) -> Optional[Dict]:
        """
        Look up a word in the online dictionary
        
        Returns:
            Dict with keys: phonetic, definition, example
            None if word not found or error occurred
        """
        raise NotImplementedError("Subclasses must implement lookup()")
    
    def test_connection(self) -> tuple[bool, str]:
        """
        Test the API connection
        
        Returns:
            (success: bool, message: str)
        """
        raise NotImplementedError("Subclasses must implement test_connection()")


class YoudaoDictionary(OnlineDictionary):
    """Youdao Dictionary API implementation"""
    
    def lookup(self, word: str) -> Optional[Dict]:
        """Look up a word using Youdao API"""
        try:
            import requests
            import hashlib
            import time
            import uuid
            
            # Youdao API requires app_key, app_secret, and generates sign
            # This is a placeholder implementation
            # Users need to register at https://ai.youdao.com/ to get credentials
            
            if not self.api_key or ':' not in self.api_key:
                logger.error("Invalid Youdao API key format. Expected 'app_key:app_secret'")
                return None
            
            app_key, app_secret = self.api_key.split(':', 1)
            
            salt = str(uuid.uuid4())
            curtime = str(int(time.time()))
            sign_str = app_key + word + salt + curtime + app_secret
            sign = hashlib.sha256(sign_str.encode('utf-8')).hexdigest()
            
            params = {
                'q': word,
                'from': 'en',
                'to': 'zh-CHS',
                'appKey': app_key,
                'salt': salt,
                'sign': sign,
                'signType': 'v3',
                'curtime': curtime
            }
            
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('errorCode') != '0':
                logger.warning(f"Youdao API error: {data.get('errorCode')}")
                return None
            
            # Parse Youdao response
            result = {
                'phonetic': '',
                'definition': '',
                'example': ''
            }
            
            # Extract basic translation
            if 'basic' in data:
                basic = data['basic']
                if 'phonetic' in basic:
                    result['phonetic'] = basic['phonetic']
                if 'explains' in basic:
                    result['definition'] = '\n'.join(basic['explains'])
            
            # Extract web translation as fallback
            if not result['definition'] and 'translation' in data:
                result['definition'] = '\n'.join(data['translation'])
            
            return result if result['definition'] else None
            
        except ImportError:
            logger.error("requests library not available. Please install: pip install requests")
            return None
        except Exception as e:
            logger.error(f"Failed to lookup word from Youdao: {e}", exc_info=True)
            return None
    
    def test_connection(self) -> tuple[bool, str]:
        """Test Youdao API connection"""
        try:
            result = self.lookup("test")
            if result:
                return True, "Connection successful!"
            else:
                return False, "API returned no results. Please check your API key."
        except Exception as e:
            return False, f"Connection failed: {str(e)}"


class GenericAPIDictionary(OnlineDictionary):
    """Generic REST API dictionary with customizable response parsing"""
    
    def __init__(self, name: str, api_url: str, api_key: str = "", 
                 headers: Optional[Dict] = None, 
                 response_mapping: Optional[Dict] = None):
        super().__init__(name, api_url, api_key)
        self.headers = headers or {}
        # Response mapping: {"phonetic": "data.phonetic", "definition": "data.definition", ...}
        self.response_mapping = response_mapping or {
            'phonetic': 'phonetic',
            'definition': 'definition',
            'example': 'example'
        }
        
        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'
    
    def lookup(self, word: str) -> Optional[Dict]:
        """Look up a word using generic REST API"""
        try:
            import requests
            
            # Replace {word} placeholder in URL
            url = self.api_url.replace('{word}', word)
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response using mapping
            result = {
                'phonetic': self._extract_field(data, self.response_mapping.get('phonetic', '')),
                'definition': self._extract_field(data, self.response_mapping.get('definition', '')),
                'example': self._extract_field(data, self.response_mapping.get('example', ''))
            }
            
            return result if any(result.values()) else None
            
        except ImportError:
            logger.error("requests library not available. Please install: pip install requests")
            return None
        except Exception as e:
            logger.error(f"Failed to lookup word from {self.name}: {e}", exc_info=True)
            return None
    
    def _extract_field(self, data: Dict, path: str) -> str:
        """Extract field from nested dict using dot notation path"""
        if not path:
            return ''
        
        try:
            keys = path.split('.')
            value = data
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key, '')
                elif isinstance(value, list) and value:
                    value = value[0]
                else:
                    return ''
            
            return str(value) if value else ''
        except Exception:
            return ''
    
    def test_connection(self) -> tuple[bool, str]:
        """Test generic API connection"""
        try:
            result = self.lookup("test")
            if result:
                return True, "Connection successful!"
            else:
                return False, "API returned no results. Please check your configuration."
        except Exception as e:
            return False, f"Connection failed: {str(e)}"


def create_online_dictionary(config: Dict) -> Optional[OnlineDictionary]:
    """
    Factory function to create an online dictionary instance
    
    Args:
        config: Dict with keys: name, type, api_url, api_key, etc.
    
    Returns:
        OnlineDictionary instance or None
    """
    dict_type = config.get('type', 'generic')
    name = config.get('name', 'Unknown')
    api_url = config.get('api_url', '')
    api_key = config.get('api_key', '')
    
    if not api_url:
        logger.warning(f"No API URL configured for {name}")
        return None
    
    if dict_type == 'youdao':
        return YoudaoDictionary(name, api_url, api_key)
    elif dict_type == 'generic':
        headers = config.get('headers', {})
        response_mapping = config.get('response_mapping', {})
        return GenericAPIDictionary(name, api_url, api_key, headers, response_mapping)
    else:
        logger.warning(f"Unknown dictionary type: {dict_type}")
        return None
