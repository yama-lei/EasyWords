# -*- coding: utf-8 -*-
"""
Field mapping dialog for EasyWords
"""

from typing import Dict, List
from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                     QComboBox, QCheckBox, QFormLayout, QGroupBox, QScrollArea, QWidget)
from aqt.utils import showInfo
from aqt import mw

from ..config import config
from .dict_inspector_dialog import DictInspectorDialog


class FieldMappingDialog(QDialog):
    """Dialog for configuring field mappings per note type"""
    
    # Standard EasyWords source fields
    SOURCE_FIELDS = ['Word', 'Phonetic', 'Definition', 'Example', 'Audio']
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EasyWords - Field Mapping Configuration")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        self.field_combos: Dict[str, QComboBox] = {}
        self.field_enabled: Dict[str, QCheckBox] = {}
        self.current_note_type = None
        self.target_fields: List[str] = []
        
        self.setup_ui()
        self.load_note_types()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(
            "Configure how EasyWords fields map to your note type fields.\n"
            "Select a note type, then choose which fields should be filled."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Note type selection
        notetype_layout = QHBoxLayout()
        notetype_layout.addWidget(QLabel("Note Type:"))
        
        self.notetype_combo = QComboBox()
        self.notetype_combo.currentIndexChanged.connect(self.on_notetype_changed)
        notetype_layout.addWidget(self.notetype_combo, 1)
        
        self.inspect_button = QPushButton("View Dictionary Fields")
        self.inspect_button.clicked.connect(self.show_dict_inspector)
        notetype_layout.addWidget(self.inspect_button)
        
        layout.addLayout(notetype_layout)
        
        # Field mapping section
        mapping_group = QGroupBox("Field Mapping")
        mapping_layout = QVBoxLayout()
        
        # Scroll area for field mappings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.form_layout = QFormLayout()
        scroll_widget.setLayout(self.form_layout)
        scroll.setWidget(scroll_widget)
        
        mapping_layout.addWidget(scroll)
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save Mapping")
        self.save_button.clicked.connect(self.save_mapping)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_note_types(self):
        """Load all available note types from Anki"""
        if not mw or not mw.col:
            return
        
        self.notetype_combo.clear()
        
        # Get all note types
        models = mw.col.models.all()
        for model in models:
            self.notetype_combo.addItem(model['name'], model['id'])
        
        # Select first note type
        if self.notetype_combo.count() > 0:
            self.notetype_combo.setCurrentIndex(0)
    
    def on_notetype_changed(self):
        """Handle note type selection change"""
        if not mw or not mw.col:
            return
        
        notetype_name = self.notetype_combo.currentText()
        if not notetype_name:
            return
        
        self.current_note_type = notetype_name
        
        # Get note type model
        model = mw.col.models.by_name(notetype_name)
        if not model:
            return
        
        # Get target fields from the note type
        self.target_fields = [field['name'] for field in model['flds']]
        
        # Load existing mapping (full format with enabled status)
        existing_mapping = config.get_field_mapping_full(notetype_name)
        
        # Rebuild field mapping UI
        self.rebuild_field_mapping_ui(existing_mapping)
    
    def rebuild_field_mapping_ui(self, existing_mapping: Dict[str, Dict]):
        """Rebuild the field mapping UI with current note type fields"""
        # Clear existing form
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.field_combos.clear()
        self.field_enabled.clear()
        
        if not self.target_fields:
            no_fields_label = QLabel("This note type has no fields.")
            self.form_layout.addRow(no_fields_label)
            return
        
        # Create combo box and checkbox for each source field
        for source_field in self.SOURCE_FIELDS:
            # Enabled checkbox
            enabled_check = QCheckBox(f"Enable {source_field}")
            enabled_check.setChecked(True)
            
            # Field combo box
            combo = QComboBox()
            combo.addItem("(Don't fill this field)", "")
            
            # Add all target fields
            for target_field in self.target_fields:
                combo.addItem(target_field, target_field)
            
            # Set current mapping if exists
            if source_field in existing_mapping:
                field_config = existing_mapping[source_field]
                target = field_config.get('target', '')
                enabled = field_config.get('enabled', True)
                
                index = combo.findData(target)
                if index >= 0:
                    combo.setCurrentIndex(index)
                enabled_check.setChecked(enabled)
            else:
                # Try to find a matching field name
                index = combo.findText(source_field)
                if index >= 0:
                    combo.setCurrentIndex(index)
            
            # Enable/disable combo based on checkbox
            combo.setEnabled(enabled_check.isChecked())
            enabled_check.toggled.connect(lambda checked, c=combo: c.setEnabled(checked))
            
            self.field_combos[source_field] = combo
            self.field_enabled[source_field] = enabled_check
            
            # Add to form with checkbox and combo in a horizontal layout
            row_layout = QHBoxLayout()
            row_layout.addWidget(enabled_check)
            row_layout.addWidget(combo, 1)
            
            label_text = f"{source_field}:"
            if source_field == 'Word':
                label_text = f"<b>{source_field}</b> (Required):"
            
            label = QLabel(label_text)
            self.form_layout.addRow(label, row_layout)
    
    def save_mapping(self):
        """Save the field mapping configuration"""
        if not self.current_note_type:
            showInfo("Please select a note type first.")
            return
        
        # Collect mapping from UI with enabled status
        mapping = {}
        for source_field, combo in self.field_combos.items():
            target_field = combo.currentData()
            enabled = self.field_enabled[source_field].isChecked()
            
            if target_field:  # Only save if a target is selected
                mapping[source_field] = {
                    'target': target_field,
                    'enabled': enabled
                }
        
        if not mapping:
            showInfo("Please map at least one field.")
            return
            
        # Validation: 'Word' field is required
        word_mapped = False
        if 'Word' in mapping and mapping['Word'].get('enabled', False):
            word_mapped = True
            
        if not word_mapped:
            showInfo("The 'Word' field must be mapped and enabled.\nEasyWords needs this field to know what to look up.")
            return
        
        # Save to config
        config.set_field_mapping(self.current_note_type, mapping)
        
        showInfo(f"Field mapping saved for '{self.current_note_type}'!")
        self.accept()
    
    def show_dict_inspector(self):
        """Show the dictionary fields inspector"""
        dialog = DictInspectorDialog(self)
        dialog.exec()
