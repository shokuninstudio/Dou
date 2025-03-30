# Dou (道) - Visual Knowledge Organization and Analysis Tool

## Overview

Dou (道) is a deceptively simple but powerful desktop application for knowledge organisation, note-taking, and thought process mapping. The name "Dou" (道) means "way" or "path" in Japanese (Dao in Chinese and Do in Korean) reflecting the app's core idea of organising thoughts, ideas and data as text-based nodes along a path.

A path can be anything you want it to be. Your daily diet, a mood or health tracker,  ideas for an app or business, a story outline, your goals ahead, or just random notes that you need help organising. You can have as many different paths you want on one canvas. Or you can create different canvases (saved as Dou files) for each path.

After you have arranged text nodes in order and linked them up, ask your favourite Ollama hosted large language model for feedback, summaries and more.

[![temp-Imaged-VQlo-A.avif](https://i.postimg.cc/4NQ4xNFq/temp-Imaged-VQlo-A.avif)](https://postimg.cc/0br1txv0)

## Features

### Visual Node Canvas
* Interactive sticky notes: Create, edit, and organize thoughts as sticky note nodes on a flexible canvas (right click to pan or use the arrow keys)
* Node Connections: Connect related ideas to form logical paths and sequences
* Visual Organization: Position nodes spatially to represent relationships and hierarchies
* Color Coding: Assign different colors to nodes (Red, Orange, Yellow, Green, Blue, Purple, Light Grey) for visual categorisation

### Advanced Editing
* Text Editing: Edit node content directly on the node or in a dedicated text viewer panel
* Resizable Nodes: Adjust node dimensions to accommodate different content lengths
* Sequential Numbering: Nodes in a path are automatically numbered to show sequence

### AI-Powered Analysis
* Integrated Chat Panel: Ask questions about your paths using natural language
* Path Analysis: Analyse specific paths or all content with AI
* Multiple Models: Connect to different Ollama AI models based on your needs

### Import and Export
* Project Files: Save and load projects as .dou files to continue work later
* Text Import: Import existing text files directly as nodes
* Export Options: Export node content as text files or formatted Markdown
* Chat Export: Save chats as text or Markdown

### User Experience
* Intuitive Interface: Split-panel design with canvas, collapsible text viewer and collapsible chat panels
* Zoom & Pan: Navigate large knowledge maps with zoom and pan functionality
* Keyboard Shortcuts: Efficient editing with shortcuts for common operations
* State Persistence: The app remembers window positions, sizes, and layout preferences

### Accessibility
* Text-to-Speech (macOS only): Listen to the chat with built-in speech synthesis (uses macOS Spoken Content settings)
* Tablet Support: Optimized for stylus input on tablets for natural note-taking
* Path Visualization: Clear visual indication of connected ideas and concepts

## Benefits
* Visual Thinking: See connections and relationships between concepts visually
* AI-Enhanced Insights: Get intelligent analysis and answers about your content
* Flexible Workflow: Create either detailed structured paths or free-form idea maps
* Preserve Context: Keep related ideas connected and in context with each other
* Knowledge Management: Build a visual library of interconnected knowledge
* Presentation Aid: Use paths to plan presentations or stories in a visual format
* Cross-Platform: Works across operating systems with special features for macOS

## Technical Details

Dou is built with:
* PySide6 (Qt for Python) for the user interface
* JSON-based file format for project persistence
* Integration with Ollama for local AI model inference
* Support for mouse, keyboard, and tablet input devices

## Getting Started
1. Install PySide6 with pip install pyside6
2. Launch Dou directly via the Terminal or build an executable for macOS, Windows or Linux with Pyinstaller
3. Double-click anywhere on the canvas to create a new node
4. Type your content into the node or text editor panel
5. Create additional nodes and connect them by dragging from the connection points
6. Use the chat panel to analyse your notes with AI
7. Save your project using File → Save Project
8. Easy to remember controls. Double click to create or edit a text node. Right click to pan the canvas. Command/CTRL + or - to zoom in or out.

(Quick note : I'm still testing dark mode consistency on different operating systems.)
---
*Dou by Shokunin Studio © 2025*

## License

This project is licensed under the GNU Lesser General Public License v3.0 (LGPL-3.0).

Since this project uses [PySide](https://doc.qt.io/qtforpython-6/licenses.html), it follows the LGPL requirements.
