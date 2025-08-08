"""
Bağlantı Noktası Bulma Modülü
CAD parçaları arasındaki potansiyel bağlantı noktalarını bulan sistem
"""

import logging
import math
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum

try:
    # Topology classes
    from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Face, TopoDS_Edge, TopoDS_Vertex

    # Surface & curve adaptors
    from OCC.Core.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve

    # Geometry type enums
    from OCC.Core.GeomAbs import (
        GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Sphere, GeomAbs_Cone,
        GeomAbs_Line, GeomAbs_Circle
    )

    # Shape tools & properties
    from OCC.Core.BRep import BRep_Tool
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties

    # Geometry primitives
    from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec

    # Precision
    from OCC.Core.Precision import precision

    # Topology utilities
    from OCC.Extend.TopologyUtils import TopologyExplorer

  
except ImportError as e:
    logging.error(f"PythonOCC connection finder import hatası: {e}")
    raise

from engine_3d.geometry_handler import GeometryHandler
from utils.constants import AssemblyDefaults

class ConnectionType(Enum):
    """Bağlantı türleri"""
    PLANAR_FACE = "planar_face"
    CYLINDRICAL_FACE = "cylindrical_face" 
    SPHERICAL_FACE = "spherical_face"
    EDGE_TO_EDGE = "edge_to_edge"
    POINT_TO_POINT = "point_to_point"
    HOLE_PIN = "hole_pin"
    SCREW_THREAD = "screw_thread"

