"""
Toolbar ve Menü Bileşenleri
Ana toolbar ve özel menü widget'ları
"""

import logging,os
from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import (
    QToolBar, QAction, QToolButton, QMenu, QActionGroup,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox,
    QSlider, QSpinBox, QCheckBox, QPushButton, QSeparator,
    QButtonGroup, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence

from utils.constants import GUIDefaults, Shortcuts, Icons

class MainToolbar(QToolBar):
    """Ana toolbar sınıfı"""
    
    # Sinyaller
    file_open_requested = pyqtSignal()
    file_save_requested = pyqtSignal()
    assembly_start_requested = pyqtSignal()
    collision_check_requested = pyqtSignal()
    view_direction_changed = pyqtSignal(str)
    display_mode_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__("Ana Toolbar", parent)
        
        self.parent_window = parent
        self.logger = logging.getLogger("CADMontaj.Toolbar")
        
        self.actions = {}
        self.widgets = {}
        
        self._setup_toolbar()
        self.logger.debug("Ana toolbar oluşturuldu")
    
    def _setup_toolbar(self):
        """Toolbar'ı kur"""
        try:
            # Toolbar ayarları
            self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            self.setMovable(True)
            self.setFloatable(False)
            
            # İkon boyutu
            icon_size = GUIDefaults.TOOLBAR_ICON_SIZE
            self.setIconSize(QSize(icon_size, icon_size))
            
            # Dosya işlemleri grubu
            self._add_file_actions()
            self.addSeparator()
            
            # Görünüm işlemleri grubu
            self._add_view_actions()
            self.addSeparator()
            
            # Montaj işlemleri grubu
            self._add_assembly_actions()
            self.addSeparator()
            
            # Görüntüleme kontrolleri
            self._add_display_controls()
            
            # Sağa yaslı spacer
            spacer = QWidget()
            spacer.setSizePolicy(spacer.sizePolicy().Expanding, spacer.sizePolicy().Preferred)
            self.addWidget(spacer)
            
            # Yardım
            self._add_help_actions()
            
        except Exception as e:
            self.logger.error(f"Toolbar kurulum hatası: {e}")
    
    def _add_file_actions(self):
        """Dosya işlemleri action'larını ekle"""
        # Dosya aç
        open_action = QAction("Aç", self)
        open_action.setShortcut(QKeySequence(Shortcuts.OPEN))
        open_action.setToolTip("CAD dosyası aç (Ctrl+O)")
        open_action.triggered.connect(self.file_open_requested.emit)
        self._try_set_icon(open_action, Icons.OPEN)
        
        self.addAction(open_action)
        self.actions["open"] = open_action
        
        # Kaydet
        save_action = QAction("Kaydet", self)
        save_action.setShortcut(QKeySequence(Shortcuts.SAVE))
        save_action.setToolTip("Montajı kaydet (Ctrl+S)")
        save_action.setEnabled(False)  # Şimdilik kapalı
        save_action.triggered.connect(self.file_save_requested.emit)
        self._try_set_icon(save_action, Icons.SAVE)
        
        self.addAction(save_action)
        self.actions["save"] = save_action
    
    def _add_view_actions(self):
        """Görünüm işlemleri action'larını ekle"""
        # Fit All
        fit_all_action = QAction("Hepsini Sığdır", self)
        fit_all_action.setShortcut(QKeySequence(Shortcuts.FIT_ALL))
        fit_all_action.setToolTip("Tüm parçaları görüntüde sığdır (F)")
        fit_all_action.triggered.connect(self._on_fit_all)
        self._try_set_icon(fit_all_action, Icons.FIT_ALL)
        
        self.addAction(fit_all_action)
        self.actions["fit_all"] = fit_all_action
        
        # Görünüm yönü seçici
        view_button = QToolButton()
        view_button.setText("Görünüm")
        view_button.setToolTip("Görünüm yönü seçin")
        view_button.setPopupMode(QToolButton.InstantPopup)
        
        view_menu = QMenu()
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
            action.triggered.connect(lambda checked, d=direction: self.view_direction_changed.emit(d))
            view_menu.addAction(action)
        
        view_button.setMenu(view_menu)
        self.addWidget(view_button)
        self.widgets["view_selector"] = view_button
        
        # Zoom kontrolleri
        zoom_in_action = QAction("Yakınlaştır", self)
        zoom_in_action.setShortcut(QKeySequence(Shortcuts.ZOOM_IN))
        zoom_in_action.setToolTip("Yakınlaştır (+)")
        zoom_in_action.triggered.connect(self._on_zoom_in)
        self._try_set_icon(zoom_in_action, Icons.ZOOM_IN)
        
        zoom_out_action = QAction("Uzaklaştır", self)
        zoom_out_action.setShortcut(QKeySequence(Shortcuts.ZOOM_OUT))
        zoom_out_action.setToolTip("Uzaklaştır (-)")
        zoom_out_action.triggered.connect(self._on_zoom_out)
        self._try_set_icon(zoom_out_action, Icons.ZOOM_OUT)
        
        self.addAction(zoom_in_action)
        self.addAction(zoom_out_action)
        self.actions["zoom_in"] = zoom_in_action
        self.actions["zoom_out"] = zoom_out_action
    
    def _add_assembly_actions(self):
        """Montaj işlemleri action'larını ekle"""
        # Montaj yap
        assembly_action = QAction("Montaj", self)
        assembly_action.setShortcut(QKeySequence(Shortcuts.START_ASSEMBLY))
        assembly_action.setToolTip("Montaj işlemini başlat (Ctrl+A)")
        assembly_action.triggered.connect(self.assembly_start_requested.emit)
        self._try_set_icon(assembly_action, Icons.ASSEMBLY)
        
        self.addAction(assembly_action)
        self.actions["assembly"] = assembly_action
        
        # Çakışma kontrolü
        collision_action = QAction("Çakışma Kontrolü", self)
        collision_action.setShortcut(QKeySequence(Shortcuts.CHECK_COLLISION))
        collision_action.setToolTip("Çakışma kontrolü yap (Ctrl+C)")
        collision_action.triggered.connect(self.collision_check_requested.emit)
        self._try_set_icon(collision_action, Icons.COLLISION_CHECK)
        
        self.addAction(collision_action)
        self.actions["collision"] = collision_action
        
        # Hizalama araçları
        align_button = QToolButton()
        align_button.setText("Hizalama")
        align_button.setToolTip("Hizalama araçları")
        align_button.setPopupMode(QToolButton.InstantPopup)
        
        align_menu = QMenu()
        align_options = [
            ("Yüzey Hizalama", "surface"),
            ("Kenar Hizalama", "edge"),
            ("Merkez Hizalama", "center")
        ]
        
        for name, align_type in align_options:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, t=align_type: self._on_alignment_requested(t))
            align_menu.addAction(action)
        
        align_button.setMenu(align_menu)
        self.addWidget(align_button)
        self.widgets["alignment"] = align_button
    
    def _add_display_controls(self):
        """Görüntüleme kontrolleri ekle"""
        # Display mode seçici
        display_mode_combo = QComboBox()
        display_mode_combo.addItems(["Shaded", "Wireframe", "Hidden Line"])
        display_mode_combo.setToolTip("Görüntüleme modunu seçin")
        display_mode_combo.currentTextChanged.connect(self.display_mode_changed.emit)
        
        self.addWidget(QLabel("Mod:"))
        self.addWidget(display_mode_combo)
        self.widgets["display_mode"] = display_mode_combo
        
        # Şeffaflık kontrolü
        transparency_slider = QSlider(Qt.Horizontal)
        transparency_slider.setRange(0, 100)
        transparency_slider.setValue(0)
        transparency_slider.setMaximumWidth(100)
        transparency_slider.setToolTip("Şeffaflık ayarı")
        transparency_slider.valueChanged.connect(self._on_transparency_changed)
        
        self.addWidget(QLabel("Şeffaflık:"))
        self.addWidget(transparency_slider)
        self.widgets["transparency"] = transparency_slider
    
    def _add_help_actions(self):
        """Yardım action'larını ekle"""
        help_action = QAction("Yardım", self)
        help_action.setShortcut(QKeySequence(Shortcuts.HELP))
        help_action.setToolTip("Yardım göster (F1)")
        help_action.triggered.connect(self._on_help)
        self._try_set_icon(help_action, Icons.HELP)
        
        self.addAction(help_action)
        self.actions["help"] = help_action
    
    def _try_set_icon(self, action: QAction, icon_name: str):
        """Icon'u ayarlamaya çalış"""
        try:
            # Icon'ları resources klasöründe arıyor olacağız
            icon_path = f"resources/icons/{icon_name}"
            if os.path.exists(icon_path):
                action.setIcon(QIcon(icon_path))
            else:
                # Varsayılan Qt icon'larını kullan
                style = self.style()
                if icon_name == Icons.OPEN:
                    action.setIcon(style.standardIcon(style.SP_DialogOpenButton))
                elif icon_name == Icons.SAVE:
                    action.setIcon(style.standardIcon(style.SP_DialogSaveButton))
                elif icon_name == Icons.HELP:
                    action.setIcon(style.standardIcon(style.SP_DialogHelpButton))
                # Diğer icon'lar için standart simgeler eklenebilir
                    
        except Exception as e:
            self.logger.debug(f"Icon ayarlama hatası: {e}")
    
    # Slot fonksiyonları
    @pyqtSlot()
    def _on_fit_all(self):
        """Fit all işlemi"""
        if hasattr(self.parent_window, 'fit_all'):
            self.parent_window.fit_all()
    
    @pyqtSlot()
    def _on_zoom_in(self):
        """Yakınlaştır"""
        # Ana pencerede zoom_in metodunu çağır
        if hasattr(self.parent_window, 'viewer') and self.parent_window.viewer:
            # Viewer'da zoom fonksiyonu yoksa, mouse wheel event simüle edebiliriz
            pass
    
    @pyqtSlot()
    def _on_zoom_out(self):
        """Uzaklaştır"""
        # Ana pencerede zoom_out metodunu çağır
        if hasattr(self.parent_window, 'viewer') and self.parent_window.viewer:
            pass
    
    @pyqtSlot(str)
    def _on_alignment_requested(self, align_type: str):
        """Hizalama isteği"""
        self.logger.info(f"Hizalama isteği: {align_type}")
        # Ana pencerede hizalama fonksiyonu çağrılabilir
    
    @pyqtSlot(int)
    def _on_transparency_changed(self, value: int):
        """Şeffaflık değişti"""
        transparency = value / 100.0
        
        if hasattr(self.parent_window, 'viewer') and self.parent_window.viewer:
            # Seçili shape'lerin şeffaflığını değiştir
            selected_shapes = self.parent_window.viewer.get_selected_shapes()
            for shape_id in selected_shapes:
                self.parent_window.viewer.set_shape_transparency(shape_id, transparency)
    
    @pyqtSlot()
    def _on_help(self):
        """Yardım göster"""
        if hasattr(self.parent_window, 'show_help'):
            self.parent_window.show_help()
    
    def update_actions_state(self, has_shapes: bool = False, has_selection: bool = False):
        """Action'ların durumunu güncelle"""
        try:
            # Dosya kaydetme - şekil varsa aktif
            if "save" in self.actions:
                self.actions["save"].setEnabled(has_shapes)
            
            # Görünüm işlemleri - şekil varsa aktif
            view_actions = ["fit_all", "zoom_in", "zoom_out"]
            for action_name in view_actions:
                if action_name in self.actions:
                    self.actions[action_name].setEnabled(has_shapes)
            
            # Montaj işlemleri - en az 2 şekil varsa aktif
            if hasattr(self.parent_window, 'current_shapes'):
                shape_count = len(self.parent_window.current_shapes)
                assembly_enabled = shape_count >= 2
                
                if "assembly" in self.actions:
                    self.actions["assembly"].setEnabled(assembly_enabled)
                if "collision" in self.actions:
                    self.actions["collision"].setEnabled(assembly_enabled)
            
            # Display kontrolleri - seçim varsa aktif
            if "transparency" in self.widgets:
                self.widgets["transparency"].setEnabled(has_selection)
                
        except Exception as e:
            self.logger.warning(f"Action state güncelleme hatası: {e}")
    
    def get_action(self, action_name: str) -> Optional[QAction]:
        """Action'ı al"""
        return self.actions.get(action_name)
    
    def get_widget(self, widget_name: str) -> Optional[QWidget]:
        """Widget'ı al"""
        return self.widgets.get(widget_name)

