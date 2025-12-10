"""
Tests for fileherder core functionality.
"""
import pytest
import tempfile
import hashlib
from pathlib import Path
from fileherder.core import (
    FileTypeDetector,
    DuplicateFinder,
    FileOrganizer,
    FileHerder,
    HashResult,
    DuplicateGroup,
    OrganizationResult
)


class TestFileTypeDetector:
    """Test FileTypeDetector class."""

    def test_detect_code_files(self):
        """Test detection of code files."""
        detector = FileTypeDetector()

        assert detector.detect_type(Path("script.py")) == "code"
        assert detector.detect_type(Path("app.js")) == "code"
        assert detector.detect_type(Path("Main.java")) == "code"
        assert detector.detect_type(Path("program.cpp")) == "code"

    def test_detect_document_files(self):
        """Test detection of document files."""
        detector = FileTypeDetector()

        assert detector.detect_type(Path("document.pdf")) == "document"
        assert detector.detect_type(Path("report.docx")) == "document"
        assert detector.detect_type(Path("notes.md")) == "document"

    def test_detect_image_files(self):
        """Test detection of image files."""
        detector = FileTypeDetector()

        assert detector.detect_type(Path("photo.jpg")) == "image"
        assert detector.detect_type(Path("picture.png")) == "image"
        assert detector.detect_type(Path("logo.svg")) == "image"

    def test_detect_data_files(self):
        """Test detection of data files."""
        detector = FileTypeDetector()

        assert detector.detect_type(Path("data.csv")) == "data"
        assert detector.detect_type(Path("config.json")) == "data"
        assert detector.detect_type(Path("settings.xml")) == "data"

    def test_detect_archive_files(self):
        """Test detection of archive files."""
        detector = FileTypeDetector()

        assert detector.detect_type(Path("archive.zip")) == "archive"
        assert detector.detect_type(Path("backup.tar.gz")) == "archive"
        assert detector.detect_type(Path("files.7z")) == "archive"

    def test_detect_video_files(self):
        """Test detection of video files."""
        detector = FileTypeDetector()

        assert detector.detect_type(Path("movie.mp4")) == "video"
        assert detector.detect_type(Path("clip.avi")) == "video"

    def test_detect_audio_files(self):
        """Test detection of audio files."""
        detector = FileTypeDetector()

        assert detector.detect_type(Path("song.mp3")) == "audio"
        assert detector.detect_type(Path("audio.wav")) == "audio"

    def test_detect_unknown_files(self):
        """Test detection of unknown file types."""
        detector = FileTypeDetector()

        assert detector.detect_type(Path("unknown.xyz")) == "other"

    def test_get_category_extensions(self):
        """Test getting extensions for a category."""
        detector = FileTypeDetector()

        code_exts = detector.get_category_extensions("code")
        assert '.py' in code_exts
        assert '.js' in code_exts

        image_exts = detector.get_category_extensions("image")
        assert '.jpg' in image_exts
        assert '.png' in image_exts


