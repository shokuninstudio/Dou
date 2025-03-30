from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

class TextNode(QGraphicsItem):
    text_changed = Signal(str)  # Signal for text changes

    def __init__(self, title, text):
        super().__init__()
        self.title = title
        self.text = text
        self.width = 250
        self.height = 300
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIsFocusable)  # Only this flag is needed for focus
        self.sticky_color = QColor(255, 255, 153)  # Light yellow like Stickies
        self.handle_size = 10
        self.resizing = False
        self.setAcceptHoverEvents(True)
        self.order_number = None  # Track node's position in the path
        self.editing = False
        self.text_editor = None
        self.setZValue(1)  # Ensure nodes stay above connections
        self.socket_radius = 8  # Visual radius
        self.socket_hitbox_radius = 24  # Larger clickable area
        self.socket_color = QColor(0, 120, 215)
        self.socket_hover_color = QColor(0, 120, 215)
        self.hovered_socket = None  # 'input' or 'output' when hovering over socket
        self.input_connected = False
        self.output_connected = False

        # Add color attributes
        self.color_map = {
            'Red': QColor(255, 200, 200),
            'Orange': QColor(255, 225, 180),
            'Yellow': QColor(255, 255, 153),  # Default sticky color
            'Green': QColor(200, 255, 200),
            'Blue': QColor(200, 200, 255),
            'Purple': QColor(230, 200, 255),
            'Light Grey': QColor(240, 240, 240)
        }
        self.current_color = 'Yellow'
        self.sticky_color = self.color_map['Yellow']
        
    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
        
    def getHandleRect(self):
        """Get the rectangle for the bottom-right resize handle"""
        return QRectF(self.width - self.handle_size, self.height - self.handle_size, 
                     self.handle_size, self.handle_size)

    def get_input_socket_pos(self):
        return QPointF(0, self.height / 2)

    def get_output_socket_pos(self):
        return QPointF(self.width, self.height / 2)

    def get_input_socket_rect(self):
        pos = self.get_input_socket_pos()
        # Center hitbox on socket's visual center
        return QRectF(pos.x() - self.socket_radius,  # Center on socket
                     pos.y() - self.socket_radius, 
                     self.socket_radius * 2,  # Same size as visual socket
                     self.socket_radius * 2)

    def get_output_socket_rect(self):
        pos = self.get_output_socket_pos()
        # Center hitbox on socket's visual center
        return QRectF(pos.x() - self.socket_radius,  # Center on socket
                     pos.y() - self.socket_radius,
                     self.socket_radius * 2,  # Same size as visual socket
                     self.socket_radius * 2)
        
    def paint(self, painter, option, widget):
        # Draw background and border
        if self.isSelected():
            painter.setPen(QPen(QColor(0, 120, 215), 4))  # Keep blue border for selection
        else:
            painter.setPen(QPen(QColor(200, 200, 100), 1))
        
        # Always use sticky_color for background, regardless of editing state
        painter.setBrush(self.sticky_color)
        painter.drawRect(self.boundingRect())
        
        painter.setPen(Qt.black)
        
        # Draw order number if it exists
        if self.order_number is not None:
            number_rect = QRectF(self.width - 30, 5, 25, 20)
            painter.drawText(number_rect, Qt.AlignRight, f"#{self.order_number}")
        
        if not self.editing:  # Only paint text if not editing
            # Draw full text content, starting below the number area
            content_rect = QRectF(5, 25, self.width-10, self.height-30)
            painter.drawText(content_rect, Qt.AlignLeft | Qt.TextWordWrap, self.text)
        
        # Draw resize handle when selected
        if self.isSelected():
            painter.setPen(QPen(QColor(0, 120, 215), 1))
            painter.setBrush(QColor(255, 255, 255))
            painter.drawRect(self.getHandleRect())

        # Draw sockets with original visual size
        painter.setPen(Qt.NoPen)
        
        # Input socket (left)
        pos = self.get_input_socket_pos()
        if self.input_connected or self.hovered_socket == 'input':
            painter.setBrush(self.socket_hover_color)
        else:
            painter.setBrush(self.socket_color)
        painter.drawEllipse(QRectF(pos.x() - self.socket_radius,
                                 pos.y() - self.socket_radius,
                                 self.socket_radius * 2,
                                 self.socket_radius * 2))

        # Output socket (right)
        pos = self.get_output_socket_pos()
        if self.output_connected or self.hovered_socket == 'output':
            painter.setBrush(self.socket_hover_color)
        else:
            painter.setBrush(self.socket_color)
        painter.drawEllipse(QRectF(pos.x() - self.socket_radius,
                                 pos.y() - self.socket_radius,
                                 self.socket_radius * 2,
                                 self.socket_radius * 2))
        
    def hoverMoveEvent(self, event):
        if self.isSelected():
            if self.getHandleRect().contains(event.pos()):
                self.setCursor(Qt.SizeFDiagCursor)
                return
        # Check if hovering over sockets
        if self.get_input_socket_rect().contains(event.pos()):
            self.hovered_socket = 'input'
            self.setCursor(Qt.CrossCursor)
        elif self.get_output_socket_rect().contains(event.pos()):
            self.hovered_socket = 'output'
            self.setCursor(Qt.CrossCursor)
        else:
            self.hovered_socket = None
            self.setCursor(Qt.ArrowCursor)
        self.update()
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if self.isSelected() and self.getHandleRect().contains(event.pos()):
            self.resizing = True
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            pos = event.pos()
            self.width = max(100, pos.x())
            self.height = max(100, pos.y())
            self.prepareGeometryChange()
            self.update()
            if self.scene():
                self.scene().update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.resizing:
            self.resizing = False
        else:
            super().mouseReleaseEvent(event)
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Notify scene of position change for connection updates
            if self.scene():
                self.scene().update()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        if not self.editing:
            self.startEditing()
        super().mouseDoubleClickEvent(event)
        
    def handleTextEdit(self):
        if self.editing and self.text_editor:
            self.text = self.text_editor.toPlainText()
            # Update the node visual
            self.update()
            # Update TextViewer
            if self.scene():
                view = self.scene().views()[0]
                if hasattr(view, 'node_selected'):
                    view.node_selected.emit(self)

    def startEditing(self):
        if not self.text_editor:
            self.text_editor = QPlainTextEdit()
            self.text_editor.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.text_editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.text_editor.textChanged.connect(self.handleTextEdit)
            self.text_editor.focusOutEvent = lambda e: self.stopEditing()
            # Set the text editor's background color to match the sticky note
            self.text_editor.setStyleSheet(f"""
                QPlainTextEdit {{
                    background-color: rgb({self.sticky_color.red()}, 
                                        {self.sticky_color.green()}, 
                                        {self.sticky_color.blue()});
                    border: none;
                }}
            """)
        
        # Position editor over node
        scene_rect = self.sceneBoundingRect()
        view = self.scene().views()[0]
        view_pos = view.mapFromScene(scene_rect.topLeft())
        global_pos = view.viewport().mapToGlobal(view_pos)
        
        self.text_editor.setGeometry(
            global_pos.x(), global_pos.y(),
            scene_rect.width(), scene_rect.height()
        )
        
        # Clear default text when starting to edit
        if self.text == "Enter text here...":
            self.text = ""
            
        self.text_editor.setPlainText(self.text)
        self.text_editor.show()
        self.text_editor.setFocus()
        self.editing = True
        self.update()

    def stopEditing(self):
        if self.editing:
            self.editing = False
            if self.text_editor:
                self.text = self.text_editor.toPlainText()
                self.text_editor.hide()
                self.update()
                # Update TextViewer
                if self.scene():
                    view = self.scene().views()[0]
                    if hasattr(view, 'node_selected'):
                        view.node_selected.emit(self)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if not self.editing:
                self.startEditing()
                event.accept()
                return
        super().keyPressEvent(event)

    def set_color(self, color_name):
        """Set the node's color"""
        if color_name in self.color_map:
            self.current_color = color_name
            self.sticky_color = self.color_map[color_name]
            
            # Update text editor background if it exists
            if self.text_editor:
                self.text_editor.setStyleSheet(f"""
                    QPlainTextEdit {{
                        background-color: rgb({self.sticky_color.red()}, 
                                            {self.sticky_color.green()}, 
                                            {self.sticky_color.blue()});
                        border: none;
                    }}
                """)
            
            self.update()
