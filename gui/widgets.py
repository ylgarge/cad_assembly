"""
Özel Widget Sınıfları
Property panel, log widget, progress widget vb.
"""

import logging
from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QGroupBox, QSplitter, QTabWidget, QListWidget,
    QListWidgetItem, QFrame, QProgressBar, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSlider, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette

class PropertyPanel(QWidget):
    """Özellikler paneli widget'ı"""
    
    property_changed = pyqtSignal(str, object)  # property_name, new_value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger("CADMontaj.PropertyPanel")
        self.current_shape_data = None
        self.property_widgets = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI'yi kur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Scroll içeriği
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        
        # Varsayılan mesaj
        self.empty_label = QLabel("Özellik görüntülenecek nesne yok")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: gray; font-style: italic;")
        self.scroll_layout.addWidget(self.empty_label)
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
        self.logger.debug("Property panel oluşturuldu")

class GeometryInfoWidget(QWidget):
    """Geometri bilgi widget'ı"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.info_labels = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """UI'yi kur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Başlık
        title_label = QLabel("Geometri Bilgileri")
        title_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(title_label)
        
        # Bilgi alanları
        info_layout = QFormLayout()
        
        # Temel bilgiler
        info_fields = [
            ("faces", "Yüzey Sayısı:"),
            ("edges", "Kenar Sayısı:"),
            ("vertices", "Köşe Sayısı:"),
            ("volume", "Hacim:"),
            ("surface_area", "Yüzey Alanı:"),
            ("bbox_dimensions", "Boyutlar:")
        ]
        
        for field_id, label_text in info_fields:
            value_label = QLabel("--")
            value_label.setAlignment(Qt.AlignRight)
            info_layout.addRow(label_text, value_label)
            self.info_labels[field_id] = value_label
        
        layout.addLayout(info_layout)
        layout.addStretch()
    
    def update_geometry_info(self, analysis_data: Dict[str, Any]):
        """Geometri bilgilerini güncelle"""
        try:
            basic_geom = analysis_data.get("basic_geometry", {})
            
            # Topology
            topology = basic_geom.get("topology", {})
            self.info_labels["faces"].setText(str(topology.get("num_faces", 0)))
            self.info_labels["edges"].setText(str(topology.get("num_edges", 0)))
            self.info_labels["vertices"].setText(str(topology.get("num_vertices", 0)))
            
            # Properties
            properties = basic_geom.get("properties", {})
            
            volume = properties.get("volume", 0)
            if volume > 0:
                self.info_labels["volume"].setText(f"{volume:.2f} mm³")
            else:
                self.info_labels["volume"].setText("--")
            
            surface_area = properties.get("surface_area", 0)
            if surface_area > 0:
                self.info_labels["surface_area"].setText(f"{surface_area:.2f} mm²")
            else:
                self.info_labels["surface_area"].setText("--")
            
            # Bounding box
            bbox = basic_geom.get("bounding_box", {})
            if bbox and "width" in bbox:
                width = bbox.get("width", 0)
                height = bbox.get("height", 0)
                depth = bbox.get("depth", 0)
                dimensions_text = f"{width:.1f}×{height:.1f}×{depth:.1f} mm"
                self.info_labels["bbox_dimensions"].setText(dimensions_text)
            else:
                self.info_labels["bbox_dimensions"].setText("--")
                
        except Exception as e:
            logging.error(f"Geometri bilgisi güncelleme hatası: {e}")
    
    def clear_info(self):
        """Bilgileri temizle"""
        for label in self.info_labels.values():
            label.setText("--")

