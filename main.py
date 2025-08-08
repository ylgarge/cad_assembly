"""
CAD Montaj Uygulaması - Ana Başlatıcı
PythonOCC Core 7.9.0 ve PyQt5 kullanarak STEP dosyalarının montajı
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from OCC.Display import backend
backend.load_backend('pyqt5')
# Proje modüllerini import et
try:
    from gui.main_window import MainWindow
    from utils.config import Config
    from utils.logger import setup_logger
except ImportError as e:
    print(f"Modül import hatası: {e}")
    print("Lütfen tüm gerekli paketlerin yüklü olduğundan emin olun:")
    print("- pip install PythonOCC")
    print("- pip install PyQt5")
    sys.exit(1)

class CADAssemblyApplication:
    def __init__(self):
        self.app = None
        self.main_window = None
        self.config = None
        self.logger = None
    
    def initialize(self):
        """Uygulamayı başlat"""
        try:
            # PyQt5 uygulamasını oluştur
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("CAD Montaj Uygulaması")
            self.app.setApplicationVersion("1.0.0")
            
            # High DPI desteği
            self.app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            self.app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
            
            # Logger kurulumu
            self.logger = setup_logger()
            self.logger.info("CAD Montaj Uygulaması başlatılıyor...")
            
            # Konfigürasyon yükleme
            self.config = Config()
            self.logger.info("Konfigürasyon yüklendi")
            
            # Ana pencereyi oluştur
            self.main_window = MainWindow(self.config, self.logger)
            self.logger.info("Ana pencere oluşturuldu")
            
            return True
            
        except Exception as e:
            error_msg = f"Uygulama başlatma hatası: {str(e)}"
            print(error_msg)
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(error_msg)
            return False
    
    def run(self):
        """Uygulamayı çalıştır"""
        if not self.initialize():
            return 1
        
        try:
            # Ana pencereyi göster
            self.main_window.show()
            self.logger.info("Ana pencere gösteriliyor")
            
            # Uygulama döngüsünü başlat
            return self.app.exec_()
            
        except Exception as e:
            error_msg = f"Uygulama çalıştırma hatası: {str(e)}"
            self.logger.error(error_msg)
            QMessageBox.critical(None, "Hata", error_msg)
            return 1
    
    def cleanup(self):
        """Temizlik işlemleri"""
        if self.logger:
            self.logger.info("Uygulama kapatılıyor...")
        
        if self.main_window:
            self.main_window.cleanup()

def main():
    """Ana fonksiyon"""
    # Çalışma dizinini ayarla
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller ile paketlenmiş uygulama
        os.chdir(sys._MEIPASS)
    else:
        # Development ortamı
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
    
    # Uygulamayı oluştur ve çalıştır
    cad_app = CADAssemblyApplication()
    
    try:
        exit_code = cad_app.run()
    except KeyboardInterrupt:
        print("\nUygulama kullanıcı tarafından sonlandırıldı")
        exit_code = 0
    except Exception as e:
        print(f"Beklenmeyen hata: {e}")
        exit_code = 1
    finally:
        cad_app.cleanup()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()