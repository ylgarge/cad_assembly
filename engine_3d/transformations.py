"""
3D Dönüşüm İşlemleri
Geometrik dönüşümler, rotasyonlar, translasyonlar ve hizalama işlemleri
"""

import logging
import math
import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from enum import Enum

try:
    # Temel geometrik sınıflar
    from OCC.Core.gp import (
        gp_Pnt, gp_Vec, gp_Dir, gp_Ax1, gp_Ax2, gp_Ax3,
        gp_Quaternion, gp_Trsf, gp_GTrsf, gp_Mat
    )

    # Dönüşüm tipleri
    from OCC.Core.gp import (
        gp_Translation, gp_Rotation, gp_Scale
    )

    # Shape dönüşümleri
    from OCC.Core.TopoDS import TopoDS_Shape
    from OCC.Core.BRepBuilderAPI import (
        BRepBuilderAPI_Transform, BRepBuilderAPI_GTransform
    )

    # Matematik fonksiyonları
    from OCC.Core import math as occ_math

    # Precision
    from OCC.Core.Precision import precision

except ImportError as e:
    logging.error(f"PythonOCC dönüşüm import hatası: {e}")
    raise

class TransformationType(Enum):
    """Dönüşüm tipleri"""
    TRANSLATION = "translation"
    ROTATION = "rotation" 
    SCALING = "scaling"
    MIRRORING = "mirroring"
    COMBINED = "combined"

class RotationAxis(Enum):
    """Rotasyon eksenleri"""
    X_AXIS = "x_axis"
    Y_AXIS = "y_axis"
    Z_AXIS = "z_axis"
    CUSTOM = "custom"