class ConnectionFinder:
    """Bağlantı noktası bulucu sınıf"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger("CADMontaj.ConnectionFinder")
        
        self.geometry_handler = GeometryHandler(config)
        
        # Toleranslar
        self.geometric_tolerance = AssemblyDefaults.GEOMETRIC_TOLERANCE
        self.angular_tolerance = AssemblyDefaults.ANGULAR_TOLERANCE
        self.connection_tolerance = AssemblyDefaults.CONNECTION_TOLERANCE
        
        if config:
            self.connection_tolerance = config.get("assembly.connection_tolerance", self.connection_tolerance)
        
        # Minimum bağlantı skoru
        self.min_connection_score = AssemblyDefaults.MIN_CONNECTION_SCORE
        
        self.logger.debug("Connection finder başlatıldı")
    
    def find_all_connections(self, 
                           shape1: TopoDS_Shape, 
                           shape2: TopoDS_Shape) -> List[Dict[str, Any]]:
        """Tüm potansiyel bağlantı noktalarını bul"""
        try:
            self.logger.debug("Bağlantı noktaları aranıyor")
            
            connections = []
            
            # Farklı bağlantı türlerini ara
            connections.extend(self._find_planar_connections(shape1, shape2))
            connections.extend(self._find_cylindrical_connections(shape1, shape2))
            connections.extend(self._find_hole_pin_connections(shape1, shape2))
            
            # Skorlara göre sırala
            connections.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            # Minimum skor filtresi
            filtered_connections = [c for c in connections if c.get("score", 0) >= self.min_connection_score]
            
            self.logger.debug(f"{len(filtered_connections)} bağlantı noktası bulundu")
            return filtered_connections
            
        except Exception as e:
            self.logger.error(f"Bağlantı bulma hatası: {e}")
            return []
    
    def _find_planar_connections(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> List[Dict[str, Any]]:
        """Düzlemsel yüzey bağlantılarını bul"""
        connections = []
        
        try:
            # Her iki shape'in yüzeylerini analiz et
            surfaces1 = self.geometry_handler._analyze_surfaces(shape1)
            surfaces2 = self.geometry_handler._analyze_surfaces(shape2)
            
            # Düzlemsel yüzeyleri filtrele
            planar_surfaces1 = [s for s in surfaces1 if s.get("is_planar")]
            planar_surfaces2 = [s for s in surfaces2 if s.get("is_planar")]
            
            # Her planar yüzey çifti için bağlantı potansiyeli kontrol et
            for surface1 in planar_surfaces1:
                for surface2 in planar_surfaces2:
                    connection = self._evaluate_planar_connection(surface1, surface2)
                    if connection:
                        connections.append(connection)
            
        except Exception as e:
            self.logger.warning(f"Düzlemsel bağlantı bulma hatası: {e}")
        
        return connections
    
    def _find_cylindrical_connections(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> List[Dict[str, Any]]:
        """Silindirik yüzey bağlantılarını bul"""
        connections = []
        
        try:
            surfaces1 = self.geometry_handler._analyze_surfaces(shape1)
            surfaces2 = self.geometry_handler._analyze_surfaces(shape2)
            
            cylindrical_surfaces1 = [s for s in surfaces1 if s.get("is_cylindrical")]
            cylindrical_surfaces2 = [s for s in surfaces2 if s.get("is_cylindrical")]
            
            for surface1 in cylindrical_surfaces1:
                for surface2 in cylindrical_surfaces2:
                    connection = self._evaluate_cylindrical_connection(surface1, surface2)
                    if connection:
                        connections.append(connection)
            
        except Exception as e:
            self.logger.warning(f"Silindirik bağlantı bulma hatası: {e}")
        
        return connections
    
    def _find_hole_pin_connections(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> List[Dict[str, Any]]:
        """Delik-pim bağlantılarını bul"""
        connections = []
        
        try:
            # Bu basitleştirilmiş bir yaklaşım
            # Küçük silindirik yüzeyler = pin, büyük silindirik boşluklar = hole
            
            surfaces1 = self.geometry_handler._analyze_surfaces(shape1)
            surfaces2 = self.geometry_handler._analyze_surfaces(shape2)
            
            # Potansiyel pin'ler (küçük yarıçaplı silindirler)
            pins1 = [s for s in surfaces1 if s.get("is_cylindrical") and s.get("cylinder_radius", 0) < 25]
            pins2 = [s for s in surfaces2 if s.get("is_cylindrical") and s.get("cylinder_radius", 0) < 25]
            
            # Potansiyel hole'lar (features analizi gerekir)
            features1 = self.geometry_handler._analyze_solid_features(shape1).get("features", {})
            features2 = self.geometry_handler._analyze_solid_features(shape2).get("features", {})
            
            holes1 = features1.get("holes", [])
            holes2 = features2.get("holes", [])
            
            # Pin-hole eşleştirmeleri
            for pin in pins1:
                for hole in holes2:
                    connection = self._evaluate_hole_pin_connection(pin, hole, "pin_to_hole")
                    if connection:
                        connections.append(connection)
            
            for pin in pins2:
                for hole in holes1:
                    connection = self._evaluate_hole_pin_connection(pin, hole, "pin_to_hole")
                    if connection:
                        connections.append(connection)
            
        except Exception as e:
            self.logger.warning(f"Delik-pim bağlantı bulma hatası: {e}")
        
        return connections
    
    def _evaluate_planar_connection(self, surface1: Dict[str, Any], surface2: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Düzlemsel bağlantıyı değerlendir"""
        try:
            normal1 = surface1.get("plane_normal")
            normal2 = surface2.get("plane_normal")
            center1 = surface1.get("center")
            center2 = surface2.get("center")
            area1 = surface1.get("area", 0)
            area2 = surface2.get("area", 0)
            
            if not all([normal1, normal2, center1, center2]):
                return None
            
            # Normal'ların ters paralel olup olmadığını kontrol et (yüzeyler birbirine bakacak)
            dot_product = sum(n1 * n2 for n1, n2 in zip(normal1, normal2))
            
            if abs(dot_product + 1.0) > self.angular_tolerance:  # +1 = tam ters
                return None
            
            # Alan uyumluluğu
            area_ratio = min(area1, area2) / max(area1, area2) if max(area1, area2) > 0 else 0
            
            if area_ratio < 0.1:  # Çok farklı alanlar
                return None
            
            # Mesafe kontrolü (çok uzaksa anlamsız)
            distance = math.sqrt(sum((c1 - c2)**2 for c1, c2 in zip(center1, center2)))
            
            if distance > 1000:  # 1 metre üzeri
                return None
            
            # Bağlantı skoru hesapla
            score = area_ratio * 0.4 + (1.0 - abs(dot_product + 1.0)) * 0.6
            
            return {
                "type": ConnectionType.PLANAR_FACE.value,
                "attach_surface": surface1,
                "base_surface": surface2,
                "score": score,
                "geometric_match": area_ratio,
                "distance": distance
            }
            
        except Exception as e:
            self.logger.debug(f"Düzlemsel bağlantı değerlendirme hatası: {e}")
            return None
    
    def _evaluate_cylindrical_connection(self, surface1: Dict[str, Any], surface2: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Silindirik bağlantıyı değerlendir"""
        try:
            radius1 = surface1.get("cylinder_radius", 0)
            radius2 = surface2.get("cylinder_radius", 0)
            axis1 = surface1.get("cylinder_axis_direction")
            axis2 = surface2.get("cylinder_axis_direction")
            center1 = surface1.get("cylinder_axis_origin")
            center2 = surface2.get("cylinder_axis_origin")
            
            if not all([axis1, axis2, center1, center2]):
                return None
            
            # Yarıçap uyumluluğu
            radius_diff = abs(radius1 - radius2)
            if radius_diff > self.connection_tolerance:
                return None
            
            # Eksen paralelliği
            dot_product = abs(sum(a1 * a2 for a1, a2 in zip(axis1, axis2)))
            
            if dot_product < 0.9:  # Eksenlerin paralel olması gerekir
                return None
            
            # Mesafe
            distance = math.sqrt(sum((c1 - c2)**2 for c1, c2 in zip(center1, center2)))
            
            # Skor hesapla
            radius_score = 1.0 - (radius_diff / max(radius1, radius2)) if max(radius1, radius2) > 0 else 0
            axis_score = dot_product
            distance_score = max(0, 1.0 - distance / 100)  # 100mm üzeri ceza
            
            score = (radius_score * 0.4 + axis_score * 0.4 + distance_score * 0.2)
            
            return {
                "type": ConnectionType.CYLINDRICAL_FACE.value,
                "attach_surface": surface1,
                "base_surface": surface2,
                "score": score,
                "radius_match": radius_score,
                "axis_alignment": axis_score,
                "distance": distance
            }
            
        except Exception as e:
            self.logger.debug(f"Silindirik bağlantı değerlendirme hatası: {e}")
            return None
    
    def _evaluate_hole_pin_connection(self, pin: Dict[str, Any], hole: Dict[str, Any], connection_type: str) -> Optional[Dict[str, Any]]:
        """Delik-pim bağlantısını değerlendir"""
        try:
            pin_radius = pin.get("cylinder_radius", pin.get("radius", 0))
            hole_radius = hole.get("radius", 0)
            pin_center = pin.get("cylinder_axis_origin", pin.get("center"))
            hole_center = hole.get("center")
            pin_axis = pin.get("cylinder_axis_direction", pin.get("axis"))
            hole_axis = hole.get("axis")
            
            if not all([pin_center, hole_center, pin_axis, hole_axis]):
                return None
            
            # Yarıçap kontrolü - pin hole'dan biraz küçük olmalı
            clearance = hole_radius - pin_radius
            
            if clearance < 0 or clearance > self.connection_tolerance * 5:
                return None
            
            # Eksen hizalama
            dot_product = abs(sum(a1 * a2 for a1, a2 in zip(pin_axis, hole_axis)))
            
            if dot_product < 0.95:
                return None
            
            # Mesafe
            distance = math.sqrt(sum((c1 - c2)**2 for c1, c2 in zip(pin_center, hole_center)))
            
            # Skor
            clearance_score = 1.0 - (clearance / (self.connection_tolerance * 5))
            axis_score = dot_product
            distance_score = max(0, 1.0 - distance / 50)
            
            score = (clearance_score * 0.5 + axis_score * 0.3 + distance_score * 0.2)
            
            return {
                "type": ConnectionType.HOLE_PIN.value,
                "pin": pin,
                "hole": hole,
                "score": score,
                "clearance": clearance,
                "axis_alignment": axis_score,
                "distance": distance
            }
            
        except Exception as e:
            self.logger.debug(f"Delik-pim değerlendirme hatası: {e}")
            return None
    
    def set_tolerance(self, tolerance: float):
        """Connection tolerance ayarla"""
        self.connection_tolerance = tolerance
        self.logger.debug(f"Connection tolerance güncellendi: {tolerance}")
    
    def set_minimum_score(self, min_score: float):
        """Minimum bağlantı skoru ayarla"""
        self.min_connection_score = max(0.0, min(1.0, min_score))
        self.logger.debug(f"Minimum connection score güncellendi: {self.min_connection_score}")
    
    def get_connection_statistics(self) -> Dict[str, Any]:
        """Bağlantı bulucu istatistikleri"""
        return {
            "connection_tolerance": self.connection_tolerance,
            "min_connection_score": self.min_connection_score,
            "geometric_tolerance": self.geometric_tolerance,
            "angular_tolerance": self.angular_tolerance
        }