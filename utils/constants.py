"""
Uygulama sabitleri
"""

import os
from enum import Enum

# Uygulama Bilgileri
APP_NAME = "CAD Montaj Uygulaması"
APP_VERSION = "1.0.0"
APP_AUTHOR = "CAD Developer"
APP_DESCRIPTION = "STEP dosyalarının montajı için CAD uygulaması"

# Dosya Formatları
class SupportedFormats(Enum):
    STEP = ".step"
    STP = ".stp"
    IGES = ".iges"
    IGS = ".igs"

SUPPORTED_IMPORT_FORMATS = [format.value for format in SupportedFormats]
SUPPORTED_EXPORT_FORMATS = [".step", ".stp", ".iges", ".stl", ".obj"]

# Dosya Filtreleri (PyQt5 dialog için)
FILE_FILTERS = {
    "step": "STEP Files (*.step *.stp)",
    "iges": "IGES Files (*.iges *.igs)",
    "all_cad": "CAD Files (*.step *.stp *.iges *.igs)",
    "all_files": "All Files (*.*)"
}

IMPORT_FILE_FILTER = ";;".join([
    FILE_FILTERS["all_cad"],
    FILE_FILTERS["step"],
    FILE_FILTERS["iges"],
    FILE_FILTERS["all_files"]
])

EXPORT_FILE_FILTER = "STEP Files (*.step);;STL Files (*.stl);;OBJ Files (*.obj)"

# Dizin Yapısı
DEFAULT_DIRECTORIES = {
    "config": os.path.join(os.path.expanduser("~"), ".cad_montaj"),
    "temp": os.path.join(os.path.expanduser("~"), ".cad_montaj", "temp"),
    "logs": os.path.join(os.path.expanduser("~"), ".cad_montaj", "logs"),
    "cache": os.path.join(os.path.expanduser("~"), ".cad_montaj", "cache"),
    "backup": os.path.join(os.path.expanduser("~"), ".cad_montaj", "backup")
}

# 3D Viewer Sabitleri
class ViewerDefaults:
    # Renk Tanımları (RGB 0-1 arası)
    BACKGROUND_GRADIENT_TOP = (0.808, 0.843, 0.871)    # Açık mavi-gri
    BACKGROUND_GRADIENT_BOTTOM = (0.502, 0.502, 0.502) # Orta gri
    
    DEFAULT_PART_COLOR = (0.7, 0.7, 0.7)               # Açık gri
    SELECTED_PART_COLOR = (1.0, 0.5, 0.0)              # Turuncu
    ASSEMBLY_PART_COLOR = (0.2, 0.8, 0.2)              # Yeşil
    COLLISION_COLOR = (1.0, 0.0, 0.0)                  # Kırmızı
    HIGHLIGHT_COLOR = (0.0, 0.8, 1.0)                  # Açık mavi
    
    # Kamera Ayarları
    DEFAULT_CAMERA_POSITION = (100, 100, 100)
    DEFAULT_CAMERA_TARGET = (0, 0, 0)
    DEFAULT_CAMERA_UP = (0, 0, 1)
    
    # Görüntüleme Ayarları
    DEFAULT_TRANSPARENCY = 0.0
    SELECTION_TRANSPARENCY = 0.3
    ASSEMBLY_TRANSPARENCY = 0.1
    
    # Mouse Sensitivities
    ROTATION_SENSITIVITY = 1.0
    ZOOM_SENSITIVITY = 1.0
    PAN_SENSITIVITY = 1.0

# Montaj Sabitleri
class AssemblyDefaults:
    # Toleranslar
    GEOMETRIC_TOLERANCE = 0.01      # mm
    ANGULAR_TOLERANCE = 0.017453    # radyan (1 derece)
    CONNECTION_TOLERANCE = 0.1      # mm
    
    # Arama Parametreleri
    MAX_SEARCH_ITERATIONS = 100
    MIN_CONNECTION_SCORE = 0.7
    MAX_COLLISION_OVERLAP = 0.001   # mm
    
    # Montaj Türleri
    CONNECTION_TYPES = [
        "PLANAR_FACE",      # Düzlemsel yüzey teması
        "CYLINDRICAL_FACE", # Silindirik yüzey teması  
        "SPHERICAL_FACE",   # Küresel yüzey teması
        "EDGE_TO_EDGE",     # Kenar-kenar teması
        "POINT_TO_POINT",   # Nokta-nokta teması
        "HOLE_PIN",         # Delik-pim bağlantısı
        "SCREW_THREAD"      # Vida bağlantısı
    ]

# GUI Sabitleri
class GUIDefaults:
    # Pencere Boyutları
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600
    DEFAULT_WINDOW_WIDTH = 1200
    DEFAULT_WINDOW_HEIGHT = 800
    
    # Toolbar
    TOOLBAR_ICON_SIZE = 24
    TOOLBAR_HEIGHT = 32
    
    # Status Bar
    STATUS_BAR_HEIGHT = 24
    
    # Splitter Oranları
    MAIN_SPLITTER_RATIO = [0.8, 0.2]  # 3D viewer : property panel
    SIDE_SPLITTER_RATIO = [0.5, 0.5]  # tree view : properties
    
    # Dialog Boyutları
    SETTINGS_DIALOG_SIZE = (500, 400)
    ABOUT_DIALOG_SIZE = (400, 300)
    FILE_INFO_DIALOG_SIZE = (450, 350)

