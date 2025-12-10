"""
ml_link_scorer.py
-----------------
Machine Learning-based link scoring for Wikipedia PathFinder.

Bu modül:
- Feature extraction (semantic, category, graph, text)
- XGBoost/LightGBM model training
- Link scoring with ML
- Online learning (incremental updates)
- Model persistence

Phase 2: Machine Learning Integration
"""

import numpy as np
import pickle
import os
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import time

# ML libraries (lazy import)
try:
    import xgboost as xgb
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    xgb = None  # type: ignore
    XGBClassifier = None  # type: ignore
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not installed. Install with: pip install xgboost")

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    StandardScaler = None  # type: ignore
    train_test_split = None  # type: ignore
    SKLEARN_AVAILABLE = False
    print("⚠️  scikit-learn not installed. Install with: pip install scikit-learn")


class MLLinkScorer:
    """
    Machine Learning-based link scorer.
    
    Features:
    - Multi-feature extraction (semantic, category, graph, text)
    - XGBoost classifier for link scoring
    - Online learning (incremental updates)
    - Feature importance analysis
    - Model persistence
    
    Usage:
        scorer = MLLinkScorer()
        
        # Train from successful paths
        scorer.train_from_paths(successful_paths)
        
        # Score links
        scores = scorer.score_links(links, target, current_page)
        
        # Update model with new data
        scorer.update_model(new_path, success=True)
    """
    
    def __init__(
        self,
        model_file: str = 'cache/ml_model.pkl',
        scaler_file: str = 'cache/ml_scaler.pkl',
        verbose: bool = False
    ):
        """
        Initialize ML Link Scorer.
        
        Args:
            model_file: Path to save/load trained model
            scaler_file: Path to save/load feature scaler
            verbose: Print debug information
        """
        self.model_file = model_file
        self.scaler_file = scaler_file
        self.verbose = verbose
        
        # Check dependencies
        if not XGBOOST_AVAILABLE or not SKLEARN_AVAILABLE:
            raise ImportError("XGBoost and scikit-learn required. Install with: pip install xgboost scikit-learn")
        
        # Model and scaler
        self.model = None
        self.scaler = None
        
        # Feature names (for consistency)
        self.feature_names = [
            'semantic_similarity',
            'category_jaccard',
            'category_hierarchical',
            'category_depth_score',
            'text_overlap',
            'text_length_ratio',
            'graph_centrality',
            'graph_edge_weight',
            'is_hub_page',
            'link_popularity'
        ]
        
        # Training data buffer (for online learning)
        self.training_buffer = []
        self.buffer_size = 100  # Update model after 100 new samples
        
        # Statistics
        self.predictions_made = 0
        self.model_updates = 0
        self.training_samples = 0
        
        # Load existing model if available
        self._load_model()
    
    def extract_features(
        self,
        link: str,
        target: str,
        current_page: str,
        embedder,
        category_analyzer,
        knowledge_graph
    ) -> np.ndarray:
        """
        Extract features for a link.
        
        Args:
            link: Candidate link
            target: Target page
            current_page: Current page
            embedder: WikiEmbedder instance
            category_analyzer: WikipediaCategoryAnalyzer instance
            knowledge_graph: WikiKnowledgeGraph instance
            
        Returns:
            Feature vector (numpy array)
        """
        features = []
        
        # 1. Semantic similarity (link → target)
        try:
            link_emb = embedder.get_embedding(link)
            target_emb = embedder.get_embedding(target)
            semantic_sim = embedder.cosine_similarity(link_emb, target_emb)
        except:
            semantic_sim = 0.0
        features.append(semantic_sim)
        
        # 2. Category Jaccard similarity
        # TEMPORARILY DISABLED - TOO SLOW (200 links × 0.5s = 100s)
        # TODO: Add caching or batch processing
        cat_jaccard = 0.0
        features.append(cat_jaccard)
        
        # 3. Category hierarchical similarity
        # TEMPORARILY DISABLED - TOO SLOW (200 links × 0.5s = 100s)
        # TODO: Add caching or batch processing
        cat_hier = 0.0
        features.append(cat_hier)
        
        # 4. Category depth score
        # TEMPORARILY DISABLED - TOO SLOW (200 links × 0.5s = 100s)
        # TODO: Add caching or batch processing
        depth_score = 0.0
        features.append(depth_score)
        
        # 5. Text overlap (normalized word overlap)
        link_words = set(link.lower().replace('_', ' ').split())
        target_words = set(target.lower().replace('_', ' ').split())
        text_overlap = len(link_words & target_words) / max(len(target_words), 1)
        features.append(text_overlap)
        
        # 6. Text length ratio
        length_ratio = min(len(link), len(target)) / max(len(link), len(target), 1)
        features.append(length_ratio)
        
        # 7. Graph centrality (if link is in graph)
        try:
            if knowledge_graph and hasattr(knowledge_graph, 'G') and knowledge_graph.G.has_node(link):
                # Simple degree centrality
                centrality = knowledge_graph.G.degree(link) / max(knowledge_graph.G.number_of_nodes(), 1)
            else:
                centrality = 0.0
        except:
            centrality = 0.0
        features.append(centrality)
        
        # 8. Graph edge weight (current → link)
        try:
            if knowledge_graph and hasattr(knowledge_graph, 'G') and knowledge_graph.G.has_edge(current_page, link):
                edge_weight = knowledge_graph.G[current_page][link].get('weight', 0.0)
            else:
                edge_weight = 0.0
        except:
            edge_weight = 0.0
        features.append(edge_weight)
        
        # 9. Is hub page (binary feature)
        hub_pages = {
            'United_States', 'United_Kingdom', 'Europe', 'Asia',
            'World_War_II', 'Computer', 'Science', 'History',
            'Geography', 'Mathematics', 'Physics', 'Chemistry',
            'Biology', 'Technology', 'Internet', 'Language'
        }
        is_hub = 1.0 if link in hub_pages else 0.0
        features.append(is_hub)
        
        # 10. Link popularity (placeholder - could be Wikipedia page views)
        # For now, use a simple heuristic based on link length
        popularity = 1.0 / (1.0 + len(link) / 20.0)  # Shorter names = more popular
        features.append(popularity)
        
        return np.array(features)
    
    def score_links(
        self,
        links: List[str],
        target: str,
        current_page: str,
        embedder,
        category_analyzer,
        knowledge_graph
    ) -> List[Tuple[str, float]]:
        """
        Score links using ML model.
        
        Args:
            links: Candidate links
            target: Target page
            current_page: Current page
            embedder: WikiEmbedder instance
            category_analyzer: WikipediaCategoryAnalyzer instance
            knowledge_graph: WikiKnowledgeGraph instance
            
        Returns:
            List of (link, score) tuples, sorted by score (descending)
        """
        if self.model is None:
            if self.verbose:
                print("⚠️  ML model not trained. Using fallback scoring.")
            return [(link, 0.5) for link in links]  # Neutral scores
        
        # Extract features for all links
        features_list = []
        for link in links:
            features = self.extract_features(
                link, target, current_page,
                embedder, category_analyzer, knowledge_graph
            )
            features_list.append(features)
        
        # Convert to numpy array
        X = np.array(features_list)
        
        # Scale features
        if self.scaler:
            X = self.scaler.transform(X)
        
        # Predict probabilities
        try:
            # Get probability of positive class (good link)
            probs = self.model.predict_proba(X)[:, 1]
            self.predictions_made += len(links)
        except Exception as e:
            if self.verbose:
                print(f"⚠️  ML prediction error: {e}")
            probs = np.array([0.5] * len(links))
        
        # Create scored list
        scored_links = list(zip(links, probs))
        scored_links.sort(key=lambda x: x[1], reverse=True)
        
        return scored_links
    
    def train_from_paths(
        self,
        paths: List[List[str]],
        embedder,
        category_analyzer,
        knowledge_graph,
        test_size: float = 0.2
    ):
        """
        Train model from successful paths.
        
        Args:
            paths: List of successful paths
            embedder: WikiEmbedder instance
            category_analyzer: WikipediaCategoryAnalyzer instance
            knowledge_graph: WikiKnowledgeGraph instance
            test_size: Fraction of data for testing
        """
        if self.verbose:
            print(f"\n🤖 Training ML model from {len(paths)} paths...")
        
        X_list = []
        y_list = []
        
        # Extract features from paths
        for path in paths:
            if len(path) < 2:
                continue
            
            target = path[-1]
            
            # For each step in path
            for i in range(len(path) - 1):
                current = path[i]
                next_page = path[i + 1]
                
                # Positive sample: next_page (correct choice)
                features = self.extract_features(
                    next_page, target, current,
                    embedder, category_analyzer, knowledge_graph
                )
                X_list.append(features)
                y_list.append(1)  # Positive label
                
                # TODO: Add negative samples (wrong choices)
                # For now, we'll train only on positive samples
        
        if len(X_list) == 0:
            if self.verbose:
                print("⚠️  No training data extracted.")
            return
        
        # Convert to numpy arrays
        X = np.array(X_list)
        y = np.array(y_list)
        
        self.training_samples = len(X)
        
        if self.verbose:
            print(f"   📊 Training samples: {len(X)}")
            print(f"   📊 Features: {X.shape[1]}")
        
        # Split train/test
        if len(X) > 10:
            if not SKLEARN_AVAILABLE:
                raise ImportError("scikit-learn required for train_test_split")
            X_train, X_test, y_train, y_test = train_test_split(  # type: ignore
                X, y, test_size=test_size, random_state=42
            )
        else:
            X_train, X_test = X, X
            y_train, y_test = y, y
        
        # Scale features
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for StandardScaler")
        self.scaler = StandardScaler()  # type: ignore
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost model
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost required for model training")
        self.model = xgb.XGBClassifier(  # type: ignore
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_acc = self.model.score(X_train_scaled, y_train)
        test_acc = self.model.score(X_test_scaled, y_test)
        
        if self.verbose:
            print(f"   ✅ Training accuracy: {train_acc:.3f}")
            print(f"   ✅ Test accuracy: {test_acc:.3f}")
        
        # Save model
        self._save_model()
    
    def update_model(
        self,
        path: List[str],
        success: bool,
        embedder,
        category_analyzer,
        knowledge_graph
    ):
        """
        Update model with new path (online learning).
        
        Args:
            path: New path
            success: Whether path was successful
            embedder: WikiEmbedder instance
            category_analyzer: WikipediaCategoryAnalyzer instance
            knowledge_graph: WikiKnowledgeGraph instance
        """
        if not success or len(path) < 2:
            return
        
        # Add to training buffer
        self.training_buffer.append(path)
        
        # Update model if buffer is full
        if len(self.training_buffer) >= self.buffer_size:
            if self.verbose:
                print(f"\n🔄 Updating ML model with {len(self.training_buffer)} new paths...")
            
            self.train_from_paths(
                self.training_buffer,
                embedder,
                category_analyzer,
                knowledge_graph
            )
            
            self.training_buffer = []
            self.model_updates += 1
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance from trained model.
        
        Returns:
            Dict mapping feature name → importance score
        """
        if self.model is None:
            return {}
        
        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance))
    
    def _save_model(self):
        """Save model and scaler to disk."""
        try:
            # Save model
            with open(self.model_file, 'wb') as f:
                pickle.dump(self.model, f)
            
            # Save scaler
            with open(self.scaler_file, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            if self.verbose:
                print(f"   💾 Model saved to {self.model_file}")
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Failed to save model: {e}")
    
    def _load_model(self):
        """Load model and scaler from disk."""
        if os.path.exists(self.model_file) and os.path.exists(self.scaler_file):
            try:
                with open(self.model_file, 'rb') as f:
                    self.model = pickle.load(f)
                
                with open(self.scaler_file, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                if self.verbose:
                    print(f"📦 ML model loaded from {self.model_file}")
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Failed to load model: {e}")
    
    def get_stats(self) -> Dict:
        """Get ML scorer statistics."""
        stats = {
            'model_trained': self.model is not None,
            'training_samples': self.training_samples,
            'predictions_made': self.predictions_made,
            'model_updates': self.model_updates,
            'buffer_size': len(self.training_buffer)
        }
        
        if self.model:
            stats['feature_importance'] = self.get_feature_importance()
        
        return stats