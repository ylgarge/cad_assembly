"""
Dialog Pencereleri - Import hataları düzeltildi
Ayarlar, hakkında, dosya bilgileri vb. dialog pencereleri
"""

import logging
import os
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTabWidget,
    QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox,
    QSlider, QDialogButtonBox, QFileDialog, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QSplitter, QFrame,
    QScrollArea, QWidget, QProgressDialog, QListWidget,
    QProgressBar  # ✅ DOĞRU: QtWidgets'tan import
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QThread, QTimer  # ❌ QProgressBar burada DEĞİL
from PyQt5.QtGui import QFont, QPixmap, QIcon

from utils import Config, APP_NAME, APP_VERSION, GUIDefaults

class SettingsDialog(QDialog):
    """Ayarlar dialog penceresi"""
    
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        
        self.config = config
        self.logger = logging.getLogger("CADMontaj.SettingsDialog")
        self.original_settings = config.get_all_settings()
        
        self._setup_ui()
        self._load_settings()
        
        self.logger.debug("Ayarlar dialog'u oluşturuldu")
    
    def _setup_ui(self):
        """UI'yi kur"""
        self.setWindowTitle("Ayarlar")
        self.setModal(True)
        self.resize(*GUIDefaults.SETTINGS_DIALOG_SIZE)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Tab'ları oluştur
        self._create_general_tab()
        self._create_viewer_tab()
        self._create_import_tab()
        self._create_assembly_tab()
        self._create_performance_tab()
        
        # Dialog butonları
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self._save_settings)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._restore_defaults)
        
        layout.addWidget(button_box)
    
    def _create_general_tab(self):
        """Genel ayarlar tab'ı"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # GUI Ayarları
        gui_group = QGroupBox("GUI Ayarları")
        gui_layout = QFormLayout(gui_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        gui_layout.addRow("Tema:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["tr", "en"])
        gui_layout.addRow("Dil:", self.language_combo)
        
        self.window_maximized_check = QCheckBox("Başlangıçta tam ekran")
        gui_layout.addRow(self.window_maximized_check)
        
        layout.addWidget(gui_group)
        
        # Dosya Ayarları
        file_group = QGroupBox("Dosya Ayarları")
        file_layout = QFormLayout(file_group)
        
        self.default_dir_edit = QLineEdit()
        default_dir_btn = QPushButton("Gözat...")
        default_dir_btn.clicked.connect(self._browse_default_directory)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.default_dir_edit)
        dir_layout.addWidget(default_dir_btn)
        file_layout.addRow("Varsayılan Dizin:", dir_layout)
        
        self.max_recent_files_spin = QSpinBox()
        self.max_recent_files_spin.setRange(1, 20)
        file_layout.addRow("Son Dosya Sayısı:", self.max_recent_files_spin)
        
        self.auto_backup_check = QCheckBox("Otomatik yedekleme")
        file_layout.addRow(self.auto_backup_check)
        
        layout.addWidget(file_group)
        
        # Log Ayarları
        log_group = QGroupBox("Log Ayarları")
        log_layout = QFormLayout(log_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("Log Seviyesi:", self.log_level_combo)
        
        self.file_logging_check = QCheckBox("Dosyaya log kaydet")
        log_layout.addRow(self.file_logging_check)
        
        self.max_log_files_spin = QSpinBox()
        self.max_log_files_spin.setRange(1, 10)
        log_layout.addRow("Maksimum Log Dosyası:", self.max_log_files_spin)
        
        layout.addWidget(log_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Genel")
    
    def _create_viewer_tab(self):
        """3D Viewer ayarları tab'ı"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Görünüm Ayarları
        view_group = QGroupBox("Görünüm Ayarları")
        view_layout = QFormLayout(view_group)
        
        self.background_gradient_check = QCheckBox("Gradient arkaplan")
        view_layout.addRow(self.background_gradient_check)
        
        self.antialiasing_check = QCheckBox("Antialiasing")
        view_layout.addRow(self.antialiasing_check)
        
        self.shadows_check = QCheckBox("Gölgeler")
        view_layout.addRow(self.shadows_check)
        
        self.mouse_sensitivity_slider = QSlider(Qt.Horizontal)
        self.mouse_sensitivity_slider.setRange(1, 100)
        self.mouse_sensitivity_label = QLabel("1.0")
        
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(self.mouse_sensitivity_slider)
        sensitivity_layout.addWidget(self.mouse_sensitivity_label)
        view_layout.addRow("Mouse Hassasiyeti:", sensitivity_layout)
        
        self.mouse_sensitivity_slider.valueChanged.connect(
            lambda v: self.mouse_sensitivity_label.setText(f"{v/50.0:.1f}")
        )
        
        layout.addWidget(view_group)
        
        # Malzeme Ayarları
        material_group = QGroupBox("Malzeme Ayarları")
        material_layout = QFormLayout(material_group)
        
        self.default_material_combo = QComboBox()
        self.default_material_combo.addItems(["plastic", "metal", "glass", "rubber"])
        material_layout.addRow("Varsayılan Malzeme:", self.default_material_combo)
        
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setRange(0, 100)
        self.transparency_label = QLabel("0%")
        
        trans_layout = QHBoxLayout()
        trans_layout.addWidget(self.transparency_slider)
        trans_layout.addWidget(self.transparency_label)
        material_layout.addRow("Varsayılan Şeffaflık:", trans_layout)
        
        self.transparency_slider.valueChanged.connect(
            lambda v: self.transparency_label.setText(f"{v}%")
        )
        
        layout.addWidget(material_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "3D Viewer")
    
    def _create_import_tab(self):
        """İçe aktarma ayarları tab'ı"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # İmport Ayarları
        import_group = QGroupBox("İçe Aktarma Ayarları")
        import_layout = QFormLayout(import_group)
        
        self.healing_shapes_check = QCheckBox("Shape healing uygula")
        import_layout.addRow(self.healing_shapes_check)
        
        self.auto_fit_all_check = QCheckBox("Otomatik fit all")
        import_layout.addRow(self.auto_fit_all_check)
        
        self.import_units_combo = QComboBox()
        self.import_units_combo.addItems(["mm", "cm", "m", "in", "ft"])
        import_layout.addRow("İçe Aktarma Birimi:", self.import_units_combo)
        
        layout.addWidget(import_group)
        
        # Validasyon Ayarları
        validation_group = QGroupBox("Dosya Doğrulama")
        validation_layout = QFormLayout(validation_group)
        
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 2000)
        self.max_file_size_spin.setSuffix(" MB")
        validation_layout.addRow("Maksimum Dosya Boyutu:", self.max_file_size_spin)
        
        self.content_check_enabled = QCheckBox("İçerik kontrolü")
        validation_layout.addRow(self.content_check_enabled)
        
        layout.addWidget(validation_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "İçe Aktarma")
    
    def _create_assembly_tab(self):
        """Montaj ayarları tab'ı"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Montaj Ayarları
        assembly_group = QGroupBox("Montaj Ayarları")
        assembly_layout = QFormLayout(assembly_group)
        
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setRange(0.001, 10.0)
        self.tolerance_spin.setDecimals(3)
        self.tolerance_spin.setSuffix(" mm")
        assembly_layout.addRow("Tolerans:", self.tolerance_spin)
        
        self.auto_collision_check = QCheckBox("Otomatik çakışma kontrolü")
        assembly_layout.addRow(self.auto_collision_check)
        
        self.show_constraints_check = QCheckBox("Kısıtlamaları göster")
        assembly_layout.addRow(self.show_constraints_check)
        
        self.highlight_connections_check = QCheckBox("Bağlantıları vurgula")
        assembly_layout.addRow(self.highlight_connections_check)
        
        self.connection_tolerance_spin = QDoubleSpinBox()
        self.connection_tolerance_spin.setRange(0.01, 1.0)
        self.connection_tolerance_spin.setDecimals(2)
        self.connection_tolerance_spin.setSuffix(" mm")
        assembly_layout.addRow("Bağlantı Toleransı:", self.connection_tolerance_spin)
        
        self.max_search_iterations_spin = QSpinBox()
        self.max_search_iterations_spin.setRange(10, 1000)
        assembly_layout.addRow("Maksimum Arama İterasyonu:", self.max_search_iterations_spin)
        
        layout.addWidget(assembly_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Montaj")
    
    def _create_performance_tab(self):
        """Performans ayarları tab'ı"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Performans Ayarları
        perf_group = QGroupBox("Performans Ayarları")
        perf_layout = QFormLayout(perf_group)
        
        self.max_triangles_spin = QSpinBox()
        self.max_triangles_spin.setRange(1000, 1000000)
        self.max_triangles_spin.setSuffix(" triangle")
        perf_layout.addRow("Maksimum Triangle:", self.max_triangles_spin)
        
        self.tessellation_quality_slider = QSlider(Qt.Horizontal)
        self.tessellation_quality_slider.setRange(1, 100)
        self.tessellation_quality_label = QLabel("0.5")
        
        tess_layout = QHBoxLayout()
        tess_layout.addWidget(self.tessellation_quality_slider)
        tess_layout.addWidget(self.tessellation_quality_label)
        perf_layout.addRow("Tessellation Kalitesi:", tess_layout)
        
        self.tessellation_quality_slider.valueChanged.connect(
            lambda v: self.tessellation_quality_label.setText(f"{v/100.0:.2f}")
        )
        
        self.use_mesh_cache_check = QCheckBox("Mesh cache kullan")
        perf_layout.addRow(self.use_mesh_cache_check)
        
        self.parallel_processing_check = QCheckBox("Paralel işlem")
        perf_layout.addRow(self.parallel_processing_check)
        
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(512, 8192)
        self.memory_limit_spin.setSuffix(" MB")
        perf_layout.addRow("Bellek Limiti:", self.memory_limit_spin)
        
        layout.addWidget(perf_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Performans")
    
    def _load_settings(self):
        """Mevcut ayarları yükle"""
        try:
            # Genel ayarlar
            self.theme_combo.setCurrentText(self.config.get("gui.theme", "light"))
            self.language_combo.setCurrentText(self.config.get("gui.language", "tr"))
            self.window_maximized_check.setChecked(self.config.get("gui.window_maximized", False))
            
            self.default_dir_edit.setText(self.config.get("import.default_directory", ""))
            self.max_recent_files_spin.setValue(self.config.get("files.max_recent_files", 10))
            self.auto_backup_check.setChecked(self.config.get("files.auto_backup", True))
            
            self.log_level_combo.setCurrentText(self.config.get("logging.level", "INFO"))
            self.file_logging_check.setChecked(self.config.get("logging.file_logging", True))
            self.max_log_files_spin.setValue(self.config.get("logging.max_log_files", 5))
            
            # Viewer ayarları
            self.background_gradient_check.setChecked(self.config.get("viewer.background_gradient", True))
            self.antialiasing_check.setChecked(self.config.get("viewer.antialiasing", True))
            self.shadows_check.setChecked(self.config.get("viewer.shadows", True))
            
            sensitivity = self.config.get("viewer.mouse_sensitivity", 1.0)
            self.mouse_sensitivity_slider.setValue(int(sensitivity * 50))
            
            self.default_material_combo.setCurrentText(self.config.get("viewer.default_material", "plastic"))
            
            transparency = self.config.get("display.transparency", 0.0)
            self.transparency_slider.setValue(int(transparency * 100))
            
            # Import ayarları
            self.healing_shapes_check.setChecked(self.config.get("import.healing_shapes", True))
            self.auto_fit_all_check.setChecked(self.config.get("import.auto_fit_all", True))
            self.import_units_combo.setCurrentText(self.config.get("import.import_units", "mm"))
            self.content_check_enabled.setChecked(self.config.get("import.check_file_content", True))
            
            # Assembly ayarları
            self.tolerance_spin.setValue(self.config.get("assembly.tolerance", 0.01))
            self.auto_collision_check.setChecked(self.config.get("assembly.auto_collision_check", True))
            self.show_constraints_check.setChecked(self.config.get("assembly.show_assembly_constraints", True))
            self.highlight_connections_check.setChecked(self.config.get("assembly.highlight_connections", True))
            self.connection_tolerance_spin.setValue(self.config.get("assembly.connection_tolerance", 0.1))
            self.max_search_iterations_spin.setValue(self.config.get("assembly.max_search_iterations", 100))
            
            # Performance ayarları
            self.max_triangles_spin.setValue(self.config.get("performance.max_triangles", 100000))
            
            tess_quality = self.config.get("performance.tessellation_quality", 0.5)
            self.tessellation_quality_slider.setValue(int(tess_quality * 100))
            
            self.use_mesh_cache_check.setChecked(self.config.get("performance.use_mesh_cache", True))
            self.parallel_processing_check.setChecked(self.config.get("performance.parallel_processing", True))
            self.memory_limit_spin.setValue(self.config.get("performance.memory_limit_mb", 2048))
            
        except Exception as e:
            self.logger.error(f"Ayar yükleme hatası: {e}")
    
    @pyqtSlot()
    def _browse_default_directory(self):
        """Varsayılan dizin seç"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Varsayılan Dizin Seç",
            self.default_dir_edit.text()
        )
        
        if directory:
            self.default_dir_edit.setText(directory)
    
    @pyqtSlot()
    def _save_settings(self):
        """Ayarları kaydet"""
        try:
            # Genel ayarlar
            self.config.set("gui.theme", self.theme_combo.currentText())
            self.config.set("gui.language", self.language_combo.currentText())
            self.config.set("gui.window_maximized", self.window_maximized_check.isChecked())
            
            self.config.set("import.default_directory", self.default_dir_edit.text())
            self.config.set("files.max_recent_files", self.max_recent_files_spin.value())
            self.config.set("files.auto_backup", self.auto_backup_check.isChecked())
            
            self.config.set("logging.level", self.log_level_combo.currentText())
            self.config.set("logging.file_logging", self.file_logging_check.isChecked())
            self.config.set("logging.max_log_files", self.max_log_files_spin.value())
            
            # Viewer ayarları
            self.config.set("viewer.background_gradient", self.background_gradient_check.isChecked())
            self.config.set("viewer.antialiasing", self.antialiasing_check.isChecked())
            self.config.set("viewer.shadows", self.shadows_check.isChecked())
            self.config.set("viewer.mouse_sensitivity", self.mouse_sensitivity_slider.value() / 50.0)
            self.config.set("viewer.default_material", self.default_material_combo.currentText())
            self.config.set("display.transparency", self.transparency_slider.value() / 100.0)
            
            # Import ayarları
            self.config.set("import.healing_shapes", self.healing_shapes_check.isChecked())
            self.config.set("import.auto_fit_all", self.auto_fit_all_check.isChecked())
            self.config.set("import.import_units", self.import_units_combo.currentText())
            self.config.set("import.check_file_content", self.content_check_enabled.isChecked())
            
            # Assembly ayarları
            self.config.set("assembly.tolerance", self.tolerance_spin.value())
            self.config.set("assembly.auto_collision_check", self.auto_collision_check.isChecked())
            self.config.set("assembly.show_assembly_constraints", self.show_constraints_check.isChecked())
            self.config.set("assembly.highlight_connections", self.highlight_connections_check.isChecked())
            self.config.set("assembly.connection_tolerance", self.connection_tolerance_spin.value())
            self.config.set("assembly.max_search_iterations", self.max_search_iterations_spin.value())
            
            # Performance ayarları
            self.config.set("performance.max_triangles", self.max_triangles_spin.value())
            self.config.set("performance.tessellation_quality", self.tessellation_quality_slider.value() / 100.0)
            self.config.set("performance.use_mesh_cache", self.use_mesh_cache_check.isChecked())
            self.config.set("performance.parallel_processing", self.parallel_processing_check.isChecked())
            self.config.set("performance.memory_limit_mb", self.memory_limit_spin.value())
            
            # Ayarları dosyaya kaydet
            self.config.save()
            
            self.logger.info("Ayarlar kaydedildi")
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Ayar kaydetme hatası: {e}")
            QMessageBox.critical(self, "Hata", f"Ayarlar kaydedilemedi: {str(e)}")
    
    @pyqtSlot()
    def _restore_defaults(self):
        """Varsayılan ayarlara dön"""
        reply = QMessageBox.question(
            self,
            "Varsayılan Ayarlar",
            "Tüm ayarlar varsayılan değerlere döndürülecek. Emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config.reset_to_defaults()
            self._load_settings()
            self.logger.info("Ayarlar varsayılan değerlere döndürüldü")

class AboutDialog(QDialog):
    """Hakkında dialog penceresi"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI'yi kur"""
        self.setWindowTitle("Hakkında")
        self.setModal(True)
        self.setFixedSize(*GUIDefaults.ABOUT_DIALOG_SIZE)
        
        layout = QVBoxLayout(self)
        
        # Logo/Icon alanı
        icon_label = QLabel()
        # icon_label.setPixmap(QPixmap("resources/icons/app_icon.png").scaled(64, 64))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Uygulama bilgileri
        app_info = QLabel(f"""
<h2>{APP_NAME}</h2>
<p><b>Versiyon:</b> {APP_VERSION}</p>
<p><b>Geliştirici:</b> CAD Developer</p>
<p><b>Açıklama:</b> STEP dosyalarının montajı için CAD uygulaması</p>
        """)
        app_info.setAlignment(Qt.AlignCenter)
        app_info.setWordWrap(True)
        layout.addWidget(app_info)
        
        # Teknoloji bilgileri
        tech_info = QLabel("""
<h3>Kullanılan Teknolojiler:</h3>
<ul>
<li>Python 3.x</li>
<li>PyQt5</li>
<li>PythonOCC Core 7.7.2</li>
<li>OpenCASCADE</li>
</ul>
        """)
        tech_info.setWordWrap(True)
        layout.addWidget(tech_info)
        
        # Kapatma butonu
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)

