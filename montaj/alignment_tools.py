"""
Hizalama Araçları Modülü
CAD parçalarının geometrik hizalama işlemleri
"""

import logging
import math
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum

try:
    from OCC.Core import (
        TopoDS_Shape, gp_Trsf, gp_Pnt, gp_Dir, gp_Vec, gp_Ax1, gp_Ax3,
        BRepBuilderAPI_Transform, GProp_GProps, BRepGProp
    )
    
except ImportError as e:
    logging.error(f"PythonOCC alignment tools import hatası: {e}")
    raise

from engine_3d.transformations import TransformationManager
from engine_3d.geometry_handler import GeometryHandler

class AlignmentType(Enum):
    """Hizalama türleri"""
    FACE_TO_FACE = "face_to_face"
    EDGE_TO_EDGE = "edge_to_edge" 
    AXIS_TO_AXIS = "axis_to_axis"
    POINT_TO_POINT = "point_to_point"
    CENTER_TO_CENTER = "center_to_center"

class AlignmentTools:
    """Hizalama araçları sınıfı"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger("CADMontaj.AlignmentTools")
        
        self.transform_manager = TransformationManager()
        self.geometry_handler = GeometryHandler(config)
        
        # Toleranslar
        self.linear_tolerance = 0.01  # mm
        self.angular_tolerance = 0.017453  # ~1 derece
        
        if config:
            self.linear_tolerance = config.get("assembly.tolerance", self.linear_tolerance)
            self.angular_tolerance = config.get("assembly.angular_tolerance", self.angular_tolerance)
        
        self.logger.debug("Alignment tools başlatıldı")
    
    def align_parts(self, 
                   source_shape: TopoDS_Shape,
                   target_shape: TopoDS_Shape, 
                   connection_info: Dict[str, Any]) -> Optional[TopoDS_Shape]:
        """
        Parçaları bağlantı bilgisine göre hizala
        
        Args:
            source_shape: Hareket edecek parça
            target_shape: Sabit kalacak parça
            connection_info: Bağlantı bilgisi
            
        Returns:
            Hizalanmış source_shape
        """
        try:
            connection_type = connection_info.get("type", "unknown")
            
            if connection_type == "planar_face":
                transformation = self._create_face_alignment(connection_info)
            elif connection_type == "cylindrical_face":
                transformation = self._create_axis_alignment(connection_info)
            elif connection_type == "hole_pin":
                transformation = self._create_hole_pin_alignment(connection_info)
            else:
                # Genel hizalama
                transformation = self._create_general_alignment(source_shape, target_shape, connection_info)
            
            if transformation:
                aligned_shape = self.transform_manager.apply_transformation(source_shape, transformation)
                return aligned_shape
            
            return None
            
        except Exception as e:
            self.logger.error(f"Parça hizalama hatası: {e}")
            return None
    
    def _create_face_alignment(self, connection_info: Dict[str, Any]) -> Optional[gp_Trsf]:
        """Yüzey hizalaması dönüşümü"""
        try:
            attach_surface = connection_info.get("attach_surface", {})
            base_surface = connection_info.get("base_surface", {})
            
            # Yüzey merkezleri ve normal'ları
            source_center = attach_surface.get("center", (0, 0, 0))
            source_normal = attach_surface.get("plane_normal", (0, 0, 1))
            
            target_center = base_surface.get("center", (0, 0, 0))
            target_normal = base_surface.get("plane_normal", (0, 0, 1))
            
            # Normal'ları ters çevir (yüzeyler birbirine bakacak)
            target_normal = (-target_normal[0], -target_normal[1], -target_normal[2])
            
            # Hizalama dönüşümü
            transformation = self.transform_manager.create_alignment_transformation(
                source_center, source_normal,
                target_center, target_normal
            )
            
            return transformation
            
        except Exception as e:
            self.logger.warning(f"Yüzey hizalama dönüşümü hatası: {e}")
            return None
    
    def _create_axis_alignment(self, connection_info: Dict[str, Any]) -> Optional[gp_Trsf]:
        """Eksen hizalaması dönüşümü"""
        try:
            attach_surface = connection_info.get("attach_surface", {})
            base_surface = connection_info.get("base_surface", {})
            
            # Eksen bilgileri
            source_origin = attach_surface.get("cylinder_axis_origin", (0, 0, 0))
            source_direction = attach_surface.get("cylinder_axis_direction", (0, 0, 1))
            
            target_origin = base_surface.get("cylinder_axis_origin", (0, 0, 0))
            target_direction = base_surface.get("cylinder_axis_direction", (0, 0, 1))
            
            # Hizalama dönüşümü
            transformation = self.transform_manager.create_alignment_transformation(
                source_origin, source_direction,
                target_origin, target_direction
            )
            
            return transformation
            
        except Exception as e:
            self.logger.warning(f"Eksen hizalama dönüşümü hatası: {e}")
            return None
    
    def _create_hole_pin_alignment(self, connection_info: Dict[str, Any]) -> Optional[gp_Trsf]:
        """Delik-pim hizalaması dönüşümü"""
        try:
            pin = connection_info.get("pin", {})
            hole = connection_info.get("hole", {})
            
            # Pin ve delik merkezleri
            pin_center = pin.get("cylinder_axis_origin", pin.get("center", (0, 0, 0)))
            pin_axis = pin.get("cylinder_axis_direction", pin.get("axis", (0, 0, 1)))
            
            hole_center = hole.get("center", (0, 0, 0))
            hole_axis = hole.get("axis", (0, 0, 1))
            
            # Pin'i deliğe hizala
            transformation = self.transform_manager.create_alignment_transformation(
                pin_center, pin_axis,
                hole_center, hole_axis
            )
            
            return transformation
            
        except Exception as e:
            self.logger.warning(f"Delik-pim hizalama dönüşümü hatası: {e}")
            return None
    
    def _create_general_alignment(self, 
                                source_shape: TopoDS_Shape,
                                target_shape: TopoDS_Shape,
                                connection_info: Dict[str, Any]) -> Optional[gp_Trsf]:
        """Genel hizalama dönüşümü"""
        try:
            # Bağlantı noktalarını al
            attach_point = connection_info.get("attach_point")
            base_point = connection_info.get("base_point")
            
            if not attach_point or not base_point:
                # Merkez noktaları kullan
                attach_point = self._get_shape_center(source_shape)
                base_point = self._get_shape_center(target_shape)
            
            # Basit öteleme
            offset = (
                base_point[0] - attach_point[0],
                base_point[1] - attach_point[1],
                base_point[2] - attach_point[2]
            )
            
            transformation = self.transform_manager.create_translation(offset)
            return transformation
            
        except Exception as e:
            self.logger.warning(f"Genel hizalama dönüşümü hatası: {e}")
            return None
    
    def _get_shape_center(self, shape: TopoDS_Shape) -> Tuple[float, float, float]:
        """Shape'in merkez noktasını al"""
        try:
            props = GProp_GProps()
            BRepGProp.VolumeProperties(shape, props)
            center = props.CentreOfMass()
            return (center.X(), center.Y(), center.Z())
        except:
            # Fallback: bounding box merkezi
            analysis = self.geometry_handler.analyze_shape(shape)
            bbox = analysis.get("bounding_box", {})
            return bbox.get("center", (0, 0, 0))
    
    def create_manual_alignment(self, 
                              translation: Tuple[float, float, float] = (0, 0, 0),
                              rotation_axis: Tuple[float, float, float] = (0, 0, 1),
                              rotation_angle: float = 0.0,
                              rotation_center: Tuple[float, float, float] = (0, 0, 0)) -> gp_Trsf:
        """Manuel hizalama dönüşümü oluştur"""
        try:
            transformations = []
            
            # Öteleme
            if any(t != 0 for t in translation):
                trans_transform = self.transform_manager.create_translation(translation)
                transformations.append(trans_transform)
            
            # Rotasyon
            if rotation_angle != 0.0:
                rot_transform = self.transform_manager.create_rotation(
                    rotation_center, rotation_axis, rotation_angle
                )
                transformations.append(rot_transform)
            
            # Dönüşümleri birleştir
            if transformations:
                return self.transform_manager.combine_transformations(transformations)
            else:
                return gp_Trsf()  # Identity transform
                
        except Exception as e:
            self.logger.error(f"Manuel hizalama oluşturma hatası: {e}")
            return gp_Trsf()
    
    def align_to_coordinate_system(self, 
                                  shape: TopoDS_Shape,
                                  target_origin: Tuple[float, float, float] = (0, 0, 0),
                                  target_x_axis: Tuple[float, float, float] = (1, 0, 0),
                                  target_z_axis: Tuple[float, float, float] = (0, 0, 1)) -> Optional[TopoDS_Shape]:
        """Shape'i belirli bir koordinat sistemine hizala"""
        try:
            # Mevcut koordinat sistemini tespit et
            shape_center = self._get_shape_center(shape)
            
            # Basit hizalama - merkezi origin'e taşı
            translation = (
                target_origin[0] - shape_center[0],
                target_origin[1] - shape_center[1], 
                target_origin[2] - shape_center[2]
            )
            
            transformation = self.transform_manager.create_translation(translation)
            
            aligned_shape = self.transform_manager.apply_transformation(shape, transformation)
            return aligned_shape
            
        except Exception as e:
            self.logger.error(f"Koordinat sistemi hizalama hatası: {e}")
            return None
    
    def calculate_optimal_orientation(self, 
                                    source_shape: TopoDS_Shape,
                                    target_shape: TopoDS_Shape) -> Optional[gp_Trsf]:
        """İki parça arasında optimal oryantasyonu hesapla"""
        try:
            # Bu basitleştirilmiş bir yaklaşım
            # Gerçek uygulamada daha karmaşık geometrik analizler gerekir
            
            # Bounding box'ları karşılaştır
            source_analysis = self.geometry_handler.analyze_shape(source_shape)
            target_analysis = self.geometry_handler.analyze_shape(target_shape)
            
            source_bbox = source_analysis.get("bounding_box", {})
            target_bbox = target_analysis.get("bounding_box", {})
            
            if not source_bbox or not target_bbox:
                return None
            
            # En büyük boyutları hizala
            source_dims = [source_bbox.get("width", 0), source_bbox.get("height", 0), source_bbox.get("depth", 0)]
            target_dims = [target_bbox.get("width", 0), target_bbox.get("height", 0), target_bbox.get("depth", 0)]
            
            # Basit rotasyon hesapla (90 derece artışlarla)
            best_angle = 0
            best_score = 0
            
            for angle in [0, 90, 180, 270]:
                score = self._calculate_orientation_score(source_dims, target_dims, angle)
                if score > best_score:
                    best_score = score
                    best_angle = angle
            
            if best_angle != 0:
                source_center = source_bbox.get("center", (0, 0, 0))
                transformation = self.transform_manager.create_rotation_xyz(
                    source_center, self.transform_manager.RotationAxis.Z_AXIS, best_angle
                )
                return transformation
            
            return gp_Trsf()  # Identity
            
        except Exception as e:
            self.logger.error(f"Optimal oryantasyon hesaplama hatası: {e}")
            return None
    
    def _calculate_orientation_score(self, dims1: List[float], dims2: List[float], angle: float) -> float:
        """Oryantasyon skoru hesapla"""
        try:
            # Basit boyut uyumluluk skoru
            score = 0
            for d1, d2 in zip(dims1, dims2):
                if max(d1, d2) > 0:
                    ratio = min(d1, d2) / max(d1, d2)
                    score += ratio
            
            return score / len(dims1)
            
        except:
            return 0.0
    
    def validate_alignment(self, 
                          original_shape: TopoDS_Shape,
                          aligned_shape: TopoDS_Shape,
                          target_shape: TopoDS_Shape,
                          connection_info: Dict[str, Any]) -> Dict[str, Any]:
        """Hizalama sonucunu doğrula"""
        try:
            validation = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "metrics": {}
            }
            
            # Temel geometri kontrolü
            if not aligned_shape or aligned_shape.IsNull():
                validation["valid"] = False
                validation["errors"].append("Hizalanmış shape geçersiz")
                return validation
            
            # Mesafe kontrolü
            original_center = self._get_shape_center(original_shape)
            aligned_center = self._get_shape_center(aligned_shape)
            target_center = self._get_shape_center(target_shape)
            
            # Hizalama kalitesi
            alignment_distance = math.sqrt(sum((a - t)**2 for a, t in zip(aligned_center, target_center)))
            validation["metrics"]["alignment_distance"] = alignment_distance
            
            if alignment_distance > self.linear_tolerance * 100:  # 100x tolerance
                validation["warnings"].append(f"Hizalama mesafesi büyük: {alignment_distance:.3f}mm")
            
            # Hareket miktarı
            movement_distance = math.sqrt(sum((o - a)**2 for o, a in zip(original_center, aligned_center)))
            validation["metrics"]["movement_distance"] = movement_distance
            
            if movement_distance > 1000:  # 1 metre üzeri
                validation["warnings"].append(f"Büyük hareket miktarı: {movement_distance:.1f}mm")
            
            return validation
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation hatası: {str(e)}"],
                "warnings": [],
                "metrics": {}
            }
    
    def get_alignment_preview_points(self, 
                                   source_shape: TopoDS_Shape,
                                   transformation: gp_Trsf,
                                   num_points: int = 8) -> List[Tuple[float, float, float]]:
        """Hizalama önizlemesi için temsili noktalar al"""
        try:
            # Bounding box köşelerini al
            analysis = self.geometry_handler.analyze_shape(source_shape)
            bbox = analysis.get("bounding_box", {})
            
            if not bbox:
                return []
            
            xmin, ymin, zmin = bbox.get("xmin", 0), bbox.get("ymin", 0), bbox.get("zmin", 0)
            xmax, ymax, zmax = bbox.get("xmax", 0), bbox.get("ymax", 0), bbox.get("zmax", 0)
            
            # Köşe noktaları
            corners = [
                (xmin, ymin, zmin), (xmax, ymin, zmin),
                (xmin, ymax, zmin), (xmax, ymax, zmin),
                (xmin, ymin, zmax), (xmax, ymin, zmax),
                (xmin, ymax, zmax), (xmax, ymax, zmax)
            ]
            
            # Dönüşümü uygula
            transformed_points = []
            for corner in corners:
                point = gp_Pnt(corner[0], corner[1], corner[2])
                point.Transform(transformation)
                transformed_points.append((point.X(), point.Y(), point.Z()))
            
            return transformed_points[:num_points]
            
        except Exception as e:
            self.logger.error(f"Önizleme noktaları alma hatası: {e}")
            return []
    
    def set_tolerances(self, linear: float = None, angular: float = None):
        """Hizalama toleranslarını ayarla"""
        if linear is not None:
            self.linear_tolerance = linear
            self.logger.debug(f"Linear tolerance güncellendi: {linear}")
        
        if angular is not None:
            self.angular_tolerance = angular
            self.logger.debug(f"Angular tolerance güncellendi: {angular}")
    
    def get_alignment_statistics(self) -> Dict[str, Any]:
        """Hizalama araçları istatistikleri"""
        return {
            "linear_tolerance": self.linear_tolerance,
            "angular_tolerance": self.angular_tolerance,
            "angular_tolerance_degrees": math.degrees(self.angular_tolerance)
        }