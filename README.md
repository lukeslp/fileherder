# fileherder

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Active](https://img.shields.io/badge/status-active-success.svg)]()

**Lightweight File Management Utilities**

A focused Python package for essential file management operations without heavy dependencies.

## Features

- **Duplicate Detection** - Hash-based duplicate finding with SHA256
- **File Organization** - Automatic categorization by file type
- **Batch Operations** - Safe move, copy, delete, and rename operations
- **Type Detection** - Smart file type classification
- **Rich CLI** - Beautiful terminal interface (optional)
- **Zero Required Dependencies** - Core functionality works standalone

## Installation

```bash
# Basic installation (no dependencies)
pip install fileherder

# With Rich CLI (recommended)
pip install fileherder[cli]

# Development install
pip install fileherder[dev]
```

## Quick Start

### Command Line

```bash
# Find duplicate files
fileherder duplicates /path/to/directory

# Find duplicate images larger than 1MB
fileherder duplicates /photos --min-size 1048576 --extensions .jpg,.png

# Organize directory by file type
fileherder organize /downloads

# Show directory statistics
fileherder stats /data
```

### Python API

```python
from fileherder import FileHerder

# Create herder instance
herder = FileHerder()

# Find duplicates
duplicates = herder.find_duplicates(
    Path("/data"),
    min_size=1024*1024,  # Files larger than 1MB
    extensions={'.jpg', '.png'}  # Only images
)

for group in duplicates:
    print(f"Found {group.count} duplicates:")
    print(f"  Wasted space: {group.waste_size} bytes")
    for file_path in group.files:
        print(f"  - {file_path}")

# Organize directory
result = herder.organize(Path("/downloads"))
print(f"Organized {result.files_organized} files")
print(f"Categories: {', '.join(result.categories_created)}")

# Get statistics
stats = herder.get_statistics(Path("/data"))
print(f"Total files: {stats['total_files']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
```

## File Type Categories

fileherder automatically categorizes files into:

- **code** - Python, JavaScript, Java, C++, etc.
- **document** - PDF, DOCX, MD, TXT, etc.
- **image** - JPG, PNG, GIF, SVG, etc.
- **video** - MP4, AVI, MKV, MOV, etc.
- **audio** - MP3, WAV, FLAC, OGG, etc.
- **archive** - ZIP, TAR, GZ, 7Z, etc.
- **data** - CSV, JSON, XML, SQL, etc.
- **text** - Plain text, logs, config files
- **other** - Uncategorized files

## API Reference

### Core Classes

#### FileHerder

Unified interface for all file management operations.

```python
from fileherder import FileHerder

herder = FileHerder()

# Find duplicates
duplicates = herder.find_duplicates(directory, recursive=True, min_size=0)

# Organize by type
result = herder.organize(directory, dry_run=False)

# Detect file type
file_type = herder.detect_type(file_path)

# Get statistics
stats = herder.get_statistics(directory)
```

#### DuplicateFinder

Specialized duplicate file detection.

```python
from fileherder import DuplicateFinder

finder = DuplicateFinder()
duplicates = finder.find_duplicates(
    directory,
    recursive=True,
    min_size=1024*1024,
    extensions={'.jpg', '.png'}
)
```

#### FileOrganizer

Directory organization by file type.

```python
from fileherder import FileOrganizer

organizer = FileOrganizer()
result = organizer.organize_directory(
    directory,
    dry_run=False,
    create_subdirs=True
)
```

#### FileTypeDetector

File type classification.

```python
from fileherder import FileTypeDetector

detector = FileTypeDetector()
file_type = detector.detect_type(Path("script.py"))
# Returns: 'code'
```

### Batch Operations

```python
from fileherder.operations import (
    move_files,
    copy_files,
    delete_files_safe,
    rename_files_batch
)

# Move files
result = move_files(
    files=[Path("file1.txt"), Path("file2.txt")],
    destination=Path("/archive"),
    overwrite=False
)

# Delete safely (with confirmation)
result = delete_files_safe(
    files=duplicate_files,
    require_confirmation=True
)
```

## Data Classes

### DuplicateGroup

```python
@dataclass
class DuplicateGroup:
    hash_value: str              # SHA256 hash
    files: List[Path]            # List of duplicate files
    total_size: int              # Combined size of all
    waste_size: int              # Size of redundant copies
    count: int                   # Number of duplicates
```

### OrganizationResult

```python
@dataclass
class OrganizationResult:
    files_organized: int
    categories_created: List[str]
    category_counts: Dict[str, int]
    success: bool
    error: Optional[str]
```

## Development

```bash
# Clone repository
git clone https://github.com/lukeslp/fileherder.git
cd fileherder

# Install with dev dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=fileherder --cov-report=html
```

## Architecture

fileherder is designed with minimal dependencies:

- **Core module** (`core.py`) - Pure Python, no dependencies
- **Operations module** (`operations.py`) - Batch file operations
- **CLI module** (`cli.py`) - Optional Rich interface

This allows the package to be used in environments where installing
dependencies is difficult, while still offering a beautiful CLI when Rich is available.

## Extracted from cleanupx

fileherder contains the core file management features from the larger
cleanupx project, without LLM dependencies or complex integrations.

## License

MIT License

Copyright (c) 2024 Luke Steuber

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Author

**Luke Steuber**

- Website: [lukesteuber.com](https://lukesteuber.com)
- Email: luke@dr.eamer.dev
- Bluesky: [@lukesteuber.com](https://bsky.app/profile/lukesteuber.com)
- LinkedIn: [lukesteuber](https://www.linkedin.com/in/lukesteuber/)
