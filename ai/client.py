# -*- coding: utf-8 -*-
"""
OpenAI API Client
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from functools import lru_cache

from ..config import config


class OpenAIClient:
    """Client for interacting with OpenAI API"""

    API_URL = "https://api.openai.com/v1/chat/completions"

    # Class-level cache for AI responses (max 256 entries)
    _cache: Dict[str, str] = {}
    _max_cache_size = 256

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.get_openai_api_key()
        self.base_url = config.get_base_url() or self.API_URL

    @classmethod
    def _get_cache_key(cls, word: str, fields: List[str]) -> str:
        """Generate cache key from word and fields"""
        return f"{word}:{','.join(sorted(fields))}"

    @classmethod
    def _get_from_cache(cls, key: str) -> Optional[Dict[str, str]]:
        """Get result from cache"""
        return cls._cache.get(key)

    @classmethod
    def _save_to_cache(cls, key: str, result: Dict[str, str]) -> None:
        """Save result to cache with LRU eviction"""
        if len(cls._cache) >= cls._max_cache_size:
            # Simple LRU: remove first (oldest) entry
            cls._cache.pop(next(iter(cls._cache)))
        cls._cache[key] = result

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the cache"""
        cls._cache.clear()
    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key)
    
    def generate_content(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> Optional[str]:
        """
        Generate content using OpenAI Chat Completion API
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            
        Returns:
            Generated content or None if failed
        """
        if not self.is_configured():
            return None
            
        model = config.get_openai_model()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            req = urllib.request.Request(
                self.base_url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"].strip()
                
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return None
            
        return None

    def suggest_fields(self, word: str, fields: List[str]) -> Dict[str, str]:
        """
        Suggest content for specific fields

        Args:
            word: The word to suggest for
            fields: List of fields to suggest (e.g. ['Definition', 'Example'])

        Returns:
            Dict mapping field name to suggested content
        """
        # Check cache first
        cache_key = self._get_cache_key(word, fields)
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result

        system_prompt = (
            "You are a helpful dictionary assistant. "
            "Provide concise definitions and examples for language learners. "
            "Return the result as a valid JSON object with keys matching the requested fields."
        )

        prompt = (
            f"Word: {word}\n"
            f"Please provide content for the following fields:\n"
            f"{', '.join(fields)}\n\n"
            "Format:\n"
            "{\n"
        )
        for field in fields:
            prompt += f'  "{field}": "...",\n'
        prompt += "}"

        response = self.generate_content(prompt, system_prompt)

        result = {}
        if response:
            try:
                # Basic cleanup if the model adds markdown code blocks
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()

                result = json.loads(response)
            except json.JSONDecodeError:
                print(f"Failed to parse AI response: {response}")

        # Save to cache (even empty results to avoid repeated failed lookups)
        self._save_to_cache(cache_key, result)
        return result
