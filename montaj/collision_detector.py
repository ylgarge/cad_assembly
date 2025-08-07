"""
Çakışma Kontrol Modülü
CAD parçaları arasındaki çakışmaları tespit eden sistem
"""

import logging
import time
from typing import Dict, Any, List, Tuple, Optional, Set
from enum import Enum

try:
    from OCC.Core import (
        TopoDS_Shape, TopoDS_Solid, TopoDS_Face, TopoDS_Edge,
        BRepExtrema_DistShapeShape, BRepAlgoAPI_Common, BRepAlgoAPI_Cut,
        BRepBuilderAPI_MakeVertex, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace,
        Bnd_Box, BRepBndLib, BRepMesh_IncrementalMesh,
        GProp_GProps, BRepGProp,
        gp_Pnt, Precision, TopAbs_SOLID, TopAbs_FACE, TopAbs_EDGE,
        BRep_Tool, TopExp_Explorer, TopAbs_ShapeEnum
    )
    from OCC.Extend.TopologyUtils import TopologyExplorer
    
except ImportError as e:
    logging.error(f"PythonOCC collision detection import hatası: {e}")
    raise

from utils.constants import AssemblyDefaults

class CollisionType(Enum):
    """Çakışma türleri"""
    NO_COLLISION = "no_collision"
    TOUCHING = "touching"
    OVERLAPPING = "overlapping"
    PENETRATING = "penetrating"
    CONTAINING = "containing"

