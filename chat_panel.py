from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import QTextCursor
import requests
import json
import subprocess
import threading
import platform
import markdown
import re

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
        
        # Add LLM server selector
        controls_layout.addWidget(QLabel("Server:"))
        self.server_selector = QComboBox()
        self.server_selector.addItems(["Ollama", "LM Studio"])
        self.server_selector.currentTextChanged.connect(self.fetch_models)
        controls_layout.addWidget(self.server_selector)
        
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
        
        # Replace QTextEdit with QTextBrowser for proper link support
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        self.chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.chat_display.setMinimumHeight(180)  # Adjusted height
        self.chat_display.setFrameStyle(QFrame.NoFrame)
        self.chat_display.setOpenExternalLinks(True)  # Now this works
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
        
        # Define server endpoints
        self.server_endpoints = {
            "Ollama": "http://localhost:11434",
            "LM Studio": "http://127.0.0.1:1234"
        }
        
        # Initial model fetch
        self.fetch_models()
        
    def fetch_models(self):
        selected_server = self.server_selector.currentText()
        
        if selected_server == "Ollama":
            try:
                response = requests.get(f'{self.server_endpoints["Ollama"]}/api/tags')
                if response.status_code == 200:
                    models = response.json()['models']
                    self.model_selector.clear()
                    for model in models:
                        self.model_selector.addItem(model['name'])
                    self.add_to_chat("Ollama models refreshed successfully")
                else:
                    self.add_to_chat("Error: Could not fetch Ollama models")
            except Exception as e:
                self.add_to_chat(f"Error connecting to Ollama: {str(e)}\nMake sure Ollama is running (ollama serve)")
        
        elif selected_server == "LM Studio":
            try:
                # LM Studio models endpoint
                response = requests.get(f'{self.server_endpoints["LM Studio"]}/v1/models')
                if response.status_code == 200:
                    models = response.json()['data']
                    self.model_selector.clear()
                    for model in models:
                        self.model_selector.addItem(model['id'])
                    self.add_to_chat("LM Studio models refreshed successfully")
                else:
                    self.add_to_chat("Error: Could not fetch LM Studio models")
            except Exception as e:
                self.add_to_chat(f"Error connecting to LM Studio: {str(e)}\nMake sure LM Studio is running with local server enabled")
            
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
    
    def add_to_chat(self, text, is_markdown=False, add_newline=True):
        """Add text to chat display, with optional markdown rendering"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
        
        if is_markdown:
            # Convert markdown to HTML with code highlighting
            html = markdown.markdown(
                text, 
                extensions=['fenced_code', 'tables', 'nl2br']
            )
            self.chat_display.insertHtml(html)
        else:
            self.chat_display.insertPlainText(text)
        
        # Add a line break only if requested
        if add_newline:
            cursor.movePosition(QTextCursor.End)
            self.chat_display.setTextCursor(cursor)
            self.chat_display.insertPlainText("\n")
        
        # Ensure new text is visible
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
        
    def send_message(self):
        message = self.input_field.text()
        if not message:
            return
            
        if not self.model_selector.currentText():
            self.add_to_chat("Error: No model selected. Please refresh models.")
            self.add_to_chat("")  # Add empty line after error
            return
            
        self.add_to_chat(f"You: {message}")
        self.add_to_chat("")  # Add empty line after user message
        self.input_field.clear()
        self.send_button.setEnabled(False)
        
        # Get selected path text
        path_text = self.get_selected_path_text()
        
        # Create context-aware prompt
        full_prompt = f"""Here is the text from the selected nodes:

{path_text}

User question: {message}

