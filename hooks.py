# -*- coding: utf-8 -*-
"""
Anki hooks integration for EasyWords add-on
"""

import aqt
from aqt import gui_hooks, mw
from aqt.qt import QAction, QMenu
import weakref

from .config import config


# Keep track of active editors to update UI
_active_editors = weakref.WeakSet()
_addnote_hook_installed = False


def setup_hooks():
    """Setup all Anki hooks"""
    setup_profile_hooks()
    setup_menu()
    setup_editor_hooks()
    setup_browser_hooks()
    setup_reviewer_hooks()


def setup_profile_hooks():
    """Setup profile-related hooks"""
    
    def on_profile_did_open():
        """Called when a profile is opened and collection is available"""
        from .note_type import ensure_note_type
        from .config import config
        
        # Create note type if auto-create is enabled
        if config.is_auto_create_note_type():
            ensure_note_type()

        _install_addnote_hook()
    
    gui_hooks.profile_did_open.append(on_profile_did_open)

def _install_addnote_hook() -> None:
    import logging
    import types

    global _addnote_hook_installed
    if _addnote_hook_installed:
        return
    if not mw or not getattr(mw, "col", None):
        return
    col = mw.col
    if not hasattr(col, "addNote"):
        return

    logger = logging.getLogger(__name__)
    original_add_note = col.addNote

    def wrapped(self, note, *args, **kwargs):
        result = original_add_note(note, *args, **kwargs)
        try:
            if config.is_auto_generate_audio_on_add():
                _maybe_generate_audio_for_note(note)
        except Exception as e:
            logger.error(f"Auto audio generation after addNote failed: {e}", exc_info=True)
        return result

    col.addNote = types.MethodType(wrapped, col)
    _addnote_hook_installed = True


def _maybe_generate_audio_for_note(note) -> None:
    import logging

    from .note_type import get_mapped_fields, get_word_from_note
    from .tts.manager import generate_audio_in_background

    logger = logging.getLogger(__name__)

    mapping = get_mapped_fields(note)
    if not mapping:
        return

    audio_field_name = mapping.get("Audio")
    if not audio_field_name or audio_field_name not in note:
        return

    if note[audio_field_name]:
        return

    word = get_word_from_note(note)
    if not word:
        return

    def _on_done(success: bool, filename: str | None) -> None:
        if not success or not filename:
            return
        try:
            if getattr(note, "id", 0) != 0:
                note.flush()
        except Exception as e:
            logger.error(f"Failed to flush note after audio generation: {e}", exc_info=True)

    def _start_generation(retry_count: int = 0) -> None:
        def _callback(success: bool, filename: str | None) -> None:
            if success:
                _on_done(True, filename)
                return
            if retry_count < 3:
                logger.info(f"Retrying audio generation for '{word}' ({retry_count + 1}/3)")
                _start_generation(retry_count + 1)
                return
            _on_done(False, None)

        generate_audio_in_background(note, audio_field_name, word, _callback)

    _start_generation()


def setup_menu():
    """Add EasyWords menu to Tools menu"""
    action = QAction("EasyWords Configuration...", mw)
    action.triggered.connect(show_config_dialog)
    mw.form.menuTools.addAction(action)


def show_config_dialog():
    """Show the configuration dialog"""
    from .gui.config_dialog import ConfigDialog
    dialog = ConfigDialog(mw)
    dialog.exec()


def setup_editor_hooks():
    """Setup editor-related hooks"""
    
    def on_editor_did_init(editor):
        """Track active editors"""
        _active_editors.add(editor)
        
    gui_hooks.editor_did_init.append(on_editor_did_init)
    
    def on_editor_did_init_buttons(buttons, editor):
        """Add EasyWords buttons to editor"""
        from .gui.icons import get_icon
        
        # Standard Fill Button
        fill_button = editor.addButton(
            icon=None,  # We'll add an icon later
            cmd="easywords_fill",
            func=lambda ed: fill_current_note(ed),
            tip="Fill word information with EasyWords",
            label="EW"
        )
        buttons.append(fill_button)
        
        # AI Button
        ai_button = editor.addButton(
            icon=None,
            cmd="easywords_ai",
            func=lambda ed: ai_fill_current_note(ed),
            tip="Generate definitions and examples with AI",
            label="AI"
        )
        buttons.append(ai_button)
        
        return buttons
    
    gui_hooks.editor_did_init_buttons.append(on_editor_did_init_buttons)
    
    # Auto-fill or auto-audio on add if enabled
    if config.is_auto_fill_on_add() or config.is_auto_generate_audio_on_add():
        def on_add_cards_did_add_note(note):
            """Auto-fill when adding a new note"""
            from .note_type import get_mapped_fields, get_word_from_note
            
            # Check if note has field mapping and word content
            mapping = get_mapped_fields(note)
            if mapping and get_word_from_note(note):
                if config.is_auto_fill_on_add():
                    fill_note_fields(note)
                elif config.is_auto_generate_audio_on_add():
                    _maybe_generate_audio_for_note(note)
        
        gui_hooks.add_cards_did_add_note.append(on_add_cards_did_add_note)

    # Auto-generate audio on field unfocus (Phase 2)
    gui_hooks.editor_did_unfocus_field.append(on_editor_did_unfocus_field)