class CollisionInfo:
    """Çakışma bilgi sınıfı"""
    
    def __init__(self):
        self.collision_type = CollisionType.NO_COLLISION
        self.distance = float('inf')
        self.overlap_volume = 0.0
        self.contact_area = 0.0
        self.contact_points = []
        self.collision_geometry = None
        self.analysis_time = 0.0
        self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye çevir"""
        return {
            "collision_type": self.collision_type.value,
            "distance": self.distance if self.distance != float('inf') else None,
            "overlap_volume": self.overlap_volume,
            "contact_area": self.contact_area,
            "contact_point_count": len(self.contact_points),
            "has_collision_geometry": self.collision_geometry is not None,
            "analysis_time": self.analysis_time,
            "details": self.details
        }

class CollisionDetector:
    """Çakışma tespit sistemi"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger("CADMontaj.CollisionDetector")
        
        # Toleranslar
        self.linear_tolerance = Precision.Confusion()  # ~1e-7
        self.touch_tolerance = 0.001  # 0.001 mm - dokunma toleransı
        self.overlap_tolerance = AssemblyDefaults.MAX_COLLISION_OVERLAP
        
        if config:
            self.touch_tolerance = config.get("assembly.tolerance", self.touch_tolerance)
            self.overlap_tolerance = config.get("assembly.max_collision_overlap", self.overlap_tolerance)
        
        # Performance ayarları
        self.use_bounding_box_precheck = True
        self.use_mesh_approximation = False
        self.mesh_quality = 0.1  # Mesh kalitesi
        
        # Cache
        self.bounding_box_cache = {}
        self.collision_cache = {}
        
        # İstatistikler
        self.collision_checks = 0
        self.cache_hits = 0
        self.total_analysis_time = 0.0
        
        self.logger.debug("Collision detector başlatıldı")
    
    def check_collision(self, 
                       shape1: TopoDS_Shape, 
                       shape2: TopoDS_Shape,
                       detailed: bool = False) -> bool:
        """
        Temel çakışma kontrolü
        
        Args:
            shape1: İlk parça
            shape2: İkinci parça
            detailed: Detaylı analiz yapılsın mı
            
        Returns:
            True = çakışma var, False = çakışma yok
        """
        collision_info = self.analyze_collision(shape1, shape2, detailed)
        return collision_info.collision_type != CollisionType.NO_COLLISION
    
    def analyze_collision(self, 
                         shape1: TopoDS_Shape, 
                         shape2: TopoDS_Shape,
                         detailed: bool = True) -> CollisionInfo:
        """
        Detaylı çakışma analizi
        
        Args:
            shape1: İlk parça
            shape2: İkinci parça
            detailed: Detaylı analiz yapılsın mı
            
        Returns:
            CollisionInfo objesi
        """
        start_time = time.time()
        self.collision_checks += 1
        
        collision_info = CollisionInfo()
        
        try:
            self.logger.debug("Çakışma analizi başlatılıyor")
            
            # Giriş validasyonu
            if not self._validate_shapes(shape1, shape2):
                collision_info.details["error"] = "Geçersiz shape'ler"
                return collision_info
            
            # Cache kontrolü
            cache_key = self._generate_cache_key(shape1, shape2)
            if cache_key in self.collision_cache and not detailed:
                self.cache_hits += 1
                return self.collision_cache[cache_key].copy()
            
            # Bounding box ön kontrolü
            if self.use_bounding_box_precheck:
                if not self._bounding_boxes_intersect(shape1, shape2):
                    collision_info.collision_type = CollisionType.NO_COLLISION
                    collision_info.distance = self._calculate_bounding_box_distance(shape1, shape2)
                    collision_info.analysis_time = time.time() - start_time
                    return collision_info
            
            # Mesafe hesaplama
            distance = self._calculate_minimum_distance(shape1, shape2)
            collision_info.distance = distance
            
            # Çakışma türü belirleme
            if distance > self.touch_tolerance:
                collision_info.collision_type = CollisionType.NO_COLLISION
            elif distance > self.linear_tolerance:
                collision_info.collision_type = CollisionType.TOUCHING
                if detailed:
                    collision_info.contact_points = self._find_contact_points(shape1, shape2)
            else:
                # Çakışma var - türünü belirle
                collision_info = self._analyze_overlap(shape1, shape2, collision_info)
            
            # Detaylı analiz
            if detailed and collision_info.collision_type != CollisionType.NO_COLLISION:
                collision_info = self._perform_detailed_analysis(shape1, shape2, collision_info)
            
            collision_info.analysis_time = time.time() - start_time
            self.total_analysis_time += collision_info.analysis_time
            
            # Cache'e ekle
            if not detailed:
                self.collision_cache[cache_key] = collision_info
            
            self.logger.debug(f"Çakışma analizi tamamlandı: {collision_info.collision_type.value}")
            return collision_info
            
        except Exception as e:
            collision_info.details["error"] = str(e)
            collision_info.analysis_time = time.time() - start_time
            self.logger.error(f"Çakışma analizi hatası: {e}")
            return collision_info
    
    def batch_collision_check(self, 
                             shapes: List[Tuple[str, TopoDS_Shape]]) -> Dict[Tuple[str, str], CollisionInfo]:
        """
        Birden fazla parça arasında toplu çakışma kontrolü
        
        Args:
            shapes: [(shape_id, shape), ...] listesi
            
        Returns:
            {(shape_id1, shape_id2): CollisionInfo, ...}
        """
        results = {}
        
        try:
            self.logger.info(f"Toplu çakışma kontrolü başlatılıyor: {len(shapes)} parça")
            
            # Tüm parça çiftlerini kontrol et
            for i in range(len(shapes)):
                for j in range(i + 1, len(shapes)):
                    id1, shape1 = shapes[i]
                    id2, shape2 = shapes[j]
                    
                    collision_info = self.analyze_collision(shape1, shape2, detailed=False)
                    results[(id1, id2)] = collision_info
            
            # İstatistikleri logla
            collision_count = sum(1 for info in results.values() 
                                if info.collision_type != CollisionType.NO_COLLISION)
            
            self.logger.info(f"Toplu çakışma kontrolü tamamlandı: {collision_count} çakışma tespit edildi")
            return results
            
        except Exception as e:
            self.logger.error(f"Toplu çakışma kontrolü hatası: {e}")
            return results
    
    def _validate_shapes(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> bool:
        """Shape'lerin geçerliliğini kontrol et"""
        try:
            if not shape1 or shape1.IsNull():
                return False
            if not shape2 or shape2.IsNull():
                return False
            return True
        except:
            return False
    
    def _generate_cache_key(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> str:
        """Cache key oluştur"""
        try:
            # Basit hash tabanlı key (gerçek uygulamada shape geometry hash'i kullanılabilir)
            hash1 = hash(str(shape1.TShape()))
            hash2 = hash(str(shape2.TShape()))
            return f"{min(hash1, hash2)}_{max(hash1, hash2)}"
        except:
            return f"{id(shape1)}_{id(shape2)}"
    
    def _bounding_boxes_intersect(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> bool:
        """Bounding box'ların kesişip kesişmediğini kontrol et"""
        try:
            bbox1 = self._get_bounding_box(shape1)
            bbox2 = self._get_bounding_box(shape2)
            
            if bbox1.IsVoid() or bbox2.IsVoid():
                return False
            
            # Bounding box değerlerini al
            xmin1, ymin1, zmin1, xmax1, ymax1, zmax1 = bbox1.Get()
            xmin2, ymin2, zmin2, xmax2, ymax2, zmax2 = bbox2.Get()
            
            # Kesişim kontrolü
            if (xmax1 < xmin2 or xmax2 < xmin1 or
                ymax1 < ymin2 or ymax2 < ymin1 or
                zmax1 < zmin2 or zmax2 < zmin1):
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Bounding box kesişim kontrolü hatası: {e}")
            return True  # Güvenli taraf
    
    def _get_bounding_box(self, shape: TopoDS_Shape) -> Bnd_Box:
        """Shape'in bounding box'ını al"""
        try:
            shape_id = id(shape)
            
            # Cache kontrol
            if shape_id in self.bounding_box_cache:
                return self.bounding_box_cache[shape_id]
            
            # Bounding box hesapla
            bbox = Bnd_Box()
            BRepBndLib.Add(shape, bbox)
            
            # Cache'e ekle
            self.bounding_box_cache[shape_id] = bbox
            
            return bbox
            
        except Exception as e:
            self.logger.warning(f"Bounding box hesaplama hatası: {e}")
            return Bnd_Box()
    
    def _calculate_bounding_box_distance(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> float:
        """Bounding box'lar arası mesafe"""
        try:
            bbox1 = self._get_bounding_box(shape1)
            bbox2 = self._get_bounding_box(shape2)
            
            if bbox1.IsVoid() or bbox2.IsVoid():
                return float('inf')
            
            xmin1, ymin1, zmin1, xmax1, ymax1, zmax1 = bbox1.Get()
            xmin2, ymin2, zmin2, xmax2, ymax2, zmax2 = bbox2.Get()
            
            # Her eksendeki mesafeyi hesapla
            dx = max(0, max(xmin1 - xmax2, xmin2 - xmax1))
            dy = max(0, max(ymin1 - ymax2, ymin2 - ymax1))
            dz = max(0, max(zmin1 - zmax2, zmin2 - zmax1))
            
            # Öklid mesafesi
            distance = (dx*dx + dy*dy + dz*dz) ** 0.5
            return distance
            
        except Exception as e:
            self.logger.warning(f"Bounding box mesafe hesaplama hatası: {e}")
            return float('inf')
    
    def _calculate_minimum_distance(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> float:
        """İki shape arasındaki minimum mesafe"""
        try:
            # BRepExtrema kullanarak hassas mesafe hesaplama
            distance_calculator = BRepExtrema_DistShapeShape(shape1, shape2)
            
            if distance_calculator.IsDone() and distance_calculator.NbSolution() > 0:
                distance = distance_calculator.Value()
                return distance
            else:
                # Alternatif yöntem - merkez mesafeleri
                return self._calculate_center_distance(shape1, shape2)
                
        except Exception as e:
            self.logger.warning(f"Minimum mesafe hesaplama hatası: {e}")
            return self._calculate_center_distance(shape1, shape2)
    
    def _calculate_center_distance(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> float:
        """Merkez noktalar arası mesafe (fallback yöntem)"""
        try:
            # Kütle merkezlerini hesapla
            props1 = GProp_GProps()
            props2 = GProp_GProps()
            
            BRepGProp.VolumeProperties(shape1, props1)
            BRepGProp.VolumeProperties(shape2, props2)
            
            center1 = props1.CentreOfMass()
            center2 = props2.CentreOfMass()
            
            # Mesafe hesapla
            distance = center1.Distance(center2)
            return distance
            
        except Exception as e:
            self.logger.warning(f"Merkez mesafe hesaplama hatası: {e}")
            return float('inf')
    
    def _find_contact_points(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> List[Tuple[float, float, float]]:
        """Temas noktalarını bul"""
        contact_points = []
        
        try:
            distance_calculator = BRepExtrema_DistShapeShape(shape1, shape2)
            
            if distance_calculator.IsDone():
                for i in range(1, distance_calculator.NbSolution() + 1):
                    point1 = distance_calculator.PointOnShape1(i)
                    point2 = distance_calculator.PointOnShape2(i)
                    
                    # Orta noktayı temas noktası olarak al
                    contact_x = (point1.X() + point2.X()) / 2
                    contact_y = (point1.Y() + point2.Y()) / 2
                    contact_z = (point1.Z() + point2.Z()) / 2
                    
                    contact_points.append((contact_x, contact_y, contact_z))
            
        except Exception as e:
            self.logger.warning(f"Temas noktası bulma hatası: {e}")
        
        return contact_points
    
    def _analyze_overlap(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape, collision_info: CollisionInfo) -> CollisionInfo:
        """Çakışma analizi yap"""
        try:
            # Boolean intersection ile çakışma geometrisini bul
            common_op = BRepAlgoAPI_Common(shape1, shape2)
            
            if common_op.IsDone():
                common_shape = common_op.Shape()
                
                if not common_shape.IsNull():
                    collision_info.collision_geometry = common_shape
                    
                    # Çakışma hacmini hesapla
                    overlap_volume = self._calculate_volume(common_shape)
                    collision_info.overlap_volume = overlap_volume
                    
                    # Çakışma türünü belirle
                    if overlap_volume > self.overlap_tolerance:
                        collision_info.collision_type = CollisionType.OVERLAPPING
                        
                        # Penetration derinliği kontrol et
                        shape1_volume = self._calculate_volume(shape1)
                        shape2_volume = self._calculate_volume(shape2)
                        
                        if overlap_volume > shape1_volume * 0.5 or overlap_volume > shape2_volume * 0.5:
                            collision_info.collision_type = CollisionType.PENETRATING
                        
                        if overlap_volume >= min(shape1_volume, shape2_volume) * 0.9:
                            collision_info.collision_type = CollisionType.CONTAINING
                    else:
                        collision_info.collision_type = CollisionType.TOUCHING
            
        except Exception as e:
            self.logger.warning(f"Çakışma analizi hatası: {e}")
            collision_info.collision_type = CollisionType.OVERLAPPING  # Güvenli taraf
        
        return collision_info
    
    def _perform_detailed_analysis(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape, collision_info: CollisionInfo) -> CollisionInfo:
        """Detaylı çakışma analizi"""
        try:
            # Temas alanı hesaplama
            if collision_info.collision_geometry:
                contact_area = self._calculate_surface_area(collision_info.collision_geometry)
                collision_info.contact_area = contact_area
            
            # Ek geometrik analizler
            collision_info.details.update({
                "shape1_volume": self._calculate_volume(shape1),
                "shape2_volume": self._calculate_volume(shape2),
                "overlap_percentage": self._calculate_overlap_percentage(shape1, shape2, collision_info.overlap_volume)
            })
            
        except Exception as e:
            self.logger.warning(f"Detaylı analiz hatası: {e}")
        
        return collision_info
    
    def _calculate_volume(self, shape: TopoDS_Shape) -> float:
        """Shape hacmini hesapla"""
        try:
            props = GProp_GProps()
            BRepGProp.VolumeProperties(shape, props)
            return props.Mass()  # Mass = Volume for unit density
        except:
            return 0.0
    
    def _calculate_surface_area(self, shape: TopoDS_Shape) -> float:
        """Shape yüzey alanını hesapla"""
        try:
            props = GProp_GProps()
            BRepGProp.SurfaceProperties(shape, props)
            return props.Mass()
        except:
            return 0.0
    
    def _calculate_overlap_percentage(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape, overlap_volume: float) -> float:
        """Çakışma yüzdesini hesapla"""
        try:
            vol1 = self._calculate_volume(shape1)
            vol2 = self._calculate_volume(shape2)
            
            if vol1 > 0 and vol2 > 0:
                min_volume = min(vol1, vol2)
                return (overlap_volume / min_volume) * 100 if min_volume > 0 else 0.0
            
            return 0.0
            
        except:
            return 0.0
    
    def get_collision_statistics(self) -> Dict[str, Any]:
        """Çakışma kontrolü istatistiklerini al"""
        try:
            cache_hit_rate = (self.cache_hits / self.collision_checks * 100) if self.collision_checks > 0 else 0
            avg_analysis_time = (self.total_analysis_time / self.collision_checks) if self.collision_checks > 0 else 0
            
            return {
                "total_checks": self.collision_checks,
                "cache_hits": self.cache_hits,
                "cache_hit_rate": cache_hit_rate,
                "total_analysis_time": self.total_analysis_time,
                "average_analysis_time": avg_analysis_time,
                "cache_size": len(self.collision_cache),
                "bounding_box_cache_size": len(self.bounding_box_cache),
                "touch_tolerance": self.touch_tolerance,
                "overlap_tolerance": self.overlap_tolerance
            }
            
        except Exception as e:
            self.logger.error(f"İstatistik hesaplama hatası: {e}")
            return {}
    
    def clear_cache(self):
        """Cache'i temizle"""
        self.collision_cache.clear()
        self.bounding_box_cache.clear()
        self.logger.debug("Collision cache temizlendi")
    
    def set_tolerance(self, tolerance: float):
        """Tolerans ayarla"""
        self.touch_tolerance = tolerance
        self.overlap_tolerance = tolerance * 0.1  # Overlap tolerance daha küçük
        self.clear_cache()  # Cache'i temizle çünkü tolerans değişti
        self.logger.debug(f"Collision tolerance güncellendi: {tolerance}")
    
    def optimize_performance(self, enable_bbox_precheck: bool = True, enable_mesh_approximation: bool = False):
        """Performans optimizasyonları"""
        self.use_bounding_box_precheck = enable_bbox_precheck
        self.use_mesh_approximation = enable_mesh_approximation
        
        self.logger.info(f"Performans optimizasyonu: bbox_precheck={enable_bbox_precheck}, mesh_approximation={enable_mesh_approximation}")
    
    def export_collision_report(self, collision_info: CollisionInfo, file_path: str) -> bool:
        """Çakışma raporunu dosyaya aktar"""
        try:
            import json
            from datetime import datetime
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "collision_analysis": collision_info.to_dict(),
                "detector_settings": {
                    "touch_tolerance": self.touch_tolerance,
                    "overlap_tolerance": self.overlap_tolerance,
                    "use_bounding_box_precheck": self.use_bounding_box_precheck,
                    "use_mesh_approximation": self.use_mesh_approximation
                },
                "statistics": self.get_collision_statistics()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Çakışma raporu aktarıldı: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Rapor aktarma hatası: {e}")
            return False
