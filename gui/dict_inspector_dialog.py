# -*- coding: utf-8 -*-
"""
Dictionary field inspector dialog for EasyWords
"""

import os
from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                     QTreeWidget, QTreeWidgetItem, QTextBrowser, QLineEdit, QSplitter, Qt)
from aqt.utils import showInfo
from aqt import mw

from ..dictionary.lookup import get_parsers


class DictInspectorDialog(QDialog):
    """Dialog for inspecting available dictionary fields"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dictionary Fields Inspector")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        
        self.setup_ui()
        self.load_dictionaries()
    
    def setup_ui(self):
        """Setup the UI components"""
        main_layout = QVBoxLayout()
        
        # Splitter for list and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Dictionary List
        left_widget = QTreeWidget()
        left_widget.setHeaderLabels(["Dictionary / Field"])
        left_widget.itemClicked.connect(self.on_item_clicked)
        self.tree = left_widget
        splitter.addWidget(left_widget)
        
        # Right side: Preview
        right_layout = QVBoxLayout()
        right_widget = QDialog() # Container
        right_widget.setLayout(right_layout)
        
        right_layout.addWidget(QLabel("<b>Preview Field Content</b>"))
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Test Word:"))
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Enter a word to test...")
        self.word_input.returnPressed.connect(self.test_lookup)
        input_layout.addWidget(self.word_input)
        
        self.test_button = QPushButton("Test Lookup")
        self.test_button.clicked.connect(self.test_lookup)
        input_layout.addWidget(self.test_button)
        
        right_layout.addLayout(input_layout)
        
        self.preview_browser = QTextBrowser()
        right_layout.addWidget(self.preview_browser)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 600])
        
        main_layout.addWidget(splitter)
        
        # Status label
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_dictionaries)
        button_layout.addWidget(self.refresh_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def load_dictionaries(self):
        """Load and display dictionary fields"""
        self.tree.clear()
        self.status_label.setText("Loading dictionary fields...")
        
        try:
            parsers = get_parsers()
            
            if not parsers:
                self.status_label.setText("No dictionaries configured.")
                return
            
            # Display each dictionary and its fields
            for parser in parsers:
                # Dictionary item
                dict_name = os.path.basename(parser.mdx_path)
                dict_item = QTreeWidgetItem(self.tree)
                dict_item.setText(0, f"📚 {dict_name}")
                dict_item.setData(0, 100, parser) # Store parser
                
                # Field items
                fields = parser.get_available_fields()
                if fields:
                    for field_name, field_desc in fields.items():
                        field_item = QTreeWidgetItem(dict_item)
                        field_item.setText(0, f"  • {field_name}")
                        field_item.setData(0, 100, parser)
                        field_item.setData(0, 101, field_name) # Store field name
                else:
                    no_fields_item = QTreeWidgetItem(dict_item)
                    no_fields_item.setText(0, "  (No fields detected)")
                
                dict_item.setExpanded(True)
            
            self.status_label.setText(f"Loaded {len(parsers)} dictionary(ies)")
            
        except Exception as e:
            self.status_label.setText(f"Error loading dictionary fields: {str(e)}")
            showInfo(f"Failed to load dictionary fields:\n{str(e)}")

    def on_item_clicked(self, item, column):
        """Handle item click"""
        # If user clicks a field, maybe pre-fill the preview?
        # For now, just focus the input
        pass
    
    def test_lookup(self):
        """Test lookup for selected dictionary"""
        word = self.word_input.text().strip()
        if not word:
            showInfo("Please enter a word.")
            return
            
        item = self.tree.currentItem()
        if not item:
            showInfo("Please select a dictionary or field.")
            return
            
        parser = item.data(0, 100)
        if not parser:
            showInfo("Please select a valid dictionary item.")
            return
            
        # Perform lookup
        try:
            result = parser.lookup(word)
            
            html = f"<h3>Result for '{word}'</h3>"
            
            if result:
                html += "<table border='1' cellspacing='0' cellpadding='5'>"
                for key, value in result.items():
                    html += f"<tr><td><b>{key}</b></td><td>{value}</td></tr>"
                html += "</table>"
            else:
                html += "<p style='color:red'>Not found in this dictionary.</p>"
                
            self.preview_browser.setHtml(html)
            
        except Exception as e:
            self.preview_browser.setHtml(f"<p style='color:red'>Error: {str(e)}</p>")