class StatusInfoWidget(QWidget):
    """Durum bilgisi widget'ı"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI'yi kur"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Mouse koordinatları
        self.mouse_coords_label = QLabel("Mouse: --")
        self.mouse_coords_label.setMinimumWidth(120)
        layout.addWidget(self.mouse_coords_label)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator1)
        
        # Seçim bilgisi
        self.selection_label = QLabel("Seçim: Yok")
        self.selection_label.setMinimumWidth(100)
        layout.addWidget(self.selection_label)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)
        
        # Zoom seviyesi
        self.zoom_label = QLabel("Zoom: 100%")
        layout.addWidget(self.zoom_label)
        
        layout.addStretch()
        
        # FPS bilgisi
        self.fps_label = QLabel("FPS: --")
        layout.addWidget(self.fps_label)
    
    def update_mouse_coords(self, x: float, y: float, z: float = 0.0):
        """Mouse koordinatlarını güncelle"""
        self.mouse_coords_label.setText(f"Mouse: {x:.1f}, {y:.1f}, {z:.1f}")
    
    def update_selection_info(self, selection_count: int):
        """Seçim bilgisini güncelle"""
        if selection_count == 0:
            self.selection_label.setText("Seçim: Yok")
        elif selection_count == 1:
            self.selection_label.setText("Seçim: 1 öğe")
        else:
            self.selection_label.setText(f"Seçim: {selection_count} öğe")
    
    def update_zoom_level(self, zoom_percent: float):
        """Zoom seviyesini güncelle"""
        self.zoom_label.setText(f"Zoom: {zoom_percent:.0f}%")
    
    def update_fps(self, fps: int):
        """FPS'i güncelle"""
        self.fps_label.setText(f"FPS: {fps}")

class ColorPickerWidget(QWidget):
    """Renk seçici widget'ı"""
    
    color_changed = pyqtSignal(tuple)  # (r, g, b) tuple'ı
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_color = (0.7, 0.7, 0.7)  # Varsayılan gri
        self._setup_ui()
    
    def _setup_ui(self):
        """UI'yi kur"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Renk önizleme
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 20)
        self.color_preview.setStyleSheet(f"background-color: rgb({int(self.current_color[0]*255)}, {int(self.current_color[1]*255)}, {int(self.current_color[2]*255)}); border: 1px solid gray;")
        self.color_preview.mousePressEvent = self._open_color_dialog
        layout.addWidget(self.color_preview)
        
        # Renk bilgisi
        self.color_label = QLabel("RGB(179, 179, 179)")
        layout.addWidget(self.color_label)
        
        layout.addStretch()
    
    def _open_color_dialog(self, event):
        """Renk seçici dialog'unu aç"""
        from PyQt5.QtWidgets import QColorDialog
        from PyQt5.QtGui import QColor
        
        # Mevcut rengi QColor'a çevir
        current_qcolor = QColor(
            int(self.current_color[0] * 255),
            int(self.current_color[1] * 255), 
            int(self.current_color[2] * 255)
        )
        
        # Color dialog aç
        color = QColorDialog.getColor(current_qcolor, self, "Renk Seç")
        
        if color.isValid():
            # RGB değerlerini normalize et (0-1 arası)
            r = color.red() / 255.0
            g = color.green() / 255.0
            b = color.blue() / 255.0
            
            self.set_color((r, g, b))
    
    def set_color(self, color: tuple):
        """Rengi ayarla"""
        try:
            self.current_color = color
            
            # Önizlemeyi güncelle
            r, g, b = [int(c * 255) for c in color]
            self.color_preview.setStyleSheet(f"background-color: rgb({r}, {g}, {b}); border: 1px solid gray;")
            
            # Label'ı güncelle
            self.color_label.setText(f"RGB({r}, {g}, {b})")
            
            # Sinyal gönder
            self.color_changed.emit(color)
            
        except Exception as e:
            logging.error(f"Renk ayarlama hatası: {e}")
    
    def get_color(self) -> tuple:
        """Mevcut rengi al"""
        return self.current_color

