# -*- coding: utf-8 -*-
"""
Configuration dialog for EasyWords
"""

from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                     QListWidget, QComboBox, QDoubleSpinBox, QCheckBox,
                     QFileDialog, QGroupBox, QFormLayout, QLineEdit, QTabWidget, QWidget)
from aqt.utils import showInfo
from aqt import mw

from ..config import config
from ..tts.manager import get_available_engines, get_voices_for_engine
from ..dictionary.lookup import reload_dictionaries


class ConfigDialog(QDialog):
    """Configuration dialog for EasyWords settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("EasyWords Configuration")
        self.setMinimumWidth(600)
        self.setMinimumHeight(600)
        
        self.setup_ui()
        self.load_config()
    
    def setup_ui(self):
        """Setup the UI components"""
        main_layout = QVBoxLayout()
        
        # Use Tabs for better organization
        tabs = QTabWidget()
        
        # General / Dictionaries Tab
        general_tab = QWidget()
        general_layout = QVBoxLayout()
        
        # Dictionary section
        dict_group = self._create_dictionary_section()
        general_layout.addWidget(dict_group)
        
        # Field Mapping & Online Dictionaries buttons
        buttons_layout = QHBoxLayout()
        
        field_mapping_button = QPushButton("Field Mappings...")
        field_mapping_button.clicked.connect(self.show_field_mapping_dialog)
        buttons_layout.addWidget(field_mapping_button)
        
        online_dict_button = QPushButton("Online Dictionaries...")
        online_dict_button.clicked.connect(self.show_online_dict_dialog)
        buttons_layout.addWidget(online_dict_button)
        
        general_layout.addLayout(buttons_layout)
        
        # Options section
        options_group = self._create_options_section()
        general_layout.addWidget(options_group)
        
        general_layout.addStretch()
        general_tab.setLayout(general_layout)
        tabs.addTab(general_tab, "General")
        
        # TTS Tab
        tts_tab = QWidget()
        tts_layout = QVBoxLayout()
        tts_group = self._create_tts_section()
        tts_layout.addWidget(tts_group)
        tts_layout.addStretch()
        tts_tab.setLayout(tts_layout)
        tabs.addTab(tts_tab, "Text-to-Speech")
        
        # AI Tab
        ai_tab = QWidget()
        ai_layout = QVBoxLayout()
        ai_group = self._create_ai_section()
        ai_layout.addWidget(ai_group)
        ai_layout.addStretch()
        ai_tab.setLayout(ai_layout)
        tabs.addTab(ai_tab, "AI Integration")
        
        main_layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def _create_dictionary_section(self):
        """Create dictionary configuration section"""
        group = QGroupBox("MDX Dictionaries")
        layout = QVBoxLayout()
        
        label = QLabel("Configure MDX dictionary paths (in priority order):")
        layout.addWidget(label)
        
        # Dictionary list
        self.dict_list = QListWidget()
        layout.addWidget(self.dict_list)
        
        # Buttons for dictionary management
        button_layout = QHBoxLayout()
        
        self.add_dict_button = QPushButton("Add Dictionary...")
        self.add_dict_button.clicked.connect(self.add_dictionary)
        button_layout.addWidget(self.add_dict_button)
        
        self.remove_dict_button = QPushButton("Remove Selected")
        self.remove_dict_button.clicked.connect(self.remove_dictionary)
        button_layout.addWidget(self.remove_dict_button)
        
        self.move_up_button = QPushButton("Move Up")
        self.move_up_button.clicked.connect(self.move_dictionary_up)
        button_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("Move Down")
        self.move_down_button.clicked.connect(self.move_dictionary_down)
        button_layout.addWidget(self.move_down_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_tts_section(self):
        """Create TTS configuration section"""
        group = QGroupBox("Text-to-Speech Settings")
        layout = QVBoxLayout()
        
        # Dependency status button
        status_button = QPushButton("Check TTS Dependencies")
        status_button.clicked.connect(self.show_dependency_status)
        layout.addWidget(status_button)
        
        # Form for settings
        form_layout = QFormLayout()
        
        # TTS Engine selection
        self.engine_combo = QComboBox()
        available_engines = get_available_engines()
        for engine_name, engine in available_engines.items():
            self.engine_combo.addItem(engine_name, engine_name)
        self.engine_combo.currentIndexChanged.connect(self.on_engine_changed)
        form_layout.addRow("TTS Engine:", self.engine_combo)
        
        # Voice selection
        self.voice_combo = QComboBox()
        form_layout.addRow("Voice:", self.voice_combo)
        
        # Speed setting
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.5, 2.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.setValue(1.0)
        form_layout.addRow("Speed:", self.speed_spin)
        
        layout.addLayout(form_layout)
        
        # Install Edge TTS button
        install_button = QPushButton("Install Edge TTS (Optional)")
        install_button.clicked.connect(self.install_edge_tts)
        layout.addWidget(install_button)
        
        group.setLayout(layout)
        return group
    
    def _create_options_section(self):
        """Create options section"""
        group = QGroupBox("General Options")
        layout = QVBoxLayout()
        
        self.auto_fill_check = QCheckBox("Automatically fill fields when adding new cards")
        layout.addWidget(self.auto_fill_check)
        
        self.auto_generate_audio_check = QCheckBox("Automatically generate audio when adding new cards")
        self.auto_generate_audio_check.setToolTip("Generate audio even if other fields are not filled automatically")
        layout.addWidget(self.auto_generate_audio_check)
        
        self.auto_play_check = QCheckBox("Automatically play audio during review")
        layout.addWidget(self.auto_play_check)
        
        self.cache_audio_check = QCheckBox("Cache generated audio files")
        layout.addWidget(self.cache_audio_check)
        
        self.auto_create_notetype_check = QCheckBox("Automatically create EasyWords note type (legacy)")
        layout.addWidget(self.auto_create_notetype_check)

        # Dictionary mode: local / online / auto
        self.dict_mode_combo = QComboBox()
        self.dict_mode_combo.addItem("Local dictionaries only", "local")
        self.dict_mode_combo.addItem("Online dictionaries only", "online")
        self.dict_mode_combo.addItem("Local first, then online (auto)", "auto")
        layout.addWidget(QLabel("Dictionary source:"))
        layout.addWidget(self.dict_mode_combo)
        
        group.setLayout(layout)
        return group

    def _create_ai_section(self):
        """Create AI configuration section"""
        group = QGroupBox("OpenAI Integration")
        layout = QFormLayout()
        
        # API Key
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("API Key:", self.openai_key_input)
        
        # Model
        self.openai_model_input = QLineEdit()
        self.openai_model_input.setPlaceholderText("gpt-3.5-turbo")
        layout.addRow("Model Name:", self.openai_model_input)
        
        # Baseurl
        self.openai_baseurl_input = QLineEdit()
        self.openai_baseurl_input.setPlaceholderText("https://api.openai.com/v1/chat/completions")
        layout.addRow("Base URL:", self.openai_baseurl_input)
        
        # Info
        info_label = QLabel(
            "Enter your OpenAI API Key to enable AI-powered field suggestions.\n"
            "This feature allows you to generate definitions and examples automatically."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; margin-top: 10px;")
        layout.addRow(info_label)

        # Test button
        self.openai_test_button = QPushButton("Test OpenAI Settings")
        self.openai_test_button.clicked.connect(self.test_openai_settings)
        layout.addRow(self.openai_test_button)
        
        group.setLayout(layout)
        return group

    def test_openai_settings(self):
        """Test current OpenAI configuration"""
        from ..ai.client import OpenAIClient
        import json
        import urllib.request
        import urllib.error

        api_key = self.openai_key_input.text().strip()
        model = self.openai_model_input.text().strip() or "gpt-3.5-turbo"
        base_url = self.openai_baseurl_input.text().strip() or "https://api.openai.com/v1/chat/completions"

        if not api_key:
            showInfo("Please enter an OpenAI API Key before testing.")
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        test_body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a test assistant."},
                {"role": "user", "content": "Say hello in one short sentence."},
            ],
        }

        request_summary = json.dumps(
            {
                "url": base_url,
                "headers": headers,
                "body": test_body,
            },
            ensure_ascii=False,
            indent=2,
        )

        try:
            req = urllib.request.Request(
                base_url,
                data=json.dumps(test_body).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
        except Exception as e:
            showInfo(
                "OpenAI test failed:\n\n"
                f"Error: {e}\n\n"
                "Request details:\n"
                f"{request_summary}"
            )
            return

        showInfo(
            "OpenAI test succeeded.\n\n"
            f"Request:\n{request_summary}\n\n"
            f"Response (truncated):\n{json.dumps(data, ensure_ascii=False)[:500]}"
        )
    
    def load_config(self):
        """Load configuration into UI"""
        # Load dictionaries
        mdx_paths = config.get_mdx_paths()
        self.dict_list.clear()
        for path in mdx_paths:
            self.dict_list.addItem(path)
        
        # Load TTS settings
        engine_name = config.get_tts_engine()
        index = self.engine_combo.findData(engine_name)
        if index >= 0:
            self.engine_combo.setCurrentIndex(index)
        
        self.on_engine_changed()  # Load voices
        
        voice_name = config.get_tts_voice()
        if voice_name:
            index = self.voice_combo.findText(voice_name)
            if index >= 0:
                self.voice_combo.setCurrentIndex(index)
        
        self.speed_spin.setValue(config.get_tts_speed())
        
        # Load options
        self.auto_fill_check.setChecked(config.is_auto_fill_on_add())
        self.auto_generate_audio_check.setChecked(config.is_auto_generate_audio_on_add())
        self.auto_play_check.setChecked(config.is_auto_play_on_review())
        self.cache_audio_check.setChecked(config.is_cache_audio())
        self.auto_create_notetype_check.setChecked(config.is_auto_create_note_type())
        mode = config.get_dictionary_mode()
        index = self.dict_mode_combo.findData(mode)
        if index >= 0:
            self.dict_mode_combo.setCurrentIndex(index)
        
        # Load AI settings
        self.openai_key_input.setText(config.get_openai_api_key())
        self.openai_model_input.setText(config.get_openai_model())
        self.openai_baseurl_input.setText(config.get_base_url())
    
    def save_config(self):
        """Save configuration from UI"""
        # Save dictionaries
        mdx_paths = []
        for i in range(self.dict_list.count()):
            mdx_paths.append(self.dict_list.item(i).text())
        config.set('mdx_paths', mdx_paths)
        
        # Reload dictionaries
        reload_dictionaries()
        
        # Save TTS settings
        engine_name = self.engine_combo.currentData()
        config.set_tts_engine(engine_name)
        
        voice_name = self.voice_combo.currentText()
        config.set_tts_voice(voice_name)
        
        config.set_tts_speed(self.speed_spin.value())
        
        # Save options
        config.set('auto_fill_on_add', self.auto_fill_check.isChecked())
        config.set('auto_generate_audio_on_add', self.auto_generate_audio_check.isChecked())
        config.set('auto_play_on_review', self.auto_play_check.isChecked())
        config.set('cache_audio', self.cache_audio_check.isChecked())
        config.set('auto_create_note_type', self.auto_create_notetype_check.isChecked())
        config.set_dictionary_mode(self.dict_mode_combo.currentData())
        
        # Save AI settings
        config.set_openai_api_key(self.openai_key_input.text().strip())
        model = self.openai_model_input.text().strip()
        if not model:
            model = "gpt-3.5-turbo"
        config.set_openai_model(model)
        base_url = self.openai_baseurl_input.text().strip()
        config.set_base_url(base_url)
        
        showInfo("Configuration saved successfully!")
        self.accept()
    
    def add_dictionary(self):
        """Add a new dictionary"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select MDX Dictionary",
            "",
            "MDX Files (*.mdx);;All Files (*.*)"
        )
        
        if file_path:
            self.dict_list.addItem(file_path)
    
    def remove_dictionary(self):
        """Remove selected dictionary"""
        current_row = self.dict_list.currentRow()
        if current_row >= 0:
            self.dict_list.takeItem(current_row)
    
    def move_dictionary_up(self):
        """Move selected dictionary up in priority"""
        current_row = self.dict_list.currentRow()
        if current_row > 0:
            item = self.dict_list.takeItem(current_row)
            self.dict_list.insertItem(current_row - 1, item)
            self.dict_list.setCurrentRow(current_row - 1)
    
    def move_dictionary_down(self):
        """Move selected dictionary down in priority"""
        current_row = self.dict_list.currentRow()
        if current_row >= 0 and current_row < self.dict_list.count() - 1:
            item = self.dict_list.takeItem(current_row)
            self.dict_list.insertItem(current_row + 1, item)
            self.dict_list.setCurrentRow(current_row + 1)
    
    def on_engine_changed(self):
        """Handle TTS engine change"""
        engine_name = self.engine_combo.currentData()
        if not engine_name:
            return
        
        # Load voices for this engine
        self.voice_combo.clear()
        voices = get_voices_for_engine(engine_name)
        for voice in voices:
            self.voice_combo.addItem(voice)
    
    def show_dependency_status(self):
        """Show dependency status"""
        from ..dependencies import get_dependency_info
        info = get_dependency_info()
        showInfo(info)
    
    def install_edge_tts(self):
        """Install Edge TTS with user permission"""
        from ..dependencies import auto_install_edge_tts_with_permission
        auto_install_edge_tts_with_permission()
    
    def show_field_mapping_dialog(self):
        """Show the field mapping configuration dialog"""
        from .field_mapping_dialog import FieldMappingDialog
        dialog = FieldMappingDialog(self)
        dialog.exec()
    
    def show_online_dict_dialog(self):
        """Show the online dictionary configuration dialog"""
        from .online_dict_dialog import OnlineDictDialog
        dialog = OnlineDictDialog(self)
        dialog.exec()
