"""
Tests for fileherder batch operations.
"""
import pytest
import tempfile
from pathlib import Path
from fileherder.operations import (
    move_files,
    copy_files,
    delete_files_safe,
    rename_files_batch,
    format_size,
    validate_paths,
    OperationResult
)


class TestMoveFiles:
    """Test move_files function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_move_files_dry_run(self, temp_dir):
        """Test moving files in dry-run mode."""
        # Create source files
        src_dir = temp_dir / "source"
        src_dir.mkdir()

        files = []
        for i in range(3):
            f = src_dir / f"file{i}.txt"
            f.write_text(f"Content {i}")
            files.append(f)

        dest_dir = temp_dir / "dest"

        # Move (dry run)
        result = move_files(files, dest_dir, dry_run=True)

        assert result.success is True
        assert result.success_count == 3
        assert result.failure_count == 0

        # Verify files weren't actually moved
        assert all(f.exists() for f in files)
        assert not dest_dir.exists()

    def test_move_files_actual(self, temp_dir):
        """Test actually moving files."""
        # Create source files
        src_dir = temp_dir / "source"
        src_dir.mkdir()

        files = []
        for i in range(3):
            f = src_dir / f"file{i}.txt"
            f.write_text(f"Content {i}")
            files.append(f)

        dest_dir = temp_dir / "dest"

        # Move
        result = move_files(files, dest_dir, dry_run=False)

        assert result.success is True
        assert result.success_count == 3

        # Verify files were moved
        assert all(not f.exists() for f in files)
        assert all((dest_dir / f.name).exists() for f in files)

    def test_move_files_handles_conflicts(self, temp_dir):
        """Test moving files with name conflicts."""
        # Create source file
        src_file = temp_dir / "source.txt"
        src_file.write_text("source content")

        # Create destination with conflicting file
        dest_dir = temp_dir / "dest"
        dest_dir.mkdir()
        (dest_dir / "source.txt").write_text("existing content")

        # Move without overwrite
        result = move_files([src_file], dest_dir, overwrite=False, dry_run=False)

        assert result.success is True

        # Should create source_1.txt
        assert (dest_dir / "source_1.txt").exists()

    def test_move_nonexistent_file(self, temp_dir):
        """Test moving non-existent file."""
        fake_file = temp_dir / "nonexistent.txt"
        dest_dir = temp_dir / "dest"

        result = move_files([fake_file], dest_dir, dry_run=False)

        assert result.success is False
        assert result.failure_count == 1
        assert len(result.errors) == 1


class TestCopyFiles:
    """Test copy_files function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_copy_files_dry_run(self, temp_dir):
        """Test copying files in dry-run mode."""
        # Create source files
        files = []
        for i in range(3):
            f = temp_dir / f"file{i}.txt"
            f.write_text(f"Content {i}")
            files.append(f)

        dest_dir = temp_dir / "dest"

        # Copy (dry run)
        result = copy_files(files, dest_dir, dry_run=True)

        assert result.success is True
        assert result.success_count == 3

        # Verify files weren't actually copied
        assert not dest_dir.exists()

    def test_copy_files_actual(self, temp_dir):
        """Test actually copying files."""
        # Create source files
        files = []
        for i in range(3):
            f = temp_dir / f"file{i}.txt"
            f.write_text(f"Content {i}")
            files.append(f)

        dest_dir = temp_dir / "dest"

        # Copy
        result = copy_files(files, dest_dir, dry_run=False)

        assert result.success is True
        assert result.success_count == 3

        # Verify files were copied (originals still exist)
        assert all(f.exists() for f in files)
        assert all((dest_dir / f.name).exists() for f in files)

    def test_copy_preserves_content(self, temp_dir):
        """Test that copied files have same content."""
        # Create source file
        src_file = temp_dir / "source.txt"
        content = "Important content"
        src_file.write_text(content)

        dest_dir = temp_dir / "dest"

        # Copy
        copy_files([src_file], dest_dir, dry_run=False)

        # Verify content
        copied_file = dest_dir / "source.txt"
        assert copied_file.read_text() == content


