"""
3D Görüntüleyici Motoru
PythonOCC tabanlı 3D viewer implementasyonu
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout

try:
    from OCC.Display.qtDisplay import qtViewer3d
    from OCC.Core import (
        gp_Pnt, gp_Dir, gp_Vec, gp_Ax1, gp_Ax2, gp_Ax3, gp_Trsf,
        Quantity_Color, Quantity_NOC_WHITE, Quantity_NOC_GRAY,
        AIS_InteractiveContext, AIS_Shape, AIS_DisplayMode_Shaded,
        V3d_View, V3d_Viewer, Aspect_GradientFillMethod_Horizontal
    )
    from OCC.Extend.TopologyUtils import TopologyExplorer
except ImportError as e:
    logging.error(f"PythonOCC import hatası: {e}")
    raise

from .geometry_handler import GeometryHandler
from .transformations import TransformationManager
from utils.constants import ViewerDefaults

class CADViewer(QWidget):
    """
    Ana 3D CAD Görüntüleyici Sınıfı
    """
    
    # Sinyaller
    shape_selected = pyqtSignal(object)  # Şekil seçildiğinde
    shape_deselected = pyqtSignal()      # Seçim kaldırıldığında  
    viewer_initialized = pyqtSignal()    # Viewer hazır olduğunda
    
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        
        self.config = config
        self.logger = logging.getLogger("CADMontaj.Viewer")
        
        # Core components
        self._display = None
        self._viewer_3d = None
        self._context = None
        
        # Shape yönetimi
        self.shapes = {}  # shape_id -> {"shape": shape, "ais_shape": ais, "metadata": dict}
        self.selected_shapes = set()
        self.shape_counter = 0
        
        # Managers
        self.geometry_handler = GeometryHandler(config)
        self.transform_manager = TransformationManager()
        
        # Settings
        self.display_mode = AIS_DisplayMode_Shaded
        self.background_gradient = True
        
        # Initialize viewer
        self._setup_viewer()
        
    def _setup_viewer(self):
        """3D viewer'ı kurulum"""
        try:
            # Layout oluştur
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            
            # qtViewer3d widget'ı oluştur
            self._viewer_3d = qtViewer3d(self)
            layout.addWidget(self._viewer_3d)
            self.setLayout(layout)
            
            # Display referansını al
            self._display = self._viewer_3d._display
            self._context = self._display.Context
            
            # Viewer ayarlarını uygula
            self._configure_viewer()
            
            # Event handler'ları bağla
            self._setup_event_handlers()
            
            self.logger.info("3D Viewer başarıyla oluşturuldu")
            self.viewer_initialized.emit()
            
        except Exception as e:
            self.logger.error(f"3D Viewer kurulum hatası: {e}")
            raise
    
    def _configure_viewer(self):
        """Viewer yapılandırmasını uygula"""
        try:
            # Arkaplan ayarı
            if self.background_gradient:
                self._set_background_gradient()
            else:
                self._display.View.SetBackgroundColor(Quantity_NOC_GRAY)
            
            # Lighting ve görsel ayarlar
            view = self._display.View
            view.SetLightOn()
            
            # Trihedron (koordinat sistemi) göster
            self._display.display_trihedron()
            
            # Grid ayarları (opsiyonel)
            # self._display.View.SetGrid(Aspect_GridType_Rectangular, Aspect_GridDrawMode_Lines)
            
            if self.config:
                # Config'den ayarları yükle
                self._apply_config_settings()
                
        except Exception as e:
            self.logger.warning(f"Viewer konfigürasyon uyarısı: {e}")
    
    def _set_background_gradient(self):
        """Gradient arkaplan ayarla"""
        try:
            top_color = ViewerDefaults.BACKGROUND_GRADIENT_TOP
            bottom_color = ViewerDefaults.BACKGROUND_GRADIENT_BOTTOM
            
            # Renkleri Quantity_Color'a çevir
            color1 = Quantity_Color(top_color[0], top_color[1], top_color[2], 1)
            color2 = Quantity_Color(bottom_color[0], bottom_color[1], bottom_color[2], 1)
            
            self._display.View.SetBgGradientColors(
                color1, color2, 
                Aspect_GradientFillMethod_Horizontal, 
                True
            )
        except Exception as e:
            self.logger.warning(f"Gradient arkaplan ayarlama hatası: {e}")
    
    def _apply_config_settings(self):
        """Konfigürasyondan ayarları uygula"""
        if not self.config:
            return
            
        # Arkaplan ayarları
        bg_gradient = self.config.get("viewer.background_gradient", True)
        if bg_gradient != self.background_gradient:
            self.background_gradient = bg_gradient
            if bg_gradient:
                self._set_background_gradient()
            else:
                self._display.View.SetBackgroundColor(Quantity_NOC_GRAY)
        
        # Antialiasing
        if self.config.get("viewer.antialiasing", True):
            self._display.View.SetAntialiasingOn()
        
        # Shadows
        if self.config.get("viewer.shadows", True):
            self._display.View.SetShadingModel(3)  # Phong shading
    
    def _setup_event_handlers(self):
        """Event handler'ları ayarla"""
        try:
            # Mouse event'leri için callback'ler
            self._display.register_select_callback(self._on_shape_selected)
            
            # Viewer resize timer
            self.resize_timer = QTimer()
            self.resize_timer.timeout.connect(self._on_resize_timeout)
            self.resize_timer.setSingleShot(True)
            
        except Exception as e:
            self.logger.warning(f"Event handler kurulum uyarısı: {e}")
    
    def _on_shape_selected(self, shape, *args):
        """Şekil seçildiğinde çağrılır"""
        self.logger.debug(f"Şekil seçildi: {shape}")
        self.shape_selected.emit(shape)
    
    def _on_resize_timeout(self):
        """Pencere boyutu değişikliği timeout'u"""
        if self._display:
            self._display.FitAll()
    
    def add_shape(self, 
                  shape, 
                  color: Optional[Tuple[float, float, float]] = None,
                  transparency: float = 0.0,
                  material: str = "default",
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Sahneye şekil ekle
        
        Args:
            shape: OCC Shape objesi
            color: RGB renk tuple'ı (0-1 arası)
            transparency: Şeffaflık (0-1 arası)
            material: Materyal adı
            metadata: Ek veri
            
        Returns:
            shape_id: Şeklin benzersiz ID'si
        """
        try:
            # Benzersiz ID oluştur
            shape_id = f"shape_{self.shape_counter}"
            self.shape_counter += 1
            
            # AIS_Shape oluştur
            ais_shape = AIS_Shape(shape)
            
            # Renk ayarı
            if color is None:
                color = ViewerDefaults.DEFAULT_PART_COLOR
            
            quantity_color = Quantity_Color(color[0], color[1], color[2], 1)
            ais_shape.SetColor(quantity_color)
            
            # Şeffaflık ayarı
            if transparency > 0:
                ais_shape.SetTransparency(transparency)
            
            # Display mode ayarı
            ais_shape.SetDisplayMode(self.display_mode)
            
            # Context'e ekle
            self._context.Display(ais_shape, False)  # False = update etme
            
            # Shape'i kaydet
            self.shapes[shape_id] = {
                "shape": shape,
                "ais_shape": ais_shape,
                "color": color,
                "transparency": transparency,
                "material": material,
                "metadata": metadata or {},
                "visible": True
            }
            
            # Görüntüyü güncelle
            self._context.UpdateCurrentViewer()
            
            self.logger.debug(f"Şekil eklendi: {shape_id}")
            return shape_id
            
        except Exception as e:
            self.logger.error(f"Şekil ekleme hatası: {e}")
            return None
    
    def remove_shape(self, shape_id: str) -> bool:
        """Şekli sahneden kaldır"""
        try:
            if shape_id not in self.shapes:
                self.logger.warning(f"Şekil bulunamadı: {shape_id}")
                return False
            
            # AIS context'ten kaldır
            ais_shape = self.shapes[shape_id]["ais_shape"]
            self._context.Remove(ais_shape, True)
            
            # Dictionary'den kaldır
            del self.shapes[shape_id]
            
            # Seçimden kaldır
            self.selected_shapes.discard(shape_id)
            
            self.logger.debug(f"Şekil kaldırıldı: {shape_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Şekil kaldırma hatası: {e}")
            return False
    
    def clear_all_shapes(self):
        """Tüm şekilleri kaldır"""
        try:
            for shape_id in list(self.shapes.keys()):
                self.remove_shape(shape_id)
            
            self.logger.info("Tüm şekiller kaldırıldı")
            
        except Exception as e:
            self.logger.error(f"Tüm şekilleri kaldırma hatası: {e}")
    
    def set_shape_color(self, shape_id: str, color: Tuple[float, float, float]):
        """Şeklin rengini değiştir"""
        try:
            if shape_id not in self.shapes:
                return False
            
            ais_shape = self.shapes[shape_id]["ais_shape"]
            quantity_color = Quantity_Color(color[0], color[1], color[2], 1)
            
            # Rengi güncelle
            self._context.SetColor(ais_shape, quantity_color, False)
            self.shapes[shape_id]["color"] = color
            
            self._context.UpdateCurrentViewer()
            return True
            
        except Exception as e:
            self.logger.error(f"Renk değişiklik hatası: {e}")
            return False
    
    def set_shape_transparency(self, shape_id: str, transparency: float):
        """Şeklin şeffaflığını değiştir"""
        try:
            if shape_id not in self.shapes:
                return False
            
            ais_shape = self.shapes[shape_id]["ais_shape"]
            
            if transparency > 0:
                self._context.SetTransparency(ais_shape, transparency, False)
            else:
                self._context.UnsetTransparency(ais_shape, False)
            
            self.shapes[shape_id]["transparency"] = transparency
            self._context.UpdateCurrentViewer()
            return True
            
        except Exception as e:
            self.logger.error(f"Şeffaflık değişiklik hatası: {e}")
            return False
    
    def select_shape(self, shape_id: str):
        """Şekli seç"""
        try:
            if shape_id not in self.shapes:
                return False
            
            ais_shape = self.shapes[shape_id]["ais_shape"]
            self._context.SetSelected(ais_shape, False)
            self.selected_shapes.add(shape_id)
            
            # Seçim rengini ayarla
            self.set_shape_color(shape_id, ViewerDefaults.SELECTED_PART_COLOR)
            
            self._context.UpdateCurrentViewer()
            return True
            
        except Exception as e:
            self.logger.error(f"Seçim hatası: {e}")
            return False
    
    def deselect_shape(self, shape_id: str):
        """Şekil seçimini kaldır"""
        try:
            if shape_id not in self.shapes or shape_id not in self.selected_shapes:
                return False
            
            ais_shape = self.shapes[shape_id]["ais_shape"]
            self._context.ClearSelected(False)
            self.selected_shapes.discard(shape_id)
            
            # Orijinal rengini geri yükle
            original_color = self.shapes[shape_id]["color"]
            self.set_shape_color(shape_id, original_color)
            
            self._context.UpdateCurrentViewer()
            return True
            
        except Exception as e:
            self.logger.error(f"Seçim kaldırma hatası: {e}")
            return False
    
    def clear_selection(self):
        """Tüm seçimleri kaldır"""
        for shape_id in list(self.selected_shapes):
            self.deselect_shape(shape_id)
    
    def fit_all(self):
        """Tüm nesneleri görüntüde sığdır"""
        try:
            self._display.FitAll()
            self.logger.debug("Fit All uygulandı")
        except Exception as e:
            self.logger.error(f"Fit All hatası: {e}")
    
    def set_view_direction(self, direction: str):
        """Görüntü yönünü ayarla"""
        try:
            view_directions = {
                "front": (0, 1, 0),
                "back": (0, -1, 0), 
                "left": (1, 0, 0),
                "right": (-1, 0, 0),
                "top": (0, 0, 1),
                "bottom": (0, 0, -1),
                "isometric": (1, 1, 1)
            }
            
            if direction.lower() in view_directions:
                dir_vec = view_directions[direction.lower()]
                view = self._display.View
                
                # Görüntü yönünü ayarla
                view.SetProj(dir_vec[0], dir_vec[1], dir_vec[2])
                view.FitAll()
                
                self.logger.debug(f"Görüntü yönü ayarlandı: {direction}")
                
        except Exception as e:
            self.logger.error(f"Görüntü yönü ayarlama hatası: {e}")
    
    def export_image(self, filename: str, width: int = 800, height: int = 600):
        """Görüntüyü dosyaya aktar"""
        try:
            self._display.View.Dump(filename, width, height)
            self.logger.info(f"Görüntü aktarıldı: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Görüntü aktarma hatası: {e}")
            return False
    
    def get_shape_info(self, shape_id: str) -> Optional[Dict[str, Any]]:
        """Şekil bilgilerini al"""
        if shape_id in self.shapes:
            shape_data = self.shapes[shape_id].copy()
            
            # Geometrik bilgileri ekle
            shape = shape_data["shape"]
            shape_data.update(self.geometry_handler.analyze_shape(shape))
            
            return shape_data
        return None
    
    def get_all_shapes(self) -> List[str]:
        """Tüm şekil ID'lerini al"""
        return list(self.shapes.keys())
    
    def get_selected_shapes(self) -> List[str]:
        """Seçili şekil ID'lerini al"""
        return list(self.selected_shapes)
    
    def resizeEvent(self, event):
        """Widget boyutu değiştiğinde"""
        super().resizeEvent(event)
        # Resize işlemini geciktir (performance için)
        self.resize_timer.start(100)
    
    def cleanup(self):
        """Temizlik işlemleri"""
        try:
            self.clear_all_shapes()
            if self._context:
                self._context.RemoveAll(True)
            self.logger.info("Viewer temizlendi")
        except Exception as e:
            self.logger.error(f"Viewer temizlik hatası: {e}")
            
    def showEvent(self, event):
        """Widget gösterildiğinde"""
        super().showEvent(event)
        if self._display:
            self._display.FitAll()