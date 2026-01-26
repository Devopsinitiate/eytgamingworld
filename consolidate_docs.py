#!/usr/bin/env python3
"""
Documentation Consolidation CLI Script

This script provides a simple command-line interface to run the
Documentation Consolidation System on the current project.
"""

import sys
from pathlib import Path

# Add the doc_consolidation package to the path
sys.path.insert(0, str(Path(__file__).parent))

from doc_consolidation.main import main

if __name__ == '__main__':
    main()