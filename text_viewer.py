from PySide6.QtWidgets import *
from PySide6.QtCore import *

class TextViewer(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for perfect alignment
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(False)
        self.text_edit.textChanged.connect(self.text_changed)
        layout.addWidget(self.text_edit)
        
        self.current_node = None
        
    def display_node(self, node):
        self.current_node = node
        # Clear default text when displaying in text viewer
        if node.text == "Enter text here...":
            node.text = ""
            self.text_edit.setText("")
        else:
            self.text_edit.setText(node.text)
        
    def text_changed(self):
        if self.current_node:
            text = self.text_edit.toPlainText()
            self.current_node.text = text
            
            # Update title from first line
            first_line = text.split('\n')[0][:30]  # Limit title length
            self.current_node.title = first_line
            
            # Force node to redraw
            self.current_node.update()
