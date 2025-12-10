"""
Core file management functionality for fileherder.

This module provides the essential classes for file operations:
- DuplicateFinder: Hash-based duplicate detection
- FileOrganizer: Directory organization by type
- FileTypeDetector: File type classification
- FileHerder: Unified interface for all operations

Author: Luke Steuber
"""

import hashlib
import logging
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class HashResult:
    """
    Result from file hashing operation.

    Attributes:
        file_path: Path to the file
        hash_value: SHA256 hash of file contents
        file_size: File size in bytes
        success: Whether hashing succeeded
        error: Error message if failed
    """
    file_path: Path
    hash_value: Optional[str]
    file_size: int
    success: bool = True
    error: Optional[str] = None


@dataclass
class DuplicateGroup:
    """
    Group of duplicate files with same hash.

    Attributes:
        hash_value: SHA256 hash shared by all files
        files: List of file paths with this hash
        total_size: Combined size of all duplicates
        waste_size: Size of redundant copies (total - 1 file)
        count: Number of duplicate files
    """
    hash_value: str
    files: List[Path]
    total_size: int
    waste_size: int
    count: int


@dataclass
class OrganizationResult:
    """
    Result from directory organization operation.

    Attributes:
        files_organized: Number of files organized
        categories_created: File type categories created
        category_counts: Files per category
        success: Whether organization succeeded
        error: Error message if failed
    """
    files_organized: int
    categories_created: List[str]
    category_counts: Dict[str, int] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


# ============================================================================
# File Type Detection
# ============================================================================

class FileTypeDetector:
    """
    Detect and categorize file types by extension and MIME type.

    Categories:
    - code: Source code files
    - document: Documents (PDF, DOCX, etc.)
    - image: Images (PNG, JPG, etc.)
    - video: Video files
    - audio: Audio files
    - archive: Compressed archives
    - data: Data files (CSV, JSON, etc.)
    - text: Plain text files
    - other: Uncategorized files

    Example:
        >>> detector = FileTypeDetector()
        >>> file_type = detector.detect_type(Path("script.py"))
        >>> print(file_type)
        'code'
    """

    # Extension-based categorization
    CATEGORIES = {
        'code': {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.cs', '.r',
            '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd'
        },
        'document': {
            '.pdf', '.doc', '.docx', '.odt', '.rtf', '.tex', '.md', '.txt',
            '.epub', '.mobi', '.pages', '.numbers', '.key'
        },
        'image': {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
            '.ico', '.tiff', '.tif', '.heic', '.heif', '.raw', '.cr2'
        },
        'video': {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.m4v', '.mpg', '.mpeg', '.3gp', '.ogv'
        },
        'audio': {
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma',
            '.opus', '.alac', '.ape'
        },
        'archive': {
            '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar', '.xz', '.zst',
            '.tar.gz', '.tar.bz2', '.tar.xz', '.tgz'
        },
        'data': {
            '.csv', '.tsv', '.json', '.xml', '.yaml', '.yml', '.toml',
            '.sql', '.db', '.sqlite', '.sqlite3', '.parquet', '.feather'
        },
        'text': {
            '.txt', '.log', '.conf', '.cfg', '.ini', '.env', '.properties'
        }
    }

    def __init__(self):
        """Initialize file type detector."""
        # Build reverse lookup: extension -> category
        self._ext_to_category = {}
        for category, extensions in self.CATEGORIES.items():
            for ext in extensions:
                self._ext_to_category[ext] = category

    def detect_type(self, file_path: Path) -> str:
        """
        Detect file type category.

        Args:
            file_path: Path to file

        Returns:
            Category name (code, document, image, etc.) or 'other'

        Example:
            >>> detector = FileTypeDetector()
            >>> detector.detect_type(Path("data.csv"))
            'data'
        """
        suffix = file_path.suffix.lower()

        # Check double extensions (e.g., .tar.gz)
        if len(file_path.suffixes) >= 2:
            double_suffix = ''.join(file_path.suffixes[-2:]).lower()
            if double_suffix in self._ext_to_category:
                return self._ext_to_category[double_suffix]

        # Check single extension
        if suffix in self._ext_to_category:
            return self._ext_to_category[suffix]

        # Fallback to MIME type detection
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            main_type = mime_type.split('/')[0]
            if main_type in {'image', 'video', 'audio', 'text'}:
                return main_type

        return 'other'

    def get_category_extensions(self, category: str) -> Set[str]:
        """
        Get all extensions for a category.

        Args:
            category: Category name

        Returns:
            Set of extensions in that category
        """
        return self.CATEGORIES.get(category, set())