class TestDeleteFilesSafe:
    """Test delete_files_safe function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_delete_files_dry_run(self, temp_dir):
        """Test deleting files in dry-run mode."""
        # Create files
        files = []
        for i in range(3):
            f = temp_dir / f"file{i}.txt"
            f.write_text(f"Content {i}")
            files.append(f)

        # Delete (dry run, no confirmation)
        result = delete_files_safe(
            files,
            require_confirmation=False,
            dry_run=True
        )

        assert result.success is True
        assert result.success_count == 3

        # Verify files still exist
        assert all(f.exists() for f in files)

    def test_delete_files_actual(self, temp_dir):
        """Test actually deleting files."""
        # Create files
        files = []
        for i in range(3):
            f = temp_dir / f"file{i}.txt"
            f.write_text(f"Content {i}")
            files.append(f)

        # Delete (no confirmation)
        result = delete_files_safe(
            files,
            require_confirmation=False,
            dry_run=False
        )

        assert result.success is True
        assert result.success_count == 3

        # Verify files were deleted
        assert all(not f.exists() for f in files)

    def test_delete_nonexistent_file(self, temp_dir):
        """Test deleting non-existent file."""
        fake_file = temp_dir / "nonexistent.txt"

        result = delete_files_safe(
            [fake_file],
            require_confirmation=False,
            dry_run=False
        )

        assert result.success is False
        assert result.failure_count == 1


class TestRenameFilesBatch:
    """Test rename_files_batch function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_rename_files_dry_run(self, temp_dir):
        """Test renaming files in dry-run mode."""
        # Create files
        file1 = temp_dir / "old1.txt"
        file2 = temp_dir / "old2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        rename_map = {
            file1: "new1.txt",
            file2: "new2.txt"
        }

        # Rename (dry run)
        result = rename_files_batch(rename_map, dry_run=True)

        assert result.success is True
        assert result.success_count == 2

        # Verify files weren't renamed
        assert file1.exists()
        assert not (temp_dir / "new1.txt").exists()

    def test_rename_files_actual(self, temp_dir):
        """Test actually renaming files."""
        # Create files
        file1 = temp_dir / "old1.txt"
        file2 = temp_dir / "old2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        rename_map = {
            file1: "new1.txt",
            file2: "new2.txt"
        }

        # Rename
        result = rename_files_batch(rename_map, dry_run=False)

        assert result.success is True
        assert result.success_count == 2

        # Verify files were renamed
        assert not file1.exists()
        assert (temp_dir / "new1.txt").exists()
        assert (temp_dir / "new2.txt").exists()

    def test_rename_handles_conflicts(self, temp_dir):
        """Test renaming with conflicting destination."""
        # Create files
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        # Try to rename file1 to file2 (conflict)
        rename_map = {file1: "file2.txt"}

        result = rename_files_batch(rename_map, dry_run=False)

        assert result.success is False
        assert result.failure_count == 1


class TestUtilityFunctions:
    """Test utility functions."""

    def test_format_size_bytes(self):
        """Test formatting bytes."""
        assert "100 B" in format_size(100)
        assert "B" in format_size(500)

    def test_format_size_kilobytes(self):
        """Test formatting kilobytes."""
        result = format_size(1536)  # 1.5 KB
        assert "KB" in result

    def test_format_size_megabytes(self):
        """Test formatting megabytes."""
        result = format_size(1536000)  # ~1.46 MB
        assert "MB" in result

    def test_format_size_gigabytes(self):
        """Test formatting gigabytes."""
        result = format_size(1536000000)  # ~1.43 GB
        assert "GB" in result

    def test_validate_paths_all_valid(self):
        """Test validating all valid paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create test files
            file1 = temp_path / "file1.txt"
            file2 = temp_path / "file2.txt"
            file1.write_text("test")
            file2.write_text("test")

            valid, errors = validate_paths([file1, file2])

            assert len(valid) == 2
            assert len(errors) == 0

    def test_validate_paths_some_invalid(self):
        """Test validating mix of valid and invalid paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create one valid file
            valid_file = temp_path / "valid.txt"
            valid_file.write_text("test")

            # Invalid paths
            missing_file = temp_path / "missing.txt"
            not_a_file = temp_path  # Directory, not file

            valid, errors = validate_paths([valid_file, missing_file, not_a_file])

            assert len(valid) == 1
            assert len(errors) == 2

    def test_validate_paths_empty_list(self):
        """Test validating empty list."""
        valid, errors = validate_paths([])

        assert len(valid) == 0
        assert len(errors) == 0


class TestOperationResult:
    """Test OperationResult dataclass."""

    def test_operation_result_success(self):
        """Test successful operation result."""
        result = OperationResult(
            success_count=5,
            failure_count=0,
            total_count=5,
            errors=[],
            success=True
        )

        assert result.success is True
        assert result.success_count == 5
        assert result.failure_count == 0
        assert len(result.errors) == 0

    def test_operation_result_partial_failure(self):
        """Test partial failure result."""
        result = OperationResult(
            success_count=3,
            failure_count=2,
            total_count=5,
            errors=[(Path("file1.txt"), "error 1"), (Path("file2.txt"), "error 2")],
            success=False
        )

        assert result.success is False
        assert result.success_count == 3
        assert result.failure_count == 2
        assert len(result.errors) == 2
