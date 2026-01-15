# -*- coding: utf-8 -*-
"""
Batch processing dialog for EasyWords
"""

from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                     QCheckBox, QGroupBox, QProgressBar)
from aqt.utils import showInfo, tooltip
from aqt import mw

from ..note_type import FIELD_WORD, FIELD_PHONETIC, FIELD_DEFINITION, FIELD_EXAMPLE, FIELD_AUDIO
from ..dictionary.lookup import lookup_word
from ..tts.manager import generate_audio, generate_audio_batch


class BatchDialog(QDialog):
    """Dialog for batch processing selected cards"""
    
    def __init__(self, parent, note_ids):
        super().__init__(parent)
        self.note_ids = note_ids
        self.setWindowTitle("EasyWords - Batch Fill")
        self.setMinimumWidth(500)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(f"Selected {len(self.note_ids)} card(s)")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)
        
        # Options group
        options_group = QGroupBox("Fill Options")
        options_layout = QVBoxLayout()
        
        self.fill_phonetic_check = QCheckBox("Fill Phonetic field")
        self.fill_phonetic_check.setChecked(True)
        options_layout.addWidget(self.fill_phonetic_check)
        
        self.fill_definition_check = QCheckBox("Fill Definition field")
        self.fill_definition_check.setChecked(True)
        options_layout.addWidget(self.fill_definition_check)
        
        self.fill_example_check = QCheckBox("Fill Example field")
        self.fill_example_check.setChecked(True)
        options_layout.addWidget(self.fill_example_check)
        
        self.fill_audio_check = QCheckBox("Generate Audio")
        self.fill_audio_check.setChecked(True)
        options_layout.addWidget(self.fill_audio_check)
        
        self.overwrite_check = QCheckBox("Overwrite existing content")
        self.overwrite_check.setChecked(False)
        options_layout.addWidget(self.overwrite_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def start_processing(self):
        """Start batch processing with optimizations"""
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.note_ids))
        self.progress_bar.setValue(0)
        
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        processed = 0
        skipped = 0
        errors = 0
        
        # Import field mapping functions once
        from ..note_type import get_mapped_fields, get_word_from_note
        
        # Cache note type mappings to avoid repeated lookups
        mapping_cache = {}
        notes_to_flush = set() # Store note IDs to flush
        notes_map = {} # ID -> Note object
        
        # Performance tracking
        dict_lookup_time = 0
        audio_gen_time = 0
        
        # Queue for audio generation
        audio_tasks = []
        
        # Phase 1: Dictionary Lookup & Field Prep
        logger.info("Phase 1: Dictionary Lookup")
        
        for i, nid in enumerate(self.note_ids):
            try:
                note = mw.col.get_note(nid)
                notes_map[nid] = note
                note_type_name = note.note_type()['name']
                
                # Check mapping cache first
                if note_type_name not in mapping_cache:
                    mapping_cache[note_type_name] = get_mapped_fields(note)
                
                mapping = mapping_cache[note_type_name]
                if not mapping:
                    skipped += 1
                    self.progress_bar.setValue(i + 1)
                    continue
                
                # Get word from note
                word = get_word_from_note(note)
                if not word:
                    skipped += 1
                    self.progress_bar.setValue(i + 1)
                    continue
                
                changed = False
                
                # Look up dictionary
                dict_start = time.time()
                result = lookup_word(word)
                dict_lookup_time += time.time() - dict_start
                
                if result:
                    # Fill phonetic
                    if self.fill_phonetic_check.isChecked() and 'Phonetic' in mapping:
                        target_field = mapping['Phonetic']
                        if target_field in note and result.get('phonetic'):
                            if self.overwrite_check.isChecked() or not note[target_field]:
                                note[target_field] = result['phonetic']
                                changed = True
                    
                    # Fill definition
                    if self.fill_definition_check.isChecked() and 'Definition' in mapping:
                        target_field = mapping['Definition']
                        if target_field in note and result.get('definition'):
                            if self.overwrite_check.isChecked() or not note[target_field]:
                                note[target_field] = result['definition']
                                changed = True
                    
                    # Fill example
                    if self.fill_example_check.isChecked() and 'Example' in mapping:
                        target_field = mapping['Example']
                        if target_field in note and result.get('example'):
                            if self.overwrite_check.isChecked() or not note[target_field]:
                                note[target_field] = result['example']
                                changed = True
                
                # Prepare Audio Task
                if self.fill_audio_check.isChecked() and 'Audio' in mapping:
                    target_field = mapping['Audio']
                    if target_field in note:
                        if self.overwrite_check.isChecked() or not note[target_field]:
                            audio_tasks.append({
                                'nid': nid,
                                'field': target_field,
                                'text': word
                            })
                            # Don't count as changed yet, will do in Phase 2
                
                if changed:
                    notes_to_flush.add(nid)
                    processed += 1
                elif not audio_tasks or audio_tasks[-1]['nid'] != nid:
                    # If no changes and no audio task, it's a skip
                    skipped += 1
                
            except Exception as e:
                logger.error(f"Error processing note {nid}: {e}", exc_info=True)
                errors += 1
            
            # Update progress bar partially (allocating 50% for Phase 1)
            progress = int((i + 1) / len(self.note_ids) * 50)
            self.progress_bar.setValue(progress)
            
            if (i + 1) % 50 == 0:
                mw.app.processEvents()
        
        # Flush initial changes
        if notes_to_flush:
            for nid in notes_to_flush:
                notes_map[nid].flush()
            notes_to_flush.clear()
        
        # Phase 2: Batch Audio Generation
        logger.info(f"Phase 2: Audio Generation ({len(audio_tasks)} tasks)")
        
        if audio_tasks:
            BATCH_SIZE = 20
            total_audio = len(audio_tasks)
            
            for i in range(0, total_audio, BATCH_SIZE):
                batch = audio_tasks[i:i+BATCH_SIZE]
                
                # Prepare items for manager
                items = [{'text': task['text']} for task in batch]
                
                # Generate
                audio_start = time.time()
                try:
                    filenames = generate_audio_batch(items)
                except Exception as e:
                    logger.error(f"Batch audio generation failed: {e}")
                    filenames = [None] * len(batch)
                    
                audio_gen_time += time.time() - audio_start
                
                # Update notes
                batch_flush_list = []
                for task, filename in zip(batch, filenames):
                    if filename:
                        note = notes_map[task['nid']]
                        note[task['field']] = f"[sound:{filename}]"
                        batch_flush_list.append(note)
                        
                        # Increment processed if not already counted (simple approximation)
                        # We might double count if it was already processed in Phase 1, but "Processed" usually means "touched"
                        # Let's just track successful updates.
                
                # Flush batch
                for note in batch_flush_list:
                    note.flush()
                
                # Update progress (Allocating remaining 50%)
                current_audio_progress = i + len(batch)
                total_progress = 50 + int(current_audio_progress / total_audio * 50)
                self.progress_bar.setValue(total_progress)
                mw.app.processEvents()
        
        # Final Stats
        total_time = time.time() - start_time
        processed_count = processed + len(audio_tasks) # Approximation
        
        # Log performance statistics
        logger.info(f"Batch processing completed in {total_time:.2f}s")
        logger.info(f"  Dictionary lookup: {dict_lookup_time:.2f}s")
        logger.info(f"  Audio generation: {audio_gen_time:.2f}s")
        
        self.progress_bar.setValue(100)
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        
        message = f"Batch processing complete!\n\n"
        message += f"Time: {total_time:.2f}s\n"
        message += f"Lookups: {dict_lookup_time:.2f}s\n"
        message += f"Audio: {audio_gen_time:.2f}s\n"
        
        if errors > 0:
            message += f"\nErrors: {errors}"
        
        showInfo(message)
        self.accept()
