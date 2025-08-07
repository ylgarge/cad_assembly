"""
Geometri İşlem Yöneticisi
OCC geometrik nesnelerinin analizi ve manipülasyonu
"""

import logging
import math
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict

try:
    from OCC.Core import (
        # Temel geometrik sınıflar
        gp_Pnt, gp_Vec, gp_Dir, gp_Ax1, gp_Ax2, gp_Ax3, gp_Pln, gp_Lin,
        gp_Circ, gp_Elips, gp_Hypr, gp_Parab,
        
        # Shape sınıfları  
        TopoDS_Shape, TopoDS_Face, TopoDS_Edge, TopoDS_Vertex, TopoDS_Solid,
        TopoDS_Compound, TopoDS_Shell, TopoDS_Wire,
        
        # Geometrik analizler
        BRep_Tool, BRepGProp_Face, BRepGProp_Edge,
        GProp_GProps, BRepGProp,
        
        # Yüzey analizleri
        BRepAdaptor_Surface, BRepAdaptor_Curve,
        GeomAbs_SurfaceType, GeomAbs_CurveType,
        GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Sphere, GeomAbs_Cone,
        GeomAbs_Torus, GeomAbs_BezierSurface, GeomAbs_BSplineSurface,
        GeomAbs_Line, GeomAbs_Circle, GeomAbs_BSplineCurve,
        
        # Bounding box
        Bnd_Box, BRepBndLib,
        
        # Mesafe hesaplamaları
        BRepExtrema_DistShapeShape,
        
        # Toleranslar
        Precision,
        
        # Topology explorer
        TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_SOLID, TopAbs_WIRE
    )
    from OCC.Extend.TopologyUtils import TopologyExplorer
    from OCC.Extend.ShapeFactory import make_box, make_cylinder, make_sphere
    
except ImportError as e:
    logging.error(f"PythonOCC geometri import hatası: {e}")
    raise

