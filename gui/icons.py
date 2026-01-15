# -*- coding: utf-8 -*-
"""
Icon utilities for EasyWords GUI
"""

from aqt.qt import QIcon, QPixmap
import os


def get_icon(name: str) -> QIcon:
    """
    Get an icon by name
    
    For now, returns an empty icon. Icons can be added later.
    """
    icon_dir = os.path.join(os.path.dirname(__file__), 'icons')
    icon_path = os.path.join(icon_dir, f"{name}.png")
    
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    
    return QIcon()