class ViewToolbar(QToolBar):
    """Görünüm toolbar'ı (özel görünüm kontrolleri için)"""
    
    view_mode_changed = pyqtSignal(str)
    projection_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__("Görünüm Toolbar", parent)
        
        self.logger = logging.getLogger("CADMontaj.ViewToolbar")
        self._setup_toolbar()
    
    def _setup_toolbar(self):
        """Görünüm toolbar'ını kur"""
        try:
            # Görünüm modu butonları
            view_mode_group = QButtonGroup(self)
            
            shaded_btn = QPushButton("Shaded")
            shaded_btn.setCheckable(True)
            shaded_btn.setChecked(True)
            shaded_btn.clicked.connect(lambda: self.view_mode_changed.emit("shaded"))
            
            wireframe_btn = QPushButton("Wireframe")
            wireframe_btn.setCheckable(True)
            wireframe_btn.clicked.connect(lambda: self.view_mode_changed.emit("wireframe"))
            
            hidden_line_btn = QPushButton("Hidden Line")
            hidden_line_btn.setCheckable(True)
            hidden_line_btn.clicked.connect(lambda: self.view_mode_changed.emit("hidden_line"))
            
            view_mode_group.addButton(shaded_btn, 0)
            view_mode_group.addButton(wireframe_btn, 1)
            view_mode_group.addButton(hidden_line_btn, 2)
            
            self.addWidget(shaded_btn)
            self.addWidget(wireframe_btn)
            self.addWidget(hidden_line_btn)
            
            self.addSeparator()
            
            # Projeksiyon modu
            projection_combo = QComboBox()
            projection_combo.addItems(["Perspective", "Orthogonal"])
            projection_combo.currentTextChanged.connect(self.projection_changed.emit)
            
            self.addWidget(QLabel("Projeksiyon:"))
            self.addWidget(projection_combo)
            
        except Exception as e:
            self.logger.error(f"View toolbar kurulum hatası: {e}")

