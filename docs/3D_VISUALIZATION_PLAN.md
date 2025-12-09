# 🎨 3D Visualization Plan - Wikipedia PathFinder

## 🎯 Amaç

Wikipedia path finding sürecini 3D interaktif görselleştirme ile göstermek:
- Graph yapısını 3D uzayda göster
- Path exploration'ı animasyonlu göster
- Semantic similarity'yi renk/mesafe ile göster
- Real-time navigation izleme

---

## 🛠️ Teknoloji Stack Önerileri

### 1. 🌟 **Plotly + Dash** (En Kolay, Web-based)

**Avantajlar:**
- ✅ Python-native (kolay entegrasyon)
- ✅ Interaktif 3D scatter plots
- ✅ Web browser'da çalışır
- ✅ Real-time updates
- ✅ Kolay deployment

**Kullanım:**
```python
import plotly.graph_objects as go
import dash

# 3D scatter plot
fig = go.Figure(data=[go.Scatter3d(
    x=x_coords,
    y=y_coords,
    z=z_coords,
    mode='markers+lines',
    marker=dict(
        size=node_sizes,
        color=similarity_scores,
        colorscale='Viridis',
        showscale=True
    )
)])

# Dash app
app = dash.Dash(__name__)
app.layout = html.Div([
    dcc.Graph(figure=fig)
])
```

**Örnek Görselleştirme:**
- X-axis: Semantic dimension 1
- Y-axis: Semantic dimension 2
- Z-axis: Depth/time
- Renk: Similarity score
- Boyut: Node importance (link count)

---

### 2. 🎮 **Three.js + React** (En Güçlü, Web-based)

**Avantajlar:**
- ✅ Çok güçlü 3D rendering
- ✅ Smooth animations
- ✅ Custom shaders
- ✅ VR/AR support

**Dezavantajlar:**
- ❌ JavaScript gerekli
- ❌ Daha karmaşık setup

**Kullanım:**
```javascript
// Three.js ile 3D graph
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

// Nodes
nodes.forEach(node => {
    const geometry = new THREE.SphereGeometry(node.size, 32, 32);
    const material = new THREE.MeshBasicMaterial({ color: node.color });
    const sphere = new THREE.Mesh(geometry, material);
    scene.add(sphere);
});

// Edges
edges.forEach(edge => {
    const geometry = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(edge.from.x, edge.from.y, edge.from.z),
        new THREE.Vector3(edge.to.x, edge.to.y, edge.to.z)
    ]);
    const material = new THREE.LineBasicMaterial({ color: 0xffffff });
    const line = new THREE.Line(geometry, material);
    scene.add(line);
});
```

---

### 3. 🔬 **NetworkX + Matplotlib (3D)** (Python-only, Basit)

**Avantajlar:**
- ✅ Tamamen Python
- ✅ NetworkX entegrasyonu kolay
- ✅ Hızlı prototipleme

**Dezavantajlar:**
- ❌ Daha az interaktif
- ❌ Performans sınırlı

**Kullanım:**
```python
import networkx as nx
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 3D layout
pos = nx.spring_layout(G, dim=3)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Nodes
for node, (x, y, z) in pos.items():
    ax.scatter(x, y, z, s=node_size, c=node_color)

# Edges
for edge in G.edges():
    x = [pos[edge[0]][0], pos[edge[1]][0]]
    y = [pos[edge[0]][1], pos[edge[1]][1]]
    z = [pos[edge[0]][2], pos[edge[1]][2]]
    ax.plot(x, y, z, 'gray', alpha=0.5)
```

---

### 4. 🚀 **PyVis + NetworkX** (Interaktif, Kolay)

**Avantajlar:**
- ✅ Çok kolay kullanım
- ✅ Interaktif HTML output
- ✅ NetworkX entegrasyonu

**Dezavantajlar:**
- ❌ 2D (ama çok güzel!)
- ❌ 3D yok

**Kullanım:**
```python
from pyvis.network import Network

net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white')
net.from_nx(G)
net.show('graph.html')
```