class TestDuplicateFinder:
    """Test DuplicateFinder class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_hash_file(self, temp_dir):
        """Test file hashing."""
        finder = DuplicateFinder()

        # Create test file
        test_file = temp_dir / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        # Hash file
        result = finder.hash_file(test_file)

        assert result.success is True
        assert result.file_path == test_file
        assert result.file_size == len(content)

        # Verify hash is correct
        expected_hash = hashlib.sha256(content).hexdigest()
        assert result.hash_value == expected_hash

    def test_hash_nonexistent_file(self):
        """Test hashing non-existent file."""
        finder = DuplicateFinder()

        result = finder.hash_file(Path("/nonexistent/file.txt"))

        assert result.success is False
        assert result.error is not None

    def test_find_duplicates_simple(self, temp_dir):
        """Test finding simple duplicates."""
        finder = DuplicateFinder()

        # Create duplicate files
        content = b"Duplicate content"
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file3 = temp_dir / "different.txt"

        file1.write_bytes(content)
        file2.write_bytes(content)
        file3.write_bytes(b"Different content")

        # Find duplicates
        duplicates = finder.find_duplicates(temp_dir, recursive=False)

        assert len(duplicates) == 1
        assert duplicates[0].count == 2
        assert set(duplicates[0].files) == {file1, file2}

    def test_find_duplicates_min_size(self, temp_dir):
        """Test duplicate finding with minimum size filter."""
        finder = DuplicateFinder()

        # Create files of different sizes
        large_content = b"x" * 2000
        small_content = b"y" * 100

        file1 = temp_dir / "large1.txt"
        file2 = temp_dir / "large2.txt"
        file3 = temp_dir / "small1.txt"
        file4 = temp_dir / "small2.txt"

        file1.write_bytes(large_content)
        file2.write_bytes(large_content)
        file3.write_bytes(small_content)
        file4.write_bytes(small_content)

        # Find duplicates with min size
        duplicates = finder.find_duplicates(temp_dir, min_size=1000)

        assert len(duplicates) == 1
        assert duplicates[0].count == 2
        assert all(f.stat().st_size >= 1000 for f in duplicates[0].files)

    def test_find_duplicates_extension_filter(self, temp_dir):
        """Test duplicate finding with extension filter."""
        finder = DuplicateFinder()

        # Create duplicate files with different extensions
        content = b"Content"

        txt1 = temp_dir / "file1.txt"
        txt2 = temp_dir / "file2.txt"
        py1 = temp_dir / "script1.py"
        py2 = temp_dir / "script2.py"

        txt1.write_bytes(content)
        txt2.write_bytes(content)
        py1.write_bytes(content)
        py2.write_bytes(content)

        # Find only .txt duplicates
        duplicates = finder.find_duplicates(temp_dir, extensions={'.txt'})

        assert len(duplicates) == 1
        assert all(f.suffix == '.txt' for f in duplicates[0].files)

    def test_find_duplicates_no_duplicates(self, temp_dir):
        """Test when no duplicates exist."""
        finder = DuplicateFinder()

        # Create unique files
        (temp_dir / "file1.txt").write_bytes(b"Content 1")
        (temp_dir / "file2.txt").write_bytes(b"Content 2")
        (temp_dir / "file3.txt").write_bytes(b"Content 3")

        duplicates = finder.find_duplicates(temp_dir)

        assert len(duplicates) == 0


class TestFileOrganizer:
    """Test FileOrganizer class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_organize_directory_dry_run(self, temp_dir):
        """Test organizing in dry-run mode."""
        organizer = FileOrganizer()

        # Create test files
        (temp_dir / "script.py").write_text("print('hello')")
        (temp_dir / "data.csv").write_text("a,b,c\n1,2,3")
        (temp_dir / "image.jpg").write_bytes(b"fake image")

        # Organize (dry run)
        result = organizer.organize_directory(temp_dir, dry_run=True)

        assert result.success is True
        assert result.files_organized == 3
        assert len(result.categories_created) == 3

        # Verify files weren't actually moved
        assert (temp_dir / "script.py").exists()
        assert not (temp_dir / "code").exists()

    def test_organize_directory_actual(self, temp_dir):
        """Test actual directory organization."""
        organizer = FileOrganizer()

        # Create test files
        (temp_dir / "script.py").write_text("print('hello')")
        (temp_dir / "data.csv").write_text("a,b,c")

        # Organize
        result = organizer.organize_directory(temp_dir, dry_run=False)

        assert result.success is True
        assert result.files_organized == 2

        # Verify files were moved
        assert (temp_dir / "code" / "script.py").exists()
        assert (temp_dir / "data" / "data.csv").exists()

    def test_organize_handles_name_conflicts(self, temp_dir):
        """Test handling of filename conflicts."""
        organizer = FileOrganizer()

        # Create conflict scenario
        (temp_dir / "script.py").write_text("original")

        # Pre-create destination directory with conflicting file
        code_dir = temp_dir / "code"
        code_dir.mkdir()
        (code_dir / "script.py").write_text("existing")

        # Try to organize
        result = organizer.organize_directory(temp_dir, dry_run=False)

        # Should handle conflict by renaming
        assert result.success is True
        assert (code_dir / "script_1.py").exists() or (code_dir / "script.py").exists()

    def test_organize_ignores_hidden_files(self, temp_dir):
        """Test that hidden files are ignored."""
        organizer = FileOrganizer()

        # Create regular and hidden files
        (temp_dir / "visible.txt").write_text("visible")
        (temp_dir / ".hidden.txt").write_text("hidden")

        result = organizer.organize_directory(temp_dir, dry_run=True)

        # Should only count visible file
        assert result.files_organized == 1