def on_editor_did_unfocus_field(changed: bool, note, current_field_idx: int):
    """
    Handle field unfocus event to trigger auto audio generation.
    """
    # Only proceed if changed is True (user edited the field)
    if not changed:
        return

    if not config.is_auto_generate_audio_on_add():
        return
        
    from .note_type import get_mapped_fields
    from .tts.manager import generate_audio_in_background
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Check if we should generate audio
    mapping = get_mapped_fields(note)
    if not mapping:
        return
        
    # Check if unfocused field is "Word"
    word_field_name = mapping.get('Word')
    if not word_field_name:
        return
        
    # Map index to field name
    field_names = list(note.keys())
    if current_field_idx >= len(field_names):
        return
        
    unfocused_field_name = field_names[current_field_idx]
    
    if unfocused_field_name != word_field_name:
        return
        
    # Check Audio field
    audio_field_name = mapping.get('Audio')
    if not audio_field_name or audio_field_name not in note:
        return
        
    # Check if Audio is empty
    if note[audio_field_name]:
        return
        
    # Get word content
    word = note[word_field_name].strip()
    if not word:
        return
        
    logger.debug(f"Auto-generating audio for '{word}'")
    
    # Find the editor for this note
    editor = None
    for ed in _active_editors:
        if ed.note is note:
            editor = ed
            break
            
    def _on_done(success, filename):
        if success and filename:
            logger.info(f"Auto-generated audio for '{word}': {filename}")
            if editor:
                # Update editor UI
                # We use setNoteField which updates the note and the UI
                # Note: note[audio_field_name] is already updated by generate_audio_in_background
                # But to be safe and ensure UI sync, we can set it again via editor
                editor.setNoteField(audio_field_name, f"[sound:{filename}]")
        else:
            logger.warning(f"Failed to auto-generate audio for '{word}'")
            # Retry logic could be implemented here if needed, 
            # but for now we just log. 
            # Requirements said "Add failure retry logic (max 3 times)".
            # We can implement a simple retry wrapper here.

    # Retry wrapper
    def _start_generation(retry_count=0):
        def _callback(success, filename):
            if success:
                _on_done(True, filename)
            elif retry_count < 3:
                logger.info(f"Retrying audio generation for '{word}' ({retry_count + 1}/3)")
                _start_generation(retry_count + 1)
            else:
                _on_done(False, None)
                
        generate_audio_in_background(note, audio_field_name, word, _callback)

    _start_generation()


def fill_current_note(editor):
    """Fill the current note being edited - seamless interaction"""
    import logging
    from aqt.utils import tooltip, showWarning

    logger = logging.getLogger(__name__)

    try:
        if not editor.note:
            logger.warning("No note in editor")
            tooltip("No note to fill", parent=editor.widget)
            return

        from .note_type import get_mapped_fields

        # Check if note has field mapping configured
        mapping = get_mapped_fields(editor.note)
        if not mapping:
            tooltip("Note type not configured for EasyWords", parent=editor.widget)
            return

        fill_note_fields(editor.note, flush=False)
        editor.loadNote()
        tooltip("✓ Fields filled", parent=editor.widget)

    except Exception as e:
        logger.error(f"Failed to fill note in editor: {e}", exc_info=True)
        showWarning(f"Failed to fill note:\n{str(e)}\n\nPlease check the Anki console for details.")


def ai_fill_current_note(editor):
    """Fill the current note using AI - seamless interaction without dialogs"""
    import logging
    from .ai.client import OpenAIClient
    from .note_type import get_mapped_fields, get_word_from_note
    from aqt.utils import showWarning, tooltip
    from aqt.operations import QueryOp

    logger = logging.getLogger(__name__)

    try:
        if not editor.note:
            tooltip("No note in editor", parent=editor.widget)
            return

        # Check configuration
        client = OpenAIClient()
        if not client.is_configured():
            showWarning("OpenAI API Key is not configured.\nPlease go to Tools > EasyWords Configuration > AI Integration.")
            return

        mapping = get_mapped_fields(editor.note)
        if not mapping:
            tooltip("Note type not configured for EasyWords", parent=editor.widget)
            return

        word = get_word_from_note(editor.note)
        if not word:
            tooltip("Word field is empty", parent=editor.widget)
            return

        # Determine fields to fill
        fields_to_fill = []
        target_fields = {} # mapped_name -> target_field

        # Check Definition
        if 'Definition' in mapping:
            target = mapping['Definition']
            if not editor.note[target]:
                fields_to_fill.append("Definition")
                target_fields['Definition'] = target

        # Check Example
        if 'Example' in mapping:
            target = mapping['Example']
            if not editor.note[target]:
                fields_to_fill.append("Example")
                target_fields['Example'] = target

        if not fields_to_fill:
            tooltip("All AI fields already filled", parent=editor.widget)
            return

        # Show brief tooltip before starting
        tooltip("AI filling...", parent=editor.widget)

        def _op(col):
            return client.suggest_fields(word, fields_to_fill)

        def _success(result):
            if not result:
                tooltip("AI request failed - check console", parent=editor.widget)
                logger.warning(f"AI returned empty result for word: {word}")
                return

            count = 0
            for field_name, content in result.items():
                if field_name in target_fields:
                    target = target_fields[field_name]
                    editor.note[target] = content
                    count += 1

            if count > 0:
                editor.loadNote()
                tooltip(f"✓ Filled {count} field(s)", parent=editor.widget)
                logger.info(f"Successfully filled {count} fields for word: {word}")
            else:
                tooltip("AI returned no content", parent=editor.widget)

        op = QueryOp(
            parent=mw,
            op=lambda col: _op(col),
            success=_success
        )
        op.run_in_background()

    except Exception as e:
        logger.error(f"AI fill failed: {e}", exc_info=True)
        tooltip(f"Error: {str(e)}", parent=editor.widget)


