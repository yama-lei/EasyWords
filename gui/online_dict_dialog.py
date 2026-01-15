# -*- coding: utf-8 -*-
"""
Online Dictionary configuration dialog
"""

from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                     QListWidget, QListWidgetItem, QCheckBox, QComboBox, 
                     QFormLayout, QGroupBox)
from aqt.utils import showInfo, askUser
from aqt import mw

from ..config import config
from ..dictionary.online import get_available_online_dicts


class OnlineDictDialog(QDialog):
    """Dialog for configuring online dictionaries"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Online Dictionaries Configuration")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.dictionaries = config.get_online_dictionaries()
        
        self.setup_ui()
        self.refresh_list()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(
            "Configure online dictionaries to be used as fallback when word is not found in MDX dictionaries."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Dictionary list
        self.dict_list = QListWidget()
        self.dict_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.dict_list)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Add new dictionary
        self.add_combo = QComboBox()
        self.available_types = get_available_online_dicts()
        for dict_type in self.available_types:
            self.add_combo.addItem(dict_type['name'], dict_type['type'])
            
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_dictionary)
        
        controls_layout.addWidget(QLabel("Add Dictionary:"))
        controls_layout.addWidget(self.add_combo, 1)
        controls_layout.addWidget(self.add_button)
        
        layout.addLayout(controls_layout)
        
        # Management buttons
        btn_layout = QHBoxLayout()
        
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_dictionary)
        btn_layout.addWidget(self.remove_button)
        
        self.move_up_button = QPushButton("Move Up")
        self.move_up_button.clicked.connect(self.move_up)
        btn_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("Move Down")
        self.move_down_button.clicked.connect(self.move_down)
        btn_layout.addWidget(self.move_down_button)
        
        self.toggle_button = QPushButton("Enable/Disable")
        self.toggle_button.clicked.connect(self.toggle_enabled)
        btn_layout.addWidget(self.toggle_button)
        
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
        # Dialog buttons
        dialog_btns = QHBoxLayout()
        dialog_btns.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_config)
        dialog_btns.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        dialog_btns.addWidget(cancel_btn)
        
        layout.addLayout(dialog_btns)
        
        self.setLayout(layout)
    
    def refresh_list(self):
        """Refresh the list widget"""
        self.dict_list.clear()
        
        for dict_config in self.dictionaries:
            name = dict_config.get('name', 'Unknown')
            enabled = dict_config.get('enabled', True)
            type_code = dict_config.get('type', '')
            
            # Find pretty name for type
            type_name = type_code
            for t in self.available_types:
                if t['type'] == type_code:
                    type_name = t['name']
                    break
            
            status = "✅" if enabled else "❌"
            text = f"{status} {type_name}"
            
            item = QListWidgetItem(text)
            item.setData(100, dict_config) # Store config in item
            self.dict_list.addItem(item)
    
    def add_dictionary(self):
        """Add selected dictionary type"""
        type_code = self.add_combo.currentData()
        type_name = self.add_combo.currentText()
        
        # Check if already added
        for d in self.dictionaries:
            if d.get('type') == type_code:
                showInfo(f"{type_name} is already added.")
                return
        
        new_dict = {
            'type': type_code,
            'name': type_name,
            'enabled': True
        }
        
        self.dictionaries.append(new_dict)
        self.refresh_list()
    
    def remove_dictionary(self):
        """Remove selected dictionary"""
        row = self.dict_list.currentRow()
        if row < 0:
            return
            
        if askUser("Are you sure you want to remove this dictionary?"):
            self.dictionaries.pop(row)
            self.refresh_list()
    
    def move_up(self):
        """Move selected dictionary up"""
        row = self.dict_list.currentRow()
        if row <= 0:
            return
            
        self.dictionaries[row], self.dictionaries[row-1] = self.dictionaries[row-1], self.dictionaries[row]
        self.refresh_list()
        self.dict_list.setCurrentRow(row-1)
    
    def move_down(self):
        """Move selected dictionary down"""
        row = self.dict_list.currentRow()
        if row < 0 or row >= len(self.dictionaries) - 1:
            return
            
        self.dictionaries[row], self.dictionaries[row+1] = self.dictionaries[row+1], self.dictionaries[row]
        self.refresh_list()
        self.dict_list.setCurrentRow(row+1)
        
    def toggle_enabled(self):
        """Toggle enabled status of selected dictionary"""
        row = self.dict_list.currentRow()
        if row < 0:
            return
            
        self.dictionaries[row]['enabled'] = not self.dictionaries[row]['enabled']
        self.refresh_list()
        self.dict_list.setCurrentRow(row)
        
    def save_config(self):
        """Save configuration"""
        config.set_online_dictionaries(self.dictionaries)
        showInfo("Online dictionaries configuration saved.")
        self.accept()
