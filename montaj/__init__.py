"""
Montaj Modülü
CAD parçalarının otomatik montajı için ana modül
"""

from .assembly_engine import AssemblyEngine, AssemblyResult, AssemblyStatus
from .collision_detector import CollisionDetector, CollisionInfo, CollisionType
from .alignment_tools import AlignmentTools, AlignmentType
from .connection_finder import ConnectionFinder, ConnectionType

__version__ = "1.0.0"
__author__ = "CAD Developer"

# Ana sınıfları export et
__all__ = [
    'AssemblyEngine',
    'AssemblyResult', 
    'AssemblyStatus',
    'CollisionDetector',
    'CollisionInfo',
    'CollisionType',
    'AlignmentTools',
    'AlignmentType', 
    'ConnectionFinder',
    'ConnectionType'
]

def create_assembly_engine(config=None):
    """Assembly engine oluştur"""
    return AssemblyEngine(config)

def create_collision_detector(config=None):
    """Collision detector oluştur"""
    return CollisionDetector(config)

def create_alignment_tools(config=None):
    """Alignment tools oluştur"""
    return AlignmentTools(config)

def create_connection_finder(config=None):
    """Connection finder oluştur"""
    return ConnectionFinder(config)

# Convenience function - tek fonksiyonla montaj
def perform_simple_assembly(base_shape, attach_shape, config=None):
    """
    Basit montaj işlemi (tek fonksiyon çağrısı)
    
    Args:
        base_shape: Ana parça
        attach_shape: Eklenecek parça
        config: Konfigürasyon
        
    Returns:
        AssemblyResult objesi
    """
    try:
        engine = create_assembly_engine(config)
        result = engine.perform_assembly(base_shape, attach_shape)
        return result
        
    except Exception as e:
        # Hata durumunda boş result döndür
        from .assembly_engine import AssemblyResult, AssemblyStatus
        result = AssemblyResult()
        result.status = AssemblyStatus.FAILED
        result.error_message = str(e)
        return result

def check_collision_simple(shape1, shape2, config=None):
    """
    Basit çakışma kontrolü
    
    Args:
        shape1: İlk parça
        shape2: İkinci parça
        config: Konfigürasyon
        
    Returns:
        True = çakışma var, False = çakışma yok
    """
    try:
        detector = create_collision_detector(config)
        return detector.check_collision(shape1, shape2)
    except Exception as e:
        import logging
        logging.error(f"Basit çakışma kontrolü hatası: {e}")
        return True  # Güvenli taraf - çakışma var varsay

def find_connections_simple(shape1, shape2, config=None):
    """
    Basit bağlantı noktası bulma
    
    Args:
        shape1: İlk parça
        shape2: İkinci parça
        config: Konfigürasyon
        
    Returns:
        Bağlantı noktaları listesi
    """
    try:
        finder = create_connection_finder(config)
        return finder.find_all_connections(shape1, shape2)
    except Exception as e:
        import logging
        logging.error(f"Basit bağlantı bulma hatası: {e}")
        return []

def align_parts_simple(source_shape, target_shape, connection_info, config=None):
    """
    Basit parça hizalama
    
    Args:
        source_shape: Hareket edecek parça
        target_shape: Sabit parça
        connection_info: Bağlantı bilgisi
        config: Konfigürasyon
        
    Returns:
        Hizalanmış parça
    """
    try:
        tools = create_alignment_tools(config)
        return tools.align_parts(source_shape, target_shape, connection_info)
    except Exception as e:
        import logging
        logging.error(f"Basit hizalama hatası: {e}")
        return None

# Modül seviyesinde yardımcı fonksiyonlar
def get_assembly_statistics(engines_list):
    """Birden fazla assembly engine'in istatistiklerini topla"""
    total_stats = {
        "total_assemblies": 0,
        "successful_assemblies": 0,
        "total_time": 0.0,
        "engines_count": len(engines_list)
    }
    
    try:
        for engine in engines_list:
            stats = engine.get_assembly_statistics()
            total_stats["total_assemblies"] += stats.get("total_assemblies", 0)
            total_stats["successful_assemblies"] += stats.get("successful_assemblies", 0)
            total_stats["total_time"] += stats.get("average_time", 0) * stats.get("total_assemblies", 0)
        
        if total_stats["total_assemblies"] > 0:
            total_stats["success_rate"] = (total_stats["successful_assemblies"] / total_stats["total_assemblies"]) * 100
            total_stats["average_time"] = total_stats["total_time"] / total_stats["total_assemblies"]
        else:
            total_stats["success_rate"] = 0
            total_stats["average_time"] = 0
            
    except Exception as e:
        import logging
        logging.error(f"Toplu istatistik hesaplama hatası: {e}")
    
    return total_stats

