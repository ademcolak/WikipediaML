"""
WikipediaML Core - Basit, temiz, etkili.
Pure KG + Smart BFS Strategy
"""

from .wikipedia import Wikipedia
from .knowledge import KnowledgeSystem
from .navigator import Navigator, PathResult

__all__ = ['Wikipedia', 'KnowledgeSystem', 'Navigator', 'PathResult']