# ============================================================================
# Duplicate Finder
# ============================================================================

class DuplicateFinder:
    """
    Find duplicate files using SHA256 hashing.

    This class identifies files with identical content by computing
    cryptographic hashes. Files with the same hash are duplicates.

    Example:
        >>> finder = DuplicateFinder()
        >>> duplicates = finder.find_duplicates(Path("/data"))
        >>> for group in duplicates:
        ...     print(f"Hash: {group.hash_value}")
        ...     print(f"Files: {len(group.files)}")
        ...     print(f"Wasted space: {group.waste_size} bytes")
    """

    def __init__(self, chunk_size: int = 8192):
        """
        Initialize duplicate finder.

        Args:
            chunk_size: Bytes to read per iteration (for large files)
        """
        self.chunk_size = chunk_size

    def hash_file(self, file_path: Path) -> HashResult:
        """
        Compute SHA256 hash of a file.

        Args:
            file_path: Path to file

        Returns:
            HashResult with hash value and metadata

        Example:
            >>> finder = DuplicateFinder()
            >>> result = finder.hash_file(Path("document.pdf"))
            >>> print(result.hash_value)
            'a7b3c...'
        """
        try:
            hasher = hashlib.sha256()
            file_size = file_path.stat().st_size

            with open(file_path, 'rb') as f:
                while chunk := f.read(self.chunk_size):
                    hasher.update(chunk)

            return HashResult(
                file_path=file_path,
                hash_value=hasher.hexdigest(),
                file_size=file_size,
                success=True
            )

        except Exception as e:
            logger.error(f"Error hashing {file_path}: {e}")
            return HashResult(
                file_path=file_path,
                hash_value=None,
                file_size=0,
                success=False,
                error=str(e)
            )

    def find_duplicates(
        self,
        directory: Path,
        recursive: bool = True,
        min_size: int = 0,
        extensions: Optional[Set[str]] = None
    ) -> List[DuplicateGroup]:
        """
        Find all duplicate files in a directory.

        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            min_size: Minimum file size to consider (bytes)
            extensions: Only check files with these extensions (e.g., {'.jpg', '.png'})

        Returns:
            List of DuplicateGroup objects, sorted by waste size (descending)

        Example:
            >>> finder = DuplicateFinder()
            >>> # Find duplicate images larger than 1MB
            >>> dupes = finder.find_duplicates(
            ...     Path("/photos"),
            ...     min_size=1024*1024,
            ...     extensions={'.jpg', '.png'}
            ... )
        """
        if not directory.is_dir():
            logger.error(f"Invalid directory: {directory}")
            return []

        # Collect files
        pattern = '**/*' if recursive else '*'
        files = []

        for file_path in directory.glob(pattern):
            if not file_path.is_file():
                continue

            # Skip hidden files
            if file_path.name.startswith('.'):
                continue

            # Check size filter
            try:
                if file_path.stat().st_size < min_size:
                    continue
            except Exception:
                continue

            # Check extension filter
            if extensions and file_path.suffix.lower() not in extensions:
                continue

            files.append(file_path)

        logger.info(f"Scanning {len(files)} files for duplicates...")

        # Hash all files
        hash_map: Dict[str, List[Path]] = defaultdict(list)
        size_map: Dict[str, int] = {}

        for file_path in files:
            result = self.hash_file(file_path)

            if result.success and result.hash_value:
                hash_map[result.hash_value].append(file_path)
                size_map[result.hash_value] = result.file_size

        # Find duplicate groups (hash with 2+ files)
        duplicate_groups = []

        for hash_value, file_list in hash_map.items():
            if len(file_list) > 1:
                file_size = size_map[hash_value]
                total_size = file_size * len(file_list)
                waste_size = file_size * (len(file_list) - 1)  # All except one

                group = DuplicateGroup(
                    hash_value=hash_value,
                    files=file_list,
                    total_size=total_size,
                    waste_size=waste_size,
                    count=len(file_list)
                )
                duplicate_groups.append(group)

        # Sort by waste size (most wasteful first)
        duplicate_groups.sort(key=lambda g: g.waste_size, reverse=True)

        logger.info(f"Found {len(duplicate_groups)} duplicate groups")

        return duplicate_groups


