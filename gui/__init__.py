"""
GUI Modülü
PyQt5 tabanlı kullanıcı arayüzü bileşenleri
"""

from .main_window import MainWindow, ImportWorker
from .toolbar import MainToolbar, ViewToolbar, AssemblyToolbar, StatusToolbar
from .dialogs import SettingsDialog, AboutDialog, FileInfoDialog, ProgressDialog, LogViewerDialog
from .widgets import (
    PropertyPanel, LogWidget, ProgressWidget, ShapeTreeWidget,
    AssemblyConstraintWidget, GeometryInfoWidget, StatusInfoWidget,
    ColorPickerWidget, MaterialPropertyWidget
)

__version__ = "1.0.0"
__author__ = "CAD Developer"

# Ana sınıfları export et
__all__ = [
    'MainWindow',
    'ImportWorker',
    'MainToolbar',
    'ViewToolbar', 
    'AssemblyToolbar',
    'StatusToolbar',
    'SettingsDialog',
    'AboutDialog',
    'FileInfoDialog',
    'ProgressDialog',
    'LogViewerDialog',
    'PropertyPanel',
    'LogWidget',
    'ProgressWidget',
    'ShapeTreeWidget',
    'AssemblyConstraintWidget',
    'GeometryInfoWidget',
    'StatusInfoWidget',
    'ColorPickerWidget',
    'MaterialPropertyWidget'
]

def create_main_window(config, logger):
    """Ana pencere oluştur"""
    return MainWindow(config, logger)

def create_settings_dialog(config, parent=None):
    """Ayarlar dialog'u oluştur"""
    return SettingsDialog(config, parent)

def create_about_dialog(parent=None):
    """Hakkında dialog'u oluştur"""
    return AboutDialog(parent)

# Modül seviyesinde yardımcı fonksiyonlar
def check_gui_dependencies():
    """GUI için gerekli bağımlılıkları kontrol et"""
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QIcon
        return True, "PyQt5 bağımlılıkları mevcut"
    except ImportError as e:
        return False, f"PyQt5 bağımlılıkları eksik: {e}"

def get_qt_version():
    """Qt versiyonunu al"""
    try:
        from PyQt5.QtCore import QT_VERSION_STR
        return QT_VERSION_STR
    except:
        return "Bilinmeyen versiyon"