class AssemblyToolbar(QToolBar):
    """Montaj toolbar'ı"""
    
    constraint_added = pyqtSignal(str, dict)
    constraint_removed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__("Montaj Toolbar", parent)
        
        self.logger = logging.getLogger("CADMontaj.AssemblyToolbar")
        self._setup_toolbar()
    
    def _setup_toolbar(self):
        """Montaj toolbar'ını kur"""
        try:
            # Kısıtlama türleri
            constraints = [
                ("Coincident", "coincident", "İki yüzeyi çakıştır"),
                ("Parallel", "parallel", "İki yüzeyi paralel yap"),
                ("Perpendicular", "perpendicular", "İki yüzeyi dik yap"),
                ("Concentric", "concentric", "İki silindiri koaksiyel yap"),
                ("Distance", "distance", "Sabit mesafe kısıtlaması")
            ]
            
            for name, constraint_type, tooltip in constraints:
                action = QAction(name, self)
                action.setToolTip(tooltip)
                action.setCheckable(True)
                action.triggered.connect(
                    lambda checked, ct=constraint_type: self._on_constraint_selected(ct, checked)
                )
                self.addAction(action)
            
            self.addSeparator()
            
            # Solve butonu
            solve_action = QAction("Solve", self)
            solve_action.setToolTip("Kısıtlamaları çöz")
            solve_action.triggered.connect(self._on_solve_constraints)
            self.addAction(solve_action)
            
            # Clear butonu
            clear_action = QAction("Clear All", self)
            clear_action.setToolTip("Tüm kısıtlamaları temizle")
            clear_action.triggered.connect(self._on_clear_constraints)
            self.addAction(clear_action)
            
        except Exception as e:
            self.logger.error(f"Assembly toolbar kurulum hatası: {e}")
    
    @pyqtSlot(str, bool)
    def _on_constraint_selected(self, constraint_type: str, checked: bool):
        """Kısıtlama seçildi"""
        if checked:
            self.logger.info(f"Kısıtlama modu: {constraint_type}")
            # Ana pencereye sinyal gönder
            constraint_data = {"type": constraint_type}
            self.constraint_added.emit(constraint_type, constraint_data)
        else:
            self.constraint_removed.emit(constraint_type)
    
    @pyqtSlot()
    def _on_solve_constraints(self):
        """Kısıtlamaları çöz"""
        self.logger.info("Kısıtlama çözümü isteniyor")
        # Ana pencerede solve fonksiyonunu çağır
    
    @pyqtSlot()
    def _on_clear_constraints(self):
        """Kısıtlamaları temizle"""
        self.logger.info("Kısıtlamalar temizleniyor")
        # Tüm constraint action'larını uncheck yap
        for action in self.actions():
            if action.isCheckable():
                action.setChecked(False)

