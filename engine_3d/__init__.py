"""
3D Engine Modülü
PythonOCC tabanlı 3D görüntüleme ve geometrik işlemler
"""

from .viewer import CADViewer
from .geometry_handler import GeometryHandler
from .transformations import TransformationManager, TransformationType, RotationAxis

__version__ = "1.0.0"
__author__ = "CAD Developer"

# Ana sınıfları export et
__all__ = [
    'CADViewer',
    'GeometryHandler', 
    'TransformationManager',
    'TransformationType',
    'RotationAxis'
]

def create_viewer(parent=None, config=None):
    """3D viewer oluştur"""
    return CADViewer(parent, config)

def create_geometry_handler(config=None):
    """Geometri handler oluştur"""  
    return GeometryHandler(config)

def create_transformation_manager():
    """Transformation manager oluştur"""
    return TransformationManager()

# Modül seviyesinde yardımcı fonksiyonlar
def check_occ_availability():
    """PythonOCC'nin mevcut olup olmadığını kontrol et"""
    try:
        from OCC.Core import gp_Pnt
        return True, "PythonOCC mevcut"
    except ImportError as e:
        return False, f"PythonOCC mevcut değil: {e}"

def get_occ_version():
    """PythonOCC versiyonunu al"""
    try:
        from OCC import VERSION
        return VERSION
    except:
        return "Bilinmeyen versiyon"

# Modül başlatma kontrolü
def initialize_engine():
    """3D engine'i başlat"""
    available, message = check_occ_availability()
    if not available:
        raise ImportError(f"3D Engine başlatılamadı: {message}")
    
    version = get_occ_version()
    print(f"3D Engine başlatıldı - PythonOCC {version}")
    return True