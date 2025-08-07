"""
Utils modülü - Yardımcı araçlar ve konfigürasyonlar
"""

from .config import Config
from .logger import setup_logger, CADLogger, get_logger, log_performance
from .constants import *

__version__ = "1.0.0"
__author__ = "CAD Developer"

# Modül seviyesinde genel fonksiyonlar
def create_default_config():
    """Varsayılan konfigürasyon oluştur"""
    return Config()

def create_logger(name="CADMontaj", config=None):
    """Logger oluştur"""
    if config:
        return CADLogger(config)
    else:
        return setup_logger(name)

# Modül başlatma kontrolü
def check_dependencies():
    """Gerekli bağımlılıkları kontrol et"""
    try:
        import PyQt5
        import OCC
        return True, "Tüm bağımlılıklar mevcut"
    except ImportError as e:
        return False, f"Eksik bağımlılık: {e}"

# Export edilen ana sınıflar
__all__ = [
    'Config',
    'setup_logger', 
    'CADLogger',
    'get_logger',
    'log_performance',
    'create_default_config',
    'create_logger',
    'check_dependencies',
    # Constants
    'APP_NAME',
    'APP_VERSION', 
    'SUPPORTED_IMPORT_FORMATS',
    'ViewerDefaults',
    'AssemblyDefaults',
    'GUIDefaults',
    'ErrorMessages',
    'SuccessMessages'
]