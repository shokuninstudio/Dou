from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import json
from text_node import TextNode
import math
from PySide6.QtGui import QClipboard
from PySide6.QtCore import Qt
import json  # Add this import

class Connection(QGraphicsPathItem):
    def __init__(self, start_node, end_node, edge_type):
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        self.edge_type = edge_type
        self.setPen(QPen(QColor(0, 120, 215), 4))
        self.setZValue(-1)  # Place connections behind nodes
        self.update_position()
        
    def update_position(self):
        # Get edge points based on edge type
        start_pos = self.get_edge_point(self.start_node, self.edge_type)
        end_pos = self.get_edge_point(self.end_node, self.get_opposite_edge(self.edge_type))
        
        # Calculate control points for the Bézier curve
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        
        # Control points are placed at 1/3 and 2/3 of the distance
        if self.edge_type in ["left", "right"]:
            ctrl1 = QPointF(start_pos.x() + dx/3, start_pos.y())
            ctrl2 = QPointF(start_pos.x() + 2*dx/3, end_pos.y())
        else:  # top or bottom
            ctrl1 = QPointF(start_pos.x(), start_pos.y() + dy/3)
            ctrl2 = QPointF(end_pos.x(), start_pos.y() + 2*dy/3)
        
        # Create Bézier curve path
        path = QPainterPath()
        path.moveTo(start_pos)
        path.cubicTo(ctrl1, ctrl2, end_pos)
        self.setPath(path)
        
    def get_edge_point(self, node, edge):
        if edge == "left":
            return node.pos() + QPointF(0, node.height/2)
        elif edge == "right":
            return node.pos() + QPointF(node.width, node.height/2)
        elif edge == "top":
            return node.pos() + QPointF(node.width/2, 0)
        else:  # bottom
            return node.pos() + QPointF(node.width/2, node.height)
            
    def get_opposite_edge(self, edge):
        opposites = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}
        return opposites.get(edge, edge)

