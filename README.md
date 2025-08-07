# CAD Montaj Uygulaması

STEP dosyalarının otomatik montajı için geliştirilmiş CAD uygulaması.

## Genel Bakış

Bu uygulama, STEP formatındaki CAD dosyalarını içe aktararak, 3D görüntüleme ve otomatik montaj işlemleri yapmanızı sağlar. PythonOCC Core ve PyQt5 teknolojileri kullanılarak geliştirilmiştir.

## Özellikler

- **Dosya Formatları**: STEP (.step, .stp) ve IGES (.iges, .igs) dosya desteği
- **3D Görüntüleme**: Gelişmiş 3D viewer ile interaktif görüntüleme
- **Otomatik Montaj**: Akıllı bağlantı noktası tespiti ve otomatik hizalama
- **Çakışma Kontrolü**: Parçalar arası çakışma tespiti ve analizi
- **Geometri Analizi**: Detaylı geometrik özellik analizi
- **Özelleştirilebilir Ayarlar**: Tolerans, görünüm ve performans ayarları

## Sistem Gereksinimleri

### Minimum Gereksinimler
- **İşletim Sistemi**: Windows 10/11, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.8 - 3.11
- **RAM**: 4 GB (8 GB önerilir)
- **Depolama**: 2 GB boş alan
- **Grafik**: OpenGL 3.3 destekli grafik kartı

### Önerilen Gereksinimler
- **RAM**: 16 GB+
- **İşlemci**: Çok çekirdekli işlemci (4+ çekirdek)
- **Grafik**: Dedicated GPU (NVIDIA/AMD)

## Kurulum

### 1. Python Kurulumu