class MaterialPropertyWidget(QWidget):
    """Malzeme özellikleri widget'ı"""
    
    material_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_material = {
            "name": "default",
            "color": (0.7, 0.7, 0.7),
            "transparency": 0.0,
            "shininess": 0.5,
            "metallic": False
        }
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI'yi kur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Malzeme presetleri
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Default", "Metal", "Plastic", "Glass", 
            "Rubber", "Wood", "Ceramic"
        ])
        self.preset_combo.currentTextChanged.connect(self._apply_preset)
        preset_layout.addWidget(self.preset_combo)
        
        layout.addLayout(preset_layout)
        
        # Renk seçici
        self.color_picker = ColorPickerWidget()
        self.color_picker.color_changed.connect(self._on_color_changed)
        
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Renk:"))
        color_layout.addWidget(self.color_picker)
        layout.addLayout(color_layout)
        
        # Şeffaflık
        transparency_layout = QHBoxLayout()
        transparency_layout.addWidget(QLabel("Şeffaflık:"))
        
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setRange(0, 100)
        self.transparency_slider.setValue(0)
        self.transparency_slider.valueChanged.connect(self._on_transparency_changed)
        transparency_layout.addWidget(self.transparency_slider)
        
        self.transparency_label = QLabel("0%")
        transparency_layout.addWidget(self.transparency_label)
        
        layout.addLayout(transparency_layout)
        
        # Parlaklık
        shininess_layout = QHBoxLayout()
        shininess_layout.addWidget(QLabel("Parlaklık:"))
        
        self.shininess_slider = QSlider(Qt.Horizontal)
        self.shininess_slider.setRange(0, 100)
        self.shininess_slider.setValue(50)
        self.shininess_slider.valueChanged.connect(self._on_shininess_changed)
        shininess_layout.addWidget(self.shininess_slider)
        
        self.shininess_label = QLabel("50%")
        shininess_layout.addWidget(self.shininess_label)
        
        layout.addLayout(shininess_layout)
        
        # Metalik
        self.metallic_check = QCheckBox("Metalik")
        self.metallic_check.toggled.connect(self._on_metallic_changed)
        layout.addWidget(self.metallic_check)
        
        layout.addStretch()
    
    def _apply_preset(self, preset_name: str):
        """Preset uygula"""
        presets = {
            "Default": {"color": (0.7, 0.7, 0.7), "transparency": 0.0, "shininess": 0.3, "metallic": False},
            "Metal": {"color": (0.8, 0.8, 0.9), "transparency": 0.0, "shininess": 0.9, "metallic": True},
            "Plastic": {"color": (0.2, 0.6, 0.8), "transparency": 0.0, "shininess": 0.2, "metallic": False},
            "Glass": {"color": (0.9, 0.9, 1.0), "transparency": 0.7, "shininess": 0.9, "metallic": False},
            "Rubber": {"color": (0.2, 0.2, 0.2), "transparency": 0.0, "shininess": 0.1, "metallic": False},
            "Wood": {"color": (0.6, 0.4, 0.2), "transparency": 0.0, "shininess": 0.2, "metallic": False},
            "Ceramic": {"color": (1.0, 1.0, 0.95), "transparency": 0.0, "shininess": 0.6, "metallic": False}
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            
            # Widget'ları güncelle
            self.color_picker.set_color(preset["color"])
            self.transparency_slider.setValue(int(preset["transparency"] * 100))
            self.shininess_slider.setValue(int(preset["shininess"] * 100))
            self.metallic_check.setChecked(preset["metallic"])
            
            # Material'ı güncelle
            self.current_material.update(preset)
            self.current_material["name"] = preset_name.lower()
            
            self.material_changed.emit(self.current_material)
    
    def _on_color_changed(self, color: tuple):
        """Renk değiştiğinde"""
        self.current_material["color"] = color
        self.material_changed.emit(self.current_material)
    
    def _on_transparency_changed(self, value: int):
        """Şeffaflık değiştiğinde"""
        transparency = value / 100.0
        self.current_material["transparency"] = transparency
        self.transparency_label.setText(f"{value}%")
        self.material_changed.emit(self.current_material)
    
    def _on_shininess_changed(self, value: int):
        """Parlaklık değiştiğinde"""
        shininess = value / 100.0
        self.current_material["shininess"] = shininess
        self.shininess_label.setText(f"{value}%")
        self.material_changed.emit(self.current_material)
    
    def _on_metallic_changed(self, metallic: bool):
        """Metalik özellik değiştiğinde"""
        self.current_material["metallic"] = metallic
        self.material_changed.emit(self.current_material)
    
    def get_material(self) -> Dict[str, Any]:
        """Mevcut malzemeyi al"""
        return self.current_material.copy()
    
    def set_material(self, material: Dict[str, Any]):
        """Malzeme ayarla"""
        self.current_material.update(material)
        
        # Widget'ları güncelle
        if "color" in material:
            self.color_picker.set_color(material["color"])
        if "transparency" in material:
            self.transparency_slider.setValue(int(material["transparency"] * 100))
        if "shininess" in material:
            self.shininess_slider.setValue(int(material["shininess"] * 100))
        if "metallic" in material:
            self.metallic_check.setChecked(material["metallic"])

class LogWidget(QWidget):
    """Log mesajları widget'ı"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.max_log_entries = 1000
        self._setup_ui()
        
        # Log handler bağlantısı için timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_logs)
        self.update_timer.start(1000)  # Her saniye güncelle
    
    def _setup_ui(self):
        """UI'yi kur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Log listesi
        self.log_list = QListWidget()
        self.log_list.setAlternatingRowColors(True)
        layout.addWidget(self.log_list)
        
        # Alt panel - kontroller
        controls_layout = QHBoxLayout()
        
        # Level seçici
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.setCurrentText("INFO")
        self.level_combo.currentTextChanged.connect(self._filter_by_level)
        controls_layout.addWidget(QLabel("Seviye:"))
        controls_layout.addWidget(self.level_combo)
        
        controls_layout.addStretch()
        
        # Temizle butonu
        clear_btn = QPushButton("Temizle")
        clear_btn.clicked.connect(self.clear_logs)
        controls_layout.addWidget(clear_btn)
        
        layout.addLayout(controls_layout)
    
    def add_log_entry(self, level: str, message: str, timestamp: str = None):
        """Log girdisi ekle"""
        try:
            if not timestamp:
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Renk belirleme
            colors = {
                "DEBUG": QColor(128, 128, 128),    # Gri
                "INFO": QColor(0, 0, 0),           # Siyah
                "WARNING": QColor(255, 140, 0),    # Turuncu
                "ERROR": QColor(255, 0, 0),        # Kırmızı
                "CRITICAL": QColor(139, 0, 0)      # Koyu kırmızı
            }
            
            # Mesaj formatla
            formatted_message = f"[{timestamp}] [{level}] {message}"
            
            # Liste öğesi oluştur
            item = QListWidgetItem(formatted_message)
            item.setData(Qt.UserRole, level)  # Level'i sakla
            
            # Rengi ayarla
            if level in colors:
                item.setForeground(colors[level])
            
            self.log_list.addItem(item)
            
            # Maksimum giriş sınırı
            if self.log_list.count() > self.max_log_entries:
                self.log_list.takeItem(0)
            
            # En son eklenen öğeye kaydır
            self.log_list.scrollToBottom()
            
        except Exception as e:
            print(f"Log ekleme hatası: {e}")
    
    def _update_logs(self):
        """Log'ları güncelle (gerçek log handler'dan)"""
        # Bu fonksiyon log handler ile entegre edilebilir
        # Şimdilik boş bırakıyoruz
        pass
    
    def _filter_by_level(self, level: str):
        """Seviyeye göre filtrele"""
        level_priority = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3,
            "CRITICAL": 4
        }
        
        min_priority = level_priority.get(level, 0)
        
        for i in range(self.log_list.count()):
            item = self.log_list.item(i)
            item_level = item.data(Qt.UserRole)
            item_priority = level_priority.get(item_level, 0)
            
            # Seçili seviye ve üzerindeki mesajları göster
            item.setHidden(item_priority < min_priority)
    
    def clear_logs(self):
        """Tüm log'ları temizle"""
        self.log_list.clear()

