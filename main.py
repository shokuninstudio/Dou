from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import sys
from node_canvas import NodeCanvas
from text_viewer import TextViewer
from chat_panel import ChatPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dou")
        
        # Setup QSettings with organization and application name
        self.settings = QSettings('Dou', 'Dou')
        
        # Restore window size from settings, or use default if not found
        size = self.settings.value('window_size', QSize(1200, 1000))
        self.resize(size)
        
        # Restore window position if available
        pos = self.settings.value('window_position')
        if pos:
            self.move(pos)

        # Create toolbar with standard buttons
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        # Remove custom styling to use native appearance
        
        # Use QPushButton instead of QToolButton to match other buttons
        load_btn = QPushButton("Load Project")
        load_btn.clicked.connect(self.load_project)
        toolbar.addWidget(load_btn)
        
        save_btn = QPushButton("Save Project")
        save_btn.clicked.connect(self.save_project)
        toolbar.addWidget(save_btn)
        
        toolbar.addSeparator()
        
        import_btn = QPushButton("Import Text")
        import_btn.clicked.connect(self.import_text)
        toolbar.addWidget(import_btn)
        
        toolbar.addSeparator()
        export_text_btn = QPushButton("Export Text")
        export_text_btn.clicked.connect(self.export_text)
        toolbar.addWidget(export_text_btn)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for main content
        self.content_splitter = QSplitter(Qt.Horizontal)
        
        # Create node canvas
        self.canvas = NodeCanvas()
        self.content_splitter.addWidget(self.canvas)
        
        # Create text viewer
        self.text_viewer = TextViewer()
        self.content_splitter.addWidget(self.text_viewer)
        
        # Connect node selection signal to text viewer
        self.canvas.node_selected.connect(self.text_viewer.display_node)
        # REMOVE connection to chat panel from here
        # self.canvas.node_selected.connect(self.chat_panel.sync_color_selector_to_node)

        # Create vertical splitter for main content and chat
        self.vertical_splitter = QSplitter(Qt.Vertical)
        
        # Add content splitter to vertical splitter
        self.vertical_splitter.addWidget(self.content_splitter)
        
        # Create chat panel with canvas reference
        self.chat_panel = ChatPanel(self.canvas)
        self.vertical_splitter.addWidget(self.chat_panel)

        # Connect node selection signal to chat panel AFTER it's created
        self.canvas.node_selected.connect(self.chat_panel.sync_color_selector_to_node)

        # Restore splitter states or set defaults
        content_state = self.settings.value('content_splitter_state')
        if content_state:
            self.content_splitter.restoreState(content_state)
        else:
            self.content_splitter.setSizes([700, 300])  # 70% canvas, 30% text viewer
            
        vertical_state = self.settings.value('vertical_splitter_state')
        if vertical_state:
            self.vertical_splitter.restoreState(vertical_state)
        else:
            self.vertical_splitter.setSizes([800, 200])  # 80% main content, 20% chat
        
        # Add vertical splitter to layout
        layout.addWidget(self.vertical_splitter)

        # Setup keyboard shortcuts
        self.setup_shortcuts()

        # Add copyright label to status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Create copyright label
        copyright_label = QLabel("Dou by Shokunin Studio © 2025")
        # Use a smaller font
        font = copyright_label.font()
        font.setPointSize(12)
        copyright_label.setFont(font)
        # Set light gray color
        copyright_label.setStyleSheet("color: #000000;")
        
        # Add to right side of status bar
        self.statusBar.addPermanentWidget(copyright_label)
        # Remove the default border of status bar
        self.statusBar.setStyleSheet("QStatusBar::item {border: none;}")

    def save_project(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Dou (*.dou)")
        if filename:
            # Canvas now handles saving its own background color
            self.canvas.save_to_file(filename)
            
    def load_project(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "Dou (*.dou)")
        if filename:
            # Canvas now handles loading its own background color
            self.canvas.load_from_file(filename)
            
    def export_markdown(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export to Markdown", "", "Markdown (*.md)")
        if filename:
            with open(filename, 'w') as f:
                nodes = []
                visited = set()
                
                def traverse_nodes(node):
                    if node in visited:
                        return
                    visited.add(node)
                    nodes.append(node)
                    for conn in self.canvas.connections:
                        if conn.start_node == node:
                            traverse_nodes(conn.end_node)
                
                # Find root nodes (nodes with no incoming connections)
                root_nodes = set(self.canvas.scene.items())
                for conn in self.canvas.connections:
                    root_nodes.discard(conn.end_node)
                    
                # Traverse from each root node
                for root in root_nodes:
                    if isinstance(root, TextNode):
                        traverse_nodes(root)
                
                # Write nodes to markdown
                for node in nodes:
                    f.write(f"# {node.title}\n\n")
                    f.write(f"{node.text}\n\n")

    def import_text(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Text File",
            "",
            "Text Files (*.txt)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    text = f.read()
                    
                # Create new node at center of view
                center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
                new_node = self.canvas.add_node("Imported Text", text)
                new_node.setPos(center)
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Import Error",
                    f"Could not import file: {str(e)}"
                )

    def export_text(self):
        if not self.canvas.selected_node:
            QMessageBox.warning(self, "Export Text", "Please select a text node first.")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Text",
            "",
            "Text Files (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.canvas.selected_node.text)
                    
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Export Error",
                    f"Could not export text: {str(e)}"
                )

    def resizeEvent(self, event):
        """Handle window resize events"""
        # Save the new size
        self.settings.setValue('window_size', self.size())
        super().resizeEvent(event)

    def moveEvent(self, event):
        """Handle window move events"""
        # Save the new position
        self.settings.setValue('window_position', self.pos())
        super().moveEvent(event)

    def closeEvent(self, event):
        """Handle window close events"""
        # Save window geometry
        self.settings.setValue('window_size', self.size())
        self.settings.setValue('window_position', self.pos())
        
        # Save splitter states
        self.settings.setValue('content_splitter_state', self.content_splitter.saveState())
        self.settings.setValue('vertical_splitter_state', self.vertical_splitter.saveState())
        
        # Ensure settings are saved
        self.settings.sync()
        super().closeEvent(event)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Copy
        copy_shortcut = QShortcut(QKeySequence.Copy, self)
        copy_shortcut.activated.connect(self.copy_nodes)
        
        # Cut
        cut_shortcut = QShortcut(QKeySequence.Cut, self)
        cut_shortcut.activated.connect(self.cut_nodes)
        
        # Paste
        paste_shortcut = QShortcut(QKeySequence.Paste, self)
        paste_shortcut.activated.connect(self.paste_nodes)

    def copy_nodes(self):
        self.canvas.copy_selected_nodes()

    def cut_nodes(self):
        self.canvas.cut_selected_nodes()

    def paste_nodes(self):
        self.canvas.paste_nodes()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
