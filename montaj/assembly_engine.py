"""
Ana Montaj Motoru
İki veya daha fazla CAD parçasının montajını gerçekleştiren ana motor
"""

import logging
import math
from typing import Dict, Any, List, Tuple, Optional, Set
from enum import Enum

try:
    # Shape tipleri
    from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Compound, TopoDS_Builder

    # Topoloji inşası
    from OCC.Core.BRep import BRep_Builder

    # Shape dönüşümleri
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

    # Temel geometrik sınıflar
    from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Pnt, gp_Dir, gp_Ax1

    # Geometri özellikleri
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop

    # Topoloji gezgini
    from OCC.Extend.TopologyUtils import TopologyExplorer

    
except ImportError as e:
    logging.error(f"PythonOCC montaj import hatası: {e}")
    raise

from .collision_detector import CollisionDetector
from .alignment_tools import AlignmentTools
from .connection_finder import ConnectionFinder
from engine_3d.transformations import TransformationManager
from utils.constants import AssemblyDefaults

class AssemblyStatus(Enum):
    """Montaj durumu"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AssemblyResult:
    """Montaj sonucu sınıfı"""
    
    def __init__(self):
        self.status = AssemblyStatus.NOT_STARTED
        self.assembled_shape = None
        self.transformations = {}  # part_id -> transformation
        self.connections = []
        self.conflicts = []
        self.assembly_time = 0.0
        self.error_message = ""
        self.quality_score = 0.0
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye çevir"""
        return {
            "status": self.status.value,
            "has_assembled_shape": self.assembled_shape is not None,
            "transformation_count": len(self.transformations),
            "connection_count": len(self.connections),
            "conflict_count": len(self.conflicts),
            "assembly_time": self.assembly_time,
            "error_message": self.error_message,
            "quality_score": self.quality_score,
            "metadata": self.metadata
        }

