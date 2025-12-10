"""
fileherder - Lightweight File Management Utilities

A focused file management package providing essential operations:
- File deduplication (hash-based)
- Directory organization
- Batch file operations
- File type detection

This package extracts the core functionality from cleanupx without
AI dependencies, providing fast, reliable file management tools.

MIT License by Luke Steuber
"""

__version__ = "1.0.0"
__author__ = "Luke Steuber"
__email__ = "luke@lukesteuber.com"
__license__ = "MIT"

from .core import (
    FileHerder,
    DuplicateFinder,
    FileOrganizer,
    FileTypeDetector,
    HashResult,
    DuplicateGroup,
    OrganizationResult
)

from .operations import (
    move_files,
    copy_files,
    delete_files_safe,
    rename_files_batch
)

__all__ = [
    # Core classes
    'FileHerder',
    'DuplicateFinder',
    'FileOrganizer',
    'FileTypeDetector',
    # Data classes
    'HashResult',
    'DuplicateGroup',
    'OrganizationResult',
    # Operations
    'move_files',
    'copy_files',
    'delete_files_safe',
    'rename_files_batch',
]