class GeometryHandler:
    """Geometrik işlemler ve analizler için yönetici sınıf"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger("CADMontaj.GeometryHandler")
        
        # Cache için geometrik analizler
        self._surface_cache = {}
        self._curve_cache = {}
        self._properties_cache = {}
        
        # Tolerans değerleri
        self.linear_tolerance = Precision.Confusion()  # ~1e-7
        self.angular_tolerance = Precision.Angular()   # ~1e-12
        
        if config:
            self.linear_tolerance = config.get("assembly.tolerance", 0.01)
    
    def analyze_shape(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """
        Shape'in kapsamlı geometrik analizi
        
        Args:
            shape: Analiz edilecek shape
            
        Returns:
            Geometrik özellikler dictionary'si
        """
        try:
            if not shape or shape.IsNull():
                return {"error": "Geçersiz shape"}
            
            analysis = {
                "shape_type": self._get_shape_type_name(shape),
                "topology": self._analyze_topology(shape),
                "properties": self._calculate_properties(shape),
                "bounding_box": self._get_bounding_box(shape),
                "surfaces": self._analyze_surfaces(shape),
                "edges": self._analyze_edges(shape),
                "vertices": self._analyze_vertices(shape)
            }
            
            # Özel analizler (shape tipine göre)
            if analysis["topology"]["num_solids"] > 0:
                analysis.update(self._analyze_solid_features(shape))
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Shape analizi hatası: {e}")
            return {"error": str(e)}
    
    def _get_shape_type_name(self, shape: TopoDS_Shape) -> str:
        """Shape tipini string olarak döndür"""
        type_map = {
            0: "COMPOUND",
            1: "COMPSOLID", 
            2: "SOLID",
            3: "SHELL",
            4: "FACE",
            5: "WIRE",
            6: "EDGE",
            7: "VERTEX"
        }
        return type_map.get(shape.ShapeType(), "UNKNOWN")
    
    def _analyze_topology(self, shape: TopoDS_Shape) -> Dict[str, int]:
        """Topological analiz - kaç face, edge vs. var"""
        try:
            explorer = TopologyExplorer(shape)
            
            topology = {
                "num_solids": explorer.number_of_solids(),
                "num_shells": explorer.number_of_shells(), 
                "num_faces": explorer.number_of_faces(),
                "num_wires": explorer.number_of_wires(),
                "num_edges": explorer.number_of_edges(),
                "num_vertices": explorer.number_of_vertices()
            }
            
            return topology
            
        except Exception as e:
            self.logger.warning(f"Topology analizi hatası: {e}")
            return {}
    
    def _calculate_properties(self, shape: TopoDS_Shape) -> Dict[str, float]:
        """Geometrik özellikler (hacim, alan, kütle merkezi vs.)"""
        try:
            # GProp_GProps nesnesi oluştur
            props = GProp_GProps()
            
            # Shape tipine göre özellik hesapla
            properties = {}
            
            if self._has_volume(shape):
                # Hacim özellikleri
                BRepGProp.VolumeProperties(shape, props)
                properties.update({
                    "volume": props.Mass(),
                    "center_of_mass": self._gp_pnt_to_tuple(props.CentreOfMass()),
                    "inertia_moments": self._get_inertia_moments(props)
                })
            
            if self._has_surface(shape):
                # Yüzey özellikleri
                BRepGProp.SurfaceProperties(shape, props)
                properties.update({
                    "surface_area": props.Mass(),
                    "surface_center": self._gp_pnt_to_tuple(props.CentreOfMass())
                })
            
            # Linear properties (kenar uzunlukları)
            BRepGProp.LinearProperties(shape, props)
            properties.update({
                "linear_length": props.Mass(),
                "linear_center": self._gp_pnt_to_tuple(props.CentreOfMass())
            })
            
            return properties
            
        except Exception as e:
            self.logger.warning(f"Özellik hesaplama hatası: {e}")
            return {}
    
    def _has_volume(self, shape: TopoDS_Shape) -> bool:
        """Shape'in hacmi var mı kontrol et"""
        return shape.ShapeType() in [2]  # SOLID
    
    def _has_surface(self, shape: TopoDS_Shape) -> bool:
        """Shape'in yüzeyi var mı kontrol et"""
        return shape.ShapeType() in [2, 3, 4]  # SOLID, SHELL, FACE
    
    def _get_inertia_moments(self, props: GProp_GProps) -> Dict[str, float]:
        """Atalet momentlerini hesapla"""
        try:
            matrix = props.MatrixOfInertia()
            return {
                "Ixx": matrix.Value(1, 1),
                "Iyy": matrix.Value(2, 2), 
                "Izz": matrix.Value(3, 3),
                "Ixy": matrix.Value(1, 2),
                "Ixz": matrix.Value(1, 3),
                "Iyz": matrix.Value(2, 3)
            }
        except:
            return {}
    
    def _get_bounding_box(self, shape: TopoDS_Shape) -> Dict[str, float]:
        """Bounding box hesapla"""
        try:
            bbox = Bnd_Box()
            BRepBndLib.Add(shape, bbox)
            
            if not bbox.IsVoid():
                xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
                return {
                    "xmin": xmin, "ymin": ymin, "zmin": zmin,
                    "xmax": xmax, "ymax": ymax, "zmax": zmax,
                    "width": xmax - xmin,
                    "height": ymax - ymin,
                    "depth": zmax - zmin,
                    "center": ((xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2)
                }
            
        except Exception as e:
            self.logger.warning(f"Bounding box hesaplama hatası: {e}")
        
        return {}
    
    def _analyze_surfaces(self, shape: TopoDS_Shape) -> List[Dict[str, Any]]:
        """Yüzeyleri analiz et"""
        surfaces = []
        
        try:
            explorer = TopologyExplorer(shape)
            
            for face in explorer.faces():
                surface_info = self._analyze_single_surface(face)
                if surface_info:
                    surfaces.append(surface_info)
                    
        except Exception as e:
            self.logger.warning(f"Yüzey analizi hatası: {e}")
        
        return surfaces
    
    def _analyze_single_surface(self, face: TopoDS_Face) -> Dict[str, Any]:
        """Tek bir yüzeyi analiz et"""
        try:
            # Surface adaptor oluştur
            surface = BRepAdaptor_Surface(face)
            
            surface_info = {
                "surface_type": self._get_surface_type_name(surface.GetType()),
                "is_planar": surface.GetType() == GeomAbs_Plane,
                "is_cylindrical": surface.GetType() == GeomAbs_Cylinder,
                "is_spherical": surface.GetType() == GeomAbs_Sphere,
                "orientation": face.Orientation()
            }
            
            # Yüzey tipine özel analizler
            if surface.GetType() == GeomAbs_Plane:
                surface_info.update(self._analyze_planar_surface(surface))
            elif surface.GetType() == GeomAbs_Cylinder:
                surface_info.update(self._analyze_cylindrical_surface(surface))
            elif surface.GetType() == GeomAbs_Sphere:
                surface_info.update(self._analyze_spherical_surface(surface))
            
            # Yüzey alanı
            props = GProp_GProps()
            BRepGProp.SurfaceProperties(face, props)
            surface_info["area"] = props.Mass()
            surface_info["center"] = self._gp_pnt_to_tuple(props.CentreOfMass())
            
            return surface_info
            
        except Exception as e:
            self.logger.warning(f"Tekil yüzey analizi hatası: {e}")
            return {}
    
    def _get_surface_type_name(self, surface_type) -> str:
        """Yüzey tipini string'e çevir"""
        type_map = {
            GeomAbs_Plane: "PLANE",
            GeomAbs_Cylinder: "CYLINDER", 
            GeomAbs_Sphere: "SPHERE",
            GeomAbs_Cone: "CONE",
            GeomAbs_Torus: "TORUS",
            GeomAbs_BezierSurface: "BEZIER",
            GeomAbs_BSplineSurface: "BSPLINE"
        }
        return type_map.get(surface_type, "OTHER")
    
    def _analyze_planar_surface(self, surface: BRepAdaptor_Surface) -> Dict[str, Any]:
        """Düzlemsel yüzey analizi"""
        try:
            plane = surface.Plane()
            
            return {
                "plane_origin": self._gp_pnt_to_tuple(plane.Location()),
                "plane_normal": self._gp_dir_to_tuple(plane.Axis().Direction()),
                "plane_x_axis": self._gp_dir_to_tuple(plane.XAxis().Direction()),
                "plane_y_axis": self._gp_dir_to_tuple(plane.YAxis().Direction())
            }
        except:
            return {}
    
    def _analyze_cylindrical_surface(self, surface: BRepAdaptor_Surface) -> Dict[str, Any]:
        """Silindirik yüzey analizi"""
        try:
            cylinder = surface.Cylinder()
            
            return {
                "cylinder_axis_origin": self._gp_pnt_to_tuple(cylinder.Location()),
                "cylinder_axis_direction": self._gp_dir_to_tuple(cylinder.Axis().Direction()),
                "cylinder_radius": cylinder.Radius(),
                "cylinder_x_axis": self._gp_dir_to_tuple(cylinder.XAxis().Direction()),
                "cylinder_y_axis": self._gp_dir_to_tuple(cylinder.YAxis().Direction())
            }
        except:
            return {}
    
    def _analyze_spherical_surface(self, surface: BRepAdaptor_Surface) -> Dict[str, Any]:
        """Küresel yüzey analizi"""
        try:
            sphere = surface.Sphere()
            
            return {
                "sphere_center": self._gp_pnt_to_tuple(sphere.Location()),
                "sphere_radius": sphere.Radius(),
                "sphere_x_axis": self._gp_dir_to_tuple(sphere.XAxis().Direction()),
                "sphere_y_axis": self._gp_dir_to_tuple(sphere.YAxis().Direction()),
                "sphere_z_axis": self._gp_dir_to_tuple(sphere.Axis().Direction())
            }
        except:
            return {}
    
    def _analyze_edges(self, shape: TopoDS_Shape) -> List[Dict[str, Any]]:
        """Kenarları analiz et"""
        edges = []
        
        try:
            explorer = TopologyExplorer(shape)
            
            for edge in explorer.edges():
                edge_info = self._analyze_single_edge(edge)
                if edge_info:
                    edges.append(edge_info)
                    
        except Exception as e:
            self.logger.warning(f"Kenar analizi hatası: {e}")
        
        return edges
    
    def _analyze_single_edge(self, edge) -> Dict[str, Any]:
        """Tek bir kenarı analiz et"""
        try:
            # Curve adaptor
            curve = BRepAdaptor_Curve(edge)
            
            edge_info = {
                "curve_type": self._get_curve_type_name(curve.GetType()),
                "is_closed": BRep_Tool.IsClosed(edge),
                "is_degenerated": BRep_Tool.Degenerated(edge)
            }
            
            # Curve tipine özel analizler
            if curve.GetType() == GeomAbs_Line:
                edge_info.update(self._analyze_linear_edge(curve))
            elif curve.GetType() == GeomAbs_Circle:
                edge_info.update(self._analyze_circular_edge(curve))
            
            # Kenar uzunluğu
            props = GProp_GProps()
            BRepGProp.LinearProperties(edge, props)
            edge_info["length"] = props.Mass()
            
            # İlk ve son noktalar
            first_param = curve.FirstParameter()
            last_param = curve.LastParameter()
            edge_info["start_point"] = self._gp_pnt_to_tuple(curve.Value(first_param))
            edge_info["end_point"] = self._gp_pnt_to_tuple(curve.Value(last_param))
            
            return edge_info
            
        except Exception as e:
            self.logger.warning(f"Tekil kenar analizi hatası: {e}")
            return {}
    
    def _get_curve_type_name(self, curve_type) -> str:
        """Curve tipini string'e çevir"""
        type_map = {
            GeomAbs_Line: "LINE",
            GeomAbs_Circle: "CIRCLE", 
            GeomAbs_BSplineCurve: "BSPLINE"
        }
        return type_map.get(curve_type, "OTHER")
    
    def _analyze_linear_edge(self, curve: BRepAdaptor_Curve) -> Dict[str, Any]:
        """Doğrusal kenar analizi"""
        try:
            line = curve.Line()
            return {
                "line_origin": self._gp_pnt_to_tuple(line.Location()),
                "line_direction": self._gp_dir_to_tuple(line.Direction())
            }
        except:
            return {}
    
    def _analyze_circular_edge(self, curve: BRepAdaptor_Curve) -> Dict[str, Any]:
        """Dairesel kenar analizi"""
        try:
            circle = curve.Circle()
            return {
                "circle_center": self._gp_pnt_to_tuple(circle.Location()),
                "circle_radius": circle.Radius(),
                "circle_axis": self._gp_dir_to_tuple(circle.Axis().Direction()),
                "circle_x_axis": self._gp_dir_to_tuple(circle.XAxis().Direction()),
                "circle_y_axis": self._gp_dir_to_tuple(circle.YAxis().Direction())
            }
        except:
            return {}
    
    def _analyze_vertices(self, shape: TopoDS_Shape) -> List[Dict[str, Any]]:
        """Köşe noktalarını analiz et"""
        vertices = []
        
        try:
            explorer = TopologyExplorer(shape)
            
            for vertex in explorer.vertices():
                point = BRep_Tool.Pnt(vertex)
                vertices.append({
                    "coordinates": self._gp_pnt_to_tuple(point),
                    "tolerance": BRep_Tool.Tolerance(vertex)
                })
                
        except Exception as e:
            self.logger.warning(f"Köşe analizi hatası: {e}")
        
        return vertices
    
    def _analyze_solid_features(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """Solid için özel özellik analizi"""
        features = {
            "holes": [],
            "cylindrical_features": [],
            "planar_features": []
        }
        
        try:
            # Hole detection (silindirik yüzeyler içinde)
            surfaces = self._analyze_surfaces(shape)
            
            for surface in surfaces:
                if surface.get("is_cylindrical"):
                    # Potansiyel hole
                    radius = surface.get("cylinder_radius", 0)
                    if radius < 50:  # Küçük yarıçap = potansiyel delik
                        features["holes"].append({
                            "center": surface.get("cylinder_axis_origin"),
                            "axis": surface.get("cylinder_axis_direction"),
                            "radius": radius
                        })
                    else:
                        features["cylindrical_features"].append(surface)
                
                elif surface.get("is_planar"):
                    features["planar_features"].append(surface)
            
        except Exception as e:
            self.logger.warning(f"Solid özellik analizi hatası: {e}")
        
        return {"features": features}
    
    def find_parallel_faces(self, shape: TopoDS_Shape, tolerance: float = None) -> List[Tuple[int, int]]:
        """Paralel yüzey çiftlerini bul"""
        if tolerance is None:
            tolerance = self.angular_tolerance
        
        parallel_pairs = []
        surfaces = self._analyze_surfaces(shape)
        
        try:
            for i, surface1 in enumerate(surfaces):
                if not surface1.get("is_planar"):
                    continue
                    
                normal1 = surface1.get("plane_normal")
                if not normal1:
                    continue
                
                for j, surface2 in enumerate(surfaces[i+1:], i+1):
                    if not surface2.get("is_planar"):
                        continue
                        
                    normal2 = surface2.get("plane_normal")
                    if not normal2:
                        continue
                    
                    # Normal vektörlerin dot product'ı
                    dot_product = abs(sum(a * b for a, b in zip(normal1, normal2)))
                    
                    # Paralel mi kontrol et (dot product ≈ 1)
                    if abs(dot_product - 1.0) < tolerance:
                        parallel_pairs.append((i, j))
            
        except Exception as e:
            self.logger.warning(f"Paralel yüzey bulma hatası: {e}")
        
        return parallel_pairs
    
    def find_coaxial_cylinders(self, shape: TopoDS_Shape, tolerance: float = None) -> List[Tuple[int, int]]:
        """Koaksiyel silindir çiftlerini bul"""
        if tolerance is None:
            tolerance = self.linear_tolerance
        
        coaxial_pairs = []
        surfaces = self._analyze_surfaces(shape)
        
        try:
            cylindrical_surfaces = [s for s in surfaces if s.get("is_cylindrical")]
            
            for i, cyl1 in enumerate(cylindrical_surfaces):
                axis1_origin = cyl1.get("cylinder_axis_origin")
                axis1_dir = cyl1.get("cylinder_axis_direction")
                
                if not axis1_origin or not axis1_dir:
                    continue
                
                for j, cyl2 in enumerate(cylindrical_surfaces[i+1:], i+1):
                    axis2_origin = cyl2.get("cylinder_axis_origin")
                    axis2_dir = cyl2.get("cylinder_axis_direction")
                    
                    if not axis2_origin or not axis2_dir:
                        continue
                    
                    # Axis direction'lar parallel mı?
                    dot_product = abs(sum(a * b for a, b in zip(axis1_dir, axis2_dir)))
                    
                    if abs(dot_product - 1.0) < self.angular_tolerance:
                        # Origin'ler aynı doğru üzerinde mi?
                        # Bu basit bir kontrol, gerçek implementasyon daha karmaşık olabilir
                        coaxial_pairs.append((i, j))
            
        except Exception as e:
            self.logger.warning(f"Koaksiyel silindir bulma hatası: {e}")
        
        return coaxial_pairs
    
    def calculate_distance(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> float:
        """İki shape arasındaki minimum mesafe"""
        try:
            dist_calculator = BRepExtrema_DistShapeShape(shape1, shape2)
            
            if dist_calculator.IsDone():
                return dist_calculator.Value()
            else:
                return float('inf')
                
        except Exception as e:
            self.logger.warning(f"Mesafe hesaplama hatası: {e}")
            return float('inf')
    
    def check_intersection(self, shape1: TopoDS_Shape, shape2: TopoDS_Shape) -> bool:
        """İki shape'in kesişip kesişmediğini kontrol et"""
        try:
            distance = self.calculate_distance(shape1, shape2)
            return distance < self.linear_tolerance
            
        except Exception as e:
            self.logger.warning(f"Kesişim kontrolü hatası: {e}")
            return False
    
    def _gp_pnt_to_tuple(self, pnt: gp_Pnt) -> Tuple[float, float, float]:
        """gp_Pnt'yi tuple'a çevir"""
        return (pnt.X(), pnt.Y(), pnt.Z())
    
    def _gp_dir_to_tuple(self, direction: gp_Dir) -> Tuple[float, float, float]:
        """gp_Dir'yi tuple'a çevir"""
        return (direction.X(), direction.Y(), direction.Z())
    
    def _gp_vec_to_tuple(self, vec: gp_Vec) -> Tuple[float, float, float]:
        """gp_Vec'yi tuple'a çevir"""
        return (vec.X(), vec.Y(), vec.Z())
    
    def clear_cache(self):
        """Cache'i temizle"""
        self._surface_cache.clear()
        self._curve_cache.clear()
        self._properties_cache.clear()
        self.logger.debug("Geometri cache temizlendi")