Please analyze the provided text and answer the question. You can use markdown formatting in your response."""
        
        selected_server = self.server_selector.currentText()
        selected_model = self.model_selector.currentText()
        
        try:
            # Add "Computer says:" without a line break
            self.add_to_chat("Computer says: ", add_newline=False)
            
            # Get position right after "Computer says: "
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            response_position = cursor.position()
            current_response = ""
            
            if selected_server == "Ollama":
                response = requests.post(f'{self.server_endpoints["Ollama"]}/api/generate', 
                    json={
                        'model': selected_model,
                        'prompt': full_prompt,
                        'stream': True
                    },
                    stream=True
                )
                
                for line in response.iter_lines():
                    if line:
                        json_response = json.loads(line)
                        if 'error' in json_response:
                            self.add_to_chat(f"Error: {json_response['error']}")
                            self.add_to_chat("")
                            break
                        
                        # Append new content and re-render the whole response
                        current_response += json_response['response']
                        
                        # Clean up orphaned bullet points
                        cleaned_response = self.clean_orphaned_bullet_points(current_response)
                        
                        # Update the chat display
                        self.update_chat_response(cleaned_response, response_position)
                
            elif selected_server == "LM Studio":
                response = requests.post(f'{self.server_endpoints["LM Studio"]}/v1/chat/completions', 
                    json={
                        'model': selected_model,
                        'messages': [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": full_prompt}
                        ],
                        'stream': True,
                        'temperature': 0.7
                    },
                    stream=True,
                    headers={"Content-Type": "application/json"}
                )
                
                for line in response.iter_lines():
                    if line:
                        # Skip empty lines and "[DONE]"
                        if line == b"data: [DONE]":
                            break
                            
                        if line.startswith(b"data: "):
                            try:
                                json_str = line[6:].decode('utf-8')  # Remove "data: " prefix
                                if json_str.strip():
                                    json_response = json.loads(json_str)
                                    
                                    if 'error' in json_response:
                                        self.add_to_chat(f"Error: {json_response['error']}")
                                        self.add_to_chat("")
                                        break
                                        
                                    if 'choices' in json_response and json_response['choices']:
                                        delta = json_response['choices'][0].get('delta', {})
                                        content = delta.get('content', '')
                                        
                                        if content:
                                            current_response += content
                                            cleaned_response = self.clean_orphaned_bullet_points(current_response)
                                            self.update_chat_response(cleaned_response, response_position)
                            except json.JSONDecodeError:
                                # Skip invalid JSON
                                continue
            
            # Add empty line after response with a paragraph break
            self.add_to_chat("")
            
            # Add an explicit HTML separator
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.chat_display.setTextCursor(cursor)
            self.chat_display.insertHtml("<div style='margin-top:10px'></div>")
                    
        except Exception as e:
            self.add_to_chat(f"Error: Could not connect to {selected_server} - {str(e)}")
            self.add_to_chat("")
            
        finally:
            self.send_button.setEnabled(True)
            
    def update_chat_response(self, response_text, position):
        """Update the chat response text at the given position"""
        # Convert to HTML
        html = markdown.markdown(
            response_text, 
            extensions=['fenced_code', 'tables', 'nl2br']
        )
        
        # Explicitly close any open lists with a non-list element
        if html.endswith("</li></ul>") or html.endswith("</li></ol>"):
            html += "<div></div>"
        
        # Remove previous response and insert updated HTML
        cursor = self.chat_display.textCursor()
        cursor.setPosition(position)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        self.chat_display.setTextCursor(cursor)
        self.chat_display.insertHtml(html)
        
        # Scroll to see latest content
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
        
        QApplication.processEvents()

    def clean_orphaned_bullet_points(self, text):
        """Clean up orphaned bullet points at the end of responses"""
        
        # Check for common patterns of orphaned bullet points:
        # 1. Lines ending with "* " or "- " (markdown bullet)
        # 2. Lines ending with a number followed by a period and space (numbered list)
        
        # Check if the text ends with a markdown bullet point without content
        if text.endswith("\n* ") or text.endswith("\n- "):
            return text[:-3]  # Remove the last 3 chars ("* " or "- " with newline)
        elif text.endswith("* ") or text.endswith("- "):
            return text[:-2]  # Remove the last 2 chars ("* " or "- " without newline)
        
        # Check for numbered list items (e.g., "1. ")
        lines = text.split("\n")
        if lines and lines[-1].strip() and re.match(r'^\d+\.\s+$', lines[-1]):
            lines.pop()  # Remove the last line if it's just a numbered list marker
            return "\n".join(lines)
        
        return text
    
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
                    # For markdown files, preserve the markdown formatting
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
                            # The response is already in markdown format, preserve it
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
                    # For text files, get plain text (strips markdown formatting)
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
