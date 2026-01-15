# -*- coding: utf-8 -*-
"""
Dependency management for EasyWords
"""

import subprocess
import sys
import os
from typing import Optional


def get_anki_python() -> str:
    """Get the Python executable used by Anki"""
    return sys.executable


def install_package(package_name: str) -> bool:
    """
    Install a Python package in Anki's environment
    
    Args:
        package_name: Name of the package to install
    
    Returns:
        True if installation succeeded, False otherwise
    """
    try:
        python_exe = get_anki_python()
        
        # Try to install using pip
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"Failed to install {package_name}: {e}")
        return False


def check_package_installed(package_name: str) -> bool:
    """
    Check if a package is installed
    
    Args:
        package_name: Name of the package to check
    
    Returns:
        True if package is installed, False otherwise
    """
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def ensure_edge_tts() -> bool:
    """
    Ensure edge-tts is installed (optional dependency)
    
    Returns:
        True if edge-tts is available, False otherwise
    """
    if check_package_installed('edge_tts'):
        return True
    
    print("edge-tts not found. This is optional - SAPI5 will be used instead.")
    return False


def ensure_pywin32() -> bool:
    """
    Ensure pywin32 is installed (for SAPI5 on Windows)
    
    Returns:
        True if pywin32 is available, False otherwise
    """
    if sys.platform != "win32":
        return False
    
    try:
        import win32com.client
        return True
    except ImportError:
        print("pywin32 not found. SAPI5 TTS will not be available.")
        return False


def ensure_mdict_utils() -> bool:
    """
    Ensure mdict-utils is installed (for MDX dictionary parsing)
    
    Returns:
        True if mdict-utils is available, False otherwise
    """
    try:
        import mdict_utils
        return True
    except ImportError:
        print("mdict-utils not found. MDX dictionaries will not be available.")
        return False


def check_all_dependencies() -> dict:
    """
    Check status of all dependencies
    
    Returns:
        Dictionary with dependency status
    """
    status = {
        'pywin32': False,
        'edge_tts': False,
        'mdict_utils': False
    }
    
    if sys.platform == "win32":
        status['pywin32'] = ensure_pywin32()
    
    status['edge_tts'] = ensure_edge_tts()
    status['mdict_utils'] = ensure_mdict_utils()
    
    return status


def get_dependency_info() -> str:
    """
    Get human-readable dependency information
    
    Returns:
        Formatted string with dependency status
    """
    status = check_all_dependencies()
    
    info = "EasyWords Dependency Status:\n\n"
    
    # MDX Dictionary Support
    if status['mdict_utils']:
        info += "[OK] MDX Dictionaries: Available\n"
    else:
        info += "[X] MDX Dictionaries: Not available (mdict-utils missing)\n"
        info += "    To install: Click 'Install MDX Support' in config\n"
    
    info += "\n"
    
    # SAPI5 (Windows only)
    if sys.platform == "win32":
        if status['pywin32']:
            info += "[OK] Windows SAPI5: Available (offline TTS)\n"
        else:
            info += "[X] Windows SAPI5: Not available (pywin32 missing)\n"
            info += "    To install: Use Anki's Python environment\n"
    else:
        info += "[!] Windows SAPI5: Not available (Windows only)\n"
    
    # Edge TTS
    if status['edge_tts']:
        info += "[OK] Edge TTS: Available (online high-quality TTS)\n"
    else:
        info += "[!] Edge TTS: Not available (optional)\n"
        info += "    This is optional - SAPI5 works offline\n"
        info += "    To install: Click 'Install Edge TTS' in config\n"
    
    # Overall status
    info += "\n"
    if sys.platform == "win32" and status['pywin32']:
        info += "[OK] At least one TTS engine is available!\n"
    elif status['edge_tts']:
        info += "[OK] Edge TTS is available!\n"
    else:
        info += "[!] No TTS engines available. Please check installation.\n"
    
    return info


def auto_install_edge_tts_with_permission() -> bool:
    """
    Install edge-tts with user permission
    
    Returns:
        True if installation succeeded, False otherwise
    """
    from aqt.utils import askUser, showInfo, tooltip
    
    if check_package_installed('edge_tts'):
        tooltip("Edge TTS is already installed!")
        return True
    
    # Ask user for permission
    msg = ("Edge TTS is not installed.\n\n"
           "Would you like to install it now?\n\n"
           "This will download and install the edge-tts package "
           "in Anki's Python environment.\n\n"
           "Note: Internet connection required.")
    
    if not askUser(msg):
        return False
    
    # Show progress
    tooltip("Installing edge-tts... Please wait...")
    
    # Install
    success = install_package("edge-tts")
    
    if success:
        showInfo("Edge TTS installed successfully!\n\n"
                 "Please restart Anki to use Edge TTS.")
        return True
    else:
        showInfo("Failed to install Edge TTS.\n\n"
                 "You can install it manually:\n"
                 f"Run: {get_anki_python()} -m pip install edge-tts")
        return False


def auto_install_mdict_utils_with_permission() -> bool:
    """
    Install mdict-utils with user permission
    
    Returns:
        True if installation succeeded, False otherwise
    """
    from aqt.utils import askUser, showInfo, tooltip
    
    if check_package_installed('mdict_utils'):
        tooltip("mdict-utils is already installed!")
        return True
    
    # Ask user for permission
    msg = ("MDX dictionary support (mdict-utils) is not installed.\n\n"
           "Would you like to install it now?\n\n"
           "This will download and install the mdict-utils package "
           "in Anki's Python environment.\n\n"
           "Note: Internet connection required.")
    
    if not askUser(msg):
        return False
    
    # Show progress
    tooltip("Installing mdict-utils... Please wait...")
    
    # Install
    success = install_package("mdict-utils")
    
    if success:
        showInfo("mdict-utils installed successfully!\n\n"
                 "You can now use MDX dictionaries with EasyWords.")
        return True
    else:
        showInfo("Failed to install mdict-utils.\n\n"
                 "You can install it manually:\n"
                 f"Run: {get_anki_python()} -m pip install mdict-utils")
        return False
