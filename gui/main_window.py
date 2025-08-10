"""
Ana GUI Penceresi
PyQt5 tabanlı ana kullanıcı arayüzü
"""

import logging
import os
from typing import Dict, Any, Optional, List
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit, QLabel,
    QProgressBar, QStatusBar, QMenuBar, QMenu, QAction, QFileDialog,
    QMessageBox, QApplication, QDockWidget, QGroupBox, QFormLayout,
    QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QSlider, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap, QFont, QKeySequence

from .toolbar import MainToolbar
from .dialogs import SettingsDialog, AboutDialog, FileInfoDialog
from .widgets import PropertyPanel, LogWidget, ProgressWidget

from engine_3d import CADViewer, create_viewer
from import_manager import import_cad_file, get_supported_formats
from montaj import AssemblyEngine, create_assembly_engine
from utils import Config, CADLogger, APP_NAME, APP_VERSION, GUIDefaults, Shortcuts

class ImportWorker(QThread):
    """Dosya import işlemi için worker thread"""
    
    import_finished = pyqtSignal(object, dict, dict)  # shape, metadata, analysis
    import_progress = pyqtSignal(int)  # progress percentage
    import_error = pyqtSignal(str)  # error message
    
    def __init__(self, file_path: str, config: Config):
        super().__init__()
        self.file_path = file_path
        self.config = config
        
    def run(self):
        try:
            self.import_progress.emit(10)
            
            # Import işlemi
            shape, metadata, analysis = import_cad_file(self.file_path, self.config)
            
            self.import_progress.emit(100)
            
            if shape is not None:
                self.import_finished.emit(shape, metadata, analysis)
            else:
                error_msg = metadata.get("error", "Bilinmeyen import hatası")
                self.import_error.emit(error_msg)
                
        except Exception as e:
            self.import_error.emit(str(e))