Python 3.8-3.11 arası bir sürümü yükleyin:
- [Python İndir](https://www.python.org/downloads/)

### 2. Sanal Ortam Oluşturma (Önerilen)

```bash
# Sanal ortam oluştur
python -m venv cad_montaj_env

# Windows'ta aktifleştir
cad_montaj_env\Scripts\activate

# macOS/Linux'ta aktifleştir
source cad_montaj_env/bin/activate
```

### 3. Gerekli Paketlerin Kurulumu

#### Ana Bağımlılıklar

```bash
# PythonOCC Core kurulumu
pip install pythonqt

# PyQt5 kurulumu
pip install PyQt5==5.15.10

# Diğer gerekli paketler
pip install numpy>=1.21.0
pip install matplotlib>=3.5.0
```

#### PythonOCC Core Kurulumu

**Windows:**
```bash
# Conda kullanarak (önerilen)
conda install -c conda-forge pythonocc-core

# Veya pip ile
pip install pythonocc-core==7.9.0
```

**macOS:**
```bash
# Homebrew ile OpenCASCADE yükle
brew install opencascade

# PythonOCC Core yükle
conda install -c conda-forge pythonocc-core
```

**Ubuntu/Debian:**
```bash
# Sistem bağımlılıklarını yükle
sudo apt-get update
sudo apt-get install build-essential cmake
sudo apt-get install libgl1-mesa-dev libglu1-mesa-dev
sudo apt-get install libxmu-dev libxi-dev

# PythonOCC Core yükle
conda install -c conda-forge pythonocc-core
```

### 4. Uygulama Dosyalarını İndirme

```bash
# Repository'yi klonla
git clone https://github.com/username/cad-montaj-uygulamasi.git
cd cad-montaj-uygulamasi
```

### 5. Bağımlılık Kontrolü

Kurulumunuzu test etmek için:

```bash
python -c "
import PyQt5
import OCC
print('✓ PyQt5 versiyon:', PyQt5.Qt.PYQT_VERSION_STR)
print('✓ PythonOCC kurulu')
print('Kurulum başarılı!')
"
```

## Çalıştırma

### Temel Çalıştırma

```bash
# Uygulama dizinine git
cd cad-montaj-uygulamasi

# Ana uygulamayı başlat
python main.py
```

### Komut Satırı Seçenekleri

```bash
# Debug modunda çalıştır
python main.py --debug

# Belirli konfigürasyon dosyası ile
python main.py --config my_config.json

# Log seviyesini ayarla
python main.py --log-level DEBUG
```

## İlk Kullanım

1. **Uygulama Başlatma**: `python main.py` komutu ile uygulamayı başlatın
2. **Dosya Yükleme**: `Ctrl+O` ile STEP/IGES dosyanızı açın
3. **Görüntüleme**: Mouse ile döndürme, yakınlaştırma işlemleri yapın
4. **Montaj**: İki parça yükleyip "Montaj" butonunu kullanın

## Sorun Giderme

### Yaygın Sorunlar ve Çözümleri

**1. PythonOCC Import Hatası**
```bash
ImportError: No module named 'OCC'
```
Çözüm:
```bash
# Conda ile tekrar yükle
conda install -c conda-forge pythonocc-core

# Veya farklı kanal dene
conda install -c dlr-sc pythonocc-core
```

**2. PyQt5 Display Hatası**
```bash
# Linux'ta eksik paketler
sudo apt-get install python3-pyqt5.qtopengl
sudo apt-get install python3-opengl
```

**3. OpenGL Hatası**
```bash
# Windows'ta
pip install PyOpenGL PyOpenGL_accelerate

# macOS'ta
brew install mesa
```

**4. Performans Sorunları**
- Ayarlar → Performans bölümünden triangle sayısını azaltın
- Mesh cache'i etkinleştirin
- Antialiasing'i kapatın

### Log Dosyaları

Log dosyaları şu konumda saklanır:
- **Windows**: `%USERPROFILE%\.cad_montaj\logs\`
- **macOS/Linux**: `~/.cad_montaj/logs/`

### Konfigürasyon

Ayar dosyası konumu:
- **Windows**: `%USERPROFILE%\.cad_montaj\config.json`
- **macOS/Linux**: `~/.cad_montaj/config.json`

## Kullanım Kılavuzu

### Temel İşlemler

#### Dosya Yükleme
```
1. Menü → Dosya → Aç (Ctrl+O)
2. STEP veya IGES dosyasını seçin
3. Dosya otomatik analiz edilir ve görüntülenir
```

#### 3D Görüntüleme Kontrolleri
- **Döndürme**: Sol tık + sürükle
- **Kaydırma**: Orta tık + sürükle
- **Yakınlaştırma**: Mouse wheel
- **Fit All**: F tuşu

#### Montaj İşlemi
```
1. İki veya daha fazla parça yükleyin
2. Montaj panelinden ana parça ve eklenecek parçayı seçin
3. Tolerans değerini ayarlayın
4. "Montaj Yap" butonuna tıklayın
```

### Gelişmiş Özellikler

#### Özel Ayarlar
- **Görünüm**: Tema, renk, şeffaflık ayarları
- **Montaj**: Tolerans, çakışma kontrolü ayarları
- **Performans**: Memory limit, mesh kalitesi ayarları

#### Kısayol Tuşları
- `Ctrl+O`: Dosya aç
- `Ctrl+S`: Kaydet
- `F`: Fit all
- `Ctrl+A`: Montaj yap
- `Ctrl+C`: Çakışma kontrolü
- `F1`: Yardım

## Geliştirici Bilgileri

### Proje Yapısı
```
cad-montaj-uygulamasi/
├── main.py                 # Ana başlatıcı
├── gui/                    # GUI bileşenleri
│   ├── main_window.py      # Ana pencere
│   ├── toolbar.py          # Toolbar'lar
│   ├── dialogs.py          # Dialog pencereleri
│   └── widgets.py          # Özel widget'lar
├── engine_3d/              # 3D motor
│   ├── viewer.py           # 3D görüntüleyici
│   ├── geometry_handler.py # Geometri işleyici
│   └── transformations.py  # Dönüşümler
├── montaj/                 # Montaj sistemi
│   ├── assembly_engine.py  # Ana montaj motoru
│   ├── collision_detector.py # Çakışma kontrolü
│   └── connection_finder.py # Bağlantı bulucu
├── import_manager/         # Dosya içe aktarma
└── utils/                  # Yardımcı araçlar
```

### API Kullanımı

```python
from import_manager import import_cad_file
from montaj import create_assembly_engine
from engine_3d import create_viewer

# Dosya yükleme
shape, metadata, analysis = import_cad_file("example.step")

# Montaj motoru
engine = create_assembly_engine()
result = engine.perform_assembly(shape1, shape2)

# 3D viewer (PyQt5 widget olarak)
viewer = create_viewer(parent_widget, config)
viewer.add_shape(shape)
```

## Katkıda Bulunma

1. Repository'yi fork edin
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Branch'inizi push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request oluşturun

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasını inceleyiniz.

## Destek ve İletişim

- **Issues**: GitHub Issues sayfasını kullanın
- **E-posta**: support@cad-montaj.com
- **Dokümantasyon**: [Wiki sayfası](https://github.com/username/cad-montaj-uygulamasi/wiki)

## Sürüm Geçmişi

### v1.0.0 (Şu anki sürüm)
- ✅ STEP/IGES dosya desteği
- ✅ 3D görüntüleme
- ✅ Otomatik montaj
- ✅ Çakışma kontrolü
- ✅ Geometri analizi
- ✅ Özelleştirilebilir ayarlar

### Gelecek Sürümler
- 🔄 STL export desteği
- 🔄 Gelişmiş material sistemi
- 🔄 Batch montaj işlemleri
- 🔄 Plugin sistemi

---

**Son Güncelleme**: 2024-12-19  
**Versiyon**: 1.0.0  
**Python**: 3.8-3.11  
**PythonOCC**: 7.9.0+  
**PyQt5**: 5.15.x