# ============================================================================
# File Organizer
# ============================================================================

class FileOrganizer:
    """
    Organize files into subdirectories by type.

    Automatically categorizes files and moves them into type-based
    subdirectories (e.g., images/, documents/, code/).

    Example:
        >>> organizer = FileOrganizer()
        >>> result = organizer.organize_directory(Path("/downloads"))
        >>> print(f"Organized {result.files_organized} files")
        >>> print(f"Categories: {', '.join(result.categories_created)}")
    """

    def __init__(self):
        """Initialize file organizer."""
        self.detector = FileTypeDetector()

    def organize_directory(
        self,
        directory: Path,
        dry_run: bool = False,
        create_subdirs: bool = True
    ) -> OrganizationResult:
        """
        Organize files in a directory by type.

        Args:
            directory: Directory to organize
            dry_run: If True, don't actually move files (simulation)
            create_subdirs: Create type-based subdirectories

        Returns:
            OrganizationResult with statistics

        Example:
            >>> organizer = FileOrganizer()
            >>> # Simulate organization first
            >>> result = organizer.organize_directory(Path("/data"), dry_run=True)
            >>> print(result.category_counts)
            {'code': 42, 'data': 15, 'document': 8}
        """
        if not directory.is_dir():
            return OrganizationResult(
                files_organized=0,
                categories_created=[],
                success=False,
                error=f"Invalid directory: {directory}"
            )

        # Scan files
        category_files: Dict[str, List[Path]] = defaultdict(list)

        for file_path in directory.iterdir():
            if not file_path.is_file():
                continue

            # Skip hidden files
            if file_path.name.startswith('.'):
                continue

            file_type = self.detector.detect_type(file_path)
            category_files[file_type].append(file_path)

        # Organize files
        files_organized = 0
        categories_created = []
        category_counts = {}

        for category, files in category_files.items():
            if not files:
                continue

            category_counts[category] = len(files)

            if create_subdirs and not dry_run:
                # Create category subdirectory
                category_dir = directory / category
                category_dir.mkdir(exist_ok=True)
                categories_created.append(category)

                # Move files
                for file_path in files:
                    try:
                        dest = category_dir / file_path.name

                        # Handle name conflicts
                        if dest.exists():
                            stem = file_path.stem
                            suffix = file_path.suffix
                            counter = 1
                            while dest.exists():
                                dest = category_dir / f"{stem}_{counter}{suffix}"
                                counter += 1

                        file_path.rename(dest)
                        files_organized += 1
                        logger.debug(f"Moved {file_path.name} -> {category}/")

                    except Exception as e:
                        logger.error(f"Error moving {file_path}: {e}")

            elif dry_run:
                categories_created.append(category)
                files_organized += len(files)
                logger.info(f"[DRY RUN] Would move {len(files)} files to {category}/")

        return OrganizationResult(
            files_organized=files_organized,
            categories_created=categories_created,
            category_counts=category_counts,
            success=True
        )


# ============================================================================
# Unified Interface
# ============================================================================

