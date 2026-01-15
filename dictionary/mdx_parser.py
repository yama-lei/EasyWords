# -*- coding: utf-8 -*-
"""
MDX dictionary parser for EasyWords

This module handles parsing MDX dictionary files using mdict-utils library.
"""

from typing import Optional, Dict
import os
import re
import logging

logger = logging.getLogger(__name__)


class MDXParser:
    """Parser for MDX dictionary files using mdict-utils"""
    
    def __init__(self, mdx_path: str):
        self.mdx_path = mdx_path
        self.is_loaded = False
        self._word_dict: Dict[str, bytes] = {}
        self._mdx = None
    
    def load(self) -> bool:
        """Load the MDX dictionary"""
        if self.is_loaded:
            return True
        
        if not os.path.exists(self.mdx_path):
            logger.error(f"MDX file not found: {self.mdx_path}")
            return False
        
        try:
            from mdict_utils.reader import MDX
            
            logger.info(f"Loading MDX dictionary: {self.mdx_path}")
            self._mdx = MDX(self.mdx_path)
            
            # Load all entries into memory for fast lookup
            for key, value in self._mdx.items():
                word_key = key.decode('utf-8').lower() if isinstance(key, bytes) else str(key).lower()
                self._word_dict[word_key] = value
            
            self.is_loaded = True
            logger.info(f"Loaded {len(self._word_dict)} dictionary entries")
            return True
            
        except ImportError as e:
            logger.error(f"mdict-utils library not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load MDX dictionary: {e}", exc_info=True)
            return False
    
    def lookup(self, word: str) -> Optional[Dict]:
        """
        Look up a word in the dictionary
        
        Returns:
            Dict with keys: phonetic, definition, example, html (optional)
            None if word not found
        """
        if not self.is_loaded:
            if not self.load():
                return None
        
        word_lower = word.lower().strip()
        if not word_lower:
            return None
        
        # Try exact match first
        html_content = self._word_dict.get(word_lower)
        
        # If not found, try without special characters
        if not html_content:
            # Try variations (e.g., "hello!" -> "hello")
            word_clean = re.sub(r'[^\w\s-]', '', word_lower)
            html_content = self._word_dict.get(word_clean)
        
        if not html_content:
            logger.debug(f"Word not found in dictionary: {word}")
            return None
        
        try:
            # Decode HTML content
            html = html_content.decode('utf-8') if isinstance(html_content, bytes) else str(html_content)
            
            # Parse the HTML to extract information
            result = self._parse_html(html)
            result['html'] = html
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse dictionary entry for '{word}': {e}", exc_info=True)
            return None
    
    def _parse_html(self, html: str) -> Dict:
        """
        Parse HTML content from MDX to extract useful information
        
        This is customized for Collins dictionary format
        """
        result = {
            'phonetic': '',
            'definition': '',
            'example': ''
        }
        
        try:
            # Extract phonetic (if present in the dictionary)
            # Collins format: look for pronunciation patterns
            phonetic_match = re.search(r'/([^/]+)/', html)
            if phonetic_match:
                result['phonetic'] = phonetic_match.group(1)
            
            # Remove HTML tags for definition
            # Strip tags but keep content
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Take first 500 chars as definition
            if len(text) > 500:
                result['definition'] = text[:500] + '...'
            else:
                result['definition'] = text
            
            # Try to find example sentences (usually in specific tags)
            # This is a simplified approach - customize based on your dictionary format
            example_match = re.findall(r'<span[^>]*class=["\']example["\'][^>]*>(.*?)</span>', html, re.DOTALL)
            if example_match:
                examples = [re.sub(r'<[^>]+>', '', ex).strip() for ex in example_match[:2]]
                result['example'] = ' '.join(examples)
            
        except Exception as e:
            logger.warning(f"Failed to parse HTML: {e}")
        
        return result
    
    def get_available_fields(self) -> Dict[str, str]:
        """
        Get available fields that this dictionary can provide
        
        Analyzes sample entries to determine which fields are available
        
        Returns:
            Dict mapping field name to description
        """
        if not self.is_loaded:
            if not self.load():
                return {}
        
        # Sample a few entries to determine available fields
        sample_size = min(10, len(self._word_dict))
        if sample_size == 0:
            return {}
        
        fields = {
            'phonetic': 0,
            'definition': 0,
            'example': 0
        }
        
        # Check sample entries
        for word_key in list(self._word_dict.keys())[:sample_size]:
            html_content = self._word_dict[word_key]
            try:
                html = html_content.decode('utf-8') if isinstance(html_content, bytes) else str(html_content)
                result = self._parse_html(html)
                
                if result.get('phonetic'):
                    fields['phonetic'] += 1
                if result.get('definition'):
                    fields['definition'] += 1
                if result.get('example'):
                    fields['example'] += 1
            except Exception as e:
                logger.warning(f"Failed to parse sample entry: {e}")
                continue
        
        # Return fields that appear in at least 20% of samples
        threshold = sample_size * 0.2
        available = {}
        
        if fields['phonetic'] >= threshold:
            available['Phonetic'] = 'Pronunciation in IPA or phonetic symbols'
        if fields['definition'] >= threshold:
            available['Definition'] = 'Word definition and meaning'
        if fields['example'] >= threshold:
            available['Example'] = 'Example sentences'
        
        return available
    
    def close(self):
        """Close the dictionary and free resources"""
        self.is_loaded = False
        self._word_dict.clear()
        self._mdx = None


def create_parser(mdx_path: str) -> MDXParser:
    """
    Factory function to create an MDX parser
    
    Returns MDXParser which uses mdict-utils library.
    """
    return MDXParser(mdx_path)