def validate_assembly_configuration(config):
    """Montaj konfigürasyonunu doğrula"""
    validation_result = {
        "valid": True,
        "warnings": [],
        "errors": []
    }
    
    try:
        if not config:
            validation_result["warnings"].append("Konfigürasyon mevcut değil, varsayılan değerler kullanılacak")
            return validation_result
        
        # Tolerance kontrolleri
        tolerance = config.get("assembly.tolerance", 0.01)
        if tolerance <= 0:
            validation_result["errors"].append("Tolerance değeri pozitif olmalı")
            validation_result["valid"] = False
        elif tolerance > 10:
            validation_result["warnings"].append("Tolerance değeri çok büyük (>10mm)")
        
        # Max iterations kontrolü
        max_iter = config.get("assembly.max_search_iterations", 100)
        if max_iter <= 0:
            validation_result["errors"].append("Max iterations pozitif olmalı")
            validation_result["valid"] = False
        elif max_iter > 1000:
            validation_result["warnings"].append("Max iterations çok büyük (>1000) - performans sorunları olabilir")
        
        # Connection tolerance kontrolü
        conn_tolerance = config.get("assembly.connection_tolerance", 0.1)
        if conn_tolerance <= 0:
            validation_result["errors"].append("Connection tolerance pozitif olmalı")
            validation_result["valid"] = False
        
        # Performance kontrolleri
        max_triangles = config.get("performance.max_triangles", 100000)
        if max_triangles > 1000000:
            validation_result["warnings"].append("Max triangles çok yüksek - bellek sorunları olabilir")
        
    except Exception as e:
        validation_result["errors"].append(f"Konfigürasyon doğrulama hatası: {str(e)}")
        validation_result["valid"] = False
    
    return validation_result

def get_supported_assembly_types():
    """Desteklenen montaj türlerini al"""
    from utils.constants import AssemblyDefaults
    return AssemblyDefaults.CONNECTION_TYPES.copy()

def get_default_assembly_parameters():
    """Varsayılan montaj parametrelerini al"""
    from utils.constants import AssemblyDefaults
    
    return {
        "geometric_tolerance": AssemblyDefaults.GEOMETRIC_TOLERANCE,
        "angular_tolerance": AssemblyDefaults.ANGULAR_TOLERANCE,
        "connection_tolerance": AssemblyDefaults.CONNECTION_TOLERANCE,
        "max_search_iterations": AssemblyDefaults.MAX_SEARCH_ITERATIONS,
        "min_connection_score": AssemblyDefaults.MIN_CONNECTION_SCORE,
        "max_collision_overlap": AssemblyDefaults.MAX_COLLISION_OVERLAP
    }

def optimize_assembly_parameters(assembly_history, target_success_rate=0.8):
    """Montaj geçmişine göre parametreleri optimize et"""
    optimization_result = {
        "optimized": False,
        "old_parameters": {},
        "new_parameters": {},
        "recommendations": []
    }
    
    try:
        if len(assembly_history) < 5:
            optimization_result["recommendations"].append("Yeterli montaj geçmişi yok (min 5)")
            return optimization_result
        
        # Son montajların başarı oranını hesapla
        recent_results = assembly_history[-10:]  # Son 10 montaj
        success_count = sum(1 for result in recent_results 
                          if result.status == AssemblyStatus.COMPLETED)
        current_success_rate = success_count / len(recent_results)
        
        if current_success_rate >= target_success_rate:
            optimization_result["recommendations"].append(f"Başarı oranı zaten yeterli: {current_success_rate:.2%}")
            return optimization_result
        
        # Başarısız montajların hata tiplerini analiz et
        failed_results = [r for r in recent_results if r.status == AssemblyStatus.FAILED]
        
        connection_failures = sum(1 for r in failed_results 
                                if "bağlantı" in r.error_message.lower())
        collision_failures = sum(1 for r in failed_results 
                               if "çakışma" in r.error_message.lower())
        
        # Parametre önerileri
        current_params = get_default_assembly_parameters()
        new_params = current_params.copy()
        
        if connection_failures > len(failed_results) * 0.5:
            # Bağlantı bulma sorunları
            new_params["connection_tolerance"] = min(1.0, current_params["connection_tolerance"] * 1.5)
            new_params["min_connection_score"] = max(0.1, current_params["min_connection_score"] * 0.8)
            optimization_result["recommendations"].append("Bağlantı toleransı artırıldı")
        
        if collision_failures > len(failed_results) * 0.3:
            # Çakışma sorunları
            new_params["geometric_tolerance"] = max(0.001, current_params["geometric_tolerance"] * 0.8)
            new_params["max_collision_overlap"] = max(0.0001, current_params["max_collision_overlap"] * 0.5)
            optimization_result["recommendations"].append("Geometrik tolerans azaltıldı")
        
        # Performans iyileştirmesi
        avg_time = sum(r.assembly_time for r in recent_results) / len(recent_results)
        if avg_time > 10.0:  # 10 saniyeden fazla
            new_params["max_search_iterations"] = max(50, current_params["max_search_iterations"] - 20)
            optimization_result["recommendations"].append("Max iterasyon azaltıldı (performans)")
        
        optimization_result["optimized"] = True
        optimization_result["old_parameters"] = current_params
        optimization_result["new_parameters"] = new_params
        
    except Exception as e:
        import logging
        logging.error(f"Parametre optimizasyonu hatası: {e}")
        optimization_result["recommendations"].append(f"Optimizasyon hatası: {str(e)}")
    
    return optimization_result

# Modül başlatma kontrolü
def check_assembly_dependencies():
    """Montaj için gerekli bağımlılıkları kontrol et"""
    try:
        from OCC.Core import TopoDS_Shape, gp_Trsf, BRepAlgoAPI_Common
        return True, "Montaj bağımlılıkları mevcut"
    except ImportError as e:
        return False, f"Montaj bağımlılıkları eksik: {e}"

def initialize_assembly_module():
    """Montaj modülünü başlat"""
    available, message = check_assembly_dependencies()
    if not available:
        raise ImportError(f"Montaj modülü başlatılamadı: {message}")
    
    import logging
    logging.info("Montaj modülü başarıyla başlatıldı")
    return True