"""Tests for the Deleter service."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import MagicMock

from src.models.file_meta import FileMeta
from src.services.deleter import DeleteResult, Deleter


class TestDeleteResult:
    """Tests for DeleteResult dataclass."""

    def test_delete_result_creation(self) -> None:
        """Test DeleteResult can be created with required fields."""
        result = DeleteResult(
            deleted_files=["/path/to/file1.jpg"],
            failed_files=[("/path/to/file2.jpg", "File in use")],
            total_deleted=1,
            total_failed=1,
            space_saved=1024,
            backup_directory="/backup/dir",
        )

        assert result.deleted_files == ["/path/to/file1.jpg"]
        assert result.failed_files == [("/path/to/file2.jpg", "File in use")]
        assert result.total_deleted == 1
        assert result.total_failed == 1
        assert result.space_saved == 1024
        assert result.backup_directory == "/backup/dir"

    def test_delete_result_empty(self) -> None:
        """Test DeleteResult with empty lists."""
        result = DeleteResult(
            deleted_files=[],
            failed_files=[],
            total_deleted=0,
            total_failed=0,
            space_saved=0,
        )

        assert result.deleted_files == []
        assert result.failed_files == []
        assert result.total_deleted == 0
        assert result.space_saved == 0
        assert result.backup_directory is None


class TestDeleter:
    """Tests for Deleter service."""

    def test_deleter_initialization(self) -> None:
        """Test Deleter can be initialized."""
        deleter = Deleter()
        assert deleter is not None
        assert deleter.backup_base_dir == (Path.home() / ".duplicate_scan_backups")

    def test_deleter_initialization_with_custom_dir(self) -> None:
        """Test Deleter can be initialized with custom backup directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir)
            deleter = Deleter(backup_base_dir=custom_dir)
            assert deleter.backup_base_dir == custom_dir

    def test_delete_files_empty_list(self) -> None:
        """Test delete_files with empty list returns empty result."""
        deleter = Deleter()
        result = deleter.delete_files([])

        assert result.deleted_files == []
        assert result.failed_files == []
        assert result.total_deleted == 0
        assert result.total_failed == 0
        assert result.space_saved == 0
        assert result.backup_directory is None

    def test_delete_files_single_file(self) -> None:
        """Test delete_files with a single file moves to backup directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Given: A file exists
            file_path = tmpdir_path / "test_file.jpg"
            file_path.write_bytes(b"test content")
            file_size = file_path.stat().st_size

            file_meta = FileMeta(
                path=str(file_path),
                size=file_size,
                modified_time=datetime.now(),
            )

            # When: Delete the file
            deleter = Deleter(backup_base_dir=tmpdir_path)
            result = deleter.delete_files([file_meta])

            # Then: File is moved to backup directory
            assert result.total_deleted == 1
            assert result.total_failed == 0
            assert result.space_saved == file_size
            assert str(file_path) in result.deleted_files
            assert result.backup_directory is not None

            # Original file should not exist
            assert not file_path.exists()

            # File should exist in backup directory
            backup_dir = Path(result.backup_directory)
            assert backup_dir.exists()
            backup_file = backup_dir / "test_file.jpg"
            assert backup_file.exists()
            assert backup_file.read_bytes() == b"test content"

    def test_delete_files_multiple_files(self) -> None:
        """Test delete_files with multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Given: Multiple files exist
            files: List[FileMeta] = []
            total_size = 0

            for i in range(3):
                file_path = tmpdir_path / f"test_file_{i}.jpg"
                content = f"test content {i}".encode()
                file_path.write_bytes(content)
                file_size = file_path.stat().st_size
                total_size += file_size

                files.append(
                    FileMeta(
                        path=str(file_path),
                        size=file_size,
                        modified_time=datetime.now(),
                    )
                )

            # When: Delete all files
            deleter = Deleter(backup_base_dir=tmpdir_path)
            result = deleter.delete_files(files)

            # Then: All files are moved to backup
            assert result.total_deleted == 3
            assert result.total_failed == 0
            assert result.space_saved == total_size

            # Original files should not exist
            for file in files:
                assert not Path(file.path).exists()

            # Files should exist in backup directory
            backup_dir = Path(result.backup_directory or "")
            assert len(list(backup_dir.iterdir())) == 3

    def test_delete_files_handles_error(self) -> None:
        """Test delete_files handles errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Given: A file that doesn't exist
            file_meta = FileMeta(
                path="/nonexistent/file.jpg",
                size=1024,
                modified_time=datetime.now(),
            )

            # When: Try to delete the file
            deleter = Deleter(backup_base_dir=tmpdir_path)
            result = deleter.delete_files([file_meta])

            # Then: Error is recorded
            assert result.total_deleted == 0
            assert result.total_failed == 1
            assert result.space_saved == 0
            assert len(result.failed_files) == 1
            assert result.failed_files[0][0] == "/nonexistent/file.jpg"

    def test_delete_files_partial_failure(self) -> None:
        """Test delete_files with some files failing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Given: One file exists, one doesn't
            existing_file = tmpdir_path / "success.jpg"
            existing_file.write_bytes(b"test content")
            file_size = existing_file.stat().st_size

            file1 = FileMeta(
                path=str(existing_file),
                size=file_size,
                modified_time=datetime.now(),
            )
            file2 = FileMeta(
                path="/nonexistent/fail.jpg",
                size=2048,
                modified_time=datetime.now(),
            )

            # When: Delete files with partial failure
            deleter = Deleter(backup_base_dir=tmpdir_path)
            result = deleter.delete_files([file1, file2])

            # Then: One success, one failure
            assert result.total_deleted == 1
            assert result.total_failed == 1
            assert result.space_saved == file_size
            assert str(existing_file) in result.deleted_files
            assert result.failed_files[0][0] == "/nonexistent/fail.jpg"

    def test_delete_files_with_callback(self) -> None:
        """Test delete_files calls progress callback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Given: Files to delete with a callback
            files: List[FileMeta] = []
            for i in range(3):
                file_path = tmpdir_path / f"file{i}.jpg"
                file_path.write_bytes(b"content")
                files.append(
                    FileMeta(
                        path=str(file_path),
                        size=7,
                        modified_time=datetime.now(),
                    )
                )

            callback = MagicMock()

            # When: Delete files with callback
            deleter = Deleter(backup_base_dir=tmpdir_path)
            result = deleter.delete_files(files, progress_callback=callback)

            # Then: Callback is called for each file
            assert callback.call_count == 3
            assert result.total_deleted == 3

    def test_delete_files_handles_filename_conflicts(self) -> None:
        """Test delete_files handles duplicate filenames correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Given: Two files with the same name in different directories
            subdir1 = tmpdir_path / "subdir1"
            subdir2 = tmpdir_path / "subdir2"
            subdir1.mkdir()
            subdir2.mkdir()

            file1 = subdir1 / "same_name.jpg"
            file2 = subdir2 / "same_name.jpg"
            file1.write_bytes(b"content1")
            file2.write_bytes(b"content2")

            files = [
                FileMeta(
                    path=str(file1),
                    size=8,
                    modified_time=datetime.now(),
                ),
                FileMeta(
                    path=str(file2),
                    size=8,
                    modified_time=datetime.now(),
                ),
            ]

            # When: Delete both files
            deleter = Deleter(backup_base_dir=tmpdir_path)
            result = deleter.delete_files(files)

            # Then: Both files are moved with unique names
            assert result.total_deleted == 2
            backup_dir = Path(result.backup_directory or "")
            backup_files = list(backup_dir.iterdir())
            assert len(backup_files) == 2

            # Check that one file has a suffix
            names = [f.name for f in backup_files]
            assert "same_name.jpg" in names
            assert "same_name_1.jpg" in names

    def test_format_size_bytes(self) -> None:
        """Test format_size with bytes."""
        deleter = Deleter()
        assert deleter.format_size(500) == "500 B"

    def test_format_size_kilobytes(self) -> None:
        """Test format_size with kilobytes."""
        deleter = Deleter()
        assert deleter.format_size(1024) == "1.0 KB"
        assert deleter.format_size(2560) == "2.5 KB"

    def test_format_size_megabytes(self) -> None:
        """Test format_size with megabytes."""
        deleter = Deleter()
        assert deleter.format_size(1024 * 1024) == "1.0 MB"
        assert deleter.format_size(1024 * 1024 * 5) == "5.0 MB"

    def test_format_size_gigabytes(self) -> None:
        """Test format_size with gigabytes."""
        deleter = Deleter()
        assert deleter.format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert deleter.format_size(1024 * 1024 * 1024 * 2) == "2.0 GB"