class FileInfoDialog(QDialog):
    """Dosya bilgileri dialog penceresi"""
    
    def __init__(self, shape_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        
        self.shape_data = shape_data
        self._setup_ui()
        self._populate_data()
    
    def _setup_ui(self):
        """UI'yi kur"""
        self.setWindowTitle("Dosya Bilgileri")
        self.setModal(True)
        self.resize(*GUIDefaults.FILE_INFO_DIALOG_SIZE)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Genel bilgiler tab'ı
        self._create_general_info_tab()
        
        # Geometri analizi tab'ı
        self._create_geometry_tab()
        
        # Analiz sonuçları tab'ı
        self._create_analysis_tab()
        
        # Kapatma butonu
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_general_info_tab(self):
        """Genel bilgiler tab'ı"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Text widget'lar oluştur
        self.file_name_label = QLabel()
        self.file_path_label = QLabel()
        self.file_size_label = QLabel()
        self.file_type_label = QLabel()
        self.import_time_label = QLabel()
        self.import_success_label = QLabel()
        
        layout.addRow("Dosya Adı:", self.file_name_label)
        layout.addRow("Dosya Yolu:", self.file_path_label)
        layout.addRow("Dosya Boyutu:", self.file_size_label)
        layout.addRow("Dosya Tipi:", self.file_type_label)
        layout.addRow("İçe Aktarma Zamanı:", self.import_time_label)
        layout.addRow("İçe Aktarma Durumu:", self.import_success_label)
        
        self.tab_widget.addTab(tab, "Genel")
    
    def _create_geometry_tab(self):
        """Geometri bilgileri tab'ı"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        
        # Geometri bilgisi widget'ları
        self.topology_labels = {}
        self.properties_labels = {}
        self.bbox_labels = {}
        
        # Topology grubu
        topology_group = QGroupBox("Topology")
        topology_layout = QFormLayout(topology_group)
        
        topology_items = ["num_solids", "num_faces", "num_edges", "num_vertices"]
        for item in topology_items:
            label = QLabel()
            self.topology_labels[item] = label
            topology_layout.addRow(f"{item}:", label)
        
        scroll_layout.addRow(topology_group)
        
        # Properties grubu
        properties_group = QGroupBox("Özellikler")
        props_layout = QFormLayout(properties_group)
        
        props_items = ["volume", "surface_area", "center_of_mass"]
        for item in props_items:
            label = QLabel()
            self.properties_labels[item] = label
            props_layout.addRow(f"{item}:", label)
        
        scroll_layout.addRow(properties_group)
        
        # Bounding box grubu
        bbox_group = QGroupBox("Bounding Box")
        bbox_layout = QFormLayout(bbox_group)
        
        bbox_items = ["width", "height", "depth", "center"]
        for item in bbox_items:
            label = QLabel()
            self.bbox_labels[item] = label
            bbox_layout.addRow(f"{item}:", label)
        
        scroll_layout.addRow(bbox_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "Geometri")
    
    def _create_analysis_tab(self):
        """Analiz sonuçları tab'ı"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        layout.addWidget(self.analysis_text)
        
        self.tab_widget.addTab(tab, "Analiz")
    
    def _populate_data(self):
        """Verileri doldur"""
        try:
            metadata = self.shape_data.get("metadata", {})
            analysis = self.shape_data.get("analysis", {})
            
            # Genel bilgiler
            self.file_name_label.setText(metadata.get("file_name", "Bilinmeyen"))
            self.file_path_label.setText(metadata.get("file_path", "Bilinmeyen"))
            
            file_size_mb = metadata.get("file_size_mb", 0)
            self.file_size_label.setText(f"{file_size_mb:.2f} MB")
            
            self.file_type_label.setText(metadata.get("file_extension", "").upper())
            self.import_time_label.setText(metadata.get("import_time", "Bilinmeyen"))
            
            success = metadata.get("import_successful", False)
            self.import_success_label.setText("✓ Başarılı" if success else "✗ Başarısız")
            
            # Geometri bilgileri
            basic_geom = analysis.get("basic_geometry", {})
            topology = basic_geom.get("topology", {})
            
            for item, label in self.topology_labels.items():
                value = topology.get(item, 0)
                label.setText(str(value))
            
            properties = basic_geom.get("properties", {})
            for item, label in self.properties_labels.items():
                if item == "center_of_mass" and item in properties:
                    center = properties[item]
                    if isinstance(center, (list, tuple)) and len(center) >= 3:
                        label.setText(f"({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")
                    else:
                        label.setText("N/A")
                else:
                    value = properties.get(item, 0)
                    if isinstance(value, float):
                        label.setText(f"{value:.2f}")
                    else:
                        label.setText(str(value))
            
            bbox = basic_geom.get("bounding_box", {})
            for item, label in self.bbox_labels.items():
                if item == "center" and item in bbox:
                    center = bbox[item]
                    if isinstance(center, (list, tuple)) and len(center) >= 3:
                        label.setText(f"({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")
                    else:
                        label.setText("N/A")
                else:
                    value = bbox.get(item, 0)
                    if isinstance(value, float):
                        label.setText(f"{value:.2f}")
                    else:
                        label.setText(str(value))
            
            # Analiz raporu
            from import_manager.geometry_analyzer import GeometryAnalyzer
            analyzer = GeometryAnalyzer()
            report = analyzer.generate_analysis_report(analysis)
            self.analysis_text.setPlainText(report)
            
        except Exception as e:
            logging.error(f"Veri doldurma hatası: {e}")

class ProgressDialog(QDialog):
    """İşlem progress dialog'u"""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(300, 100)
        
        layout = QVBoxLayout(self)
        
        # Mesaj
        self.message_label = QLabel(message)
        layout.addWidget(self.message_label)
        
        # Progress bar - QtWidgets'tan import edildi
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        # Cancel butonu
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def set_progress(self, value: int, maximum: int = 100):
        """Progress değerini ayarla"""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)
    
    def set_message(self, message: str):
        """Mesajı güncelle"""
        self.message_label.setText(message)

class LogViewerDialog(QDialog):
    """Log görüntüleyici dialog'u"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Log Görüntüleyici")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Log listesi
        self.log_list = QListWidget()
        layout.addWidget(self.log_list)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self._refresh_logs)
        btn_layout.addWidget(refresh_btn)
        
        clear_btn = QPushButton("Temizle")
        clear_btn.clicked.connect(self._clear_logs)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self._refresh_logs()
    
    def _refresh_logs(self):
        """Log'ları yenile"""
        # Bu implementation log dosyasından okuyabilir
        # Şimdilik basit bir örnek
        sample_logs = [
            "[INFO] Uygulama başlatıldı",
            "[DEBUG] Viewer oluşturuldu", 
            "[INFO] Dosya yüklendi: example.step",
            "[WARNING] Geometri healing uygulandı",
            "[ERROR] Montaj başarısız: uygun bağlantı bulunamadı"
        ]
        
        self.log_list.clear()
        for log_entry in sample_logs:
            self.log_list.addItem(log_entry)
    
    def _clear_logs(self):
        """Log'ları temizle"""
        self.log_list.clear()