# İkon Sabitleri
class Icons:
    # Dosya İşlemleri
    NEW = "new.png"
    OPEN = "open.png"
    SAVE = "save.png"
    SAVE_AS = "save_as.png"
    
    # Montaj İşlemleri  
    ASSEMBLY = "assembly.png"
    ALIGN = "align.png"
    COLLISION_CHECK = "collision.png"
    
    # Görünüm İşlemleri
    FIT_ALL = "fit_all.png"
    ZOOM_IN = "zoom_in.png"
    ZOOM_OUT = "zoom_out.png"
    ROTATE = "rotate.png"
    PAN = "pan.png"
    
    # Display Modes
    SHADED = "shaded.png"
    WIREFRAME = "wireframe.png"
    HIDDEN_LINE = "hidden_line.png"
    
    # Diğer
    SETTINGS = "settings.png"
    HELP = "help.png"
    EXIT = "exit.png"

# Hata Mesajları
class ErrorMessages:
    # Dosya Hataları
    FILE_NOT_FOUND = "Dosya bulunamadı: {}"
    FILE_NOT_READABLE = "Dosya okunabilir değil: {}"
    INVALID_FILE_FORMAT = "Geçersiz dosya formatı: {}"
    FILE_CORRUPTED = "Dosya bozuk: {}"
    
    # Import Hataları
    IMPORT_FAILED = "Dosya içe aktarma başarısız: {}"
    GEOMETRY_INVALID = "Geometri geçerli değil"
    UNITS_MISMATCH = "Birim uyumsuzluğu tespit edildi"
    
    # Montaj Hataları
    ASSEMBLY_FAILED = "Montaj işlemi başarısız"
    NO_CONNECTION_FOUND = "Bağlantı noktası bulunamadı"
    COLLISION_DETECTED = "Çakışma tespit edildi"
    INSUFFICIENT_CONSTRAINTS = "Yetersiz kısıtlama"
    
    # 3D Viewer Hataları
    VIEWER_INIT_FAILED = "3D görüntüleyici başlatma başarısız"
    SHAPE_DISPLAY_FAILED = "Şekil görüntüleme başarısız: {}"
    
    # Genel Hatalar
    OUT_OF_MEMORY = "Bellek yetersiz"
    UNEXPECTED_ERROR = "Beklenmeyen hata: {}"

# Başarı Mesajları
class SuccessMessages:
    FILE_IMPORTED = "Dosya başarıyla içe aktarıldı: {}"
    FILE_EXPORTED = "Dosya başarıyla dışa aktarıldı: {}"
    ASSEMBLY_COMPLETED = "Montaj işlemi tamamlandı"
    SETTINGS_SAVED = "Ayarlar kaydedildi"

# Performance Sabitleri
class PerformanceLimits:
    MAX_TRIANGLES_DEFAULT = 100000
    MAX_VERTICES_DEFAULT = 50000
    MAX_FACES_DEFAULT = 10000
    
    # Memory Limits (MB)
    MAX_MEMORY_USAGE = 2048
    WARNING_MEMORY_THRESHOLD = 1536
    
    # Time Limits (seconds)
    MAX_IMPORT_TIME = 30
    MAX_ASSEMBLY_TIME = 60
    MAX_DISPLAY_TIME = 5

# Keyboard Shortcuts
class Shortcuts:
    # Dosya İşlemleri
    NEW = "Ctrl+N"
    OPEN = "Ctrl+O"
    SAVE = "Ctrl+S"
    SAVE_AS = "Ctrl+Shift+S"
    EXIT = "Ctrl+Q"
    
    # Düzenleme
    UNDO = "Ctrl+Z"
    REDO = "Ctrl+Y"
    DELETE = "Delete"
    
    # Görünüm
    FIT_ALL = "F"
    ZOOM_IN = "+"
    ZOOM_OUT = "-"
    
    # Montaj
    START_ASSEMBLY = "Ctrl+A"
    CHECK_COLLISION = "Ctrl+C"
    
    # Diğer
    SETTINGS = "Ctrl+,"
    HELP = "F1"

# Unit Conversion
class Units:
    MILLIMETER = "mm"
    CENTIMETER = "cm" 
    METER = "m"
    INCH = "in"
    FOOT = "ft"
    
    # Conversion factors to millimeters
    TO_MM = {
        MILLIMETER: 1.0,
        CENTIMETER: 10.0,
        METER: 1000.0,
        INCH: 25.4,
        FOOT: 304.8
    }

# Threads ve Multiprocessing
class Threading:
    MAX_WORKER_THREADS = 4
    IMPORT_THREAD_PRIORITY = 1
    ASSEMBLY_THREAD_PRIORITY = 2
    DISPLAY_THREAD_PRIORITY = 3