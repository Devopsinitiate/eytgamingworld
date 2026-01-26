"""
Documentation Consolidation System

A comprehensive system for organizing, consolidating, and structuring
scattered markdown documentation files into a well-organized hierarchy
following Django project best practices.
"""

__version__ = "1.0.0"
__author__ = "Documentation Consolidation System"

try:
    # Try relative imports first (when used as a package)
    from .models import FileAnalysis, ConsolidationGroup, DocumentationStructure
    from .analyzer import ContentAnalyzer
    from .engine import ConsolidationEngine
    from .generator import StructureGenerator
except ImportError:
    # Fall back to direct imports (when used as standalone modules)
    from models import FileAnalysis, ConsolidationGroup, DocumentationStructure
    from analyzer import ContentAnalyzer
    from engine import ConsolidationEngine
    from generator import StructureGenerator

__all__ = [
    'FileAnalysis',
    'ConsolidationGroup', 
    'DocumentationStructure',
    'ContentAnalyzer',
    'ConsolidationEngine',
    'StructureGenerator'
]