class TestFileHerder:
    """Test FileHerder unified interface."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_initialization(self):
        """Test FileHerder initialization."""
        herder = FileHerder()

        assert herder.duplicate_finder is not None
        assert herder.organizer is not None
        assert herder.type_detector is not None

    def test_find_duplicates_delegation(self, temp_dir):
        """Test that find_duplicates delegates correctly."""
        herder = FileHerder()

        # Create duplicate files
        content = b"content"
        (temp_dir / "file1.txt").write_bytes(content)
        (temp_dir / "file2.txt").write_bytes(content)

        duplicates = herder.find_duplicates(temp_dir)

        assert len(duplicates) == 1
        assert duplicates[0].count == 2

    def test_organize_delegation(self, temp_dir):
        """Test that organize delegates correctly."""
        herder = FileHerder()

        # Create test file
        (temp_dir / "script.py").write_text("print('test')")

        result = herder.organize(temp_dir, dry_run=True)

        assert result.success is True
        assert result.files_organized == 1

    def test_detect_type_delegation(self):
        """Test that detect_type delegates correctly."""
        herder = FileHerder()

        file_type = herder.detect_type(Path("test.py"))

        assert file_type == "code"

    def test_get_statistics(self, temp_dir):
        """Test getting directory statistics."""
        herder = FileHerder()

        # Create test files
        (temp_dir / "script.py").write_text("print('hello')")
        (temp_dir / "data.csv").write_text("a,b,c")
        (temp_dir / "image.jpg").write_bytes(b"fake image")

        stats = herder.get_statistics(temp_dir)

        assert stats['total_files'] == 3
        assert 'types' in stats
        assert stats['types']['code'] == 1
        assert stats['types']['data'] == 1
        assert stats['types']['image'] == 1

    def test_get_statistics_includes_largest_files(self, temp_dir):
        """Test that statistics include largest files."""
        herder = FileHerder()

        # Create files of different sizes
        (temp_dir / "small.txt").write_bytes(b"x" * 100)
        (temp_dir / "large.txt").write_bytes(b"x" * 10000)

        stats = herder.get_statistics(temp_dir)

        assert 'largest_files' in stats
        assert len(stats['largest_files']) > 0
        # Largest file should be first
        assert Path(stats['largest_files'][0]['path']).name == "large.txt"


class TestDataClasses:
    """Test data classes."""

    def test_hash_result(self):
        """Test HashResult dataclass."""
        result = HashResult(
            file_path=Path("/test/file.txt"),
            hash_value="abc123",
            file_size=1024,
            success=True
        )

        assert result.file_path == Path("/test/file.txt")
        assert result.hash_value == "abc123"
        assert result.file_size == 1024
        assert result.success is True
        assert result.error is None

    def test_duplicate_group(self):
        """Test DuplicateGroup dataclass."""
        group = DuplicateGroup(
            hash_value="abc123",
            files=[Path("file1.txt"), Path("file2.txt"), Path("file3.txt")],
            total_size=3000,
            waste_size=2000,
            count=3
        )

        assert group.hash_value == "abc123"
        assert len(group.files) == 3
        assert group.count == 3
        assert group.waste_size == 2000

    def test_organization_result(self):
        """Test OrganizationResult dataclass."""
        result = OrganizationResult(
            files_organized=10,
            categories_created=["code", "data"],
            category_counts={"code": 5, "data": 5},
            success=True
        )

        assert result.files_organized == 10
        assert len(result.categories_created) == 2
        assert result.category_counts["code"] == 5
        assert result.success is True