def fill_note_fields(note, flush=True):
    """
    Fill note fields with dictionary and TTS data using field mapping
    
    This function works with any note type that has configured field mapping.
    It will fill available fields based on the mapping configuration.
    
    Args:
        note: The note to fill
        flush: Whether to flush changes to database (False for new notes in editor)
    """
    from .note_type import get_mapped_fields, get_word_from_note
    from .dictionary.lookup import lookup_word
    from .tts.manager import generate_audio
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get field mapping for this note type
        mapping = get_mapped_fields(note)
        if not mapping:
            logger.warning(f"Note type '{note.note_type()['name']}' has no field mapping configured")
            return
        
        # Get the word to look up
        word = get_word_from_note(note)
        if not word:
            logger.debug("Word field is empty or not found, skipping")
            return
        
        # Lookup dictionary
        try:
            result = lookup_word(word)
            
            if result:
                # Fill phonetic if mapped and result available
                if 'Phonetic' in mapping:
                    target_field = mapping['Phonetic']
                    if target_field in note and result.get('phonetic'):
                        if not note[target_field]:
                            note[target_field] = result['phonetic']
                            logger.debug(f"Filled phonetic for '{word}' into '{target_field}'")
                
                # Fill definition if mapped and result available
                if 'Definition' in mapping:
                    target_field = mapping['Definition']
                    if target_field in note and result.get('definition'):
                        if not note[target_field]:
                            note[target_field] = result['definition']
                            logger.debug(f"Filled definition for '{word}' into '{target_field}'")
                
                # Fill example if mapped and result available
                if 'Example' in mapping:
                    target_field = mapping['Example']
                    if target_field in note and result.get('example'):
                        if not note[target_field]:
                            note[target_field] = result['example']
                            logger.debug(f"Filled example for '{word}' into '{target_field}'")
        except Exception as e:
            logger.error(f"Failed to lookup word '{word}': {e}", exc_info=True)
            from aqt.utils import showWarning
            showWarning(f"Dictionary lookup failed for '{word}':\n{str(e)}")
        
        # Generate audio if Audio field is mapped and empty
        if 'Audio' in mapping:
            target_field = mapping['Audio']
            if target_field in note:
                try:
                    if not note[target_field]:
                        audio_file = generate_audio(word)
                        if audio_file:
                            note[target_field] = f"[sound:{audio_file}]"
                            logger.info(f"Generated audio for '{word}' into '{target_field}'")
                        else:
                            logger.warning(f"Failed to generate audio for '{word}'")
                except Exception as e:
                    logger.error(f"Failed to generate audio for '{word}': {e}", exc_info=True)
                    from aqt.utils import showWarning
                    showWarning(f"Audio generation failed for '{word}':\n{str(e)}")
        
        # Only flush if note has been saved before (has an id)
        if flush and note.id != 0:
            note.flush()
            
    except Exception as e:
        logger.error(f"Unexpected error in fill_note_fields: {e}", exc_info=True)
        from aqt.utils import showWarning
        showWarning(f"Failed to fill note fields:\n{str(e)}\n\nPlease check the Anki console for details.")


def setup_browser_hooks():
    """Setup browser-related hooks"""
    
    def on_browser_menus_did_init(browser):
        """Add EasyWords menu to browser"""
        menu = QMenu("EasyWords", browser)
        browser.form.menubar.addMenu(menu)
        
        action_fill = QAction("Fill Selected Cards...", browser)
        action_fill.triggered.connect(lambda: batch_fill_cards(browser))
        menu.addAction(action_fill)
    
    gui_hooks.browser_menus_did_init.append(on_browser_menus_did_init)


def batch_fill_cards(browser):
    """Open batch fill dialog"""
    from .gui.batch_dialog import BatchDialog
    from aqt.utils import tooltip

    selected_nids = browser.selectedNotes()
    if not selected_nids:
        tooltip("Please select some cards first", parent=browser)
        return

    dialog = BatchDialog(browser, selected_nids)
    dialog.exec()


def setup_reviewer_hooks():
    """Setup reviewer-related hooks"""
    
    # Auto-play audio during review is handled by the {{Audio}} field
    # which Anki automatically plays when it contains [sound:...] tags
    pass
