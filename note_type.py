# -*- coding: utf-8 -*-
"""
Note type management for EasyWords add-on
"""

from typing import Optional, List, Dict
import aqt
from aqt import mw
from anki.models import ModelManager, NotetypeDict


NOTE_TYPE_NAME = "EasyWords Vocabulary"

# Field names
FIELD_WORD = "Word"
FIELD_PHONETIC = "Phonetic"
FIELD_DEFINITION = "Definition"
FIELD_EXAMPLE = "Example"
FIELD_AUDIO = "Audio"

FIELD_NAMES = [
    FIELD_WORD,
    FIELD_PHONETIC,
    FIELD_DEFINITION,
    FIELD_EXAMPLE,
    FIELD_AUDIO
]


def get_note_type() -> Optional[NotetypeDict]:
    """Get the EasyWords note type if it exists"""
    if not mw or not mw.col:
        return None
    mm: ModelManager = mw.col.models
    return mm.by_name(NOTE_TYPE_NAME)


def ensure_note_type() -> Optional[NotetypeDict]:
    """
    Ensure the EasyWords note type exists, create if not.
    Returns the note type, or None if collection is not available.
    
    Note: This is now optional. Users can use any note type with field mapping.
    """
    if not mw or not mw.col:
        return None
    
    mm: ModelManager = mw.col.models
    
    # Check if note type already exists
    existing = get_note_type()
    if existing:
        return existing
    
    # Create new note type
    note_type = mm.new(NOTE_TYPE_NAME)
    
    # Add fields
    for field_name in FIELD_NAMES:
        field = mm.new_field(field_name)
        mm.add_field(note_type, field)
    
    # Create card template
    template = mm.new_template("Card 1")
    
    # Front template
    template['qfmt'] = """
<div class="word">{{Word}}</div>
<div class="phonetic">{{Phonetic}}</div>
"""
    
    # Back template
    template['afmt'] = """
{{FrontSide}}

<hr id=answer>

<div class="definition">
  <strong>Definition:</strong><br>
  {{Definition}}
</div>

{{#Example}}
<div class="example">
  <strong>Example:</strong><br>
  {{Example}}
</div>
{{/Example}}

{{Audio}}
"""
    
    # Styling
    note_type['css'] = """
.card {
  font-family: arial;
  font-size: 20px;
  text-align: center;
  color: black;
  background-color: white;
}

.word {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
  margin: 20px 0;
}

.phonetic {
  font-size: 18px;
  color: #7f8c8d;
  margin: 10px 0;
}

.definition {
  text-align: left;
  margin: 20px;
  padding: 15px;
  background-color: #ecf0f1;
  border-radius: 5px;
}

.example {
  text-align: left;
  margin: 20px;
  padding: 15px;
  background-color: #e8f5e9;
  border-radius: 5px;
  font-style: italic;
}

.definition strong,
.example strong {
  color: #2c3e50;
}
"""
    
    mm.add_template(note_type, template)
    mm.add(note_type)
    
    return note_type


def get_field_index(note_type: NotetypeDict, field_name: str) -> Optional[int]:
    """Get the index of a field in a note type"""
    for idx, field in enumerate(note_type['flds']):
        if field['name'] == field_name:
            return idx
    return None


def is_easywords_note(note) -> bool:
    """Check if a note is an EasyWords note type"""
    return note.note_type()['name'] == NOTE_TYPE_NAME


def has_word_field(note) -> bool:
    """Check if a note has a Word field"""
    return FIELD_WORD in note


def get_mapped_fields(note) -> Optional[Dict[str, str]]:
    """
    Get field mapping for a note
    
    Args:
        note: The note to get mapping for
    
    Returns:
        Dict mapping source field to target field name, or None if no mapping
        Format: {"Word": "target_field", "Phonetic": "target_field", ...}
    """
    from .config import config
    
    note_type_name = note.note_type()['name']
    mapping = config.get_field_mapping(note_type_name)
    
    if mapping:
        return mapping
    
    # Fallback: check if note has standard EasyWords fields
    if is_easywords_note(note):
        return {
            FIELD_WORD: FIELD_WORD,
            FIELD_PHONETIC: FIELD_PHONETIC,
            FIELD_DEFINITION: FIELD_DEFINITION,
            FIELD_EXAMPLE: FIELD_EXAMPLE,
            FIELD_AUDIO: FIELD_AUDIO
        }
    
    # Fallback 2: Auto-discover fields by name
    # If the note has fields that match our standard names, use them.
    found_mapping = {}
    note_fields = note.keys()
    
    for field in FIELD_NAMES:
        if field in note_fields:
            found_mapping[field] = field
            
    # Require at least "Word" field to be considered a valid mapping
    if FIELD_WORD in found_mapping:
        return found_mapping
    
    return None


def get_word_from_note(note) -> Optional[str]:
    """
    Get the word field content from a note using field mapping
    
    Args:
        note: The note to get word from
    
    Returns:
        The word content, or None if not found
    """
    mapping = get_mapped_fields(note)
    if not mapping:
        return None
    
    word_field = mapping.get('Word')
    if word_field and word_field in note:
        return note[word_field].strip()
    
    return None
