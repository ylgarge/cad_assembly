"""
Dosya Doğrulama Modülü
CAD dosyalarının geçerliliğini ve güvenliğini kontrol eder
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import hashlib
import mimetypes

from utils.constants import SUPPORTED_IMPORT_FORMATS, ErrorMessages

class FileValidator:
    """CAD dosyalarını doğrulayan sınıf"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger("CADMontaj.FileValidator")
        
        # Güvenlik ayarları
        self.max_file_size_mb = 500  # MB
        self.allowed_extensions = SUPPORTED_IMPORT_FORMATS
        self.check_file_content = True
        self.quarantine_suspicious_files = True
        
        if config:
            self.max_file_size_mb = config.get("import.max_file_size_mb", 500)
            self.check_file_content = config.get("import.check_file_content", True)
        
        # STEP ve IGES dosya başlıkları
        self.step_headers = [
            b"ISO-10303",
            b"STEP",
            b"FILE_DESCRIPTION",
            b"FILE_NAME",
            b"FILE_SCHEMA"
        ]
        
        self.iges_headers = [
            b"START",
            b"GLOBAL",
            b"DIRECTORY",
            b"PARAMETER"
        ]
        
        # Validation cache
        self.validation_cache = {}
    
    def validate_file(self, file_path: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Dosyayı kapsamlı olarak doğrula
        
        Args:
            file_path: Doğrulanacak dosya yolu
            
        Returns:
            (is_valid, validation_info) tuple'ı
        """
        validation_info = {
            "file_path": file_path,
            "validation_time": self._get_current_time(),
            "checks_performed": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            self.logger.debug(f"Dosya doğrulama başlatılıyor: {file_path}")
            
            # Temel dosya varlık kontrolü
            if not self._check_file_exists(file_path, validation_info):
                return False, validation_info
            
            # Dosya boyutu kontrolü
            if not self._check_file_size(file_path, validation_info):
                return False, validation_info
            
            # Dosya uzantısı kontrolü
            if not self._check_file_extension(file_path, validation_info):
                return False, validation_info
            
            # Dosya okuma izinleri kontrolü
            if not self._check_file_permissions(file_path, validation_info):
                return False, validation_info
            
            # İçerik kontrolü (eğer etkinse)
            if self.check_file_content:
                if not self._check_file_content(file_path, validation_info):
                    return False, validation_info
            
            # Dosya bütünlüğü kontrolü
            self._calculate_file_hash(file_path, validation_info)
            
            self.logger.debug(f"Dosya doğrulama başarılı: {file_path}")
            validation_info["is_valid"] = True
            return True, validation_info
            
        except Exception as e:
            error_msg = f"Dosya doğrulama hatası: {str(e)}"
            self.logger.error(error_msg)
            validation_info["errors"].append(error_msg)
            validation_info["is_valid"] = False
            return False, validation_info
    
    def validate_step_file(self, file_path: str) -> bool:
        """STEP dosyasını doğrula"""
        try:
            is_valid, info = self.validate_file(file_path)
            
            if not is_valid:
                return False
            
            # STEP'e özel kontroller
            file_extension = Path(file_path).suffix.lower()
            if file_extension not in ['.step', '.stp']:
                self.logger.warning(f"STEP dosyası bekleniyor, alınan: {file_extension}")
                return False
            
            # İçerik kontrolü
            if self.check_file_content:
                return self._validate_step_content(file_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"STEP doğrulama hatası: {e}")
            return False
    
    def validate_iges_file(self, file_path: str) -> bool:
        """IGES dosyasını doğrula"""
        try:
            is_valid, info = self.validate_file(file_path)
            
            if not is_valid:
                return False
            
            # IGES'e özel kontroller
            file_extension = Path(file_path).suffix.lower()
            if file_extension not in ['.iges', '.igs']:
                self.logger.warning(f"IGES dosyası bekleniyor, alınan: {file_extension}")
                return False
            
            # İçerik kontrolü
            if self.check_file_content:
                return self._validate_iges_content(file_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"IGES doğrulama hatası: {e}")
            return False
    
    def _check_file_exists(self, file_path: str, validation_info: Dict[str, Any]) -> bool:
        """Dosyanın var olup olmadığını kontrol et"""
        validation_info["checks_performed"].append("file_existence")
        
        if not os.path.exists(file_path):
            error_msg = ErrorMessages.FILE_NOT_FOUND.format(file_path)
            validation_info["errors"].append(error_msg)
            self.logger.error(error_msg)
            return False
        
        if not os.path.isfile(file_path):
            error_msg = f"Yol bir dosya değil: {file_path}"
            validation_info["errors"].append(error_msg)
            self.logger.error(error_msg)
            return False
        
        return True
    
    def _check_file_size(self, file_path: str, validation_info: Dict[str, Any]) -> bool:
        """Dosya boyutunu kontrol et"""
        validation_info["checks_performed"].append("file_size")
        
        try:
            file_size_bytes = os.path.getsize(file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            validation_info["file_size_bytes"] = file_size_bytes
            validation_info["file_size_mb"] = round(file_size_mb, 2)
            
            if file_size_bytes == 0:
                error_msg = f"Dosya boş: {file_path}"
                validation_info["errors"].append(error_msg)
                self.logger.error(error_msg)
                return False
            
            if file_size_mb > self.max_file_size_mb:
                error_msg = f"Dosya çok büyük: {file_size_mb:.2f}MB (limit: {self.max_file_size_mb}MB)"
                validation_info["errors"].append(error_msg)
                self.logger.error(error_msg)
                return False
            
            # Büyük dosyalar için uyarı
            if file_size_mb > self.max_file_size_mb * 0.8:
                warning_msg = f"Büyük dosya uyarısı: {file_size_mb:.2f}MB"
                validation_info["warnings"].append(warning_msg)
                self.logger.warning(warning_msg)
            
            return True
            
        except Exception as e:
            error_msg = f"Dosya boyutu kontrolü hatası: {str(e)}"
            validation_info["errors"].append(error_msg)
            self.logger.error(error_msg)
            return False
    
    def _check_file_extension(self, file_path: str, validation_info: Dict[str, Any]) -> bool:
        """Dosya uzantısını kontrol et"""
        validation_info["checks_performed"].append("file_extension")
        
        file_extension = Path(file_path).suffix.lower()
        validation_info["file_extension"] = file_extension
        
        if not file_extension:
            error_msg = f"Dosyanın uzantısı yok: {file_path}"
            validation_info["errors"].append(error_msg)
            self.logger.error(error_msg)
            return False
        
        if file_extension not in self.allowed_extensions:
            error_msg = f"Desteklenmeyen dosya uzantısı: {file_extension}"
            validation_info["errors"].append(error_msg)
            self.logger.error(error_msg)
            return False
        
        return True
    
    def _check_file_permissions(self, file_path: str, validation_info: Dict[str, Any]) -> bool:
        """Dosya okuma iznini kontrol et"""
        validation_info["checks_performed"].append("file_permissions")
        
        if not os.access(file_path, os.R_OK):
            error_msg = ErrorMessages.FILE_NOT_READABLE.format(file_path)
            validation_info["errors"].append(error_msg)
            self.logger.error(error_msg)
            return False
        
        return True
    
    def _check_file_content(self, file_path: str, validation_info: Dict[str, Any]) -> bool:
        """Dosya içeriğini kontrol et"""
        validation_info["checks_performed"].append("file_content")
        
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension in ['.step', '.stp']:
            return self._validate_step_content(file_path)
        elif file_extension in ['.iges', '.igs']:
            return self._validate_iges_content(file_path)
        else:
            # Bilinmeyen format için temel metin kontrolü
            return self._basic_text_content_check(file_path)
    
    def _validate_step_content(self, file_path: str) -> bool:
        """STEP dosyası içeriğini doğrula"""
        try:
            with open(file_path, 'rb') as f:
                # İlk birkaç KB'yi oku
                header_data = f.read(8192)  # 8KB
                
                # ASCII mi kontrol et
                try:
                    header_text = header_data.decode('ascii', errors='ignore')
                except:
                    self.logger.warning(f"STEP dosyası ASCII değil: {file_path}")
                    return False
                
                # STEP başlık kontrolü
                step_found = False
                for header in self.step_headers:
                    if header.decode('ascii') in header_text:
                        step_found = True
                        break
                
                if not step_found:
                    self.logger.warning(f"STEP başlıkları bulunamadı: {file_path}")
                    return False
                
                # Temel STEP yapısı kontrolü
                if "ENDSEC;" not in header_text:
                    self.logger.warning(f"STEP yapısı geçersiz: {file_path}")
                    return False
                
                self.logger.debug(f"STEP içerik doğrulama başarılı: {file_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"STEP içerik doğrulama hatası: {e}")
            return False
    
    def _validate_iges_content(self, file_path: str) -> bool:
        """IGES dosyası içeriğini doğrula"""
        try:
            with open(file_path, 'r', encoding='ascii', errors='ignore') as f:
                # İlk satırları oku
                lines = []
                for i, line in enumerate(f):
                    lines.append(line.strip())
                    if i >= 10:  # İlk 10 satır yeterli
                        break
                
                if not lines:
                    return False
                
                # IGES başlık kontrolü
                iges_structure_found = False
                
                # IGES dosyalarında "START" section kontrolü
                for line in lines:
                    if line.endswith('S') or 'START' in line:
                        iges_structure_found = True
                        break
                
                if not iges_structure_found:
                    self.logger.warning(f"IGES yapısı bulunamadı: {file_path}")
                    return False
                
                self.logger.debug(f"IGES içerik doğrulama başarılı: {file_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"IGES içerik doğrulama hatası: {e}")
            return False
    
    def _basic_text_content_check(self, file_path: str) -> bool:
        """Temel metin dosyası kontrolü"""
        try:
            with open(file_path, 'rb') as f:
                sample_data = f.read(1024)  # İlk 1KB
                
                # Tamamen binary mi kontrol et
                null_bytes = sample_data.count(b'\x00')
                if null_bytes > len(sample_data) * 0.3:  # %30'dan fazla null byte
                    self.logger.warning(f"Dosya binary gibi görünüyor: {file_path}")
                    return False
                
                return True
                
        except Exception as e:
            self.logger.error(f"Temel içerik kontrolü hatası: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: str, validation_info: Dict[str, Any]):
        """Dosyanın hash'ini hesapla (bütünlük kontrolü için)"""
        try:
            hash_md5 = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            
            file_hash = hash_md5.hexdigest()
            validation_info["file_hash_md5"] = file_hash
            
            self.logger.debug(f"Dosya hash'i hesaplandı: {file_hash[:8]}...")
            
        except Exception as e:
            warning_msg = f"Hash hesaplama hatası: {str(e)}"
            validation_info["warnings"].append(warning_msg)
            self.logger.warning(warning_msg)
    
    def check_file_integrity(self, file_path: str, expected_hash: str) -> bool:
        """Dosya bütünlüğünü hash ile kontrol et"""
        try:
            is_valid, info = self.validate_file(file_path)
            
            if not is_valid:
                return False
            
            current_hash = info.get("file_hash_md5")
            
            if current_hash and current_hash == expected_hash:
                self.logger.debug(f"Dosya bütünlüğü doğrulandı: {file_path}")
                return True
            else:
                self.logger.error(f"Dosya bütünlüğü hatası: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Bütünlük kontrolü hatası: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Dosya hakkında detaylı bilgi al"""
        try:
            is_valid, validation_info = self.validate_file(file_path)
            
            if not is_valid:
                return None
            
            file_stats = os.stat(file_path)
            
            info = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_extension": Path(file_path).suffix.lower(),
                "file_size_bytes": file_stats.st_size,
                "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                "created_time": self._timestamp_to_string(file_stats.st_ctime),
                "modified_time": self._timestamp_to_string(file_stats.st_mtime),
                "is_valid": is_valid,
                "validation_info": validation_info
            }
            
            # MIME type tespiti
            mime_type, encoding = mimetypes.guess_type(file_path)
            if mime_type:
                info["mime_type"] = mime_type
            if encoding:
                info["encoding"] = encoding
            
            return info
            
        except Exception as e:
            self.logger.error(f"Dosya bilgisi alma hatası: {e}")
            return None
    
    def batch_validate_files(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """Birden fazla dosyayı toplu olarak doğrula"""
        results = {}
        
        for file_path in file_paths:
            try:
                is_valid, info = self.validate_file(file_path)
                results[file_path] = {
                    "is_valid": is_valid,
                    "validation_info": info
                }
            except Exception as e:
                results[file_path] = {
                    "is_valid": False,
                    "validation_info": {"error": str(e)}
                }
        
        self.logger.info(f"Toplu doğrulama tamamlandı: {len(file_paths)} dosya")
        return results
    
    def is_safe_filename(self, filename: str) -> bool:
        """Dosya adının güvenli olup olmadığını kontrol et"""
        try:
            # Tehlikeli karakterler
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
            
            for char in dangerous_chars:
                if char in filename:
                    return False
            
            # Rezerve isimler (Windows)
            reserved_names = [
                'CON', 'PRN', 'AUX', 'NUL', 
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            ]
            
            name_without_ext = Path(filename).stem.upper()
            if name_without_ext in reserved_names:
                return False
            
            # Uzunluk kontrolü
            if len(filename) > 255:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Dosya adı güvenlik kontrolü hatası: {e}")
            return False
    
    def sanitize_filename(self, filename: str) -> str:
        """Dosya adını güvenli hale getir"""
        try:
            # Tehlikeli karakterleri değiştir
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
            sanitized = filename
            
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, '_')
            
            # Başındaki ve sonundaki boşlukları kaldır
            sanitized = sanitized.strip()
            
            # Uzunluğu sınırla
            if len(sanitized) > 250:
                name_part = Path(sanitized).stem[:240]
                ext_part = Path(sanitized).suffix
                sanitized = name_part + ext_part
            
            return sanitized
            
        except Exception as e:
            self.logger.error(f"Dosya adı temizleme hatası: {e}")
            return filename
    
    def _get_current_time(self) -> str:
        """Mevcut zamanı string olarak al"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _timestamp_to_string(self, timestamp: float) -> str:
        """Unix timestamp'i string'e çevir"""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).isoformat()
    
    def clear_validation_cache(self):
        """Validation cache'ini temizle"""
        self.validation_cache.clear()
        self.logger.debug("Validation cache temizlendi")
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Doğrulama istatistiklerini al"""
        # Bu basit bir implementation, gerçekte daha detaylı istatistik tutulabilir
        return {
            "cache_size": len(self.validation_cache),
            "max_file_size_mb": self.max_file_size_mb,
            "supported_formats": self.allowed_extensions,
            "content_check_enabled": self.check_file_content
        }