def setup_application_style(app, theme="light"):
    """Uygulama stilini ayarla"""
    try:
        if theme == "dark":
            # Koyu tema
            app.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QMenuBar::item {
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #5c5c5c;
                }
                QMenu {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #5c5c5c;
                }
                QMenu::item:selected {
                    background-color: #5c5c5c;
                }
                QToolBar {
                    background-color: #3c3c3c;
                    border: 1px solid #5c5c5c;
                }
                QStatusBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #4c4c4c;
                    border: 1px solid #6c6c6c;
                    padding: 5px;
                    color: #ffffff;
                }
                QPushButton:hover {
                    background-color: #5c5c5c;
                }
                QPushButton:pressed {
                    background-color: #3c3c3c;
                }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: #4c4c4c;
                    border: 1px solid #6c6c6c;
                    color: #ffffff;
                    padding: 2px;
                }
                QTreeWidget, QListWidget, QTableWidget {
                    background-color: #3c3c3c;
                    alternate-background-color: #4c4c4c;
                    color: #ffffff;
                    border: 1px solid #6c6c6c;
                }
                QHeaderView::section {
                    background-color: #5c5c5c;
                    color: #ffffff;
                    padding: 4px;
                    border: 1px solid #6c6c6c;
                }
                QGroupBox {
                    border: 2px solid #6c6c6c;
                    margin: 5px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QTabWidget::pane {
                    border: 1px solid #6c6c6c;
                }
                QTabBar::tab {
                    background-color: #4c4c4c;
                    color: #ffffff;
                    padding: 5px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #5c5c5c;
                }
                QSlider::groove:horizontal {
                    border: 1px solid #6c6c6c;
                    height: 8px;
                    background: #4c4c4c;
                    margin: 2px 0;
                }
                QSlider::handle:horizontal {
                    background: #8c8c8c;
                    border: 1px solid #6c6c6c;
                    width: 18px;
                    margin: -2px 0;
                    border-radius: 3px;
                }
                QProgressBar {
                    border: 1px solid #6c6c6c;
                    border-radius: 3px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                    border-radius: 3px;
                }
                QCheckBox::indicator {
                    width: 13px;
                    height: 13px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #4c4c4c;
                    border: 1px solid #6c6c6c;
                }
                QCheckBox::indicator:checked {
                    background-color: #0078d4;
                    border: 1px solid #0078d4;
                }
            """)
        else:
            # Açık tema (varsayılan)
            app.setStyleSheet("""
                QMainWindow {
                    background-color: #f0f0f0;
                }
                QToolBar {
                    border: 1px solid #c0c0c0;
                    background-color: #f8f8f8;
                }
                QStatusBar {
                    border-top: 1px solid #c0c0c0;
                }
                QPushButton {
                    padding: 5px 10px;
                    border: 1px solid #c0c0c0;
                    border-radius: 3px;
                    background-color: #ffffff;
                }
                QPushButton:hover {
                    background-color: #e8e8e8;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #c0c0c0;
                    border-radius: 5px;
                    margin: 5px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QTreeWidget, QListWidget, QTableWidget {
                    border: 1px solid #c0c0c0;
                    alternate-background-color: #f8f8f8;
                }
                QHeaderView::section {
                    background-color: #e0e0e0;
                    padding: 4px;
                    border: 1px solid #c0c0c0;
                }
                QTabWidget::pane {
                    border: 1px solid #c0c0c0;
                }
                QTabBar::tab {
                    background-color: #e0e0e0;
                    padding: 5px 10px;
                    margin-right: 2px;
                    border: 1px solid #c0c0c0;
                    border-bottom-color: transparent;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                    border-bottom-color: transparent;
                }
                QProgressBar {
                    border: 1px solid #c0c0c0;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #f0f0f0;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                    border-radius: 3px;
                }
            """)
            
        return True
        
    except Exception as e:
        logging.warning(f"Stil ayarlama hatası: {e}")
        return False

def apply_widget_theme(widget, theme="light"):
    """Tek bir widget'a tema uygula"""
    try:
        if theme == "dark":
            palette = widget.palette()
            palette.setColor(widget.palette().Window, QColor(43, 43, 43))
            palette.setColor(widget.palette().WindowText, QColor(255, 255, 255))
            palette.setColor(widget.palette().Base, QColor(60, 60, 60))
            palette.setColor(widget.palette().AlternateBase, QColor(76, 76, 76))
            palette.setColor(widget.palette().ToolTipBase, QColor(0, 0, 0))
            palette.setColor(widget.palette().ToolTipText, QColor(255, 255, 255))
            palette.setColor(widget.palette().Text, QColor(255, 255, 255))
            palette.setColor(widget.palette().Button, QColor(76, 76, 76))
            palette.setColor(widget.palette().ButtonText, QColor(255, 255, 255))
            palette.setColor(widget.palette().BrightText, QColor(255, 0, 0))
            palette.setColor(widget.palette().Link, QColor(42, 130, 218))
            palette.setColor(widget.palette().Highlight, QColor(42, 130, 218))
            palette.setColor(widget.palette().HighlightedText, QColor(0, 0, 0))
            widget.setPalette(palette)
            
    except Exception as e:
        logging.warning(f"Widget tema uygulama hatası: {e}")

# GUI event handling utilities
def center_widget_on_parent(widget, parent):
    """Widget'ı parent'ın ortasında konumlandır"""
    try:
        if parent:
            parent_geometry = parent.geometry()
            widget_geometry = widget.geometry()
            
            x = parent_geometry.x() + (parent_geometry.width() - widget_geometry.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - widget_geometry.height()) // 2
            
            widget.move(x, y)
    except Exception as e:
        logging.warning(f"Widget ortalama hatası: {e}")

def setup_window_icon(window, icon_path=None):
    """Pencere ikonunu ayarla"""
    try:
        from PyQt5.QtGui import QIcon
        
        if icon_path and os.path.exists(icon_path):
            window.setWindowIcon(QIcon(icon_path))
        else:
            # Varsayılan sistem ikonu kullan
            style = window.style()
            icon = style.standardIcon(style.SP_ComputerIcon)
            window.setWindowIcon(icon)
            
    except Exception as e:
        logging.warning(f"İkon ayarlama hatası: {e}")

def create_separator_line(orientation="horizontal"):
    """Ayırıcı çizgi oluştur"""
    try:
        from PyQt5.QtWidgets import QFrame
        from PyQt5.QtCore import Qt
        
        line = QFrame()
        if orientation.lower() == "horizontal":
            line.setFrameShape(QFrame.HLine)
        else:
            line.setFrameShape(QFrame.VLine)
        
        line.setFrameShadow(QFrame.Sunken)
        return line
        
    except Exception as e:
        logging.error(f"Ayırıcı çizgi oluşturma hatası: {e}")
        return None

def show_loading_cursor():
    """Loading cursor göster"""
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        QApplication.setOverrideCursor(Qt.WaitCursor)
    except:
        pass

def restore_cursor():
    """Normal cursor'a geri dön"""
    try:
        from PyQt5.QtWidgets import QApplication
        QApplication.restoreOverrideCursor()
    except:
        pass

# Modül başlatma kontrolü
def initialize_gui():
    """GUI modülünü başlat"""
    available, message = check_gui_dependencies()
    if not available:
        raise ImportError(f"GUI modülü başlatılamadı: {message}")
    
    qt_version = get_qt_version()
    logging.info(f"GUI modülü başlatıldı - Qt {qt_version}")
    return True

# Import gerekli modüller
import logging
import os
from PyQt5.QtGui import QColor