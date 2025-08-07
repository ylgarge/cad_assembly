"""
Log sistemi yönetimi
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Renkli console log formatter"""
    
    # ANSI renk kodları
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m'   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Rengi ekle
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        
        return super().format(record)

def setup_logger(name: str = "CADMontaj", 
                 level: str = "INFO",
                 log_to_file: bool = True,
                 log_directory: str = None,
                 max_log_files: int = 5,
                 max_file_size_mb: int = 10) -> logging.Logger:
    """
    Log sistemini ayarla
    
    Args:
        name: Logger ismi
        level: Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Dosyaya log yazma
        log_directory: Log dizini
        max_log_files: Maksimum log dosyası sayısı
        max_file_size_mb: Maksimum dosya boyutu (MB)
    
    Returns:
        Yapılandırılmış logger
    """
    
    # Logger oluştur
    logger = logging.getLogger(name)
    
    # Eğer zaten handler'lar eklenmiş ise, tekrar ekleme
    if logger.handlers:
        return logger
    
    # Log seviyesini ayarla
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    
    # Console formatter (renkli)
    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    console_formatter = ColoredFormatter(console_format, datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(console_handler)
    
    # Dosya handler (eğer isteniyorsa)
    if log_to_file:
        if log_directory is None:
            log_directory = os.path.join(os.path.expanduser("~"), ".cad_montaj", "logs")
        
        # Log dizinini oluştur
        os.makedirs(log_directory, exist_ok=True)
        
        # Log dosyası adı
        log_filename = f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        log_filepath = os.path.join(log_directory, log_filename)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_filepath,
            maxBytes=max_file_size_mb * 1024 * 1024,  # MB to bytes
            backupCount=max_log_files,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        
        # Dosya formatter (renksiz)
        file_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    return logger

class CADLogger:
    """CAD uygulaması için özel logger sınıfı"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Config'e göre logger ayarla"""
        if self.config:
            level = self.config.get("logging.level", "INFO")
            file_logging = self.config.get("logging.file_logging", True)
            log_directory = self.config.get("logging.log_directory")
            max_log_files = self.config.get("logging.max_log_files", 5)
            log_rotation_size = self.config.get("logging.log_rotation_size", 10)
        else:
            level = "INFO"
            file_logging = True
            log_directory = None
            max_log_files = 5
            log_rotation_size = 10
        
        return setup_logger(
            name="CADMontaj",
            level=level,
            log_to_file=file_logging,
            log_directory=log_directory,
            max_log_files=max_log_files,
            max_file_size_mb=log_rotation_size
        )
    
    def debug(self, message: str, **kwargs):
        """Debug log"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Info log"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning log"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Error log"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Critical log"""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Exception log (otomatik stack trace ile)"""
        self.logger.exception(message, **kwargs)
    
    def log_operation(self, operation_name: str, details: str = ""):
        """İşlem logla"""
        self.info(f"İşlem: {operation_name} {details}")
    
    def log_file_operation(self, operation: str, file_path: str, success: bool = True):
        """Dosya işlemi logla"""
        status = "başarılı" if success else "başarısız"
        self.info(f"Dosya {operation}: {file_path} - {status}")
    
    def log_assembly_operation(self, operation: str, part1: str, part2: str = None, success: bool = True):
        """Montaj işlemi logla"""
        status = "başarılı" if success else "başarısız"
        if part2:
            self.info(f"Montaj {operation}: {part1} + {part2} - {status}")
        else:
            self.info(f"Montaj {operation}: {part1} - {status}")
    
    def log_viewer_operation(self, operation: str, details: str = ""):
        """3D viewer işlemi logla"""
        self.debug(f"Viewer: {operation} {details}")
    
    def log_error_with_context(self, error: Exception, context: str = ""):
        """Hata ve context bilgisi ile logla"""
        error_msg = f"Hata: {str(error)}"
        if context:
            error_msg += f" - Context: {context}"
        self.error(error_msg, exc_info=True)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Mevcut logger'ı al veya yenisini oluştur"""
    if name is None:
        name = "CADMontaj"
    
    return logging.getLogger(name)

# Performans ölçümü için decorator
def log_performance(logger: logging.Logger):
    """Fonksiyon performansını ölçen decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time
                
                logger.debug(f"{func.__name__} çalışma süresi: {execution_time:.3f}s")
                return result
                
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                logger.error(f"{func.__name__} hata ile sonlandı ({execution_time:.3f}s): {str(e)}")
                raise
        
        return wrapper
    return decorator