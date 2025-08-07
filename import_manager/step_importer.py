"""
STEP Dosya İçe Aktarma Modülü
STEP formatında CAD dosyalarının içe aktarılması
"""

import logging
import os
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

try:
    from OCC.Extend.DataExchange import read_step_file, read_iges_file
    from OCC.Core import (
        # STEP okuma
        STEPControl_Reader, IFSelect_ReturnStatus,
        
        # Shape kontrolleri
        TopoDS_Shape, TopoDS_Compound,
        
        # Healing (shape onarımı)
        ShapeFix_Shape,
        
        # Units
        Interface_Static,
        
        # Topology
        BRep_Builder, TopoDS_Builder
    )
    from OCC.Extend.TopologyUtils import TopologyExplorer
    
except ImportError as e:
    logging.error(f"PythonOCC STEP import hatası: {e}")
    raise

from .file_validator import FileValidator
from .geometry_analyzer import GeometryAnalyzer
from utils.constants import SUPPORTED_IMPORT_FORMATS, ErrorMessages, SuccessMessages

class StepImporter:
    """STEP ve IGES dosyalarını içe aktaran sınıf"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger("CADMontaj.StepImporter")
        
        # Validator ve analyzer
        self.validator = FileValidator(config)
        self.analyzer = GeometryAnalyzer(config)
        
        # Import ayarları
        self.healing_enabled = True
        self.merge_compounds = True
        self.import_units = "mm"
        
        if config:
            self.healing_enabled = config.get("import.healing_shapes", True)
            self.import_units = config.get("import.import_units", "mm")
        
        # İstatistikler
        self.import_stats = {
            "total_imports": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "last_import_time": None
        }
    
    def import_step_file(self, file_path: str) -> Tuple[Optional[TopoDS_Shape], Dict[str, Any]]:
        """
        STEP dosyasını içe aktar
        
        Args:
            file_path: STEP dosyası yolu
            
        Returns:
            (shape, metadata) tuple'ı
        """
        try:
            self.logger.info(f"STEP dosyası içe aktarılıyor: {file_path}")
            
            # Dosya doğrulama
            if not self.validator.validate_step_file(file_path):
                raise ValueError(f"Geçersiz STEP dosyası: {file_path}")
            
            # Import başlat
            import_start_time = self._get_current_time()
            
            # STEP okuma
            shape = self._read_step_file(file_path)
            
            if not shape or shape.IsNull():
                raise ValueError("STEP dosyası okunamadı veya boş")
            
            # Shape healing (eğer etkinse)
            if self.healing_enabled:
                shape = self._heal_shape(shape)
            
            # Geometrik analiz
            analysis_data = self.analyzer.analyze_imported_shape(shape, file_path)
            
            # Metadata oluştur
            metadata = self._create_import_metadata(file_path, import_start_time, analysis_data)
            
            # İstatistikleri güncelle
            self._update_import_stats(True, import_start_time)
            
            self.logger.info(f"STEP dosyası başarıyla içe aktarıldı: {file_path}")
            return shape, metadata
            
        except Exception as e:
            error_msg = f"STEP import hatası: {str(e)}"
            self.logger.error(error_msg)
            self._update_import_stats(False, self._get_current_time())
            
            # Hata metadata'sı
            error_metadata = {
                "file_path": file_path,
                "error": str(e),
                "import_successful": False,
                "import_time": self._get_current_time()
            }
            
            return None, error_metadata
    
    def import_iges_file(self, file_path: str) -> Tuple[Optional[TopoDS_Shape], Dict[str, Any]]:
        """
        IGES dosyasını içe aktar
        
        Args:
            file_path: IGES dosyası yolu
            
        Returns:
            (shape, metadata) tuple'ı
        """
        try:
            self.logger.info(f"IGES dosyası içe aktarılıyor: {file_path}")
            
            # Dosya doğrulama
            if not self.validator.validate_iges_file(file_path):
                raise ValueError(f"Geçersiz IGES dosyası: {file_path}")
            
            import_start_time = self._get_current_time()
            
            # IGES okuma
            shape = self._read_iges_file(file_path)
            
            if not shape or shape.IsNull():
                raise ValueError("IGES dosyası okunamadı veya boş")
            
            # Shape healing
            if self.healing_enabled:
                shape = self._heal_shape(shape)
            
            # Geometrik analiz  
            analysis_data = self.analyzer.analyze_imported_shape(shape, file_path)
            
            # Metadata
            metadata = self._create_import_metadata(file_path, import_start_time, analysis_data)
            
            self._update_import_stats(True, import_start_time)
            
            self.logger.info(f"IGES dosyası başarıyla içe aktarıldı: {file_path}")
            return shape, metadata
            
        except Exception as e:
            error_msg = f"IGES import hatası: {str(e)}"
            self.logger.error(error_msg)
            self._update_import_stats(False, self._get_current_time())
            
            error_metadata = {
                "file_path": file_path,
                "error": str(e),
                "import_successful": False,
                "import_time": self._get_current_time()
            }
            
            return None, error_metadata
    
    def import_cad_file(self, file_path: str) -> Tuple[Optional[TopoDS_Shape], Dict[str, Any]]:
        """
        CAD dosyasını formatına göre içe aktar (otomatik format tespiti)
        
        Args:
            file_path: CAD dosyası yolu
            
        Returns:
            (shape, metadata) tuple'ı
        """
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension in ['.step', '.stp']:
                return self.import_step_file(file_path)
            elif file_extension in ['.iges', '.igs']:
                return self.import_iges_file(file_path)
            else:
                raise ValueError(f"Desteklenmeyen dosya formatı: {file_extension}")
                
        except Exception as e:
            self.logger.error(f"CAD dosya import hatası: {e}")
            return None, {"error": str(e)}
    
    def _read_step_file(self, file_path: str) -> Optional[TopoDS_Shape]:
        """STEP dosyasını oku"""
        try:
            # PythonOCC'nin read_step_file fonksiyonunu kullan
            shape = read_step_file(file_path)
            
            if shape and not shape.IsNull():
                self.logger.debug(f"STEP shape başarıyla okundu: {file_path}")
                return shape
            else:
                # Manuel okuma dene
                return self._manual_step_read(file_path)
                
        except Exception as e:
            self.logger.warning(f"STEP okuma hatası, manuel okuma deneniyor: {e}")
            return self._manual_step_read(file_path)
    
    def _manual_step_read(self, file_path: str) -> Optional[TopoDS_Shape]:
        """Manuel STEP okuma (daha detaylı kontrol için)"""
        try:
            reader = STEPControl_Reader()
            
            # Dosyayı oku
            status = reader.ReadFile(file_path)
            
            if status == IFSelect_ReturnStatus.IFSelect_RetDone:
                # Root'ları transfer et
                reader.PrintCheckTransfer(False, IFSelect_ReturnStatus.IFSelect_RetDone)
                
                # Shape'leri transfer et
                nb_roots = reader.NbRootsForTransfer()
                self.logger.debug(f"STEP dosyasında {nb_roots} root bulundu")
                
                if nb_roots > 0:
                    reader.TransferRoots()
                    nb_shapes = reader.NbShapes()
                    
                    if nb_shapes > 0:
                        if nb_shapes == 1:
                            # Tek shape
                            return reader.Shape(1)
                        else:
                            # Birden fazla shape - compound oluştur
                            return self._create_compound_from_shapes(reader, nb_shapes)
                    
            self.logger.error(f"STEP dosyası okunamadı: {file_path}")
            return None
            
        except Exception as e:
            self.logger.error(f"Manuel STEP okuma hatası: {e}")
            return None
    
    def _read_iges_file(self, file_path: str) -> Optional[TopoDS_Shape]:
        """IGES dosyasını oku"""
        try:
            # PythonOCC'nin read_iges_file fonksiyonunu kullan
            shape = read_iges_file(file_path)
            
            if shape and not shape.IsNull():
                self.logger.debug(f"IGES shape başarıyla okundu: {file_path}")
                return shape
            else:
                self.logger.error(f"IGES dosyası okunamadı: {file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"IGES okuma hatası: {e}")
            return None
    
    def _create_compound_from_shapes(self, reader: STEPControl_Reader, nb_shapes: int) -> TopoDS_Shape:
        """Birden fazla shape'ten compound oluştur"""
        try:
            builder = BRep_Builder()
            compound = TopoDS_Compound()
            builder.MakeCompound(compound)
            
            for i in range(1, nb_shapes + 1):
                shape = reader.Shape(i)
                if not shape.IsNull():
                    builder.Add(compound, shape)
            
            self.logger.debug(f"Compound oluşturuldu: {nb_shapes} shape")
            return compound
            
        except Exception as e:
            self.logger.error(f"Compound oluşturma hatası: {e}")
            return None
    
    def _heal_shape(self, shape: TopoDS_Shape) -> TopoDS_Shape:
        """Shape'i onar (geometrik problemleri düzelt)"""
        try:
            if not shape or shape.IsNull():
                return shape
            
            self.logger.debug("Shape healing işlemi başlatılıyor")
            
            # ShapeFix_Shape kullan
            shape_fixer = ShapeFix_Shape(shape)
            shape_fixer.Perform()
            
            healed_shape = shape_fixer.Shape()
            
            if healed_shape and not healed_shape.IsNull():
                self.logger.debug("Shape healing başarılı")
                return healed_shape
            else:
                self.logger.warning("Shape healing başarısız, orijinal shape döndürülüyor")
                return shape
                
        except Exception as e:
            self.logger.warning(f"Shape healing hatası: {e}")
            return shape  # Orijinal shape'i döndür
    
    def _create_import_metadata(self, 
                               file_path: str, 
                               start_time: str, 
                               analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import metadata'sını oluştur"""
        try:
            file_info = os.stat(file_path)
            
            metadata = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size_bytes": file_info.st_size,
                "file_extension": Path(file_path).suffix.lower(),
                "import_time": start_time,
                "import_successful": True,
                "healing_applied": self.healing_enabled,
                "import_units": self.import_units,
                "geometry_analysis": analysis_data
            }
            
            # Dosya timestamp'leri
            metadata["file_created"] = self._timestamp_to_string(file_info.st_ctime)
            metadata["file_modified"] = self._timestamp_to_string(file_info.st_mtime)
            
            return metadata
            
        except Exception as e:
            self.logger.warning(f"Metadata oluşturma hatası: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "import_time": start_time,
                "import_successful": True
            }
    
    def _update_import_stats(self, success: bool, import_time: str):
        """Import istatistiklerini güncelle"""
        self.import_stats["total_imports"] += 1
        self.import_stats["last_import_time"] = import_time
        
        if success:
            self.import_stats["successful_imports"] += 1
        else:
            self.import_stats["failed_imports"] += 1
    
    def _get_current_time(self) -> str:
        """Mevcut zamanı string olarak al"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _timestamp_to_string(self, timestamp: float) -> str:
        """Unix timestamp'i string'e çevir"""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).isoformat()
    
    def get_import_statistics(self) -> Dict[str, Any]:
        """Import istatistiklerini al"""
        stats = self.import_stats.copy()
        
        if stats["total_imports"] > 0:
            stats["success_rate"] = stats["successful_imports"] / stats["total_imports"] * 100
        else:
            stats["success_rate"] = 0
            
        return stats
    
    def reset_import_statistics(self):
        """Import istatistiklerini sıfırla"""
        self.import_stats = {
            "total_imports": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "last_import_time": None
        }
        self.logger.info("Import istatistikleri sıfırlandı")
    
    def set_import_options(self, 
                          healing_enabled: bool = None,
                          import_units: str = None,
                          merge_compounds: bool = None):
        """Import seçeneklerini ayarla"""
        if healing_enabled is not None:
            self.healing_enabled = healing_enabled
            self.logger.debug(f"Healing ayarlandı: {healing_enabled}")
            
        if import_units is not None:
            self.import_units = import_units
            self.logger.debug(f"Import birimleri ayarlandı: {import_units}")
            
        if merge_compounds is not None:
            self.merge_compounds = merge_compounds
            self.logger.debug(f"Compound birleştirme ayarlandı: {merge_compounds}")
    
    def get_supported_formats(self) -> List[str]:
        """Desteklenen formatları al"""
        return SUPPORTED_IMPORT_FORMATS.copy()
    
    def is_supported_format(self, file_path: str) -> bool:
        """Dosya formatının desteklenip desteklenmediğini kontrol et"""
        file_extension = Path(file_path).suffix.lower()
        return file_extension in SUPPORTED_IMPORT_FORMATS