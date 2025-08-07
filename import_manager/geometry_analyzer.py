"""
Geometri Analiz Modülü
İçe aktarılan geometrilerin analizi ve raporlanması
"""

import logging
import math,os
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

try:
    from OCC.Core import (
        TopoDS_Shape, 
        GProp_GProps, BRepGProp,
        Bnd_Box, BRepBndLib,
        BRepAdaptor_Surface, BRepAdaptor_Curve,
        GeomAbs_SurfaceType, GeomAbs_CurveType,
        BRep_Tool,
        TopAbs_SOLID, TopAbs_SHELL, TopAbs_FACE, TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX
    )
    from OCC.Extend.TopologyUtils import TopologyExplorer
    
except ImportError as e:
    logging.error(f"PythonOCC geometri analiz import hatası: {e}")
    raise

from engine_3d.geometry_handler import GeometryHandler
from utils.constants import AssemblyDefaults

class GeometryAnalyzer:
    """İçe aktarılan geometrileri analiz eden sınıf"""
    
    def __init__(self, config=None):
        self.config = config
        self.logger = logging.getLogger("CADMontaj.GeometryAnalyzer")
        
        # Geometry handler'ı kullan
        self.geometry_handler = GeometryHandler(config)
        
        # Analiz ayarları
        self.detail_level = "medium"  # basic, medium, detailed
        self.analyze_features = True
        self.analyze_materials = False
        self.analyze_assemblies = True
        
        if config:
            self.detail_level = config.get("analysis.detail_level", "medium")
            self.analyze_features = config.get("analysis.analyze_features", True)
        
        # Analiz cache
        self.analysis_cache = {}
    
    def analyze_imported_shape(self, 
                              shape: TopoDS_Shape, 
                              file_path: str = None) -> Dict[str, Any]:
        """
        İçe aktarılan shape'in kapsamlı analizi
        
        Args:
            shape: Analiz edilecek shape
            file_path: Kaynak dosya yolu (opsiyonel)
            
        Returns:
            Analiz sonuçları
        """
        try:
            self.logger.info(f"Geometri analizi başlatılıyor: {file_path or 'shape'}")
            
            analysis_results = {
                "analysis_timestamp": self._get_current_time(),
                "source_file": file_path,
                "analysis_level": self.detail_level,
                "shape_valid": not (shape is None or shape.IsNull())
            }
            
            if not analysis_results["shape_valid"]:
                analysis_results["error"] = "Geçersiz veya boş shape"
                return analysis_results
            
            # Temel geometrik analiz
            basic_analysis = self.geometry_handler.analyze_shape(shape)
            analysis_results["basic_geometry"] = basic_analysis
            
            # Detay seviyesine göre ek analizler
            if self.detail_level in ["medium", "detailed"]:
                analysis_results["geometric_properties"] = self._analyze_geometric_properties(shape)
                analysis_results["complexity_analysis"] = self._analyze_complexity(shape)
                
                if self.analyze_features:
                    analysis_results["features"] = self._analyze_manufacturing_features(shape)
            
            if self.detail_level == "detailed":
                analysis_results["surface_analysis"] = self._detailed_surface_analysis(shape)
                analysis_results["quality_assessment"] = self._assess_geometry_quality(shape)
                
                if self.analyze_assemblies:
                    analysis_results["assembly_potential"] = self._analyze_assembly_potential(shape)
            
            # Dosya spesifik analizler
            if file_path:
                analysis_results["file_analysis"] = self._analyze_file_characteristics(file_path, shape)
            
            self.logger.info("Geometri analizi tamamlandı")
            return analysis_results
            
        except Exception as e:
            error_msg = f"Geometri analizi hatası: {str(e)}"
            self.logger.error(error_msg)
            return {
                "analysis_timestamp": self._get_current_time(),
                "error": error_msg,
                "shape_valid": False
            }
    
    def _analyze_geometric_properties(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """Geometrik özelliklerin detaylı analizi"""
        try:
            properties = {}
            
            # Hacim özellikleri
            if self._has_volume(shape):
                volume_props = GProp_GProps()
                BRepGProp.VolumeProperties(shape, volume_props)
                
                properties["volume"] = {
                    "value": volume_props.Mass(),
                    "center_of_mass": self._gp_pnt_to_tuple(volume_props.CentreOfMass()),
                    "moment_of_inertia": self._extract_inertia_matrix(volume_props)
                }
            
            # Yüzey özellikleri
            surface_props = GProp_GProps()
            BRepGProp.SurfaceProperties(shape, surface_props)
            
            properties["surface"] = {
                "area": surface_props.Mass(),
                "center": self._gp_pnt_to_tuple(surface_props.CentreOfMass())
            }
            
            # Bounding box detayları
            bbox = Bnd_Box()
            BRepBndLib.Add(shape, bbox)
            
            if not bbox.IsVoid():
                xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
                properties["bounding_box"] = {
                    "dimensions": {
                        "width": xmax - xmin,
                        "height": ymax - ymin,
                        "depth": zmax - zmin
                    },
                    "volume": (xmax - xmin) * (ymax - ymin) * (zmax - zmin),
                    "center": ((xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2),
                    "diagonal_length": math.sqrt((xmax - xmin)**2 + (ymax - ymin)**2 + (zmax - zmin)**2)
                }
            
            return properties
            
        except Exception as e:
            self.logger.warning(f"Geometrik özellik analizi hatası: {e}")
            return {}
    
    def _analyze_complexity(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """Geometrik karmaşıklık analizi"""
        try:
            explorer = TopologyExplorer(shape)
            
            complexity = {
                "topology_counts": {
                    "solids": explorer.number_of_solids(),
                    "shells": explorer.number_of_shells(),
                    "faces": explorer.number_of_faces(),
                    "wires": explorer.number_of_wires(),
                    "edges": explorer.number_of_edges(),
                    "vertices": explorer.number_of_vertices()
                }
            }
            
            # Karmaşıklık skoru hesapla
            score = (
                complexity["topology_counts"]["solids"] * 10 +
                complexity["topology_counts"]["faces"] * 2 +
                complexity["topology_counts"]["edges"] * 1 +
                complexity["topology_counts"]["vertices"] * 0.1
            )
            
            complexity["complexity_score"] = score
            
            # Karmaşıklık kategorisi
            if score < 50:
                complexity["complexity_category"] = "basit"
            elif score < 200:
                complexity["complexity_category"] = "orta"
            elif score < 1000:
                complexity["complexity_category"] = "karmaşık"
            else:
                complexity["complexity_category"] = "çok_karmaşık"
            
            # Yüzey türü dağılımı
            surface_types = self._analyze_surface_type_distribution(shape)
            complexity["surface_type_distribution"] = surface_types
            
            return complexity
            
        except Exception as e:
            self.logger.warning(f"Karmaşıklık analizi hatası: {e}")
            return {}
    
    def _analyze_manufacturing_features(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """İmalat özelliklerini analiz et (delikler, yuvalar vs.)"""
        try:
            features = {
                "holes": [],
                "pockets": [],
                "bosses": [],
                "fillets": [],
                "chamfers": [],
                "threads": []
            }
            
            # Silindirik yüzeylerden hole detection
            surfaces = self.geometry_handler._analyze_surfaces(shape)
            
            for i, surface in enumerate(surfaces):
                if surface.get("is_cylindrical"):
                    radius = surface.get("cylinder_radius", 0)
                    
                    # Küçük yarıçaplı silindirik yüzeyler = potansiyel delik
                    if radius < 25:  # 25mm altı delik olarak kabul et
                        features["holes"].append({
                            "surface_index": i,
                            "center": surface.get("cylinder_axis_origin"),
                            "axis": surface.get("cylinder_axis_direction"),
                            "radius": radius,
                            "type": "cylindrical_hole"
                        })
                    else:
                        features["bosses"].append({
                            "surface_index": i,
                            "center": surface.get("cylinder_axis_origin"),
                            "radius": radius,
                            "type": "cylindrical_boss"
                        })
            
            # Feature istatistikleri
            feature_stats = {
                "total_features": sum(len(features[key]) for key in features),
                "hole_count": len(features["holes"]),
                "boss_count": len(features["bosses"])
            }
            
            return {
                "features": features,
                "statistics": feature_stats
            }
            
        except Exception as e:
            self.logger.warning(f"İmalat özellik analizi hatası: {e}")
            return {}
    
    def _detailed_surface_analysis(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """Yüzeylerin detaylı analizi"""
        try:
            analysis = {
                "surface_summary": {},
                "surface_details": [],
                "continuity_analysis": {},
                "curvature_analysis": {}
            }
            
            explorer = TopologyExplorer(shape)
            surface_types = {}
            
            for face in explorer.faces():
                try:
                    surface = BRepAdaptor_Surface(face)
                    surface_type = surface.GetType()
                    
                    type_name = self._get_surface_type_name(surface_type)
                    
                    if type_name not in surface_types:
                        surface_types[type_name] = 0
                    surface_types[type_name] += 1
                    
                    # Yüzey alanı
                    props = GProp_GProps()
                    BRepGProp.SurfaceProperties(face, props)
                    area = props.Mass()
                    
                    surface_detail = {
                        "type": type_name,
                        "area": area,
                        "orientation": face.Orientation()
                    }
                    
                    analysis["surface_details"].append(surface_detail)
                    
                except Exception as e:
                    self.logger.debug(f"Tekil yüzey analizi hatası: {e}")
                    continue
            
            analysis["surface_summary"] = surface_types
            
            return analysis
            
        except Exception as e:
            self.logger.warning(f"Detaylı yüzey analizi hatası: {e}")
            return {}
    
    def _assess_geometry_quality(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """Geometri kalitesini değerlendir"""
        try:
            quality = {
                "overall_score": 0,
                "issues": [],
                "warnings": [],
                "recommendations": []
            }
            
            # Temel validasyon
            if shape.IsNull():
                quality["issues"].append("Shape null")
                return quality
            
            explorer = TopologyExplorer(shape)
            
            # Edge kontrolleri
            degenerated_edges = 0
            for edge in explorer.edges():
                if BRep_Tool.Degenerated(edge):
                    degenerated_edges += 1
            
            if degenerated_edges > 0:
                quality["warnings"].append(f"{degenerated_edges} dejenere kenar bulundu")
            
            # Yüzey kontrolleri
            total_faces = explorer.number_of_faces()
            if total_faces == 0:
                quality["issues"].append("Hiç yüzey bulunamadı")
            elif total_faces > 10000:
                quality["warnings"].append(f"Çok fazla yüzey: {total_faces} (performans sorunu olabilir)")
            
            # Kalite skoru hesapla
            score = 100
            score -= len(quality["issues"]) * 20
            score -= len(quality["warnings"]) * 5
            score -= degenerated_edges * 2
            
            quality["overall_score"] = max(0, min(100, score))
            
            # Öneriler
            if score < 80:
                quality["recommendations"].append("Geometri healing uygulanması önerilir")
            
            if total_faces > 5000:
                quality["recommendations"].append("Görüntüleme performansı için shape simplification düşünülebilir")
            
            return quality
            
        except Exception as e:
            self.logger.warning(f"Kalite değerlendirme hatası: {e}")
            return {"overall_score": 0, "error": str(e)}
    
    def _analyze_assembly_potential(self, shape: TopoDS_Shape) -> Dict[str, Any]:
        """Montaj potansiyelini analiz et"""
        try:
            assembly_analysis = {
                "connection_surfaces": [],
                "mating_features": [],
                "constraints": [],
                "assembly_score": 0
            }
            
            # Düzlemsel yüzeyleri bul (potansiyel mate yüzeyleri)
            surfaces = self.geometry_handler._analyze_surfaces(shape)
            
            planar_surfaces = [s for s in surfaces if s.get("is_planar")]
            cylindrical_surfaces = [s for s in surfaces if s.get("is_cylindrical")]
            
            # Büyük düzlemsel yüzeyler = potansiyel mate yüzeyi
            for surface in planar_surfaces:
                area = surface.get("area", 0)
                if area > 100:  # 100 mm² üstü
                    assembly_analysis["connection_surfaces"].append({
                        "type": "planar_mate",
                        "area": area,
                        "normal": surface.get("plane_normal"),
                        "center": surface.get("center")
                    })
            
            # Silindirik yüzeyler = potansiyel pin/hole bağlantıları
            for surface in cylindrical_surfaces:
                radius = surface.get("cylinder_radius", 0)
                if radius < 50:  # Küçük silindir = pin/hole
                    assembly_analysis["mating_features"].append({
                        "type": "cylindrical_feature",
                        "radius": radius,
                        "axis": surface.get("cylinder_axis_direction"),
                        "center": surface.get("cylinder_axis_origin")
                    })
            
            # Assembly score hesapla
            score = 0
            score += len(assembly_analysis["connection_surfaces"]) * 10
            score += len(assembly_analysis["mating_features"]) * 5
            
            assembly_analysis["assembly_score"] = min(100, score)
            
            return assembly_analysis
            
        except Exception as e:
            self.logger.warning(f"Montaj potansiyeli analizi hatası: {e}")
            return {}
    
    def _analyze_file_characteristics(self, file_path: str, shape: TopoDS_Shape) -> Dict[str, Any]:
        """Dosya karakteristiklerini analiz et"""
        try:
            file_analysis = {
                "file_name": Path(file_path).name,
                "file_extension": Path(file_path).suffix.lower(),
                "file_size_mb": os.path.getsize(file_path) / (1024 * 1024),
                "geometry_efficiency": {}
            }
            
            # Geometri verimliliği (dosya boyutu vs geometri karmaşıklığı)
            explorer = TopologyExplorer(shape)
            total_entities = (
                explorer.number_of_solids() +
                explorer.number_of_faces() +
                explorer.number_of_edges()
            )
            
            if file_analysis["file_size_mb"] > 0:
                entities_per_mb = total_entities / file_analysis["file_size_mb"]
                file_analysis["geometry_efficiency"]["entities_per_mb"] = entities_per_mb
                
                # Verimlilik değerlendirmesi
                if entities_per_mb > 1000:
                    file_analysis["geometry_efficiency"]["rating"] = "yüksek"
                elif entities_per_mb > 100:
                    file_analysis["geometry_efficiency"]["rating"] = "orta"
                else:
                    file_analysis["geometry_efficiency"]["rating"] = "düşük"
            
            return file_analysis
            
        except Exception as e:
            self.logger.warning(f"Dosya karakteristik analizi hatası: {e}")
            return {}
    
    def _analyze_surface_type_distribution(self, shape: TopoDS_Shape) -> Dict[str, int]:
        """Yüzey türlerinin dağılımını analiz et"""
        try:
            surface_types = {}
            explorer = TopologyExplorer(shape)
            
            for face in explorer.faces():
                try:
                    surface = BRepAdaptor_Surface(face)
                    type_name = self._get_surface_type_name(surface.GetType())
                    
                    if type_name not in surface_types:
                        surface_types[type_name] = 0
                    surface_types[type_name] += 1
                    
                except:
                    continue
            
            return surface_types
            
        except Exception as e:
            self.logger.warning(f"Yüzey türü dağılım analizi hatası: {e}")
            return {}
    
    def _get_surface_type_name(self, surface_type) -> str:
        """Yüzey tipini string'e çevir"""
        from OCC.Core import (
            GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Sphere, GeomAbs_Cone,
            GeomAbs_Torus, GeomAbs_BezierSurface, GeomAbs_BSplineSurface
        )
        
        type_map = {
            GeomAbs_Plane: "DÜZLEM",
            GeomAbs_Cylinder: "SİLİNDİR",
            GeomAbs_Sphere: "KÜRE",
            GeomAbs_Cone: "KONİ",
            GeomAbs_Torus: "TORUS",
            GeomAbs_BezierSurface: "BEZIER",
            GeomAbs_BSplineSurface: "BSPLINE"
        }
        return type_map.get(surface_type, "DİĞER")
    
    def _has_volume(self, shape: TopoDS_Shape) -> bool:
        """Shape'in hacmi var mı"""
        return shape.ShapeType() == TopAbs_SOLID
    
    def _extract_inertia_matrix(self, props: GProp_GProps) -> Dict[str, float]:
        """Atalet matrisini çıkar"""
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
    
    def _gp_pnt_to_tuple(self, pnt) -> Tuple[float, float, float]:
        """gp_Pnt'yi tuple'a çevir"""
        try:
            return (pnt.X(), pnt.Y(), pnt.Z())
        except:
            return (0, 0, 0)
    
    def _get_current_time(self) -> str:
        """Mevcut zamanı al"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_analysis_report(self, analysis_data: Dict[str, Any]) -> str:
        """Analiz sonuçlarından rapor oluştur"""
        try:
            report_lines = []
            report_lines.append("=== GEOMETRİ ANALİZİ RAPORU ===")
            report_lines.append(f"Tarih: {analysis_data.get('analysis_timestamp', 'Bilinmeyen')}")
            report_lines.append("")
            
            # Temel bilgiler
            if "source_file" in analysis_data and analysis_data["source_file"]:
                report_lines.append(f"Kaynak Dosya: {analysis_data['source_file']}")
            
            report_lines.append(f"Analiz Seviyesi: {analysis_data.get('analysis_level', 'Bilinmeyen')}")
            report_lines.append("")
            
            # Temel geometri
            basic_geom = analysis_data.get("basic_geometry", {})
            if basic_geom:
                topology = basic_geom.get("topology", {})
                report_lines.append("TEMEL GEOMETRİ:")
                report_lines.append(f"  - Katı sayısı: {topology.get('num_solids', 0)}")
                report_lines.append(f"  - Yüzey sayısı: {topology.get('num_faces', 0)}")
                report_lines.append(f"  - Kenar sayısı: {topology.get('num_edges', 0)}")
                report_lines.append("")
            
            # Karmaşıklık
            complexity = analysis_data.get("complexity_analysis", {})
            if complexity:
                report_lines.append("KARMAŞIKLIK ANALİZİ:")
                report_lines.append(f"  - Kategori: {complexity.get('complexity_category', 'Bilinmeyen')}")
                report_lines.append(f"  - Skor: {complexity.get('complexity_score', 0):.1f}")
                report_lines.append("")
            
            # Özellikler
            features = analysis_data.get("features", {})
            if features:
                stats = features.get("statistics", {})
                report_lines.append("İMALAT ÖZELLİKLERİ:")
                report_lines.append(f"  - Toplam özellik: {stats.get('total_features', 0)}")
                report_lines.append(f"  - Delik sayısı: {stats.get('hole_count', 0)}")
                report_lines.append("")
            
            # Kalite
            quality = analysis_data.get("quality_assessment", {})
            if quality:
                report_lines.append("KALİTE DEĞERLENDİRMESİ:")
                report_lines.append(f"  - Genel skor: {quality.get('overall_score', 0)}/100")
                
                issues = quality.get("issues", [])
                if issues:
                    report_lines.append("  - Sorunlar:")
                    for issue in issues:
                        report_lines.append(f"    * {issue}")
                
                warnings = quality.get("warnings", [])
                if warnings:
                    report_lines.append("  - Uyarılar:")
                    for warning in warnings:
                        report_lines.append(f"    * {warning}")
                report_lines.append("")
            
            # Montaj potansiyeli
            assembly = analysis_data.get("assembly_potential", {})
            if assembly:
                report_lines.append("MONTAJ POTANSİYELİ:")
                report_lines.append(f"  - Montaj skoru: {assembly.get('assembly_score', 0)}/100")
                report_lines.append(f"  - Bağlantı yüzeyi sayısı: {len(assembly.get('connection_surfaces', []))}")
                report_lines.append("")
            
            report_lines.append("=== RAPOR SONU ===")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            self.logger.error(f"Rapor oluşturma hatası: {e}")
            return f"Rapor oluşturma hatası: {str(e)}"
    
    def export_analysis_to_json(self, analysis_data: Dict[str, Any], output_path: str) -> bool:
        """Analiz sonuçlarını JSON'a aktar"""
        try:
            import json
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Analiz JSON'a aktarıldı: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"JSON aktarma hatası: {e}")
            return False
    
    def compare_geometries(self, 
                          analysis1: Dict[str, Any], 
                          analysis2: Dict[str, Any]) -> Dict[str, Any]:
        """İki geometri analizini karşılaştır"""
        try:
            comparison = {
                "comparison_timestamp": self._get_current_time(),
                "geometry1": analysis1.get("source_file", "Geometry 1"),
                "geometry2": analysis2.get("source_file", "Geometry 2"),
                "differences": {},
                "similarities": {}
            }
            
            # Topology karşılaştırması
            topo1 = analysis1.get("basic_geometry", {}).get("topology", {})
            topo2 = analysis2.get("basic_geometry", {}).get("topology", {})
            
            if topo1 and topo2:
                comparison["differences"]["topology"] = {
                    "faces_diff": topo2.get("num_faces", 0) - topo1.get("num_faces", 0),
                    "edges_diff": topo2.get("num_edges", 0) - topo1.get("num_edges", 0),
                    "vertices_diff": topo2.get("num_vertices", 0) - topo1.get("num_vertices", 0)
                }
            
            # Karmaşıklık karşılaştırması
            comp1 = analysis1.get("complexity_analysis", {}).get("complexity_score", 0)
            comp2 = analysis2.get("complexity_analysis", {}).get("complexity_score", 0)
            
            comparison["differences"]["complexity_score_diff"] = comp2 - comp1
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Geometri karşılaştırma hatası: {e}")
            return {"error": str(e)}
    
    def clear_analysis_cache(self):
        """Analiz cache'ini temizle"""
        self.analysis_cache.clear()
        self.logger.debug("Analiz cache temizlendi")