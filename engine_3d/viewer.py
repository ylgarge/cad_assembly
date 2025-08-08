"""
3D Görüntüleyici Motoru
PythonOCC tabanlı 3D viewer implementasyonu
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


try:
    # Backend'i yükle (eğer yüklenmemişse)
    try:
        from OCC.Display import backend
        backend.load_backend('pyqt5')
    except ImportError:
        import OCC.Display.backend
        OCC.Display.backend.load_backend('pyqt5')

    # 3D görüntüleyici
    from OCC.Display.qtDisplay import qtViewer3d

    # Temel geometrik sınıflar
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec, gp_Ax1, gp_Ax2, gp_Ax3, gp_Trsf

    # Renkler
    from OCC.Core.Quantity import Quantity_Color, Quantity_NOC_WHITE, Quantity_NOC_GRAY

    # 3D Görselleştirme bileşenleri
    from OCC.Core.AIS import AIS_InteractiveContext, AIS_Shape, AIS_DisplayMode_Shaded
    from OCC.Core.V3d import V3d_View, V3d_Viewer
    from OCC.Core.Aspect import Aspect_GradientFillMethod_Horizontal

    # Topoloji gezgini
    from OCC.Extend.TopologyUtils import TopologyExplorer
    OCC_AVAILABLE = True


except ImportError as e:
    logging.error(f"PythonOCC import hatası: {e}")
    OCC_AVAILABLE = False

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
        try:
            self.geometry_handler = GeometryHandler(config)
            self.transform_manager = TransformationManager()
        except:
            self.geometry_handler = None
            self.transform_manager = None
        
        # Settings
        if OCC_AVAILABLE:
            self.display_mode = AIS_DisplayMode_Shaded
        self.background_gradient = True
        
        # Initialize viewer
        self._setup_viewer()
        
    def _setup_viewer(self):
        """3D viewer'ı kurulum"""
        try:
            if not OCC_AVAILABLE:
                self._setup_fallback_viewer()
                return
            
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
            self._setup_fallback_viewer()
    
    def _setup_fallback_viewer(self):
        """PythonOCC kullanılamadığında fallback viewer"""
        try:
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Basit placeholder
            placeholder = QLabel("3D Viewer\n\nPythonOCC mevcut değil veya yüklenemedi.\n\nLütfen PythonOCC kurulumunu kontrol edin.")
            placeholder.setStyleSheet("""
                QLabel {
                    background-color: #f0f0f0;
                    border: 2px dashed #cccccc;
                    font-size: 14px;
                    color: #666666;
                    text-align: center;
                    padding: 20px;
                }
            """)
            placeholder.setAlignment(1 | 4)  # Qt.AlignHCenter | Qt.AlignVCenter
            
            layout.addWidget(placeholder)
            self.setLayout(layout)
            
            # Timer ile viewer_initialized signal'ini gönder
            QTimer.singleShot(100, self.viewer_initialized.emit)
            
            self.logger.warning("Fallback viewer oluşturuldu - PythonOCC mevcut değil")
            
        except Exception as e:
            self.logger.error(f"Fallback viewer kurulum hatası: {e}")
    
    def _configure_viewer(self):
        """Viewer yapılandırmasını uygula"""
        try:
            if not OCC_AVAILABLE or not self._display:
                return
            
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
            
            if self.config:
                # Config'den ayarları yükle
                self._apply_config_settings()
                
        except Exception as e:
            self.logger.warning(f"Viewer konfigürasyon uyarısı: {e}")
    
    def _set_background_gradient(self):
        """Gradient arkaplan ayarla"""
        try:
            if not OCC_AVAILABLE or not self._display:
                return
            
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
        if not self.config or not OCC_AVAILABLE:
            return
            
        try:
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
        except Exception as e:
            self.logger.warning(f"Config ayarları uygulama hatası: {e}")
    
    def _setup_event_handlers(self):
        """Event handler'ları ayarla"""
        try:
            if not OCC_AVAILABLE or not self._display:
                return
            
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
                  shape=None, 
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
            if not OCC_AVAILABLE or not self._display or not shape:
                # Fallback: sadece ID döndür
                shape_id = f"shape_{self.shape_counter}"
                self.shape_counter += 1
                
                self.shapes[shape_id] = {
                    "shape": shape,
                    "ais_shape": None,
                    "color": color or ViewerDefaults.DEFAULT_PART_COLOR,
                    "transparency": transparency,
                    "material": material,
                    "metadata": metadata or {},
                    "visible": True
                }
                
                self.logger.debug(f"Shape eklendi (fallback): {shape_id}")
                return shape_id
            
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
            
            if OCC_AVAILABLE and self._context and self.shapes[shape_id]["ais_shape"]:
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
            
            if OCC_AVAILABLE and self._context and self.shapes[shape_id]["ais_shape"]:
                ais_shape = self.shapes[shape_id]["ais_shape"]
                quantity_color = Quantity_Color(color[0], color[1], color[2], 1)
                
                # Rengi güncelle
                self._context.SetColor(ais_shape, quantity_color, False)
                self._context.UpdateCurrentViewer()
            
            self.shapes[shape_id]["color"] = color
            return True
            
        except Exception as e:
            self.logger.error(f"Renk değişiklik hatası: {e}")
            return False
    
    def fit_all(self):
        """Tüm nesneleri görüntüde sığdır"""
        try:
            if OCC_AVAILABLE and self._display:
                self._display.FitAll()
                self.logger.debug("Fit All uygulandı")
        except Exception as e:
            self.logger.error(f"Fit All hatası: {e}")
    
    def set_view_direction(self, direction: str):
        """Görüntü yönünü ayarla"""
        try:
            if not OCC_AVAILABLE or not self._display:
                return
            
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
    
    def get_all_shapes(self) -> List[str]:
        """Tüm şekil ID'lerini al"""
        return list(self.shapes.keys())
    
    def get_selected_shapes(self) -> List[str]:
        """Seçili şekil ID'lerini al"""
        return list(self.selected_shapes)
    
    def select_shape(self, shape_id: str):
        """Şekli seç"""
        try:
            if shape_id not in self.shapes:
                return False
            
            if OCC_AVAILABLE and self._context and self.shapes[shape_id]["ais_shape"]:
                ais_shape = self.shapes[shape_id]["ais_shape"]
                self._context.SetSelected(ais_shape, False)
                self._context.UpdateCurrentViewer()
            
            self.selected_shapes.add(shape_id)
            
            # Seçim rengini ayarla
            self.set_shape_color(shape_id, ViewerDefaults.SELECTED_PART_COLOR)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Seçim hatası: {e}")
            return False
    
    def set_shape_transparency(self, shape_id: str, transparency: float):
        """Şeklin şeffaflığını değiştir"""
        try:
            if shape_id not in self.shapes:
                return False
            
            if OCC_AVAILABLE and self._context and self.shapes[shape_id]["ais_shape"]:
                ais_shape = self.shapes[shape_id]["ais_shape"]
                
                if transparency > 0:
                    self._context.SetTransparency(ais_shape, transparency, False)
                else:
                    self._context.UnsetTransparency(ais_shape, False)
                
                self._context.UpdateCurrentViewer()
            
            self.shapes[shape_id]["transparency"] = transparency
            return True
            
        except Exception as e:
            self.logger.error(f"Şeffaflık değişiklik hatası: {e}")
            return False
    
    def cleanup(self):
        """Temizlik işlemleri"""
        try:
            self.clear_all_shapes()
            if OCC_AVAILABLE and self._context:
                self._context.RemoveAll(True)
            self.logger.info("Viewer temizlendi")
        except Exception as e:
            self.logger.error(f"Viewer temizlik hatası: {e}")
    
    def resizeEvent(self, event):
        """Widget boyutu değiştiğinde"""
        super().resizeEvent(event)
        # Resize işlemini geciktir (performance için)
        if hasattr(self, 'resize_timer'):
            self.resize_timer.start(100)
    
    def showEvent(self, event):
        """Widget gösterildiğinde"""
        super().showEvent(event)
        if OCC_AVAILABLE and self._display:
            self._display.FitAll()
    
    def get_shape_info(self, shape_id: str) -> Optional[Dict[str, Any]]:
        """Şekil bilgilerini al"""
        if shape_id in self.shapes:
            shape_data = self.shapes[shape_id].copy()
            
            # Geometrik bilgileri ekle
            if self.geometry_handler and shape_data["shape"]:
                try:
                    shape_data.update(self.geometry_handler.analyze_shape(shape_data["shape"]))
                except:
                    pass
            
            return shape_data
        return None