class ProgressWidget(QWidget):
    """Progress gösterimi widget'ı"""
    
    operation_cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self.setVisible(False)
    
    def _setup_ui(self):
        """UI'yi kur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Mesaj label'ı
        self.message_label = QLabel("İşlem devam ediyor...")
        layout.addWidget(self.message_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # İptal butonu
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.clicked.connect(self.operation_cancelled.emit)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def start_operation(self, message: str, indeterminate: bool = False):
        """İşlem başlat"""
        self.message_label.setText(message)
        
        if indeterminate:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        
        self.setVisible(True)
    
    def update_progress(self, value: int, message: str = None):
        """Progress güncelle"""
        self.progress_bar.setValue(value)
        
        if message:
            self.message_label.setText(message)
    
    def finish_operation(self):
        """İşlem bitir"""
        self.setVisible(False)

class ShapeTreeWidget(QTreeWidget):
    """Shape'leri gösteren ağaç widget'ı"""
    
    shape_selected = pyqtSignal(str)  # shape_id
    shape_visibility_changed = pyqtSignal(str, bool)  # shape_id, visible
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """UI'yi kur"""
        self.setHeaderLabels(["Model", "Tür", "Durum"])
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        self.setSelectionMode(self.ExtendedSelection)
        
        # Kolonları boyutlandır
        header = self.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
    
    def _setup_connections(self):
        """Bağlantıları kur"""
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.itemChanged.connect(self._on_item_changed)
    
    def add_shape(self, shape_id: str, shape_data: Dict[str, Any]):
        """Shape ekle"""
        try:
            metadata = shape_data.get("metadata", {})
            
            # Ana öğe
            item = QTreeWidgetItem(self)
            
            # Shape adı
            file_name = metadata.get("file_name", f"Shape {shape_id}")
            item.setText(0, file_name)
            item.setData(0, Qt.UserRole, shape_id)
            
            # Tür
            file_ext = metadata.get("file_extension", "").upper()
            item.setText(1, file_ext)
            
            # Durum
            success = metadata.get("import_successful", False)
            status = "✓ Yüklendi" if success else "✗ Hata"
            item.setText(2, status)
            
            # Görünürlük checkbox'ı
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
            
            # Analiz verilerini alt öğeler olarak ekle
            self._add_analysis_children(item, shape_data.get("analysis", {}))
            
            self.expandAll()
            
        except Exception as e:
            logging.error(f"Shape ağaca ekleme hatası: {e}")
    
    def _add_analysis_children(self, parent_item: QTreeWidgetItem, analysis: Dict[str, Any]):
        """Analiz verilerini alt öğe olarak ekle"""
        try:
            basic_geom = analysis.get("basic_geometry", {})
            
            # Topology bilgileri
            topology = basic_geom.get("topology", {})
            if topology:
                topo_item = QTreeWidgetItem(parent_item)
                topo_item.setText(0, "Topology")
                
                for key, value in topology.items():
                    if isinstance(value, int) and value > 0:
                        child_item = QTreeWidgetItem(topo_item)
                        display_name = key.replace("num_", "").title()
                        child_item.setText(0, f"{display_name}: {value}")
            
            # Özellikler
            properties = basic_geom.get("properties", {})
            if properties:
                props_item = QTreeWidgetItem(parent_item)
                props_item.setText(0, "Özellikler")
                
                # Hacim
                if "volume" in properties and properties["volume"] > 0:
                    vol_item = QTreeWidgetItem(props_item)
                    vol_item.setText(0, f"Hacim: {properties['volume']:.2f} mm³")
                
                # Yüzey alanı
                if "surface_area" in properties and properties["surface_area"] > 0:
                    area_item = QTreeWidgetItem(props_item)
                    area_item.setText(0, f"Yüzey Alanı: {properties['surface_area']:.2f} mm²")
            
        except Exception as e:
            logging.debug(f"Analiz alt öğe ekleme hatası: {e}")
    
    def remove_shape(self, shape_id: str):
        """Shape'i kaldır"""
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.UserRole) == shape_id:
                self.takeTopLevelItem(i)
                break
    
    def clear_shapes(self):
        """Tüm shape'leri temizle"""
        self.clear()
    
    def _on_selection_changed(self):
        """Seçim değiştiğinde"""
        selected_items = self.selectedItems()
        
        for item in selected_items:
            shape_id = item.data(0, Qt.UserRole)
            if shape_id:
                self.shape_selected.emit(shape_id)
                break
    
    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Öğe değiştiğinde (checkbox)"""
        if column == 0:  # İsim kolonu
            shape_id = item.data(0, Qt.UserRole)
            if shape_id:
                visible = item.checkState(0) == Qt.Checked
                self.shape_visibility_changed.emit(shape_id, visible)

class AssemblyConstraintWidget(QWidget):
    """Montaj kısıtlamaları widget'ı"""
    
    constraint_added = pyqtSignal(dict)
    constraint_removed = pyqtSignal(str)
    constraint_modified = pyqtSignal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.constraints = {}  # constraint_id -> constraint_data
        self._setup_ui()
    
    def _setup_ui(self):
        """UI'yi kur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Başlık
        title_label = QLabel("Montaj Kısıtlamaları")
        title_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(title_label)
        
        # Kısıtlama listesi
        self.constraint_table = QTableWidget()
        self.constraint_table.setColumnCount(4)
        self.constraint_table.setHorizontalHeaderLabels(["Tür", "Parça 1", "Parça 2", "Değer"])
        
        header = self.constraint_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        layout.addWidget(self.constraint_table)
        
        # Kontrol butonları
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Ekle")
        add_btn.clicked.connect(self._add_constraint)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Kaldır")
        remove_btn.clicked.connect(self._remove_constraint)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        
        clear_btn = QPushButton("Tümünü Temizle")
        clear_btn.clicked.connect(self._clear_constraints)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
    
    def add_constraint(self, constraint_data: Dict[str, Any]):
        """Kısıtlama ekle"""
        try:
            constraint_id = f"constraint_{len(self.constraints)}"
            self.constraints[constraint_id] = constraint_data
            
            # Tabloya ekle
            row = self.constraint_table.rowCount()
            self.constraint_table.insertRow(row)
            
            # Veri doldur
            constraint_type = constraint_data.get("type", "Unknown")
            part1 = constraint_data.get("part1", "")
            part2 = constraint_data.get("part2", "")
            value = constraint_data.get("value", "")
            
            self.constraint_table.setItem(row, 0, QTableWidgetItem(constraint_type))
            self.constraint_table.setItem(row, 1, QTableWidgetItem(str(part1)))
            self.constraint_table.setItem(row, 2, QTableWidgetItem(str(part2)))
            self.constraint_table.setItem(row, 3, QTableWidgetItem(str(value)))
            
            # ID'yi sakla
            self.constraint_table.item(row, 0).setData(Qt.UserRole, constraint_id)
            
        except Exception as e:
            logging.error(f"Kısıtlama ekleme hatası: {e}")
    
    def _add_constraint(self):
        """Yeni kısıtlama ekle"""
        # Basit örnek kısıtlama
        constraint_data = {
            "type": "Coincident",
            "part1": "Part A",
            "part2": "Part B", 
            "value": ""
        }
        
        self.add_constraint(constraint_data)
        self.constraint_added.emit(constraint_data)
    
    def _remove_constraint(self):
        """Seçili kısıtlamayı kaldır"""
        current_row = self.constraint_table.currentRow()
        
        if current_row >= 0:
            item = self.constraint_table.item(current_row, 0)
            if item:
                constraint_id = item.data(Qt.UserRole)
                
                # Listeden kaldır
                if constraint_id in self.constraints:
                    del self.constraints[constraint_id]
                
                # Tablodan kaldır
                self.constraint_table.removeRow(current_row)
                
                self.constraint_removed.emit(constraint_id)
    
    def _clear_constraints(self):
        """Tüm kısıtlamaları temizle"""
        self.constraints.clear()
        self.constraint_table.setRowCount(0)
    
    def get_constraints(self) -> Dict[str, Dict[str, Any]]:
        """Tüm kısıtlamaları al"""
        return self.constraints.copy()