"""
visualizer.py
-------------
3D visualization for Wikipedia PathFinder using Plotly.

Features:
- 3D scatter plot of knowledge graph
- PCA dimensionality reduction (384-dim → 3-dim)
- Interactive node/edge visualization
- Path highlighting
- Semantic similarity coloring
"""

import plotly.graph_objects as go
import numpy as np
from sklearn.decomposition import PCA
from typing import Optional, List
import networkx as nx


class WikiVisualizer:
    """
    Wikipedia Knowledge Graph 3D Visualizer.
    
    Uses PCA to reduce embedding dimensions to 3D space,
    then creates interactive Plotly visualization.
    """
    
    def __init__(self, knowledge_graph, embedder):
        """
        Initialize visualizer.
        
        Args:
            knowledge_graph: KnowledgeGraph instance
            embedder: Embedder instance
        """
        self.graph = knowledge_graph
        self.embedder = embedder
        self.pca = PCA(n_components=3)
        self._coords_3d: Optional[np.ndarray] = None
        self._node_list: Optional[List[str]] = None
    
    def _prepare_3d_coordinates(self, nodes: List[str]) -> np.ndarray:
        """
        Convert node embeddings to 3D coordinates using PCA.
        
        Args:
            nodes: List of Wikipedia page titles
            
        Returns:
            numpy array of shape (n_nodes, 3)
        """
        # Get embeddings for all nodes
        embeddings = []
        for node in nodes:
            emb = self.embedder.get_embedding(node)
            embeddings.append(emb)
        
        embeddings = np.array(embeddings)
        
        # Apply PCA
        coords_3d = self.pca.fit_transform(embeddings)
        
        return coords_3d
    
    def visualize_graph(self, 
                       max_nodes: int = 100,
                       path: Optional[List[str]] = None,
                       target: Optional[str] = None) -> go.Figure:
        """
        Create 3D visualization of knowledge graph.
        
        Args:
            max_nodes: Maximum number of nodes to display
            path: Optional path to highlight
            target: Optional target page for similarity coloring
            
        Returns:
            Plotly Figure object
        """
        # Get nodes from graph
        all_nodes = list(self.graph.graph.nodes())
        
        # Limit nodes if too many
        if len(all_nodes) > max_nodes:
            # Prioritize nodes with high degree (hub pages)
            node_degrees = [(node, self.graph.graph.degree(node)) 
                          for node in all_nodes]
            node_degrees.sort(key=lambda x: x[1], reverse=True)
            nodes = [node for node, _ in node_degrees[:max_nodes]]
        else:
            nodes = all_nodes
        
        # Add path nodes if provided
        if path:
            for node in path:
                if node not in nodes:
                    nodes.append(node)
        
        self._node_list = nodes
        
        # Get 3D coordinates
        print(f"📊 Computing 3D coordinates for {len(nodes)} nodes...")
        self._coords_3d = self._prepare_3d_coordinates(nodes)
        
        # Calculate node properties
        sizes = []
        colors = []
        hover_texts = []
        
        for i, node in enumerate(nodes):
            # Size based on degree
            degree = self.graph.graph.degree(node)
            size = min(10 + degree * 2, 30)  # Cap at 30
            sizes.append(size)
            
            # Color based on similarity to target
            if target:
                target_emb = self.embedder.get_embedding(target)
                node_emb = self.embedder.get_embedding(node)
                similarity = self.embedder.cosine_similarity(node_emb, target_emb)
                colors.append(similarity)
            else:
                colors.append(0.5)
            
            # Hover text
            hover_text = f"<b>{node}</b><br>"
            hover_text += f"Degree: {degree}<br>"
            if target:
                hover_text += f"Similarity to {target}: {colors[i]:.3f}"
            hover_texts.append(hover_text)
        
        # Create figure
        fig = go.Figure()
        
        # Add edges
        edge_traces = self._create_edge_traces(nodes, path)
        for trace in edge_traces:
            fig.add_trace(trace)
        
        # Add nodes
        node_trace = go.Scatter3d(
            x=self._coords_3d[:, 0],
            y=self._coords_3d[:, 1],
            z=self._coords_3d[:, 2],
            mode='markers+text',
            text=[node.replace('_', ' ') for node in nodes],
            textposition='top center',
            textfont=dict(size=8, color='white'),
            marker=dict(
                size=sizes,
                color=colors,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(
                    title="Similarity" if target else "Value",
                    thickness=15,
                    len=0.7
                ),
                line=dict(color='white', width=0.5),
                opacity=0.9
            ),
            hovertext=hover_texts,
            hoverinfo='text',
            name='Pages'
        )
        fig.add_trace(node_trace)
        
        # Highlight path if provided
        if path:
            path_trace = self._create_path_trace(path)
            fig.add_trace(path_trace)
        
        # Layout
        title = "Wikipedia Knowledge Graph - 3D Visualization"
        if path:
            title += f"<br><sub>Path: {' → '.join(path)}</sub>"
        
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor='center',
                font=dict(size=16, color='white')
            ),
            scene=dict(
                xaxis=dict(
                    title='PC1',
                    backgroundcolor='rgb(20, 20, 20)',
                    gridcolor='rgb(50, 50, 50)',
                    showbackground=True
                ),
                yaxis=dict(
                    title='PC2',
                    backgroundcolor='rgb(20, 20, 20)',
                    gridcolor='rgb(50, 50, 50)',
                    showbackground=True
                ),
                zaxis=dict(
                    title='PC3',
                    backgroundcolor='rgb(20, 20, 20)',
                    gridcolor='rgb(50, 50, 50)',
                    showbackground=True
                ),
                bgcolor='rgb(10, 10, 10)'
            ),
            paper_bgcolor='rgb(10, 10, 10)',
            plot_bgcolor='rgb(10, 10, 10)',
            showlegend=False,
            hovermode='closest',
            height=800
        )
        
        return fig
    
    def _create_edge_traces(self, 
                           nodes: List[str],
                           path: Optional[List[str]] = None) -> List[go.Scatter3d]:
        """
        Create edge traces for the graph.
        
        Args:
            nodes: List of nodes to visualize
            path: Optional path to highlight
            
        Returns:
            List of Scatter3d traces for edges
        """
        edge_traces = []
        
        # Get edges from graph
        if self._coords_3d is None:
            return edge_traces
            
        for edge in self.graph.graph.edges():
            if edge[0] in nodes and edge[1] in nodes:
                idx0 = nodes.index(edge[0])
                idx1 = nodes.index(edge[1])
                
                x0, y0, z0 = self._coords_3d[idx0]
                x1, y1, z1 = self._coords_3d[idx1]
                
                # Check if edge is in path
                is_path_edge = False
                if path:
                    for i in range(len(path) - 1):
                        if (edge[0] == path[i] and edge[1] == path[i+1]) or \
                           (edge[1] == path[i] and edge[0] == path[i+1]):
                            is_path_edge = True
                            break
                
                # Different color for path edges
                color = 'rgb(255, 100, 100)' if is_path_edge else 'rgb(100, 100, 100)'
                width = 3 if is_path_edge else 1
                
                edge_trace = go.Scatter3d(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    z=[z0, z1, None],
                    mode='lines',
                    line=dict(color=color, width=width),
                    hoverinfo='none',
                    showlegend=False
                )
                edge_traces.append(edge_trace)
        
        return edge_traces
    
    def _create_path_trace(self, path: List[str]) -> go.Scatter3d:
        """
        Create highlighted trace for the path.
        
        Args:
            path: List of pages in the path
            
        Returns:
            Scatter3d trace for path nodes
        """
        if self._node_list is None or self._coords_3d is None:
            # Return empty trace if not initialized
            return go.Scatter3d(x=[], y=[], z=[], mode='markers')
            
        path_coords = []
        for node in path:
            if node in self._node_list:
                idx = self._node_list.index(node)
                path_coords.append(self._coords_3d[idx])
        
        path_coords = np.array(path_coords)
        
        path_trace = go.Scatter3d(
            x=path_coords[:, 0],
            y=path_coords[:, 1],
            z=path_coords[:, 2],
            mode='markers+lines',
            marker=dict(
                size=15,
                color='red',
                symbol='diamond',
                line=dict(color='white', width=2)
            ),
            line=dict(color='red', width=4),
            text=[f"Step {i+1}: {node}" for i, node in enumerate(path)],
            hoverinfo='text',
            name='Path',
            showlegend=True
        )
        
        return path_trace
    
    def save_html(self, fig: go.Figure, filename: str = "wiki_graph_3d.html"):
        """
        Save visualization as HTML file.
        
        Args:
            fig: Plotly figure
            filename: Output filename
        """
        fig.write_html(filename)
        print(f"✅ Visualization saved to {filename}")
        print(f"   Open it in your browser to interact!")