class TransformationManager:
    """3D dönüşüm işlemlerini yöneten sınıf"""
    
    def __init__(self):
        self.logger = logging.getLogger("CADMontaj.TransformationManager")
        
        # Dönüşüm geçmişi
        self.transformation_history = []
        
        # Precision değerleri
        self.linear_precision = precision.Confusion()
        self.angular_precision = precision.Angular()
        
    def create_translation(self, 
                         vector: Tuple[float, float, float]) -> gp_Trsf:
        """
        Öteleme dönüşümü oluştur
        
        Args:
            vector: (x, y, z) öteleme vektörü
            
        Returns:
            gp_Trsf dönüşüm objesi
        """
        try:
            transformation = gp_Trsf()
            translation_vec = gp_Vec(vector[0], vector[1], vector[2])
            transformation.SetTranslation(translation_vec)
            
            self.logger.debug(f"Öteleme dönüşümü oluşturuldu: {vector}")
            return transformation
            
        except Exception as e:
            self.logger.error(f"Öteleme dönüşümü hatası: {e}")
            return gp_Trsf()  # Identity transform
    
    def create_rotation(self, 
                       axis_origin: Tuple[float, float, float],
                       axis_direction: Tuple[float, float, float],
                       angle_degrees: float) -> gp_Trsf:
        """
        Rotasyon dönüşümü oluştur
        
        Args:
            axis_origin: Rotasyon ekseni başlangıç noktası
            axis_direction: Rotasyon ekseni yönü (normalize edilmiş)
            angle_degrees: Derece cinsinden açı
            
        Returns:
            gp_Trsf dönüşüm objesi
        """
        try:
            transformation = gp_Trsf()
            
            # Rotasyon ekseni oluştur
            origin = gp_Pnt(axis_origin[0], axis_origin[1], axis_origin[2])
            direction = gp_Dir(axis_direction[0], axis_direction[1], axis_direction[2])
            axis = gp_Ax1(origin, direction)
            
            # Radyan'a çevir
            angle_radians = math.radians(angle_degrees)
            
            transformation.SetRotation(axis, angle_radians)
            
            self.logger.debug(f"Rotasyon dönüşümü oluşturuldu: {angle_degrees}° eksen {axis_direction}")
            return transformation
            
        except Exception as e:
            self.logger.error(f"Rotasyon dönüşümü hatası: {e}")
            return gp_Trsf()
    
    def create_rotation_xyz(self, 
                           rotation_point: Tuple[float, float, float],
                           axis: RotationAxis,
                           angle_degrees: float) -> gp_Trsf:
        """
        Ana eksenler etrafında rotasyon oluştur
        
        Args:
            rotation_point: Rotasyon merkezi
            axis: Rotasyon ekseni (X, Y, Z)
            angle_degrees: Derece cinsinden açı
            
        Returns:
            gp_Trsf dönüşüm objesi
        """
        axis_directions = {
            RotationAxis.X_AXIS: (1, 0, 0),
            RotationAxis.Y_AXIS: (0, 1, 0), 
            RotationAxis.Z_AXIS: (0, 0, 1)
        }
        
        if axis in axis_directions:
            return self.create_rotation(
                rotation_point, 
                axis_directions[axis], 
                angle_degrees
            )
        else:
            self.logger.warning(f"Geçersiz rotasyon ekseni: {axis}")
            return gp_Trsf()
    
    def create_scaling(self, 
                      scale_center: Tuple[float, float, float],
                      scale_factor: float) -> gp_Trsf:
        """
        Ölçekleme dönüşümü oluştur
        
        Args:
            scale_center: Ölçekleme merkezi
            scale_factor: Ölçek faktörü (1.0 = değişiklik yok)
            
        Returns:
            gp_Trsf dönüşüm objesi
        """
        try:
            transformation = gp_Trsf()
            center = gp_Pnt(scale_center[0], scale_center[1], scale_center[2])
            
            transformation.SetScale(center, scale_factor)
            
            self.logger.debug(f"Ölçekleme dönüşümü oluşturuldu: faktör {scale_factor}")
            return transformation
            
        except Exception as e:
            self.logger.error(f"Ölçekleme dönüşümü hatası: {e}")
            return gp_Trsf()
    
    def create_mirroring(self, 
                        mirror_plane_origin: Tuple[float, float, float],
                        mirror_plane_normal: Tuple[float, float, float]) -> gp_Trsf:
        """
        Aynalama dönüşümü oluştur
        
        Args:
            mirror_plane_origin: Ayna düzlemi üzerinde bir nokta
            mirror_plane_normal: Ayna düzleminin normal vektörü
            
        Returns:
            gp_Trsf dönüşüm objesi
        """
        try:
            transformation = gp_Trsf()
            
            origin = gp_Pnt(mirror_plane_origin[0], mirror_plane_origin[1], mirror_plane_origin[2])
            normal = gp_Dir(mirror_plane_normal[0], mirror_plane_normal[1], mirror_plane_normal[2])
            axis = gp_Ax1(origin, normal)
            
            transformation.SetMirror(axis)
            
            self.logger.debug(f"Aynalama dönüşümü oluşturuldu")
            return transformation
            
        except Exception as e:
            self.logger.error(f"Aynalama dönüşümü hatası: {e}")
            return gp_Trsf()
    
    def combine_transformations(self, transformations: List[gp_Trsf]) -> gp_Trsf:
        """
        Birden fazla dönüşümü birleştir
        
        Args:
            transformations: Dönüşümler listesi (sıralı)
            
        Returns:
            Birleştirilmiş dönüşüm
        """
        try:
            combined = gp_Trsf()
            
            for transform in transformations:
                combined = combined.Multiplied(transform)
            
            self.logger.debug(f"{len(transformations)} dönüşüm birleştirildi")
            return combined
            
        except Exception as e:
            self.logger.error(f"Dönüşüm birleştirme hatası: {e}")
            return gp_Trsf()
    
    def apply_transformation(self, 
                           shape: TopoDS_Shape, 
                           transformation: gp_Trsf) -> Optional[TopoDS_Shape]:
        """
        Shape'e dönüşüm uygula
        
        Args:
            shape: Dönüştürülecek shape
            transformation: Uygulanacak dönüşüm
            
        Returns:
            Dönüştürülmüş shape
        """
        try:
            if not shape or shape.IsNull():
                self.logger.warning("Geçersiz shape için dönüşüm uygulanamaz")
                return None
            
            # BRepBuilderAPI_Transform kullan
            transform_builder = BRepBuilderAPI_Transform(shape, transformation)
            transform_builder.Build()
            
            if transform_builder.IsDone():
                transformed_shape = transform_builder.Shape()
                self.logger.debug("Dönüşüm başarıyla uygulandı")
                return transformed_shape
            else:
                self.logger.error("Dönüşüm uygulama başarısız")
                return None
                
        except Exception as e:
            self.logger.error(f"Dönüşüm uygulama hatası: {e}")
            return None
    
    def create_alignment_transformation(self, 
                                      source_point: Tuple[float, float, float],
                                      source_direction: Tuple[float, float, float],
                                      target_point: Tuple[float, float, float], 
                                      target_direction: Tuple[float, float, float]) -> gp_Trsf:
        """
        Hizalama dönüşümü oluştur (bir koordinat sistemini diğerine hizala)
        
        Args:
            source_point: Kaynak koordinat sistemi orijini
            source_direction: Kaynak Z ekseni yönü
            target_point: Hedef koordinat sistemi orijini  
            target_direction: Hedef Z ekseni yönü
            
        Returns:
            Hizalama dönüşümü
        """
        try:
            # Kaynak koordinat sistemi
            src_origin = gp_Pnt(source_point[0], source_point[1], source_point[2])
            src_z_dir = gp_Dir(source_direction[0], source_direction[1], source_direction[2])
            
            # Target koordinat sistemi  
            tgt_origin = gp_Pnt(target_point[0], target_point[1], target_point[2])
            tgt_z_dir = gp_Dir(target_direction[0], target_direction[1], target_direction[2])
            
            # X ve Y eksenlerini otomatik hesapla
            # Basit yaklaşım: Z'ye dik olan iki eksen bul
            
            # Kaynak koordinat sistemi
            if abs(src_z_dir.Z()) < 0.9:  # Z ekseni çok dik değilse
                src_x_dir = gp_Dir(0, 0, 1).Crossed(src_z_dir)
            else:
                src_x_dir = gp_Dir(1, 0, 0).Crossed(src_z_dir)
            
            src_y_dir = src_z_dir.Crossed(src_x_dir)
            src_coord_sys = gp_Ax3(src_origin, src_z_dir, src_x_dir)
            
            # Hedef koordinat sistemi
            if abs(tgt_z_dir.Z()) < 0.9:
                tgt_x_dir = gp_Dir(0, 0, 1).Crossed(tgt_z_dir)
            else:
                tgt_x_dir = gp_Dir(1, 0, 0).Crossed(tgt_z_dir)
                
            tgt_y_dir = tgt_z_dir.Crossed(tgt_x_dir)
            tgt_coord_sys = gp_Ax3(tgt_origin, tgt_z_dir, tgt_x_dir)
            
            # Dönüşüm oluştur
            transformation = gp_Trsf()
            transformation.SetTransformation(src_coord_sys, tgt_coord_sys)
            
            self.logger.debug("Hizalama dönüşümü oluşturuldu")
            return transformation
            
        except Exception as e:
            self.logger.error(f"Hizalama dönüşümü hatası: {e}")
            return gp_Trsf()
    
    def calculate_transformation_matrix(self, transformation: gp_Trsf) -> np.ndarray:
        """
        gp_Trsf'yi 4x4 transformation matrix'e çevir
        
        Args:
            transformation: OCC transformation objesi
            
        Returns:
            4x4 numpy array transformation matrix
        """
        try:
            # Rotasyon kısmını al (3x3)
            rotation_matrix = np.array([
                [transformation.Value(1, 1), transformation.Value(1, 2), transformation.Value(1, 3)],
                [transformation.Value(2, 1), transformation.Value(2, 2), transformation.Value(2, 3)], 
                [transformation.Value(3, 1), transformation.Value(3, 2), transformation.Value(3, 3)]
            ])
            
            # Translation kısmını al
            translation_vector = np.array([
                transformation.Value(1, 4),
                transformation.Value(2, 4), 
                transformation.Value(3, 4)
            ])
            
            # 4x4 matrix oluştur
            matrix = np.eye(4)
            matrix[:3, :3] = rotation_matrix
            matrix[:3, 3] = translation_vector
            
            return matrix
            
        except Exception as e:
            self.logger.error(f"Transformation matrix hesaplama hatası: {e}")
            return np.eye(4)
    
    def matrix_to_transformation(self, matrix: np.ndarray) -> gp_Trsf:
        """
        4x4 numpy matrix'i gp_Trsf'ye çevir
        
        Args:
            matrix: 4x4 transformation matrix
            
        Returns:
            gp_Trsf objesi
        """
        try:
            if matrix.shape != (4, 4):
                raise ValueError("Matrix 4x4 olmalı")
            
            transformation = gp_Trsf()
            
            # gp_Mat oluştur (3x3 rotasyon)
            rotation_mat = gp_Mat(
                matrix[0, 0], matrix[0, 1], matrix[0, 2],
                matrix[1, 0], matrix[1, 1], matrix[1, 2],
                matrix[2, 0], matrix[2, 1], matrix[2, 2]
            )
            
            # Translation vektörü
            translation = gp_Vec(matrix[0, 3], matrix[1, 3], matrix[2, 3])
            
            # Dönüşümü ayarla
            transformation.SetValues(
                matrix[0, 0], matrix[0, 1], matrix[0, 2], matrix[0, 3],
                matrix[1, 0], matrix[1, 1], matrix[1, 2], matrix[1, 3],
                matrix[2, 0], matrix[2, 1], matrix[2, 2], matrix[2, 3]
            )
            
            return transformation
            
        except Exception as e:
            self.logger.error(f"Matrix'ten transformation dönüşümü hatası: {e}")
            return gp_Trsf()
    
    def get_transformation_info(self, transformation: gp_Trsf) -> Dict[str, Any]:
        """
        Transformation hakkında bilgi al
        
        Args:
            transformation: Analiz edilecek dönüşüm
            
        Returns:
            Transformation bilgileri
        """
        try:
            info = {
                "form": transformation.Form(),
                "scale_factor": transformation.ScaleFactor(),
                "is_negative": transformation.IsNegative(),
                "translation": self._get_translation_vector(transformation),
                "rotation_info": self._get_rotation_info(transformation)
            }
            
            # Form tipini string'e çevir
            form_names = {
                0: "Identity",
                1: "Rotation", 
                2: "Translation",
                3: "PntMirror",
                4: "Ax1Mirror", 
                5: "Ax2Mirror",
                6: "Scale",
                7: "CompoundTrsf"
            }
            
            info["form_name"] = form_names.get(transformation.Form(), "Unknown")
            
            return info
            
        except Exception as e:
            self.logger.error(f"Transformation bilgi alma hatası: {e}")
            return {}
    
    def _get_translation_vector(self, transformation: gp_Trsf) -> Tuple[float, float, float]:
        """Dönüşümden translation vektörü çıkar"""
        try:
            return (
                transformation.Value(1, 4),
                transformation.Value(2, 4),
                transformation.Value(3, 4)
            )
        except:
            return (0, 0, 0)
    
    def _get_rotation_info(self, transformation: gp_Trsf) -> Dict[str, Any]:
        """Dönüşümden rotasyon bilgisi çıkar"""
        try:
            # Bu basitleştirilmiş bir yaklaşım
            # Tam implementation quaternion kullanabilir
            rotation_matrix = np.array([
                [transformation.Value(1, 1), transformation.Value(1, 2), transformation.Value(1, 3)],
                [transformation.Value(2, 1), transformation.Value(2, 2), transformation.Value(2, 3)],
                [transformation.Value(3, 1), transformation.Value(3, 2), transformation.Value(3, 3)]
            ])
            
            # Trace'den angle hesapla
            trace = np.trace(rotation_matrix)
            angle = math.acos(max(-1, min(1, (trace - 1) / 2)))
            angle_degrees = math.degrees(angle)
            
            return {
                "angle_degrees": angle_degrees,
                "angle_radians": angle,
                "rotation_matrix": rotation_matrix.tolist()
            }
            
        except Exception as e:
            self.logger.warning(f"Rotasyon bilgisi çıkarma hatası: {e}")
            return {}
    
    def invert_transformation(self, transformation: gp_Trsf) -> gp_Trsf:
        """Dönüşümün tersini hesapla"""
        try:
            inverted = transformation.Inverted()
            self.logger.debug("Dönüşüm ters çevrildi")
            return inverted
        except Exception as e:
            self.logger.error(f"Dönüşüm ters çevirme hatası: {e}")
            return gp_Trsf()
    
    def is_similar_transformation(self, 
                                 transform1: gp_Trsf, 
                                 transform2: gp_Trsf,
                                 tolerance: float = 1e-6) -> bool:
        """İki dönüşümün benzer olup olmadığını kontrol et"""
        try:
            # Matrisleri karşılaştır
            matrix1 = self.calculate_transformation_matrix(transform1)
            matrix2 = self.calculate_transformation_matrix(transform2)
            
            diff = np.abs(matrix1 - matrix2)
            max_diff = np.max(diff)
            
            return max_diff < tolerance
            
        except Exception as e:
            self.logger.error(f"Dönüşüm karşılaştırma hatası: {e}")
            return False
    
    def save_transformation_history(self, 
                                   shape_id: str, 
                                   transformation: gp_Trsf,
                                   description: str = ""):
        """Dönüşüm geçmişini kaydet"""
        try:
            history_entry = {
                "shape_id": shape_id,
                "transformation": transformation,
                "description": description,
                "timestamp": self._get_current_timestamp(),
                "transformation_info": self.get_transformation_info(transformation)
            }
            
            self.transformation_history.append(history_entry)
            
            # Geçmişi sınırla (son 100 dönüşüm)
            if len(self.transformation_history) > 100:
                self.transformation_history = self.transformation_history[-100:]
                
        except Exception as e:
            self.logger.error(f"Dönüşüm geçmişi kaydetme hatası: {e}")
    
    def _get_current_timestamp(self) -> str:
        """Mevcut zaman damgası al"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_transformation_history(self, shape_id: str = None) -> List[Dict[str, Any]]:
        """Dönüşüm geçmişini al"""
        if shape_id:
            return [entry for entry in self.transformation_history 
                   if entry["shape_id"] == shape_id]
        else:
            return self.transformation_history.copy()
    
    def clear_transformation_history(self):
        """Dönüşüm geçmişini temizle"""
        self.transformation_history.clear()
        self.logger.debug("Dönüşüm geçmişi temizlendi")