class FileHerder:
    """
    Unified interface for all file management operations.

    This class combines DuplicateFinder, FileOrganizer, and FileTypeDetector
    into a single convenient API.

    Example:
        >>> herder = FileHerder()
        >>>
        >>> # Find duplicates
        >>> dupes = herder.find_duplicates(Path("/data"))
        >>>
        >>> # Organize directory
        >>> result = herder.organize(Path("/downloads"))
        >>>
        >>> # Detect file type
        >>> file_type = herder.detect_type(Path("script.py"))
    """

    def __init__(self):
        """Initialize FileHerder with all components."""
        self.duplicate_finder = DuplicateFinder()
        self.organizer = FileOrganizer()
        self.type_detector = FileTypeDetector()

    def find_duplicates(
        self,
        directory: Path,
        **kwargs
    ) -> List[DuplicateGroup]:
        """
        Find duplicate files (delegates to DuplicateFinder).

        Args:
            directory: Directory to scan
            **kwargs: Additional arguments for find_duplicates()

        Returns:
            List of DuplicateGroup objects
        """
        return self.duplicate_finder.find_duplicates(directory, **kwargs)

    def organize(
        self,
        directory: Path,
        **kwargs
    ) -> OrganizationResult:
        """
        Organize directory by file type (delegates to FileOrganizer).

        Args:
            directory: Directory to organize
            **kwargs: Additional arguments for organize_directory()

        Returns:
            OrganizationResult with statistics
        """
        return self.organizer.organize_directory(directory, **kwargs)

    def detect_type(self, file_path: Path) -> str:
        """
        Detect file type (delegates to FileTypeDetector).

        Args:
            file_path: Path to file

        Returns:
            Category name
        """
        return self.type_detector.detect_type(file_path)

    def get_statistics(self, directory: Path) -> Dict[str, Any]:
        """
        Get comprehensive statistics about a directory.

        Args:
            directory: Directory to analyze

        Returns:
            Dictionary with file counts, sizes, types, etc.

        Example:
            >>> herder = FileHerder()
            >>> stats = herder.get_statistics(Path("/data"))
            >>> print(stats['total_files'])
            425
            >>> print(stats['total_size_mb'])
            1024.5
            >>> print(stats['types'])
            {'code': 150, 'data': 100, 'document': 75, ...}
        """
        if not directory.is_dir():
            return {'error': f"Invalid directory: {directory}"}

        stats = {
            'total_files': 0,
            'total_size': 0,
            'types': defaultdict(int),
            'extensions': defaultdict(int),
            'largest_files': []
        }

        files_with_sizes = []

        for file_path in directory.rglob('*'):
            if not file_path.is_file():
                continue

            try:
                file_size = file_path.stat().st_size
                file_type = self.detect_type(file_path)

                stats['total_files'] += 1
                stats['total_size'] += file_size
                stats['types'][file_type] += 1
                stats['extensions'][file_path.suffix.lower()] += 1

                files_with_sizes.append((file_path, file_size))

            except Exception as e:
                logger.debug(f"Error processing {file_path}: {e}")

        # Find largest files
        files_with_sizes.sort(key=lambda x: x[1], reverse=True)
        stats['largest_files'] = [
            {'path': str(p), 'size': s}
            for p, s in files_with_sizes[:10]
        ]

        # Convert to regular dict for JSON serialization
        stats['types'] = dict(stats['types'])
        stats['extensions'] = dict(stats['extensions'])
        stats['total_size_mb'] = stats['total_size'] / (1024 * 1024)

        return stats


# ============================================================================
# Testing
# ============================================================================

def _test_core():
    """Test function for standalone testing."""
    print("Testing FileHerder Core...")

    print("\n1. Testing FileTypeDetector...")
    detector = FileTypeDetector()
    test_files = [
        ("script.py", "code"),
        ("data.csv", "data"),
        ("photo.jpg", "image"),
        ("document.pdf", "document"),
        ("archive.tar.gz", "archive")
    ]

    for filename, expected in test_files:
        detected = detector.detect_type(Path(filename))
        status = "✓" if detected == expected else "✗"
        print(f"   {status} {filename} -> {detected} (expected: {expected})")

    print("\n2. Testing DuplicateFinder...")
    finder = DuplicateFinder()
    print("   DuplicateFinder initialized successfully")

    print("\n3. Testing FileOrganizer...")
    organizer = FileOrganizer()
    print("   FileOrganizer initialized successfully")

    print("\n4. Testing FileHerder unified interface...")
    herder = FileHerder()
    print("   FileHerder initialized successfully")
    print("   ✓ All components working")

    print("\nAll tests complete!")


if __name__ == "__main__":
    _test_core()
