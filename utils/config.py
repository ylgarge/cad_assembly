"""
Konfigürasyon yönetimi
"""

import os
import json
from typing import Dict, Any

class Config:
    """Uygulama konfigürasyon yöneticisi"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.settings = self._load_default_settings()
        self._load_config()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Varsayılan ayarları yükle"""
        return {
            # GUI Ayarları
            "gui": {
                "window_width": 1200,
                "window_height": 800,
                "window_maximized": False,
                "theme": "light",
                "language": "tr"
            },
            
            # 3D Viewer Ayarları
            "viewer": {
                "background_gradient": True,
                "background_color_1": [206, 215, 222],
                "background_color_2": [128, 128, 128],
                "antialiasing": True,
                "shadows": True,
                "default_material": "plastic",
                "mouse_sensitivity": 1.0
            },
            
            # İçe Aktarma Ayarları
            "import": {
                "default_directory": os.path.expanduser("~/Documents"),
                "supported_formats": [".step", ".stp", ".iges", ".igs"],
                "auto_fit_all": True,
                "import_units": "mm",
                "healing_shapes": True
            },
            
            # Montaj Ayarları
            "assembly": {
                "tolerance": 0.01,
                "auto_collision_check": True,
                "show_assembly_constraints": True,
                "highlight_connections": True,
                "connection_tolerance": 0.1,
                "max_search_iterations": 100
            },
            
            # Görsel Ayarları
            "display": {
                "default_part_color": [0.7, 0.7, 0.7],
                "selected_part_color": [1.0, 0.5, 0.0],
                "assembly_part_color": [0.2, 0.8, 0.2],
                "collision_color": [1.0, 0.0, 0.0],
                "transparency": 0.0,
                "edge_display": True,
                "wireframe_mode": False
            },
            
            # Dosya Ayarları
            "files": {
                "recent_files": [],
                "max_recent_files": 10,
                "auto_backup": True,
                "backup_interval": 300,  # saniye
                "temp_directory": os.path.join(os.path.expanduser("~"), ".cad_montaj", "temp")
            },
            
            # Log Ayarları
            "logging": {
                "level": "INFO",
                "file_logging": True,
                "log_directory": os.path.join(os.path.expanduser("~"), ".cad_montaj", "logs"),
                "max_log_files": 5,
                "log_rotation_size": 10  # MB
            },
            
            # Performance Ayarları
            "performance": {
                "max_triangles": 100000,
                "tessellation_quality": 0.5,
                "use_mesh_cache": True,
                "parallel_processing": True,
                "memory_limit_mb": 2048
            }
        }
    
    def _load_config(self):
        """Konfigürasyonu dosyadan yükle"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Kullanıcı ayarlarını varsayılan ayarlarla birleştir
                    self._merge_configs(self.settings, user_config)
            except Exception as e:
                print(f"Konfigürasyon yükleme hatası: {e}")
        
        # Gerekli dizinleri oluştur
        self._create_directories()
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]):
        """Kullanıcı konfigürasyonunu varsayılan ile birleştir"""
        for key, value in user.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    self._merge_configs(default[key], value)
                else:
                    default[key] = value
            else:
                default[key] = value
    
    def _create_directories(self):
        """Gerekli dizinleri oluştur"""
        directories = [
            self.get("files.temp_directory"),
            self.get("logging.log_directory")
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except Exception as e:
                    print(f"Dizin oluşturma hatası {directory}: {e}")
    
    def get(self, key: str, default=None):
        """Ayar değerini al (nokta notasyonu ile)"""
        keys = key.split('.')
        value = self.settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Ayar değerini güncelle (nokta notasyonu ile)"""
        keys = key.split('.')
        current = self.settings
        
        # Son anahtara kadar git
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Son anahtarı güncelle
        current[keys[-1]] = value
    
    def save(self):
        """Konfigürasyonu dosyaya kaydet"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Konfigürasyon kaydetme hatası: {e}")
    
    def add_recent_file(self, file_path: str):
        """Son açılan dosyaları listesine ekle"""
        recent_files = self.get("files.recent_files", [])
        
        # Eğer dosya zaten listede varsa, önce kaldır
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Listenin başına ekle
        recent_files.insert(0, file_path)
        
        # Maksimum sayıyı aşmasın
        max_files = self.get("files.max_recent_files", 10)
        if len(recent_files) > max_files:
            recent_files = recent_files[:max_files]
        
        self.set("files.recent_files", recent_files)
        self.save()
    
    def get_recent_files(self) -> list:
        """Son açılan dosyaları al"""
        recent_files = self.get("files.recent_files", [])
        # Var olmayan dosyaları temizle
        existing_files = [f for f in recent_files if os.path.exists(f)]
        
        if len(existing_files) != len(recent_files):
            self.set("files.recent_files", existing_files)
            self.save()
        
        return existing_files
    
    def reset_to_defaults(self):
        """Ayarları varsayılana sıfırla"""
        self.settings = self._load_default_settings()
        self.save()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Tüm ayarları al"""
        return self.settings.copy()
    
    def update_settings(self, settings: Dict[str, Any]):
        """Toplu ayar güncelleme"""
        self._merge_configs(self.settings, settings)
        self.save()