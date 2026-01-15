# -*- coding: utf-8 -*-
"""
EasyWords - Vocabulary Builder Add-on for Anki

Automatically add phonetics, definitions, examples and TTS audio to vocabulary cards
using MDX dictionaries. Supports batch processing and auto-playback during review.
"""

from . import hooks


def init_addon():
    """Initialize the EasyWords add-on"""
    # Setup hooks (note type creation is handled in hooks after collection loads)
    hooks.setup_hooks()


# Initialize the add-on
init_addon()
