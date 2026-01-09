--------------------------------------------------------------------------------
☁️ AWS EC2 ile WikipediaML Geliştirme ve Eğitim Planı
Bu belge, yerel bilgisayarın veya Kaggle gibi kısıtlı ortamların yetmediği durumlarda, AWS EC2 (Elastic Compute Cloud) kullanarak Wikipedia Bilgi Grafiği'ni (KG) oluşturma ve Neural Scorer (MLP) modelini eğitme sürecini adım adım açıklamaktadır.
📖 Genel Strateji: "Bulut Gücüyle Haritalama"
Sistemin Play modunda başarısız olmasının temel nedeni olan "hedef vizyonu eksikliğini" gidermek için, tüm Wikipedia bağlantı yapısını bir Bilgi Grafiği olarak yerel bir dosyaya (.pkl) dönüştürmemiz gerekir. AWS EC2, bu devasa veriyi (6M+ makale) işlemek için gerekli RAM ve CPU gücünü sağlayacak "ağır iş makinesi" görevini görecektir.

--------------------------------------------------------------------------------
🛠️ ADIM 1: AWS EC2 Makinesini Hazırlama
Kaggle'ın aksine, EC2 size tam kontrol sağlar ve işlemler arka planda haftalarca sürebilir.
1. Örnek (Instance) Seçimi: En az 16 GB (tercihen 32 GB+) RAM'e sahip bir t3.large veya m5.xlarge makine seçilmelidir.
2. İşletim Sistemi: Amazon Linux 2 veya Ubuntu 22.04 LTS önerilir.
3. Güvenlik: SSH (Port 22) erişimine izin verilmeli; tarayıcı üzerinden kontrol isteniyorsa Jupyter Portu (8888) açılmalıdır.

--------------------------------------------------------------------------------
🏗️ ADIM 2: Yazılım ve Proje Kurulumu
Makineye bağlandıktan sonra (SSH üzerinden), aşağıdaki komutlarla geliştirme ortamı hazırlanır:
# Sistem güncellemeleri ve gerekli araçların kurulumu
sudo yum update -y
sudo yum install python3 python3-devel git gcc -y

# Projenin klonlanması
git clone https://github.com/ademcolak/WikipediaML.git
cd WikipediaML

# Bağımlılıkların yüklenmesi (igraph, sentence-transformers vb.)
pip3 install -r requirements.txt

--------------------------------------------------------------------------------
🗺️ ADIM 3: Bilgi Grafiği (Map) Oluşturma
Bu aşama projenin "beynini" oluşturur. Wikipedia'nın statik verilerini işlemeliyiz.
1. Dökümleri İndir: Wikipedia SQL dökümlerinden pagelinks ve page tabloları sunucuya çekilir.
2. Temizleme: Sadece ana makaleler (Namespace 0) tutulur, "Redlink"ler ve meta sayfalar ayıklanır.
3. Binary Format: Hızlı erişim için veriler Compressed Sparse Row (CSR) veya igraph formatında data/knowledge_graph.pkl olarak kaydedilir.

--------------------------------------------------------------------------------
🧠 ADIM 4: Sentetik Veri Üretimi ve MLP Eğitimi
Ajanın iki kavram arasındaki gerçek mesafeyi öğrenmesi için bu adım kritiktir.
1. BFS Simülasyonu: Bilgi grafiği üzerinde 1.000.000 rastgele sayfa çifti seçilir ve aralarındaki gerçek en kısa yol mesafesi (tıklama sayısı) hesaplanır.
2. Model Eğitimi: Oluşturulan bu verilerle, bir MLP Scorer eğitilir. Model, embedding'leri alıp hedefe olan mesafeyi tahmin etmeyi öğrenir.
3. Kalıcılık (Persistence): Eğitim sırasında data/training_state.pkl dosyası otomatik olarak güncellenir. Eğer bağlantınız koparsa veya makineyi kapatıp açarsanız, kod en son kaldığı iterasyondan devam eder.

--------------------------------------------------------------------------------
🔄 ADIM 5: Senkronizasyon ve Veri Birleştirme (Merge)
AWS üzerinde üretilen verileri yerel bilgisayarına veya Kaggle'a aktarabilirsin.
• Veri Aktarımı: AWS'deki data/ klasörünü yerel data/ klasörünle değiştir.
• Otomatik Birleştirme: Projenin mevcut mimarisi, data/ içindeki .pkl dosyalarını otomatik olarak yükler. Farklı zamanlarda aldığın eğitim çıktılarını aynı klasöre koyup kodu çalıştırdığında, sistem kümülatif olarak veri havuzunu büyütmeye devam edecektir.

--------------------------------------------------------------------------------
🎮 ADIM 6: Play (Inference) Stratejisi
Eğitilen bu devasa haritayı oyun sırasında şu şekilde kullanacaksın:
1. Hibrit Navigasyon: A* algoritması, eğitilen MLP modelini bir "pusula" olarak kullanır.
2. Hub Önceliği: Hedef uzakken yüksek bağlantılı (PageRank yüksek) sayfalara öncelik verilir.
3. Hata Yönetimi: Bot bir çıkmaz sokağa girerse, "Ziyaret Edilenler" listesini kullanarak geri döner ve diğer dalları dener.

--------------------------------------------------------------------------------