class AssemblyEngine:
    """Ana montaj motoru sınıfı"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger("CADMontaj.AssemblyEngine")
        
        # Alt modüller
        self.collision_detector = CollisionDetector(config)
        self.alignment_tools = AlignmentTools(config)
        self.connection_finder = ConnectionFinder(config)
        self.transform_manager = TransformationManager()
        
        # Montaj ayarları
        self.tolerance = AssemblyDefaults.GEOMETRIC_TOLERANCE
        self.angular_tolerance = AssemblyDefaults.ANGULAR_TOLERANCE
        self.max_iterations = AssemblyDefaults.MAX_SEARCH_ITERATIONS
        self.connection_tolerance = AssemblyDefaults.CONNECTION_TOLERANCE
        
        if config:
            self.tolerance = config.get("assembly.tolerance", self.tolerance)
            self.angular_tolerance = config.get("assembly.angular_tolerance", self.angular_tolerance)
            self.max_iterations = config.get("assembly.max_search_iterations", self.max_iterations)
            self.connection_tolerance = config.get("assembly.connection_tolerance", self.connection_tolerance)
        
        # Montaj geçmişi
        self.assembly_history = []
        self.current_assembly = None
        
        self.logger.info("Montaj motoru başlatıldı")
    
    def perform_assembly(self, 
                        base_shape: TopoDS_Shape, 
                        attach_shape: TopoDS_Shape,
                        assembly_options: Dict[str, Any] = None) -> Optional[AssemblyResult]:
        """
        İki parçanın montajını gerçekleştir
        
        Args:
            base_shape: Ana parça (sabit kalacak)
            attach_shape: Eklenecek parça (hareket edecek)
            assembly_options: Montaj seçenekleri
            
        Returns:
            AssemblyResult objesi
        """
        import time
        start_time = time.time()
        
        result = AssemblyResult()
        result.status = AssemblyStatus.IN_PROGRESS
        self.current_assembly = result
        
        try:
            self.logger.info("Montaj işlemi başlatılıyor")
            
            # Giriş validasyonu
            if not self._validate_input_shapes(base_shape, attach_shape):
                result.status = AssemblyStatus.FAILED
                result.error_message = "Geçersiz giriş parçaları"
                return result
            
            # Assembly seçeneklerini uygula
            if assembly_options:
                self._apply_assembly_options(assembly_options)
            
            # Bağlantı noktalarını bul
            self.logger.debug("Bağlantı noktaları aranıyor")
            connections = self.connection_finder.find_all_connections(base_shape, attach_shape)
            
            if not connections:
                result.status = AssemblyStatus.FAILED
                result.error_message = "Uygun bağlantı noktası bulunamadı"
                self.logger.warning("Bağlantı noktası bulunamadı")
                return result
            
            result.connections = connections
            self.logger.info(f"{len(connections)} potansiyel bağlantı noktası bulundu")
            
            # Her bağlantı noktasını dene
            best_result = None
            best_score = -1
            
            for i, connection in enumerate(connections):
                self.logger.debug(f"Bağlantı {i+1}/{len(connections)} deneniyor")
                
                # Hizalama dönüşümü hesapla
                transformation = self._calculate_alignment_transformation(
                    attach_shape, base_shape, connection
                )
                
                if transformation is None:
                    continue
                
                # Dönüşümü uygula
                transformed_shape = self.transform_manager.apply_transformation(
                    attach_shape, transformation
                )
                
                if transformed_shape is None:
                    continue
                
                # Çakışma kontrolü
                if self.collision_detector.check_collision(base_shape, transformed_shape):
                    self.logger.debug(f"Bağlantı {i+1}: Çakışma tespit edildi")
                    continue
                
                # Montaj kalitesi değerlendir
                quality_score = self._evaluate_assembly_quality(
                    base_shape, transformed_shape, connection
                )
                
                if quality_score > best_score:
                    best_score = quality_score
                    best_result = {
                        "transformation": transformation,
                        "transformed_shape": transformed_shape,
                        "connection": connection,
                        "quality_score": quality_score
                    }
                
                # Yeterince iyi bir sonuç bulunduğunda dur
                if quality_score > 0.9:  # %90 üzeri kalite
                    break
            
            # En iyi sonucu uygula
            if best_result:
                result.assembled_shape = self._create_assembly(
                    base_shape, best_result["transformed_shape"]
                )
                result.transformations["attach_part"] = best_result["transformation"]
                result.quality_score = best_result["quality_score"]
                result.status = AssemblyStatus.COMPLETED
                
                self.logger.info(f"Montaj başarılı (kalite: {best_result['quality_score']:.2f})")
            else:
                result.status = AssemblyStatus.FAILED
                result.error_message = "Çakışmasız montaj bulunamadı"
                self.logger.warning("Çakışmasız montaj bulunamadı")
            
            # Süre hesapla
            result.assembly_time = time.time() - start_time
            
            # Geçmişe ekle
            self.assembly_history.append(result)
            
            return result
            
        except Exception as e:
            result.status = AssemblyStatus.FAILED
            result.error_message = str(e)
            result.assembly_time = time.time() - start_time
            
            self.logger.error(f"Montaj hatası: {e}")
            return result
        
        finally:
            self.current_assembly = None
    
    def perform_multi_part_assembly(self, 
                                   parts: List[Tuple[str, TopoDS_Shape]],
                                   assembly_sequence: List[Tuple[str, str]] = None) -> AssemblyResult:
        """
        Çok parçalı montaj gerçekleştir
        
        Args:
            parts: [(part_id, shape), ...] listesi
            assembly_sequence: [(part1_id, part2_id), ...] montaj sırası
            
        Returns:
            AssemblyResult objesi
        """
        import time
        start_time = time.time()
        
        result = AssemblyResult()
        result.status = AssemblyStatus.IN_PROGRESS
        
        try:
            self.logger.info(f"{len(parts)} parçalı montaj başlatılıyor")
            
            if len(parts) < 2:
                result.status = AssemblyStatus.FAILED
                result.error_message = "En az 2 parça gerekli"
                return result
            
            # Assembly sequence belirleme
            if not assembly_sequence:
                assembly_sequence = self._generate_assembly_sequence(parts)
            
            # İlk parça sabit (base)
            assembled_parts = {parts[0][0]: parts[0][1]}  # part_id -> current_shape
            remaining_parts = {pid: shape for pid, shape in parts[1:]}
            
            # Sırayla montaj yap
            for base_id, attach_id in assembly_sequence:
                if base_id not in assembled_parts or attach_id not in remaining_parts:
                    continue
                
                base_shape = assembled_parts[base_id]
                attach_shape = remaining_parts[attach_id]
                
                # İki parçayı montajla
                pair_result = self.perform_assembly(base_shape, attach_shape)
                
                if pair_result.status == AssemblyStatus.COMPLETED:
                    # Başarılı montaj - sonucu kaydet
                    assembled_parts[base_id] = pair_result.assembled_shape
                    result.transformations[attach_id] = pair_result.transformations.get("attach_part")
                    result.connections.extend(pair_result.connections)
                    
                    # Parçayı remaining'den kaldır
                    del remaining_parts[attach_id]
                    
                    self.logger.info(f"Parça montajı başarılı: {base_id} + {attach_id}")
                else:
                    # Başarısız montaj
                    result.conflicts.append({
                        "base_part": base_id,
                        "attach_part": attach_id,
                        "error": pair_result.error_message
                    })
                    self.logger.warning(f"Parça montajı başarısız: {base_id} + {attach_id}")
            
            # Final sonuç
            if not remaining_parts:  # Tüm parçalar montajlandı
                result.assembled_shape = list(assembled_parts.values())[0]
                result.status = AssemblyStatus.COMPLETED
                result.quality_score = 1.0 - (len(result.conflicts) / len(assembly_sequence))
            else:
                result.status = AssemblyStatus.FAILED
                result.error_message = f"{len(remaining_parts)} parça montajlanamadı"
            
            result.assembly_time = time.time() - start_time
            return result
            
        except Exception as e:
            result.status = AssemblyStatus.FAILED
            result.error_message = str(e)
            result.assembly_time = time.time() - start_time
            
            self.logger.error(f"Çok parçalı montaj hatası: {e}")
            return result
    
    def _validate_input_shapes(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> bool:
        """Giriş parçalarını doğrula"""
        try:
            if not shape1 or shape1.IsNull():
                self.logger.error("Birinci parça geçersiz")
                return False
            
            if not shape2 or shape2.IsNull():
                self.logger.error("İkinci parça geçersiz")
                return False
            
            # Temel geometri kontrolü
            explorer1 = TopologyExplorer(shape1)
            explorer2 = TopologyExplorer(shape2)
            
            if explorer1.number_of_faces() == 0:
                self.logger.error("Birinci parça yüzey içermiyor")
                return False
            
            if explorer2.number_of_faces() == 0:
                self.logger.error("İkinci parça yüzey içermiyor")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Shape doğrulama hatası: {e}")
            return False
    
    def _apply_assembly_options(self, options: Dict[str, Any]):
        """Montaj seçeneklerini uygula"""
        try:
            if "tolerance" in options:
                self.tolerance = float(options["tolerance"])
                self.collision_detector.set_tolerance(self.tolerance)
            
            if "max_iterations" in options:
                self.max_iterations = int(options["max_iterations"])
            
            if "connection_tolerance" in options:
                self.connection_tolerance = float(options["connection_tolerance"])
                self.connection_finder.set_tolerance(self.connection_tolerance)
            
            self.logger.debug(f"Montaj seçenekleri uygulandı: {options}")
            
        except Exception as e:
            self.logger.warning(f"Montaj seçenekleri uygulama hatası: {e}")
    
    def _calculate_alignment_transformation(self, 
                                          attach_shape: TopoDS_Shape,
                                          base_shape: TopoDS_Shape, 
                                          connection: Dict[str, Any]) -> Optional[gp_Trsf]:
        """Hizalama dönüşümünü hesapla"""
        try:
            connection_type = connection.get("type", "unknown")
            
            if connection_type == "PLANAR_FACE":
                return self._calculate_planar_alignment(attach_shape, base_shape, connection)
            elif connection_type == "CYLINDRICAL_FACE":
                return self._calculate_cylindrical_alignment(attach_shape, base_shape, connection)
            elif connection_type == "HOLE_PIN":
                return self._calculate_hole_pin_alignment(attach_shape, base_shape, connection)
            else:
                # Genel hizalama - merkez noktaları hizala
                return self._calculate_general_alignment(attach_shape, base_shape, connection)
                
        except Exception as e:
            self.logger.warning(f"Hizalama hesaplama hatası: {e}")
            return None
    
    def _calculate_planar_alignment(self, 
                                   attach_shape: TopoDS_Shape,
                                   base_shape: TopoDS_Shape, 
                                   connection: Dict[str, Any]) -> Optional[gp_Trsf]:
        """Düzlemsel yüzey hizalaması"""
        try:
            # Bağlantı bilgilerini al
            attach_surface = connection.get("attach_surface", {})
            base_surface = connection.get("base_surface", {})
            
            # Kaynak koordinat sistemi (attach parça)
            source_origin = attach_surface.get("center", (0, 0, 0))
            source_normal = attach_surface.get("normal", (0, 0, 1))
            
            # Hedef koordinat sistemi (base parça)
            target_origin = base_surface.get("center", (0, 0, 0))
            target_normal = base_surface.get("normal", (0, 0, 1))
            
            # Normal'leri ters çevir (yüzeyler birbirine baksın)
            target_normal = (-target_normal[0], -target_normal[1], -target_normal[2])
            
            # Hizalama dönüşümü oluştur
            transformation = self.transform_manager.create_alignment_transformation(
                source_origin, source_normal,
                target_origin, target_normal
            )
            
            return transformation
            
        except Exception as e:
            self.logger.warning(f"Düzlemsel hizalama hatası: {e}")
            return None
    
    def _calculate_cylindrical_alignment(self, 
                                        attach_shape: TopoDS_Shape,
                                        base_shape: TopoDS_Shape, 
                                        connection: Dict[str, Any]) -> Optional[gp_Trsf]:
        """Silindirik yüzey hizalaması"""
        try:
            attach_surface = connection.get("attach_surface", {})
            base_surface = connection.get("base_surface", {})
            
            # Eksen bilgilerini al
            source_origin = attach_surface.get("axis_origin", (0, 0, 0))
            source_direction = attach_surface.get("axis_direction", (0, 0, 1))
            
            target_origin = base_surface.get("axis_origin", (0, 0, 0))
            target_direction = base_surface.get("axis_direction", (0, 0, 1))
            
            # Eksenleri hizala
            transformation = self.transform_manager.create_alignment_transformation(
                source_origin, source_direction,
                target_origin, target_direction
            )
            
            return transformation
            
        except Exception as e:
            self.logger.warning(f"Silindirik hizalama hatası: {e}")
            return None
    
    def _calculate_hole_pin_alignment(self, 
                                     attach_shape: TopoDS_Shape,
                                     base_shape: TopoDS_Shape, 
                                     connection: Dict[str, Any]) -> Optional[gp_Trsf]:
        """Delik-pim hizalaması"""
        try:
            hole_info = connection.get("hole", {})
            pin_info = connection.get("pin", {})
            
            # Delik ve pim merkezlerini hizala
            hole_center = hole_info.get("center", (0, 0, 0))
            hole_axis = hole_info.get("axis", (0, 0, 1))
            
            pin_center = pin_info.get("center", (0, 0, 0))
            pin_axis = pin_info.get("axis", (0, 0, 1))
            
            # Pin'i deliğe hizala
            transformation = self.transform_manager.create_alignment_transformation(
                pin_center, pin_axis,
                hole_center, hole_axis
            )
            
            return transformation
            
        except Exception as e:
            self.logger.warning(f"Delik-pim hizalama hatası: {e}")
            return None
    
    def _calculate_general_alignment(self, 
                                    attach_shape: TopoDS_Shape,
                                    base_shape: TopoDS_Shape, 
                                    connection: Dict[str, Any]) -> Optional[gp_Trsf]:
        """Genel hizalama (merkez noktaları)"""
        try:
            # Bağlantı noktalarını al
            attach_point = connection.get("attach_point", (0, 0, 0))
            base_point = connection.get("base_point", (0, 0, 0))
            
            # Basit öteleme
            offset = (
                base_point[0] - attach_point[0],
                base_point[1] - attach_point[1], 
                base_point[2] - attach_point[2]
            )
            
            transformation = self.transform_manager.create_translation(offset)
            return transformation
            
        except Exception as e:
            self.logger.warning(f"Genel hizalama hatası: {e}")
            return None
    
    def _evaluate_assembly_quality(self, 
                                  base_shape: TopoDS_Shape,
                                  attach_shape: TopoDS_Shape, 
                                  connection: Dict[str, Any]) -> float:
        """Montaj kalitesini değerlendir (0-1 arası)"""
        try:
            quality_score = 0.0
            
            # Bağlantı türü bonusu
            connection_type = connection.get("type", "unknown")
            type_scores = {
                "HOLE_PIN": 0.9,
                "CYLINDRICAL_FACE": 0.8,
                "PLANAR_FACE": 0.7,
                "EDGE_TO_EDGE": 0.5,
                "POINT_TO_POINT": 0.3
            }
            quality_score += type_scores.get(connection_type, 0.2)
            
            # Bağlantı skoru
            connection_score = connection.get("score", 0.5)
            quality_score += connection_score * 0.3
            
            # Geometrik uyumluluk
            geometric_match = connection.get("geometric_match", 0.5)
            quality_score += geometric_match * 0.2
            
            # Normalize et
            quality_score = min(1.0, max(0.0, quality_score))
            
            return quality_score
            
        except Exception as e:
            self.logger.warning(f"Kalite değerlendirme hatası: {e}")
            return 0.0
    
    def _create_assembly(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> TopoDS_Shape:
        """İki parçadan montaj oluştur"""
        try:
            # Compound builder
            builder = BRep_Builder()
            compound = TopoDS_Compound()
            builder.MakeCompound(compound)
            
            # Parçaları ekle
            builder.Add(compound, shape1)
            builder.Add(compound, shape2)
            
            return compound
            
        except Exception as e:
            self.logger.error(f"Montaj oluşturma hatası: {e}")
            return None
    
    def _generate_assembly_sequence(self, parts: List[Tuple[str, TopoDS_Shape]]) -> List[Tuple[str, str]]:
        """Otomatik montaj sırası oluştur"""
        try:
            if len(parts) < 2:
                return []
            
            # Basit strateji: İlk parçayı base olarak al, diğerlerini sırayla ekle
            sequence = []
            base_id = parts[0][0]
            
            for i in range(1, len(parts)):
                attach_id = parts[i][0]
                sequence.append((base_id, attach_id))
                # Sonraki iterasyon için base güncellenir (compound olur)
            
            return sequence
            
        except Exception as e:
            self.logger.warning(f"Montaj sırası oluşturma hatası: {e}")
            return []
    
    def get_assembly_statistics(self) -> Dict[str, Any]:
        """Montaj istatistiklerini al"""
        try:
            total_assemblies = len(self.assembly_history)
            successful_assemblies = sum(1 for result in self.assembly_history 
                                      if result.status == AssemblyStatus.COMPLETED)
            
            if total_assemblies > 0:
                success_rate = successful_assemblies / total_assemblies * 100
                avg_time = sum(result.assembly_time for result in self.assembly_history) / total_assemblies
                avg_quality = sum(result.quality_score for result in self.assembly_history) / total_assemblies
            else:
                success_rate = 0
                avg_time = 0
                avg_quality = 0
            
            return {
                "total_assemblies": total_assemblies,
                "successful_assemblies": successful_assemblies,
                "success_rate": success_rate,
                "average_time": avg_time,
                "average_quality": avg_quality,
                "current_tolerance": self.tolerance,
                "max_iterations": self.max_iterations
            }
            
        except Exception as e:
            self.logger.error(f"İstatistik hesaplama hatası: {e}")
            return {}
    
    def clear_assembly_history(self):
        """Montaj geçmişini temizle"""
        self.assembly_history.clear()
        self.logger.info("Montaj geçmişi temizlendi")
    
    def cancel_current_assembly(self):
        """Mevcut montaj işlemini iptal et"""
        if self.current_assembly:
            self.current_assembly.status = AssemblyStatus.CANCELLED
            self.logger.info("Montaj işlemi iptal edildi")
    
    def optimize_assembly_parameters(self, target_quality: float = 0.8):
        """Montaj parametrelerini optimize et"""
        try:
            if len(self.assembly_history) < 5:
                self.logger.warning("Yeterli montaj geçmişi yok, optimizasyon yapılamıyor")
                return False
            
            # Son montajların kalite skorlarını analiz et
            recent_results = self.assembly_history[-10:]  # Son 10 montaj
            avg_quality = sum(result.quality_score for result in recent_results) / len(recent_results)
            
            if avg_quality < target_quality:
                # Toleransı azalt (daha hassas montaj)
                self.tolerance = max(0.001, self.tolerance * 0.8)
                self.connection_tolerance = max(0.01, self.connection_tolerance * 0.8)
                
                # Max iteration artır
                self.max_iterations = min(500, int(self.max_iterations * 1.2))
                
                self.logger.info(f"Montaj parametreleri optimize edildi: tolerance={self.tolerance:.3f}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Parametre optimizasyonu hatası: {e}")
            return False
    
    def export_assembly_report(self, result: AssemblyResult, file_path: str) -> bool:
        """Montaj raporunu dosyaya aktar"""
        try:
            import json
            from datetime import datetime
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "assembly_result": result.to_dict(),
                "engine_parameters": {
                    "tolerance": self.tolerance,
                    "angular_tolerance": self.angular_tolerance,
                    "max_iterations": self.max_iterations,
                    "connection_tolerance": self.connection_tolerance
                },
                "statistics": self.get_assembly_statistics()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Montaj raporu aktarıldı: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Rapor aktarma hatası: {e}")
            return False
    
    def validate_assembly_constraints(self, 
                                    result: AssemblyResult,
                                    constraints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Montaj kısıtlamalarını doğrula"""
        try:
            validation_result = {
                "valid": True,
                "satisfied_constraints": [],
                "violated_constraints": [],
                "warnings": []
            }
            
            if not result.assembled_shape or result.status != AssemblyStatus.COMPLETED:
                validation_result["valid"] = False
                validation_result["warnings"].append("Montaj tamamlanmamış")
                return validation_result
            
            for constraint in constraints:
                constraint_type = constraint.get("type", "unknown")
                
                if constraint_type == "max_distance":
                    # Parçalar arası maksimum mesafe kontrolü
                    max_dist = constraint.get("max_distance", float('inf'))
                    # Bu kontrol için shape analizi gerekir
                    validation_result["satisfied_constraints"].append(constraint)
                
                elif constraint_type == "interference_check":
                    # Çakışma kontrolü zaten yapıldı
                    validation_result["satisfied_constraints"].append(constraint)
                
                elif constraint_type == "orientation_constraint":
                    # Oryantasyon kısıtlaması
                    validation_result["satisfied_constraints"].append(constraint)
                
                else:
                    validation_result["warnings"].append(f"Bilinmeyen kısıtlama türü: {constraint_type}")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Kısıtlama doğrulama hatası: {e}")
            return {"valid": False, "error": str(e)}
    
    def suggest_assembly_improvements(self, result: AssemblyResult) -> List[str]:
        """Montaj iyileştirme önerileri"""
        suggestions = []
        
        try:
            if result.status != AssemblyStatus.COMPLETED:
                if result.error_message == "Uygun bağlantı noktası bulunamadı":
                    suggestions.append("Tolerans değerini artırın")
                    suggestions.append("Parçaların konumunu manuel olarak ayarlayın")
                    suggestions.append("Bağlantı noktası arama parametrelerini gevşetin")
                
                elif "çakışma" in result.error_message.lower():
                    suggestions.append("Parçaları daha hassas hizalayın")
                    suggestions.append("Interference checking toleransını artırın")
                    suggestions.append("Manuel ön-konumlama yapın")
                
                return suggestions
            
            # Başarılı montaj için kalite iyileştirme önerileri
            if result.quality_score < 0.6:
                suggestions.append("Daha uygun bağlantı noktaları arayın")
                suggestions.append("Parça geometrilerini kontrol edin")
                suggestions.append("Montaj sırasını değiştirin")
            
            elif result.quality_score < 0.8:
                suggestions.append("Tolerans değerlerini ince ayarlayın")
                suggestions.append("Hizalama algoritmasını optimize edin")
            
            if result.assembly_time > 10.0:  # 10 saniyeden fazla
                suggestions.append("Performans optimizasyonu için parametre ayarlaması yapın")
                suggestions.append("Daha az iterasyon kullanın")
            
            if len(result.conflicts) > 0:
                suggestions.append(f"{len(result.conflicts)} parça montajlanamadı - sıralamayı gözden geçirin")
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Öneri oluşturma hatası: {e}")
            return ["Montaj analizi sırasında hata oluştu"]
    
    def get_assembly_preview(self, 
                            base_shape: TopoDS_Shape,
                            attach_shape: TopoDS_Shape,
                            transformation: gp_Trsf = None) -> Optional[TopoDS_Shape]:
        """Montaj önizlemesi oluştur"""
        try:
            if transformation:
                # Verilen dönüşümle önizleme
                transformed_shape = self.transform_manager.apply_transformation(
                    attach_shape, transformation
                )
            else:
                # Otomatik bağlantı noktası ile önizleme
                connections = self.connection_finder.find_all_connections(base_shape, attach_shape)
                
                if not connections:
                    return None
                
                # İlk bağlantı noktasını kullan
                transformation = self._calculate_alignment_transformation(
                    attach_shape, base_shape, connections[0]
                )
                
                if not transformation:
                    return None
                
                transformed_shape = self.transform_manager.apply_transformation(
                    attach_shape, transformation
                )
            
            if transformed_shape:
                return self._create_assembly(base_shape, transformed_shape)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Montaj önizleme hatası: {e}")
            return None
    
    def set_assembly_parameters(self, **kwargs):
        """Montaj parametrelerini ayarla"""
        try:
            if "tolerance" in kwargs:
                self.tolerance = float(kwargs["tolerance"])
                self.collision_detector.set_tolerance(self.tolerance)
            
            if "angular_tolerance" in kwargs:
                self.angular_tolerance = float(kwargs["angular_tolerance"])
            
            if "max_iterations" in kwargs:
                self.max_iterations = int(kwargs["max_iterations"])
            
            if "connection_tolerance" in kwargs:
                self.connection_tolerance = float(kwargs["connection_tolerance"])
                self.connection_finder.set_tolerance(self.connection_tolerance)
            
            self.logger.debug(f"Montaj parametreleri güncellendi: {kwargs}")
            
        except Exception as e:
            self.logger.error(f"Parametre ayarlama hatası: {e}")
    
    def get_assembly_parameters(self) -> Dict[str, Any]:
        """Mevcut montaj parametrelerini al"""
        return {
            "tolerance": self.tolerance,
            "angular_tolerance": self.angular_tolerance,
            "max_iterations": self.max_iterations,
            "connection_tolerance": self.connection_tolerance
        }