class MainWindow(QMainWindow):
    """Ana uygulama penceresi"""
    
    def __init__(self, config: Config, logger: CADLogger):
        super().__init__()
        
        self.config = config
        self.logger = logger
        
        # Uygulama durumu
        self.current_shapes = {}  # shape_id -> shape_data
        self.selected_shapes = set()
        self.assembly_engine = None
        self.import_worker = None
        
        # UI bileşenleri
        self.viewer = None
        self.toolbar = None
        self.status_bar = None
        self.dock_widgets = {}
        
        # Setup UI
        self._setup_ui()
        self._setup_connections()
        self._apply_config()
        
        self.logger.info("Ana pencere oluşturuldu")
    
    def _setup_ui(self):
        """Kullanıcı arayüzünü kur"""
        try:
            # Pencere ayarları
            self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
            self.setMinimumSize(GUIDefaults.MIN_WINDOW_WIDTH, GUIDefaults.MIN_WINDOW_HEIGHT)
            
            # Ana widget ve layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Ana splitter (yatay)
            main_splitter = QSplitter(Qt.Horizontal)
            central_layout = QVBoxLayout(central_widget)
            central_layout.addWidget(main_splitter)
            
            # 3D Viewer oluştur
            self.viewer = create_viewer(self, self.config)
            self.viewer.setMinimumSize(600, 400)  # Minimum 600x400
            main_splitter.addWidget(self.viewer)
            
            # Sağ panel (properties + tree)
            right_panel = self._create_right_panel()
            main_splitter.addWidget(right_panel)
            
            # Splitter oranları
            main_splitter.setStretchFactor(0, 3)  # Viewer 3 birim
            main_splitter.setStretchFactor(1, 1)  # Panel 1 birim
            main_splitter.setSizes([800, 200])    # İlk boyutlar
            
            # Toolbar oluştur
            self.toolbar = MainToolbar(self)
            self.addToolBar(self.toolbar)
            
            # Menu bar oluştur
            self._setup_menu_bar()
            
            # Status bar oluştur
            self._setup_status_bar()
            
            # Dock widgets oluştur
            self._setup_dock_widgets()
            
            # Varsayılan pencere boyutu
            default_size = self.config.get("gui.window_width", GUIDefaults.DEFAULT_WINDOW_WIDTH)
            default_height = self.config.get("gui.window_height", GUIDefaults.DEFAULT_WINDOW_HEIGHT)
            self.resize(default_size, default_height)
            
            self.logger.debug("UI kurulumu tamamlandı")
            
        except Exception as e:
            self.logger.error(f"UI kurulum hatası: {e}")
            raise
    
    def _create_right_panel(self) -> QWidget:
        """Sağ paneli oluştur"""
        panel = QWidget()
        panel.setMinimumWidth(250)  # Minimum genişlik
        layout = QVBoxLayout(panel)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Model ağacı tab'ı
        self.model_tree = self._create_model_tree()
        tab_widget.addTab(self.model_tree, "Model Ağacı")
        
        # Özellikler tab'ı
        self.property_panel = PropertyPanel()
        tab_widget.addTab(self.property_panel, "Özellikler")
        
        # Montaj tab'ı
        self.assembly_panel = self._create_assembly_panel()
        tab_widget.addTab(self.assembly_panel, "Montaj")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def _create_model_tree(self) -> QTreeWidget:
        """Model ağacı widget'ını oluştur"""
        tree = QTreeWidget()
        tree.setHeaderLabels(["Model", "Tür", "Durum"])
        tree.setAlternatingRowColors(True)
        tree.setRootIsDecorated(True)
        
        # Context menu için
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        
        return tree
    
    def _create_assembly_panel(self) -> QWidget:
        """Montaj panelini oluştur"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Montaj kontrolleri
        controls_group = QGroupBox("Montaj Kontrolleri")
        controls_layout = QFormLayout(controls_group)
        
        # Ana parça seçimi
        self.base_part_combo = QComboBox()
        self.base_part_combo.setToolTip("Ana parça seçin")
        controls_layout.addRow("Ana Parça:", self.base_part_combo)
        
        # Eklenecek parça seçimi
        self.attach_part_combo = QComboBox()
        self.attach_part_combo.setToolTip("Eklenecek parça seçin")
        controls_layout.addRow("Eklenecek Parça:", self.attach_part_combo)
        
        # Tolerans ayarı
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setRange(0.001, 10.0)
        self.tolerance_spin.setValue(0.01)
        self.tolerance_spin.setSuffix(" mm")
        self.tolerance_spin.setToolTip("Montaj toleransı")
        controls_layout.addRow("Tolerans:", self.tolerance_spin)
        
        # Montaj butonu
        self.assembly_button = QPushButton("Montaj Yap")
        self.assembly_button.setToolTip("Seçili parçaları montajla")
        controls_layout.addRow(self.assembly_button)
        
        layout.addWidget(controls_group)
        
        # Montaj sonuçları
        results_group = QGroupBox("Montaj Sonuçları")
        results_layout = QVBoxLayout(results_group)
        
        self.assembly_results = QTextEdit()
        self.assembly_results.setMaximumHeight(150)
        self.assembly_results.setReadOnly(True)
        results_layout.addWidget(self.assembly_results)
        
        layout.addWidget(results_group)
        layout.addStretch()
        
        return panel
    
    def _setup_menu_bar(self):
        """Menu bar'ı kur"""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu("Dosya")
        
        # Dosya aç
        open_action = QAction("Aç...", self)
        open_action.setShortcut(QKeySequence(Shortcuts.OPEN))
        open_action.setToolTip("CAD dosyası aç")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # Son dosyalar
        recent_menu = file_menu.addMenu("Son Dosyalar")
        self._update_recent_files_menu(recent_menu)
        
        file_menu.addSeparator()
        
        # Kaydet
        save_action = QAction("Kaydet", self)
        save_action.setShortcut(QKeySequence(Shortcuts.SAVE))
        save_action.setEnabled(False)  # Şimdilik devre dışı
        file_menu.addAction(save_action)
        
        # Farklı kaydet
        save_as_action = QAction("Farklı Kaydet...", self)
        save_as_action.setShortcut(QKeySequence(Shortcuts.SAVE_AS))
        save_as_action.setEnabled(False)  # Şimdilik devre dışı
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Çıkış
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut(QKeySequence(Shortcuts.EXIT))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Görünüm menüsü
        view_menu = menubar.addMenu("Görünüm")
        
        # Fit All
        fit_all_action = QAction("Hepsini Sığdır", self)
        fit_all_action.setShortcut(QKeySequence(Shortcuts.FIT_ALL))
        fit_all_action.triggered.connect(self.fit_all)
        view_menu.addAction(fit_all_action)
        
        view_menu.addSeparator()
        
        # Görünüm yönleri
        view_directions = [
            ("Önden", "front"),
            ("Arkadan", "back"),
            ("Soldan", "left"),
            ("Sağdan", "right"),
            ("Üstten", "top"),
            ("Alttan", "bottom"),
            ("İzometrik", "isometric")
        ]
        
        for name, direction in view_directions:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, d=direction: self.set_view_direction(d))
            view_menu.addAction(action)
        
        # Montaj menüsü
        assembly_menu = menubar.addMenu("Montaj")
        
        assembly_action = QAction("Montaj Yap", self)
        assembly_action.setShortcut(QKeySequence(Shortcuts.START_ASSEMBLY))
        assembly_action.triggered.connect(self.start_assembly)
        assembly_menu.addAction(assembly_action)
        
        collision_action = QAction("Çakışma Kontrolü", self)
        collision_action.setShortcut(QKeySequence(Shortcuts.CHECK_COLLISION))
        collision_action.triggered.connect(self.check_collisions)
        assembly_menu.addAction(collision_action)
        
        # Araçlar menüsü
        tools_menu = menubar.addMenu("Araçlar")
        
        settings_action = QAction("Ayarlar...", self)
        settings_action.setShortcut(QKeySequence(Shortcuts.SETTINGS))
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu("Yardım")
        
        help_action = QAction("Yardım", self)
        help_action.setShortcut(QKeySequence(Shortcuts.HELP))
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("Hakkında...", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Status bar'ı kur"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Sol taraf - genel mesajlar
        self.status_label = QLabel("Hazır")
        self.status_bar.addWidget(self.status_label)
        
        # Ortada - progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Sağ taraf - shape sayısı
        self.shape_count_label = QLabel("Parça: 0")
        self.status_bar.addPermanentWidget(self.shape_count_label)
    
    def _setup_dock_widgets(self):
        """Dock widget'ları kur"""
        # Log widget
        log_dock = QDockWidget("Log", self)
        self.log_widget = LogWidget()
        log_dock.setWidget(self.log_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, log_dock)
        self.dock_widgets["log"] = log_dock
        
        # İlk başta gizli
        log_dock.hide()
    
    def _setup_connections(self):
        """Signal/slot bağlantılarını kur"""
        try:
            # Viewer sinyalleri
            if self.viewer:
                self.viewer.shape_selected.connect(self._on_shape_selected)
                self.viewer.shape_deselected.connect(self._on_shape_deselected)
                self.viewer.viewer_initialized.connect(self._on_viewer_ready)
            
            # *** TOOLBAR SİNYALLERİNİ BAĞLA ***
            if self.toolbar:
                # Dosya işlemleri
                self.toolbar.file_open_requested.connect(self.open_file)
                self.toolbar.file_save_requested.connect(self._on_save_requested)
                
                # Görünüm işlemleri
                self.toolbar.view_direction_changed.connect(self.set_view_direction)
                self.toolbar.display_mode_changed.connect(self._on_display_mode_changed)
                
                # Montaj işlemleri
                self.toolbar.assembly_start_requested.connect(self.start_assembly)
                self.toolbar.collision_check_requested.connect(self.check_collisions)
                
                self.logger.info("Toolbar sinyalleri bağlandı")
            
            # Model tree
            if hasattr(self, 'model_tree'):
                self.model_tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
            
            # Montaj kontrolleri
            if hasattr(self, 'assembly_button'):
                self.assembly_button.clicked.connect(self.start_assembly)
            
            # Combo box değişiklikleri
            if hasattr(self, 'base_part_combo'):
                self.base_part_combo.currentTextChanged.connect(self._on_base_part_changed)
            if hasattr(self, 'attach_part_combo'):
                self.attach_part_combo.currentTextChanged.connect(self._on_attach_part_changed)
            
            self.logger.debug("Signal/slot bağlantıları kuruldu")
            
        except Exception as e:
            self.logger.error(f"Bağlantı kurulum hatası: {e}")

    # YENİ SLOT FONKSİYONLARI EKLE
    @pyqtSlot()
    def _on_save_requested(self):
        """Kaydet butonu tıklandığında"""
        self.logger.info("Kaydet işlemi başlatıldı")
        # TODO: Save implementation

    @pyqtSlot(str)
    def _on_display_mode_changed(self, mode: str):
        """Display mode değiştiğinde"""
        self.logger.info(f"Display mode değiştirildi: {mode}")
        
        try:
            if not self.viewer or not hasattr(self.viewer, '_context'):
                return
            
            # Mode'a göre display mode ayarla
            display_mode = 1  # Shaded
            if mode.lower() == "wireframe":
                display_mode = 0  # Wireframe
            elif mode.lower() == "hidden line":
                display_mode = 2  # Hidden line (eğer destekleniyorsa)
            
            # Tüm shape'lerin display mode'unu değiştir
            for shape_id, shape_data in self.current_shapes.items():
                try:
                    ais_shape = shape_data.get("ais_shape")
                    if ais_shape:
                        self.viewer._context.SetDisplayMode(ais_shape, display_mode, True)
                except Exception as e:
                    self.logger.warning(f"Shape {shape_id} display mode hatası: {e}")
            
            # Viewer'ı güncelle
            self.viewer._context.UpdateCurrentViewer()
            self.logger.info(f"Display mode güncellendi: {mode}")
            
        except Exception as e:
            self.logger.error(f"Display mode değiştirme hatası: {e}")
            
         
    def _apply_config(self):
        """Konfigürasyonu uygula"""
        try:
            # Pencere boyutu
            if self.config.get("gui.window_maximized", False):
                self.showMaximized()
            
            # Theme (şimdilik basit)
            theme = self.config.get("gui.theme", "light")
            if theme == "dark":
                self.setStyleSheet("QMainWindow { background-color: #2b2b2b; color: white; }")
            
            self.logger.debug("Konfigürasyon uygulandı")
            
        except Exception as e:
            self.logger.warning(f"Konfigürasyon uygulama hatası: {e}")
    
    def _update_recent_files_menu(self, menu: QMenu):
        """Son dosyalar menüsünü güncelle"""
        menu.clear()
        
        recent_files = self.config.get_recent_files()
        
        if not recent_files:
            no_files_action = QAction("Son dosya yok", self)
            no_files_action.setEnabled(False)
            menu.addAction(no_files_action)
            return
        
        for file_path in recent_files[:10]:  # Son 10 dosya
            if os.path.exists(file_path):
                file_name = os.path.basename(file_path)
                action = QAction(file_name, self)
                action.setToolTip(file_path)
                action.triggered.connect(lambda checked, path=file_path: self.open_file(path))
                menu.addAction(action)
    
    # Slot fonksiyonları
    @pyqtSlot()
    def open_file(self, file_path: str = None):
        """Dosya aç"""
        try:
            if not file_path:
                supported_formats = get_supported_formats()
                filter_text = "CAD Dosyaları (*" + " *".join(supported_formats) + ")"
                
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "CAD Dosyası Aç",
                    self.config.get("import.default_directory", ""),
                    filter_text
                )
            
            if not file_path:
                return
            
            self.logger.info(f"Dosya açılıyor: {file_path}")
            
            # Progress göster
            self._show_progress("Dosya yükleniyor...", True)
            
            # Worker thread'de import yap
            self.import_worker = ImportWorker(file_path, self.config)
            self.import_worker.import_finished.connect(self._on_import_finished)
            self.import_worker.import_progress.connect(self._update_progress)
            self.import_worker.import_error.connect(self._on_import_error)
            self.import_worker.start()
            
        except Exception as e:
            self.logger.error(f"Dosya açma hatası: {e}")
            self._show_error("Dosya açma hatası", str(e))
            self._hide_progress()
    
    @pyqtSlot(object, dict, dict)
    def _on_import_finished(self, shape, metadata, analysis):
        """Import tamamlandığında"""
        try:
            self._hide_progress()
            
            # Shape'i viewer'a ekle
            shape_id = self.viewer.add_shape(shape)
            
            if shape_id:
                # Shape verilerini sakla
                self.current_shapes[shape_id] = {
                    "shape": shape,
                    "metadata": metadata,
                    "analysis": analysis,
                    "file_path": metadata.get("file_path", "")
                }
                
                # Model ağacına ekle
                self._add_shape_to_tree(shape_id, metadata)
                
                # Combo box'ları güncelle
                self._update_assembly_combos()
                
                # Viewer'da fit all
                self.viewer.fit_all()
                
                # Son dosyalar listesine ekle
                file_path = metadata.get("file_path")
                if file_path:
                    self.config.add_recent_file(file_path)
                
                # Status güncelle
                self._update_status()
                
                self.logger.info(f"Dosya başarıyla yüklendi: {file_path}")
                self.status_label.setText(f"Dosya yüklendi: {os.path.basename(file_path)}")
                
            else:
                self._show_error("Import Hatası", "Shape viewer'a eklenemedi")
                
        except Exception as e:
            self.logger.error(f"Import sonucu işleme hatası: {e}")
            self._show_error("Import Hatası", str(e))
    
    @pyqtSlot(str)
    def _on_import_error(self, error_message: str):
        """Import hatası"""
        self._hide_progress()
        self.logger.error(f"Import hatası: {error_message}")
        self._show_error("Import Hatası", error_message)
    
    @pyqtSlot(int)
    def _update_progress(self, value: int):
        """Progress güncelle"""
        self.progress_bar.setValue(value)
    
    @pyqtSlot(object)
    def _on_shape_selected(self, shape):
        """Shape seçildiğinde"""
        self.logger.debug(f"Shape seçildi: {shape}")
        # Property panel'i güncelle
        # self.property_panel.update_properties(shape)
    
    @pyqtSlot()
    def _on_shape_deselected(self):
        """Shape seçimi kaldırıldığında"""
        self.logger.debug("Shape seçimi kaldırıldı")
        # self.property_panel.clear_properties()
    
    @pyqtSlot()
    def _on_viewer_ready(self):
        """Viewer hazır olduğunda"""
        self.logger.info("3D Viewer hazır")
        
        # Assembly engine'i başlat
        self.assembly_engine = create_assembly_engine(self.config)
        
        self.status_label.setText("Hazır - Dosya açmak için Ctrl+O")
    
    @pyqtSlot()
    def _on_tree_selection_changed(self):
        """Model ağacı seçimi değiştiğinde"""
        selected_items = self.model_tree.selectedItems()
        
        if selected_items:
            item = selected_items[0]
            shape_id = item.data(0, Qt.UserRole)
            
            if shape_id and shape_id in self.current_shapes:
                # Viewer'da seç
                self.viewer.select_shape(shape_id)
                
                # Property panel güncelle
                shape_data = self.current_shapes[shape_id]
                self.property_panel.update_properties(shape_data)
    
    def _add_shape_to_tree(self, shape_id: str, metadata: Dict[str, Any]):
        """Shape'i model ağacına ekle"""
        try:
            file_name = os.path.basename(metadata.get("file_path", "Bilinmeyen"))
            
            item = QTreeWidgetItem(self.model_tree)
            item.setText(0, file_name)
            item.setText(1, metadata.get("file_extension", "").upper())
            item.setText(2, "Yüklendi")
            item.setData(0, Qt.UserRole, shape_id)
            
            # Analiz varsa alt öğeler ekle
            analysis = self.current_shapes[shape_id].get("analysis", {})
            basic_geom = analysis.get("basic_geometry", {})
            
            if basic_geom:
                topology = basic_geom.get("topology", {})
                
                # Topology bilgileri
                topo_item = QTreeWidgetItem(item)
                topo_item.setText(0, "Topology")
                
                for key, value in topology.items():
                    if isinstance(value, int) and value > 0:
                        child_item = QTreeWidgetItem(topo_item)
                        child_item.setText(0, f"{key}: {value}")
            
            self.model_tree.expandAll()
            
        except Exception as e:
            self.logger.warning(f"Model ağacına ekleme hatası: {e}")
    
    def _update_assembly_combos(self):
        """Montaj combo box'larını güncelle"""
        try:
            self.base_part_combo.clear()
            self.attach_part_combo.clear()
            
            for shape_id, shape_data in self.current_shapes.items():
                file_name = os.path.basename(shape_data["metadata"].get("file_path", f"Shape {shape_id}"))
                
                self.base_part_combo.addItem(file_name, shape_id)
                self.attach_part_combo.addItem(file_name, shape_id)
                
        except Exception as e:
            self.logger.warning(f"Assembly combo güncelleme hatası: {e}")
    
    def _update_status(self):
        """Status bar'ı güncelle"""
        shape_count = len(self.current_shapes)
        self.shape_count_label.setText(f"Parça: {shape_count}")
    
    def _show_progress(self, message: str, indeterminate: bool = False):
        """Progress göster"""
        self.progress_bar.setVisible(True)
        if indeterminate:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
        
        self.status_label.setText(message)
    
    def _hide_progress(self):
        """Progress gizle"""
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
    
    def _show_error(self, title: str, message: str):
        """Hata mesajı göster"""
        QMessageBox.critical(self, title, message)
    
    def _show_info(self, title: str, message: str):
        """Bilgi mesajı göster"""
        QMessageBox.information(self, title, message)
    
    # Toolbar ve menu fonksiyonları
    def fit_all(self):
        """Tüm nesneleri sığdır"""
        if self.viewer:
            self.viewer.fit_all()
    
    def set_view_direction(self, direction: str):
        """Görünüm yönü ayarla"""
        if self.viewer:
            self.viewer.set_view_direction(direction)
    
    def start_assembly(self):
        """Montaj işlemini başlat"""
        try:
            if not self.assembly_engine:
                self._show_error("Montaj Hatası", "Montaj motoru hazır değil")
                return
            
            # Seçili parçaları al
            base_shape_id = self.base_part_combo.currentData()
            attach_shape_id = self.attach_part_combo.currentData()
            
            if not base_shape_id or not attach_shape_id:
                self._show_error("Montaj Hatası", "Ana parça ve eklenecek parçayı seçin")
                return
            
            if base_shape_id == attach_shape_id:
                self._show_error("Montaj Hatası", "Aynı parçayı seçemezsiniz")
                return
            
            base_shape = self.current_shapes[base_shape_id]["shape"]
            attach_shape = self.current_shapes[attach_shape_id]["shape"]
            
            # Tolerans al
            tolerance = self.tolerance_spin.value()
            
            self.logger.info(f"Montaj başlatılıyor: {base_shape_id} + {attach_shape_id}")
            
            # Progress göster
            self._show_progress("Montaj işlemi yapılıyor...", True)
            
            # Montaj yap (şimdilik basit)
            result = self.assembly_engine.perform_assembly(base_shape, attach_shape)
            
            self._hide_progress()
            
            if result:
                # Başarılı montaj
                self.assembly_results.append("✓ Montaj başarılı!")
                self.assembly_results.append(f"Ana parça: {self.base_part_combo.currentText()}")
                self.assembly_results.append(f"Eklenen parça: {self.attach_part_combo.currentText()}")
                self.assembly_results.append(f"Tolerans: {tolerance} mm")
                self.assembly_results.append("-" * 40)
                
                # Sonuç shape'i viewer'a ekle
                result_id = self.viewer.add_shape(result, color=(0.2, 0.8, 0.2))
                if result_id:
                    self.current_shapes[result_id] = {
                        "shape": result,
                        "metadata": {"type": "assembly_result"},
                        "analysis": {},
                        "file_path": ""
                    }
                
                self._update_status()
                self.logger.info("Montaj başarılı")
                
            else:
                self.assembly_results.append("✗ Montaj başarısız!")
                self.assembly_results.append("Uygun bağlantı noktası bulunamadı.")
                self.assembly_results.append("-" * 40)
                self.logger.warning("Montaj başarısız")
                
        except Exception as e:
            self._hide_progress()
            error_msg = f"Montaj hatası: {str(e)}"
            self.logger.error(error_msg)
            self._show_error("Montaj Hatası", error_msg)
            self.assembly_results.append(f"✗ Hata: {str(e)}")
    
    def check_collisions(self):
        """Çakışma kontrolü yap"""
        try:
            if not self.assembly_engine:
                self._show_error("Çakışma Kontrolü", "Montaj motoru hazır değil")
                return
            
            if len(self.current_shapes) < 2:
                self._show_info("Çakışma Kontrolü", "En az 2 parça gerekli")
                return
            
            self.logger.info("Çakışma kontrolü başlatılıyor")
            
            shapes = list(self.current_shapes.values())
            collision_count = 0
            
            # Tüm shape çiftlerini kontrol et
            for i in range(len(shapes)):
                for j in range(i + 1, len(shapes)):
                    shape1 = shapes[i]["shape"]
                    shape2 = shapes[j]["shape"]
                    
                    if self.assembly_engine.collision_detector.check_collision(shape1, shape2):
                        collision_count += 1
            
            if collision_count > 0:
                self._show_info("Çakışma Kontrolü", f"{collision_count} çakışma tespit edildi!")
            else:
                self._show_info("Çakışma Kontrolü", "Çakışma tespit edilmedi")
            
            self.logger.info(f"Çakışma kontrolü tamamlandı: {collision_count} çakışma")
            
        except Exception as e:
            error_msg = f"Çakışma kontrolü hatası: {str(e)}"
            self.logger.error(error_msg)
            self._show_error("Çakışma Kontrolü Hatası", error_msg)
    
    @pyqtSlot()
    def show_settings(self):
        """Ayarlar dialog'unu göster"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_() == dialog.Accepted:
            # Ayarlar değiştiyse konfigürasyonu yenile
            self._apply_config()
    
    @pyqtSlot()
    def show_about(self):
        """Hakkında dialog'unu göster"""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    @pyqtSlot()
    def show_help(self):
        """Yardım göster"""
        help_text = f"""
{APP_NAME} v{APP_VERSION}

Klavye Kısayolları:
• Ctrl+O: Dosya aç
• Ctrl+S: Kaydet
• F: Hepsini sığdır
• Ctrl+A: Montaj yap
• Ctrl+C: Çakışma kontrolü

Mouse Kontrolleri:
• Sol tık + sürükle: Döndür
• Orta tık + sürükle: Kaydır
• Mouse wheel: Yakınlaştır/Uzaklaştır
"""
        self._show_info("Yardım", help_text)
    
    def _show_tree_context_menu(self, position):
        """Model ağacı context menu"""
        item = self.model_tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # Bilgileri göster
        info_action = QAction("Bilgileri Göster", self)
        info_action.triggered.connect(lambda: self._show_shape_info(item))
        menu.addAction(info_action)
        
        # Kaldır
        remove_action = QAction("Kaldır", self)
        remove_action.triggered.connect(lambda: self._remove_shape(item))
        menu.addAction(remove_action)
        
        menu.exec_(self.model_tree.mapToGlobal(position))
    
    def _show_shape_info(self, item: QTreeWidgetItem):
        """Shape bilgilerini göster"""
        shape_id = item.data(0, Qt.UserRole)
        if shape_id and shape_id in self.current_shapes:
            shape_data = self.current_shapes[shape_id]
            dialog = FileInfoDialog(shape_data, self)
            dialog.exec_()
    
    def _remove_shape(self, item: QTreeWidgetItem):
        """Shape'i kaldır"""
        shape_id = item.data(0, Qt.UserRole)
        if shape_id and shape_id in self.current_shapes:
            # Viewer'dan kaldır
            self.viewer.remove_shape(shape_id)
            
            # Data'dan kaldır
            del self.current_shapes[shape_id]
            
            # Tree'den kaldır
            self.model_tree.takeTopLevelItem(self.model_tree.indexOfTopLevelItem(item))
            
            # Combo'ları güncelle
            self._update_assembly_combos()
            self._update_status()
            
            self.logger.info(f"Shape kaldırıldı: {shape_id}")
    
    def _on_base_part_changed(self):
        """Ana parça değiştiğinde"""
        # Attach combo'da aynı parçayı seçemeyecek şekilde güncelle
        pass
    
    def _on_attach_part_changed(self):
        """Eklenecek parça değiştiğinde"""
        pass
    
    # Pencere kapanırken
    def closeEvent(self, event):
        """Pencere kapatılırken"""
        try:
            # Konfigürasyonu kaydet
            self.config.set("gui.window_maximized", self.isMaximized())
            if not self.isMaximized():
                self.config.set("gui.window_width", self.width())
                self.config.set("gui.window_height", self.height())
            
            self.config.save()
            
            # Cleanup
            self.cleanup()
            
            self.logger.info("Uygulama kapatılıyor")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Kapatma hatası: {e}")
            event.accept()
    
    def cleanup(self):
        """Temizlik işlemleri"""
        try:
            # Worker thread'i durdur
            if self.import_worker and self.import_worker.isRunning():
                self.import_worker.terminate()
                self.import_worker.wait(3000)
            
            # Viewer temizle
            if self.viewer:
                self.viewer.cleanup()
            
            self.logger.info("Temizlik tamamlandı")
            
        except Exception as e:
            self.logger.error(f"Temizlik hatası: {e}")