---

## 🎨 Önerilen Yaklaşım: **Plotly + Dash**

### Neden?
1. ✅ Python-native (mevcut kod ile kolay entegrasyon)
2. ✅ 3D interaktif
3. ✅ Real-time updates
4. ✅ Web-based (herkes erişebilir)
5. ✅ Kolay deployment

### Implementasyon Planı

#### Faz 1: Temel 3D Graph Visualization

```python
# src/visualizer.py
import plotly.graph_objects as go
import numpy as np
from sklearn.decomposition import PCA

class WikiVisualizer:
    def __init__(self, knowledge_graph, embedder):
        self.graph = knowledge_graph
        self.embedder = embedder
    
    def visualize_3d(self, path=None):
        """
        Knowledge graph'ı 3D olarak görselleştir.
        
        Boyutlar:
        - X, Y, Z: PCA ile 384-dim embedding → 3-dim
        - Renk: Semantic similarity to target
        - Boyut: Node importance (degree)
        """
        # Node embeddings al
        nodes = list(self.graph.graph.nodes())
        embeddings = [self.embedder.get_embedding(node) for node in nodes]
        
        # PCA ile 3D'ye indir
        pca = PCA(n_components=3)
        coords_3d = pca.fit_transform(embeddings)
        
        # Node sizes (degree)
        sizes = [self.graph.graph.degree(node) * 5 for node in nodes]
        
        # Colors (similarity to target if path given)
        if path:
            target_emb = self.embedder.get_embedding(path[-1])
            colors = [
                self.embedder.cosine_similarity(emb, target_emb)
                for emb in embeddings
            ]
        else:
            colors = [0.5] * len(nodes)
        
        # Create 3D scatter
        fig = go.Figure(data=[go.Scatter3d(
            x=coords_3d[:, 0],
            y=coords_3d[:, 1],
            z=coords_3d[:, 2],
            mode='markers+text',
            text=nodes,
            textposition='top center',
            marker=dict(
                size=sizes,
                color=colors,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Similarity"),
                line=dict(color='white', width=0.5)
            )
        )])
        
        # Add edges
        edge_traces = []
        for edge in self.graph.graph.edges():
            x0, y0, z0 = coords_3d[nodes.index(edge[0])]
            x1, y1, z1 = coords_3d[nodes.index(edge[1])]
            
            edge_trace = go.Scatter3d(
                x=[x0, x1, None],
                y=[y0, y1, None],
                z=[z0, z1, None],
                mode='lines',
                line=dict(color='gray', width=1),
                hoverinfo='none'
            )
            edge_traces.append(edge_trace)
        
        fig.add_traces(edge_traces)
        
        # Layout
        fig.update_layout(
            title='Wikipedia Knowledge Graph - 3D Visualization',
            scene=dict(
                xaxis_title='PC1',
                yaxis_title='PC2',
                zaxis_title='PC3',
                bgcolor='rgb(20, 20, 20)'
            ),
            showlegend=False,
            hovermode='closest'
        )
        
        return fig
```

#### Faz 2: Real-time Path Animation

```python
def animate_path_finding(self, start, target):
    """
    Path finding sürecini animasyonlu göster.
    
    Her adımda:
    - Mevcut node highlight
    - Explored nodes fade in
    - Path trail göster
    """
    frames = []
    
    # Her depth için frame oluştur
    for depth, explored_nodes in self.search_history:
        # Frame data
        frame_data = self._create_frame(explored_nodes, depth)
        frames.append(go.Frame(data=frame_data, name=str(depth)))
    
    # Animation
    fig = go.Figure(
        data=frames[0].data,
        frames=frames,
        layout=go.Layout(
            updatemenus=[dict(
                type='buttons',
                buttons=[
                    dict(label='Play', method='animate', args=[None]),
                    dict(label='Pause', method='animate', args=[[None]])
                ]
            )]
        )
    )
    
    return fig
```

#### Faz 3: Dash Web App

