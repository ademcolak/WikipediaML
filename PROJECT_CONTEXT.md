# Wikipedia Oyunu - Proje Bağlamı

## 🎯 Proje Amacı
Wikipedia oyununu otomatik oynayan bir AI sistemi geliştirmek. Wikipedia oyunu: Bir başlangıç sayfasından sadece linklere tıklayarak hedef sayfaya ulaşmaya çalışmak.

## 🎓 Öğrenme Yaklaşımı
- **Adım adım ilerleme**: Her aşamayı detaylıca anlayarak ilerlemek
- **Görselleştirme**: Tüm adımları, hangi sayfaya gidildiğini, neden gidildiğini görmek
- **Açıklayıcı**: Her değişiklik ve eklemenin nedenini anlamak

## 🗺️ Genel Yol Haritası

### Faz 1: Basic Pathfinding (Model yok - Sadece algoritma)
Basit graph search algoritmalarıyla (BFS, DFS) Wikipedia oyununu çözebilir hale getirmek.

### Faz 2: Embedded Model ile Akıllı Seçim
Sentence transformers gibi embedded modeller kullanarak linkleri semantic similarity'e göre seçmek.

### Faz 3: Claude API Entegrasyonu
Claude API ile link seçimi ve reasoning yapabilmek.

### Faz 4: Knowledge Graph
Öğrenilen path'leri ve ilişkileri bir knowledge graph'ta saklamak ve bunu kullanarak daha akıllı kararlar vermek.

## 📋 İlkeler
- Her adımda çalışır durumda bir kod olmalı
- Test edilebilir olmalı
- Verbose output (hangi kararlar alındığını görmeli)
- Performance tracking (kaç adımda buldu, kaç sayfa taradı vs.)

## 🔧 Mevcut Durum
- ✅ WikipediaScraper: Sayfalardan HTML çekme ve link bulma
- ✅ WikiNavigator: Rastgele gezinti (random walk)
- ⏳ Hedef odaklı navigasyon (henüz yok)
- ⏳ ML/AI entegrasyonu (henüz yok)