class NodeCanvas(QGraphicsView):
    node_selected = Signal(object)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        # Create a very large scene to enable infinite panning
        self.scene.setSceneRect(-100000, -100000, 200000, 200000)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        
        # Enable dragging and zooming
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRubberBandSelectionMode(Qt.IntersectsItemShape)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.connections = []
        self.dragging_node = None
        self.temp_connection = None

        # Add zoom settings
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Set zoom range limits
        self.zoom_in_factor = 1.25
        self.zoom_out_factor = 1 / self.zoom_in_factor
        self.zoom_range = (0.1, 5.0)  # Min and max zoom levels
        self.current_zoom = 1.0

        # Enable touch gestures
        self.viewport().setAttribute(Qt.WA_AcceptTouchEvents)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        
        # Store gesture state
        self.last_gesture_factor = 1.0
        
        # Set dark grey background
        self.setBackgroundBrush(QColor(60, 60, 60))
        self.scene.setBackgroundBrush(QColor(60, 60, 60))
        
        # Hide scrollbars but keep their functionality
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Pan tracking
        self.panning = False
        self.last_mouse_pos = None

        # Remove margins for perfect alignment
        self.setContentsMargins(0, 0, 0, 0)

        self.node_counter = 0  # Add counter for node numbering

        self.dragging_connection = False
        self.connection_start_node = None
        self.connection_start_socket = None
        self.temp_connection_end = None

        # Add tablet support
        self.setTabletTracking(True)
        self.setMouseTracking(True)
        self.setTabletTracking(True)
        # Add this line to prevent tablet buttons from being converted to mouse events
        self.setAttribute(Qt.WA_TabletTracking)
        self.last_tablet_button = Qt.NoButton
        self.is_tablet_event = False  # Add this flag
        self.drag_offset = None  # Add this new variable
        self.last_tablet_click_time = 0  # Add this line only
        self.last_tablet_pos = None      # Add this line only
    
    def add_node(self, title, text):
        self.node_counter += 1  # Increment counter
        node = TextNode(title, text)
        node.order_number = self.node_counter  # Assign number to node
        self.scene.addItem(node)
        return node
        
    def mouseDoubleClickEvent(self, event):
        # Ignore synthesized mouse events from tablet buttons
        if event.source() == Qt.MouseEventSynthesizedByApplication:
            return
        
        item = self.itemAt(event.pos())
        if item is None:  # Only create new node when double-clicking empty space
            scene_pos = self.mapToScene(event.pos())
            new_node = self.add_node("New Node", "Enter text here...")
            new_node.setPos(scene_pos)
            self.node_selected.emit(new_node)
        else:
            super().mouseDoubleClickEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.panning = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if isinstance(item, TextNode):
                scene_pos = self.mapToScene(event.pos())
                local_pos = item.mapFromScene(scene_pos)
                
                # Check if clicking on a socket
                if item.get_input_socket_rect().contains(local_pos) and item.input_connected:
                    # Find and disconnect the existing connection
                    for conn in self.connections[:]:  # Use slice to allow removal during iteration
                        if conn.end_node == item:
                            self.start_connection(conn.start_node, 'output')
                            conn.start_node.output_connected = False
                            item.input_connected = False
                            self.scene.removeItem(conn)
                            self.connections.remove(conn)
                            break
                    event.accept()
                    return
                elif item.get_output_socket_rect().contains(local_pos) and item.output_connected:
                    # Find and disconnect the existing connection
                    for conn in self.connections[:]:
                        if conn.start_node == item:
                            self.start_connection(item, 'output')
                            conn.end_node.input_connected = False
                            item.output_connected = False
                            self.scene.removeItem(conn)
                            self.connections.remove(conn)
                            break
                    event.accept()
                    return
                # If no existing connection, start a new one
                elif item.get_input_socket_rect().contains(local_pos):
                    self.start_connection(item, 'input')
                    event.accept()
                    return
                elif item.get_output_socket_rect().contains(local_pos):
                    self.start_connection(item, 'output')
                    event.accept()
                    return

                if not item.editing:  # Only change selection if not editing
                    if not item.isSelected():
                        self.scene.clearSelection()
                        item.setSelected(True)
                    self.selected_node = item
                    self.dragging_node = item
                    self.node_selected.emit(item)
            else:
                self.scene.clearSelection()
                self.selected_node = None
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.panning and self.last_mouse_pos is not None:
            delta = event.pos() - self.last_mouse_pos
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y())
            self.last_mouse_pos = event.pos()
            event.accept()
        elif self.dragging_connection:
            self.temp_connection_end = self.mapToScene(event.pos())
            self.scene.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)
            if self.dragging_node:
                # Update all connections positions when moving nodes
                for conn in self.connections:
                    conn.update_position()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.panning = False
            self.last_mouse_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        elif self.dragging_connection:
            item = self.itemAt(event.pos())
            if isinstance(item, TextNode):
                scene_pos = self.mapToScene(event.pos())
                local_pos = item.mapFromScene(scene_pos)
                
                # Check if released on valid socket
                valid_connection = False
                if self.connection_start_socket == 'output':
                    if item.get_input_socket_rect().contains(local_pos):
                        self.create_connection(self.connection_start_node, item)
                        valid_connection = True
                else:  # input socket
                    if item.get_output_socket_rect().contains(local_pos):
                        self.create_connection(item, self.connection_start_node)
                        valid_connection = True
                
            self.end_connection()
            event.accept()
        else:
            self.dragging_node = None
            super().mouseReleaseEvent(event)

    def save_to_file(self, filename):
        """Save the entire project to a .dou file"""
        try:
            # Collect all nodes data
            nodes_data = {}
            node_items = [item for item in self.scene.items() if isinstance(item, TextNode)]
            
            for node in node_items:
                # Create a unique ID for each node
                node_id = str(id(node))
                nodes_data[node_id] = {
                    'title': node.title,
                    'text': node.text,
                    'pos_x': node.pos().x(),
                    'pos_y': node.pos().y(),
                    'width': node.width,
                    'height': node.height,
                    'color': node.current_color,
                    'order_number': node.order_number
                }
            
            # Collect all connections data
            connections_data = []
            for conn in self.connections:
                start_id = str(id(conn.start_node))
                end_id = str(id(conn.end_node))
                
                if start_id in nodes_data and end_id in nodes_data:
                    connections_data.append({
                        'start_node': start_id,
                        'end_node': end_id,
                        'edge_type': conn.edge_type
                    })
            
            # Prepare data structure for the file
            project_data = {
                'nodes': nodes_data,
                'connections': connections_data,
                'version': '1.0'  # For future compatibility
            }
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(project_data, file, indent=2)
                
            return True
            
        except Exception as e:
            QMessageBox.critical(None, "Save Error", f"Failed to save project: {str(e)}")
            return False
            
    def load_from_file(self, filename):
        """Load a project from a .dou file"""
        try:
            # Clear existing canvas
            self.scene.clear()
            self.connections = []
            self.selected_node = None
            
            # Read file
            with open(filename, 'r', encoding='utf-8') as file:
                project_data = json.load(file)
            
            # Check version for compatibility
            version = project_data.get('version', '1.0')
            
            # Temporary dictionary to map saved node IDs to new node objects
            id_to_node = {}
            
            # Create all nodes first
            for node_id, node_data in project_data['nodes'].items():
                node = TextNode(node_data['title'], node_data['text'])
                
                # Set node properties
                node.width = node_data['width']
                node.height = node_data['height']
                node.setPos(node_data['pos_x'], node_data['pos_y'])
                node.order_number = node_data['order_number']
                
                # Set color if saved
                if 'color' in node_data:
                    node.set_color(node_data['color'])
                
                # Add to scene and mapping
                self.scene.addItem(node)
                id_to_node[node_id] = node
            
            # Create all connections
            for conn_data in project_data['connections']:
                start_node = id_to_node.get(conn_data['start_node'])
                end_node = id_to_node.get(conn_data['end_node'])
                
                if start_node and end_node:
                    # Create connection with the same edge type
                    connection = Connection(start_node, end_node, conn_data['edge_type'])
                    self.scene.addItem(connection)
                    self.connections.append(connection)
                    
                    # Update connected state of nodes
                    start_node.output_connected = True
                    end_node.input_connected = True
            
            # Renumber nodes to ensure order is correctly shown
            self.renumber_nodes()
            
            # Fit view to content
            self.resetZoom()
            
            return True
            
        except Exception as e:
            QMessageBox.critical(None, "Load Error", f"Failed to load project: {str(e)}")
            return False

    def get_path_from_node(self, start_node):
        """Extract text from connected nodes starting from given node."""
        nodes = []
        visited = set()
        
        def traverse_nodes(node):
            if node in visited:
                return
            visited.add(node)
            nodes.append(node)
            for conn in self.connections:
                if conn.start_node == node:
                    traverse_nodes(conn.end_node)
                    
        traverse_nodes(start_node)
        return nodes

    def get_all_paths(self):
        """Get all separate paths in the canvas."""
        paths = []
        visited = set()
        
        # Find root nodes (nodes with no incoming connections)
        root_nodes = [item for item in self.scene.items() 
                     if isinstance(item, TextNode) and 
                     not any(conn.end_node == item for conn in self.connections)]
        
        for root in root_nodes:
            if root not in visited:
                path = self.get_path_from_node(root)
                paths.append(path)
                visited.update(path)
                
        return paths

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            angle = event.angleDelta().y()
            if angle > 0:
                self.zoom_view(self.zoom_in_factor)
            else:
                self.zoom_view(self.zoom_out_factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            self.delete_selected_nodes()
            event.accept()
        elif event.modifiers() & (Qt.ControlModifier | Qt.MetaModifier):  # Control or Command
            if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
                self.zoom_view(self.zoom_in_factor)
                event.accept()
            elif event.key() == Qt.Key_Minus:
                self.zoom_view(self.zoom_out_factor)
                event.accept()
            elif event.key() == Qt.Key_0:
                # Reset zoom
                self.resetZoom()
                event.accept()
        super().keyPressEvent(event)

    def renumber_nodes(self):
        """Renumber all nodes sequentially based on current order numbers"""
        nodes = [item for item in self.scene.items() if isinstance(item, TextNode)]
        if not nodes:
            self.node_counter = 0  # Reset counter if no nodes left
            return
            
        # Sort nodes by their current numbers to maintain relative order
        nodes.sort(key=lambda n: n.order_number if n.order_number is not None else float('inf'))
        
        # Reassign numbers sequentially
        for i, node in enumerate(nodes, 1):
            node.order_number = i
            node.update()
        self.node_counter = len(nodes)

    def delete_selected_nodes(self):
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, TextNode)]
        if not selected_nodes:
            return

        # Remove connections first
        connections_to_remove = []
        for conn in self.connections:
            if conn.start_node in selected_nodes or conn.end_node in selected_nodes:
                # Update socket connection states
                if conn.start_node not in selected_nodes:
                    conn.start_node.output_connected = False
                    conn.start_node.update()
                if conn.end_node not in selected_nodes:
                    conn.end_node.input_connected = False
                    conn.end_node.update()
                connections_to_remove.append(conn)
                self.scene.removeItem(conn)
                
        for conn in connections_to_remove:
            self.connections.remove(conn)

        # Remove the nodes
        for node in selected_nodes:
            self.scene.removeItem(node)

        # Renumber remaining nodes
        self.renumber_nodes()

    def zoom_view(self, factor):
        old_pos = self.mapToScene(self.viewport().rect().center())
        
        # Check zoom bounds
        new_zoom = self.current_zoom * factor
        if new_zoom < self.zoom_range[0] or new_zoom > self.zoom_range[1]:
            return
            
        self.current_zoom = new_zoom
        self.scale(factor, factor)
        
        # Maintain the center point
        new_pos = self.mapToScene(self.viewport().rect().center())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

    def resetZoom(self):
        self.resetTransform()
        self.current_zoom = 1.0

    def viewportEvent(self, event):
        if event.type() == QEvent.Gesture:
            return self.handle_gesture(event)
        return super().viewportEvent(event)
        
    def handle_gesture(self, event):
        gesture = event.gesture(Qt.PinchGesture)
        if gesture:
            scale_factor = gesture.scaleFactor() / self.last_gesture_factor
            self.last_gesture_factor = gesture.scaleFactor()
            
            # Only zoom if there's significant change
            if abs(1.0 - scale_factor) > 0.05:
                self.zoom_view(scale_factor)
            return True
        return False

    def start_connection(self, node, socket_type):
        self.dragging_connection = True
        self.connection_start_node = node
        self.connection_start_socket = socket_type
        self.temp_connection_end = node.scenePos()

    def end_connection(self):
        self.dragging_connection = False
        self.connection_start_node = None
        self.connection_start_socket = None
        self.temp_connection_end = None
        self.scene.update()

    def create_connection(self, start_node, end_node):
        # Check if connection already exists
        for conn in self.connections:
            if conn.start_node == start_node and conn.end_node == end_node:
                return

        connection = Connection(start_node, end_node, "right")
        self.scene.addItem(connection)
        self.connections.append(connection)
        
        # Update socket connection states
        start_node.output_connected = True
        end_node.input_connected = True
        start_node.update()
        end_node.update()

    def drawForeground(self, painter, rect):
        # Draw temporary connection while dragging
        if self.dragging_connection and self.connection_start_node:
            painter.setPen(QPen(QColor(0, 120, 215), 4))
            
            if self.connection_start_socket == 'output':
                start_pos = self.connection_start_node.scenePos() + \
                           self.connection_start_node.get_output_socket_pos()
            else:
                start_pos = self.connection_start_node.scenePos() + \
                           self.connection_start_node.get_input_socket_pos()

            # Create temporary Bézier curve
            path = QPainterPath()
            path.moveTo(start_pos)
            
            dx = self.temp_connection_end.x() - start_pos.x()
            dy = self.temp_connection_end.y() - start_pos.y()
            
            ctrl1 = QPointF(start_pos.x() + dx/3, start_pos.y())
            ctrl2 = QPointF(start_pos.x() + 2*dx/3, self.temp_connection_end.y())
            
            path.cubicTo(ctrl1, ctrl2, self.temp_connection_end)
            painter.drawPath(path)

        super().drawForeground(painter, rect)

    def copy_selected_nodes(self):
        """Copy selected nodes to clipboard"""
        nodes = [item for item in self.scene.selectedItems() if isinstance(item, TextNode)]
        if not nodes:
            return
            
        # Create serializable data for each node
        nodes_data = []
        for node in nodes:
            nodes_data.append({
                'title': node.title,
                'text': node.text,
                'pos': [node.pos().x(), node.pos().y()],
                'width': node.width,
                'height': node.height
            })
        
        # Store as JSON in clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(json.dumps(nodes_data))

    def cut_selected_nodes(self):
        """Cut selected nodes"""
        self.copy_selected_nodes()
        self.delete_selected_nodes()

    def paste_nodes(self):
        """Paste nodes from clipboard"""
        clipboard = QApplication.clipboard()
        try:
            data = json.loads(clipboard.text())
            if not isinstance(data, list):
                return
                
            # Clear current selection
            self.scene.clearSelection()
            
            # Get cursor position in scene coordinates
            cursor_pos = self.mapToScene(self.mapFromGlobal(QCursor.pos()))
            
            # Calculate bounding box of copied nodes
            if data:
                min_x = min(node['pos'][0] for node in data)
                min_y = min(node['pos'][1] for node in data)
                
                # Paste relative to cursor position
                for node_data in data:
                    # Calculate offset from original position
                    offset_x = node_data['pos'][0] - min_x
                    offset_y = node_data['pos'][1] - min_y
                    
                    # Create new node
                    new_node = self.add_node(node_data['title'], node_data['text'])
                    new_node.setPos(cursor_pos.x() + offset_x, cursor_pos.y() + offset_y)
                    new_node.width = node_data['width']
                    new_node.height = node_data['height']
                    new_node.setSelected(True)
                    
        except (json.JSONDecodeError, KeyError):
            pass  # Invalid clipboard content

    def tabletEvent(self, event):
        """Handle tablet events separately from mouse events"""
        self.is_tablet_event = True
        
        # Handle right button press on tablet
        if event.type() == QEvent.TabletPress and event.button() == Qt.RightButton:
            self.panning = True
            self.last_mouse_pos = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        
        # Get precise tablet position and map to scene coordinates
        tablet_pos = event.position()
        scene_pos = self.mapToScene(tablet_pos.toPoint())
        item = self.scene.itemAt(scene_pos, self.transform())
        
        if event.type() == QEvent.TabletPress:
            current_time = QTime.currentTime().msecsSinceStartOfDay()
            if event.button() == Qt.LeftButton:
                if (self.last_tablet_pos is not None and 
                    (current_time - self.last_tablet_click_time) < QApplication.doubleClickInterval() and
                    (tablet_pos.toPoint() - self.last_tablet_pos).manhattanLength() < 10):
                    # Double-tap on text node
                    if isinstance(item, TextNode):
                        # Just select the node, don't set editing flag directly
                        item.setSelected(True)
                        self.node_selected.emit(item)
                        # This will trigger editing through the proper channel
                        item.startEditing()
                        event.accept()
                        self.last_tablet_click_time = 0
                        self.last_tablet_pos = None
                        return
                    elif item is None:
                        # Create new node when double-tapping empty space
                        new_node = self.add_node("New Node", "Enter text here...")
                        new_node.setPos(scene_pos)
                        self.node_selected.emit(new_node)
                        new_node.update()
                        self.scene.update()
                        event.accept()
                        self.last_tablet_click_time = 0
                        self.last_tablet_pos = None
                        return
                self.last_tablet_click_time = current_time
                self.last_tablet_pos = tablet_pos.toPoint()
            
            self.last_tablet_button = event.button()
            
            # Handle node interaction
            if isinstance(item, TextNode):
                # Check socket interaction first
                item_pos = item.mapFromScene(scene_pos)
                
                # Check input socket
                if item.get_input_socket_rect().contains(item_pos):
                    if item.input_connected:
                        # Find and disconnect existing connection
                        for conn in self.connections[:]:
                            if conn.end_node == item:
                                self.start_connection(conn.start_node, 'output')
                                conn.start_node.output_connected = False
                                item.input_connected = False
                                self.scene.removeItem(conn)
                                self.connections.remove(conn)
                                break
                    else:
                        self.start_connection(item, 'input')
                    event.accept()
                    return
                    
                # Check output socket
                if item.get_output_socket_rect().contains(item_pos):
                    if item.output_connected:
                        # Find and disconnect existing connection
                        for conn in self.connections[:]:
                            if conn.start_node == item:
                                self.start_connection(item, 'output')
                                conn.end_node.input_connected = False
                                item.output_connected = False
                                self.scene.removeItem(conn)
                                self.connections.remove(conn)
                                break
                    else:
                        self.start_connection(item, 'output')
                    event.accept()
                    return
                
                # Handle resize handle
                if item.isSelected() and item.getHandleRect().contains(item_pos):
                    item.resizing = True
                    event.accept()
                    return
                    
                # Handle selection and dragging
                if not item.isSelected():
                    if not event.modifiers() & Qt.ShiftModifier:
                        self.scene.clearSelection()
                    item.setSelected(True)
                self.dragging_node = item
                self.drag_offset = scene_pos - item.pos()
                self.node_selected.emit(item)
                
            # ...rest of tablet press handling...
            
        elif event.type() == QEvent.TabletMove:
            # Handle resizing during tablet move (add this block)
            resizing_node = None
            for item in self.scene.selectedItems():
                if isinstance(item, TextNode) and item.resizing:
                    resizing_node = item
                    break
                    
            if resizing_node:
                item_pos = resizing_node.mapFromScene(scene_pos)
                resizing_node.width = max(100, item_pos.x())
                resizing_node.height = max(100, item_pos.y())
                resizing_node.prepareGeometryChange()
                
                # Update all connections
                for conn in self.connections:
                    if conn.start_node == resizing_node or conn.end_node == resizing_node:
                        conn.update_position()
                
                resizing_node.update()
                self.scene.update()
                event.accept()
                return
                
            # Handle connection dragging (existing code)
            if self.dragging_connection:
                self.temp_connection_end = scene_pos
                self.scene.update()
                event.accept()
                return
                
        elif event.type() == QEvent.TabletRelease:
            # Handle connection completion
            if self.dragging_connection:
                if isinstance(item, TextNode):
                    item_pos = item.mapFromScene(scene_pos)
                    valid_connection = False
                    
                    if self.connection_start_socket == 'output':
                        if item.get_input_socket_rect().contains(item_pos):
                            self.create_connection(self.connection_start_node, item)
                            valid_connection = True
                    else:  # input socket
                        if item.get_output_socket_rect().contains(item_pos):
                            self.create_connection(item, self.connection_start_node)
                            valid_connection = True
                            
                self.end_connection()
                event.accept()
                return
                
            # ...rest of tablet release handling...