```python
# app.py
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🌐 Wikipedia PathFinder - 3D Visualization"),
            html.Hr(),
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Label("Start Page:"),
            dcc.Input(id='start-input', value='Potato', type='text'),
            html.Label("Target Page:"),
            dcc.Input(id='target-input', value='Pizza', type='text'),
            html.Button('Find Path', id='find-button', n_clicks=0),
        ], width=3),
        
        dbc.Col([
            dcc.Graph(id='3d-graph', style={'height': '80vh'})
        ], width=9)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div(id='stats-output')
        ])
    ])
])

@app.callback(
    [Output('3d-graph', 'figure'),
     Output('stats-output', 'children')],
    [Input('find-button', 'n_clicks')],
    [Input('start-input', 'value'),
     Input('target-input', 'value')]
)
def update_graph(n_clicks, start, target):
    if n_clicks > 0:
        # Path finding
        result = navigator.hybrid_search(start, target)
        
        # Visualization
        fig = visualizer.visualize_3d(result.path)
        
        # Stats
        stats = html.Div([
            html.H4("📊 Results"),
            html.P(f"Path: {' → '.join(result.path)}"),
            html.P(f"Steps: {result.steps}"),
            html.P(f"Time: {result.time_seconds:.2f}s")
        ])
        
        return fig, stats
    
    return go.Figure(), ""

if __name__ == '__main__':
    app.run_server(debug=True)
```

---

## 📊 Görselleştirme Özellikleri

### 1. Node Özellikleri
- **Boyut**: Degree (kaç link var)
- **Renk**: Semantic similarity to target
- **Şekil**: 
  - Sphere: Normal page
  - Cube: Hub page
  - Star: Start/Target

### 2. Edge Özellikleri
- **Kalınlık**: Traversal count (kaç kere kullanıldı)
- **Renk**: 
  - Green: Successful path
  - Gray: Explored but not used
  - Red: Dead end

### 3. Animation
- **Fade in**: Yeni explore edilen nodes
- **Pulse**: Current node
- **Trail**: Path history
- **Speed control**: Slider ile hız ayarı

---

## 🚀 Dependencies

```txt
# Visualization
plotly>=5.18.0
dash>=2.14.0
dash-bootstrap-components>=1.5.0

# Dimensionality reduction
scikit-learn>=1.3.0

# Optional: Advanced viz
kaleido>=0.2.1  # Static image export
```

---

## 📈 Örnek Kullanım

```bash
# Web app başlat
python app.py

# Browser'da aç
http://localhost:8050

# Path bul ve 3D'de gör
Start: Potato
Target: Pizza
[Find Path] → 3D animation başlar
```

---

## 🎯 Gelecek İyileştirmeler

1. **VR Support**: WebXR ile VR headset desteği
2. **Clustering**: Benzer sayfaları grupla (K-means)
3. **Time-series**: Path finding sürecini zaman içinde göster
4. **Comparison**: Farklı algoritmaları yan yana göster
5. **Export**: Video/GIF export

---

## 💡 Alternatif: TensorBoard Projector

TensorFlow kullanıyorsan, TensorBoard Projector da harika:

```python
from tensorboard.plugins import projector
import tensorflow as tf

# Embeddings
embeddings = tf.Variable(embedding_matrix)

# Metadata
with open('metadata.tsv', 'w') as f:
    for page in pages:
        f.write(f"{page}\n")

# TensorBoard
writer = tf.summary.create_file_writer('logs')
with writer.as_default():
    tf.summary.text('embeddings', embeddings, step=0)

# Projector config
config = projector.ProjectorConfig()
embedding = config.embeddings.add()
embedding.tensor_name = "embeddings/.ATTRIBUTES/VARIABLE_VALUE"
embedding.metadata_path = 'metadata.tsv'
projector.visualize_embeddings('logs', config)
```

Sonra:
```bash
tensorboard --logdir=logs
```

---

**Önerim:** Plotly + Dash ile başla, sonra ihtiyaca göre Three.js'e geç!