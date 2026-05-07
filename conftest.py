"""
Pytest configuration for 9R-2.0 worktree.

Prevents pytest from collecting the parent project's modules
when running tests from the worktree.
"""

import os
import sys

# Ensure worktree root is first in sys.path
_worktree_root = os.path.dirname(os.path.abspath(__file__))
if _worktree_root not in sys.path:
    sys.path.insert(0, _worktree_root)

# Remove parent project from sys.path to avoid import conflicts
_parent_root = os.path.dirname(_worktree_root)  # /AstrBot/data/workspaces/9R-2.0
if _parent_root in sys.path:
    sys.path.remove(_parent_root)

# Also remove any parent that might be at index 0
for p in list(sys.path):
    if p == _parent_root or p == os.path.dirname(_parent_root):
        sys.path.remove(p)
