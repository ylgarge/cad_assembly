"""
Import Manager Modülü
CAD dosyalarının içe aktarılması, doğrulanması ve analizi
"""

from .step_importer import StepImporter
from .file_validator import FileValidator
from .geometry_analyzer import GeometryAnalyzer

__version__ = "1.0.0"
__author__ = "CAD Developer"

# Ana sınıfları export et
__all__ = [
    'StepImporter',
    'FileValidator', 
    'GeometryAnalyzer'
]

def create_step_importer(config=None):
    """STEP importer oluştur"""
    return StepImporter(config)

def create_file_validator(config=None):
    """File validator oluştur"""
    return FileValidator(config)

def create_geometry_analyzer(config=None):
    """Geometry analyzer oluştur"""
    return GeometryAnalyzer(config)

# Convenience function - tek fonksiyonla import
def import_cad_file(file_path: str, config=None):
    """
    CAD dosyasını içe aktar (validation + import + analysis)
    
    Args:
        file_path: CAD dosya yolu
        config: Konfigürasyon
        
    Returns:
        (shape, metadata, analysis) tuple'ı
    """
    try:
        # Validator
        validator = create_file_validator(config)
        is_valid, validation_info = validator.validate_file(file_path)
        
        if not is_valid:
            return None, validation_info, None
        
        # Importer
        importer = create_step_importer(config)
        shape, metadata = importer.import_cad_file(file_path)
        
        if shape is None:
            return None, metadata, None
        
        # Analyzer
        analyzer = create_geometry_analyzer(config)
        analysis = analyzer.analyze_imported_shape(shape, file_path)
        
        # Metadata'ya validation bilgilerini ekle
        metadata["validation"] = validation_info
        
        return shape, metadata, analysis
        
    except Exception as e:
        error_metadata = {
            "file_path": file_path,
            "error": str(e),
            "import_successful": False
        }
        return None, error_metadata, None

# Modül seviyesinde yardımcı fonksiyonlar
def get_supported_formats():
    """Desteklenen dosya formatlarını al"""
    from utils.constants import SUPPORTED_IMPORT_FORMATS
    return SUPPORTED_IMPORT_FORMATS.copy()

def is_supported_file(file_path: str) -> bool:
    """Dosyanın desteklenip desteklenmediğini kontrol et"""
    validator = create_file_validator()
    return validator.is_supported_format(file_path)

def validate_file_quick(file_path: str) -> bool:
    """Dosyayı hızlıca doğrula"""
    validator = create_file_validator()
    is_valid, _ = validator.validate_file(file_path)
    return is_valid

# Batch işlemler için
def batch_import_files(file_paths: list, config=None):
    """Birden fazla dosyayı toplu olarak içe aktar"""
    results = {}
    
    for file_path in file_paths:
        try:
            shape, metadata, analysis = import_cad_file(file_path, config)
            results[file_path] = {
                "success": shape is not None,
                "shape": shape,
                "metadata": metadata,
                "analysis": analysis
            }
        except Exception as e:
            results[file_path] = {
                "success": False,
                "error": str(e)
            }
    
    return results

def get_import_statistics(file_paths: list, config=None):
    """Dosya listesi için import istatistikleri"""
    stats = {
        "total_files": len(file_paths),
        "supported_files": 0,
        "valid_files": 0,
        "file_sizes": [],
        "formats": {}
    }
    
    validator = create_file_validator(config)
    
    for file_path in file_paths:
        # Format kontrolü
        if validator.is_supported_format(file_path):
            stats["supported_files"] += 1
            
            # Format istatistikleri
            from pathlib import Path
            ext = Path(file_path).suffix.lower()
            stats["formats"][ext] = stats["formats"].get(ext, 0) + 1
            
            # Validation
            is_valid, info = validator.validate_file(file_path)
            if is_valid:
                stats["valid_files"] += 1
                
                # Dosya boyutu
                file_size_mb = info.get("file_size_mb", 0)
                stats["file_sizes"].append(file_size_mb)
    
    # Boyut istatistikleri
    if stats["file_sizes"]:
        stats["total_size_mb"] = sum(stats["file_sizes"])
        stats["average_size_mb"] = stats["total_size_mb"] / len(stats["file_sizes"])
        stats["max_size_mb"] = max(stats["file_sizes"])
        stats["min_size_mb"] = min(stats["file_sizes"])
    
    return stats

# Modül başlatma kontrolü
def check_import_dependencies():
    """Import için gerekli bağımlılıkları kontrol et"""
    try:
        from OCC.Extend.DataExchange import read_step_file
        return True, "Import bağımlılıkları mevcut"
    except ImportError as e:
        return False, f"Import bağımlılıkları eksik: {e}"