class StatusToolbar(QToolBar):
    """Durum bilgisi toolbar'ı"""
    
    def __init__(self, parent=None):
        super().__init__("Durum Toolbar", parent)
        
        self.info_widgets = {}
        self._setup_toolbar()
    
    def _setup_toolbar(self):
        """Durum toolbar'ını kur"""
        try:
            # Mouse koordinatları
            self.mouse_coords = QLabel("X: 0, Y: 0, Z: 0")
            self.mouse_coords.setMinimumWidth(150)
            self.addWidget(QLabel("Mouse:"))
            self.addWidget(self.mouse_coords)
            self.info_widgets["mouse_coords"] = self.mouse_coords
            
            self.addSeparator()
            
            # Seçim bilgisi
            self.selection_info = QLabel("Seçim yok")
            self.selection_info.setMinimumWidth(100)
            self.addWidget(QLabel("Seçim:"))
            self.addWidget(self.selection_info)
            self.info_widgets["selection"] = self.selection_info
            
            self.addSeparator()
            
            # Performans bilgisi
            self.fps_label = QLabel("FPS: --")
            self.addWidget(self.fps_label)
            self.info_widgets["fps"] = self.fps_label
            
        except Exception as e:
            logging.error(f"Status toolbar kurulum hatası: {e}")
    
    def update_mouse_coords(self, x: float, y: float, z: float):
        """Mouse koordinatlarını güncelle"""
        self.mouse_coords.setText(f"X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}")
    
    def update_selection_info(self, selection_text: str):
        """Seçim bilgisini güncelle"""
        self.selection_info.setText(selection_text)
    
    def update_fps(self, fps: int):
        """FPS bilgisini güncelle"""
        self.fps_label.setText(f"FPS: {fps}")

