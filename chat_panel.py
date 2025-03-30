from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import QTextCursor
import requests
import json
import subprocess
import threading
import platform

class ChatPanel(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas  # Store reference to canvas
        layout = QVBoxLayout(self)
        
        # Combine path and model selectors into one row
        controls_layout = QHBoxLayout()
        
        # Path controls
        controls_layout.addWidget(QLabel("Analyze Path:"))
        self.path_selector = QComboBox()
        self.path_selector.addItem("All Paths")
        controls_layout.addWidget(self.path_selector)
        self.update_paths_button = QPushButton("Update Paths")
        self.update_paths_button.clicked.connect(self.update_path_list)
        controls_layout.addWidget(self.update_paths_button)
        
        # Add some spacing between controls
        controls_layout.addSpacing(20)
        
        # Model controls
        controls_layout.addWidget(QLabel("Model:"))
        self.model_selector = QComboBox()
        controls_layout.addWidget(self.model_selector)
        self.refresh_button = QPushButton("Refresh Models")
        self.refresh_button.clicked.connect(self.fetch_models)
        controls_layout.addWidget(self.refresh_button)
        
        # Add color selection controls
        controls_layout.addSpacing(20)
        controls_layout.addWidget(QLabel("Colour Label:"))
        self.color_selector = QComboBox()
        self.color_selector.addItems(['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple', 'Light Grey'])
        self.color_selector.currentTextChanged.connect(self.update_node_color)
        controls_layout.addWidget(self.color_selector)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Chat display with proper spacing
        chat_frame = QFrame()
        chat_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(5, 5, 5, 5)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.chat_display.setMinimumHeight(180)  # Adjusted height
        self.chat_display.setFrameStyle(QFrame.NoFrame)
        chat_layout.addWidget(self.chat_display)
        
        layout.addWidget(chat_frame)
        
        # Input area with spacing
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(5, 5, 5, 5)
        
        self.input_field = QLineEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        
        # Connect the returnPressed signal to send_message
        self.input_field.returnPressed.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        
        # Add Clear and Save buttons
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_chat)
        input_layout.addWidget(self.clear_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_chat)
        input_layout.addWidget(self.save_button)
        
        # Only add Speak button on macOS
        if platform.system() == 'Darwin':
            self.speak_button = QPushButton("Speak")
            self.speak_button.clicked.connect(self.speak_text)
            input_layout.addWidget(self.speak_button)
            # Track speech process
            self.current_speech = None

        layout.addWidget(input_frame)
        
        # Initial model fetch
        self.fetch_models()
        
    def fetch_models(self):
        try:
            response = requests.get('http://localhost:11434/api/tags')
            if response.status_code == 200:
                models = response.json()['models']
                self.model_selector.clear()
                for model in models:
                    self.model_selector.addItem(model['name'])
                self.chat_display.append("Models refreshed successfully")
            else:
                self.chat_display.append("Error: Could not fetch models")
        except Exception as e:
            self.chat_display.append(f"Error connecting to Ollama: {str(e)}\nMake sure Ollama is running (ollama serve)")
            
    def update_path_list(self):
        self.path_selector.clear()
        self.path_selector.addItem("All Paths")
        
        paths = self.canvas.get_all_paths()
        for i, path in enumerate(paths, 1):
            first_node = path[0] if path else None
            title = first_node.title if first_node else f"Path {i}"
            self.path_selector.addItem(title, path)
    
    def get_selected_path_text(self):
        index = self.path_selector.currentIndex()
        if index <= 0:  # "All Paths" selected
            all_text = []
            for path in self.canvas.get_all_paths():
                if path:  # Skip empty paths
                    # Sort nodes by order number if present
                    path.sort(key=lambda node: node.order_number if node.order_number is not None else float('inf'))
                    path_text = "\n\n".join(f"#{node.order_number}: {node.title}\n{node.text}" 
                                          for node in path)
                    all_text.append(path_text)
            return "\n\n---\n\n".join(all_text)
        else:
            path = self.path_selector.currentData()
            if path:
                path.sort(key=lambda node: node.order_number if node.order_number is not None else float('inf'))
                return "\n\n".join(f"#{node.order_number}: {node.title}\n{node.text}" 
                                 for node in path)
            return ""
    
    def send_message(self):
        message = self.input_field.text()
        if not message:
            return
            
        if not self.model_selector.currentText():
            self.chat_display.append("Error: No model selected. Please refresh models.")
            self.chat_display.append("")  # Add empty line after error
            return
            
        self.chat_display.append(f"You: {message}")
        self.chat_display.append("")  # Add empty line after user message
        self.input_field.clear()
        self.send_button.setEnabled(False)
        
        # Get selected path text
        path_text = self.get_selected_path_text()
        
        # Create context-aware prompt
        full_prompt = f"""Here is the text from the selected nodes:

{path_text}

User question: {message}

Please analyze the provided text and answer the question."""
        
        try:
            response = requests.post('http://localhost:11434/api/generate', 
                json={
                    'model': self.model_selector.currentText(),
                    'prompt': full_prompt,
                    'stream': True
                },
                stream=True
            )
            
            self.chat_display.append("Computer says: ")
            current_response = ""
            
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    if 'error' in json_response:
                        self.chat_display.append(f"Error: {json_response['error']}")
                        self.chat_display.append("")  # Add empty line after error
                        break
                    
                    # Update chat display with better scroll handling
                    cursor = self.chat_display.textCursor()
                    cursor.movePosition(QTextCursor.End)
                    self.chat_display.setTextCursor(cursor)
                    self.chat_display.insertPlainText(json_response['response'])
                    
                    # Ensure new text is visible
                    self.chat_display.verticalScrollBar().setValue(
                        self.chat_display.verticalScrollBar().maximum()
                    )
                    QApplication.processEvents()
            
            # Add empty line after AI response
            self.chat_display.append("")
                    
        except Exception as e:
            self.chat_display.append(f"Error: Could not connect to Ollama - {str(e)}")
            self.chat_display.append("")  # Add empty line after error
            
        finally:
            self.send_button.setEnabled(True)
    
    def clear_chat(self):
        """Clear the chat display"""
        self.chat_display.clear()

    def save_chat(self):
        """Save the chat content to a text file or markdown file"""
        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Chat",
            "",
            "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)"
        )
        
        if filename:
            try:
                # Determine if markdown based on selected filter or file extension
                is_markdown = selected_filter == "Markdown Files (*.md)" or filename.lower().endswith('.md')
                
                if is_markdown:
                    # Save as markdown with formatting
                    content = self.chat_display.toPlainText()
                    formatted_content = ""
                    
                    # Process content line by line for markdown formatting
                    lines = content.split('\n')
                    i = 0
                    while i < len(lines):
                        line = lines[i]
                        
                        # Format user messages
                        if line.startswith("You:"):
                            formatted_content += f"**{line}**\n\n"
                        # Format computer responses
                        elif line.startswith("Computer says:"):
                            formatted_content += f"**{line}**\n\n"
                            # Collect the multi-line response
                            i += 1
                            response_text = ""
                            while i < len(lines) and not (lines[i].startswith("You:") or 
                                                         lines[i].startswith("Computer says:") or 
                                                         lines[i].strip() == ""):
                                response_text += lines[i] + "\n"
                                i += 1
                            if response_text:
                                formatted_content += response_text + "\n"
                            continue
                        # Keep error messages and other content as is
                        else:
                            formatted_content += line + "\n"
                        
                        i += 1
                    
                    with open(filename, 'w', encoding='utf-8') as file:
                        file.write(formatted_content)
                else:
                    # Save as plain text (original behavior)
                    with open(filename, 'w', encoding='utf-8') as file:
                        file.write(self.chat_display.toPlainText())
                        
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to save chat: {str(e)}"
                )
    
    def update_node_color(self, color_name):
        """Update the color of the selected node"""
        selected_nodes = [item for item in self.canvas.scene.selectedItems() 
                         if hasattr(item, 'set_color')]
        for node in selected_nodes:
            node.set_color(color_name)

    def speak_text(self):
        """Speak the selected text or all text from chat display"""
        # Kill any existing speech process
        if self.current_speech and self.current_speech.poll() is None:
            self.current_speech.terminate()
            self.current_speech = None
            self.speak_button.setText("Speak")
            return

        # Get selected text or all text if nothing selected
        cursor = self.chat_display.textCursor()
        text = cursor.selectedText()
        if not text:
            text = self.chat_display.toPlainText()

        if text:
            self.speak_button.setText("Stop")
            # Run speech in separate thread to avoid blocking UI
            def speak():
                try:
                    self.current_speech = subprocess.Popen(['say', text])
                    self.current_speech.wait()
                    # Reset button text when speech finishes
                    if not self.current_speech or self.current_speech.poll() is not None:
                        self.speak_button.setText("Speak")
                except Exception as e:
                    print(f"Speech error: {e}")
                    self.speak_button.setText("Speak")

            threading.Thread(target=speak, daemon=True).start()
