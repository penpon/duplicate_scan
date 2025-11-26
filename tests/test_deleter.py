"""Tests for the Deleter service."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

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
        )

        assert result.deleted_files == ["/path/to/file1.jpg"]
        assert result.failed_files == [("/path/to/file2.jpg", "File in use")]
        assert result.total_deleted == 1
        assert result.total_failed == 1
        assert result.space_saved == 1024

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


class TestDeleter:
    """Tests for Deleter service."""

    def test_deleter_initialization(self) -> None:
        """Test Deleter can be initialized."""
        deleter = Deleter()
        assert deleter is not None

    def test_delete_files_empty_list(self) -> None:
        """Test delete_files with empty list returns empty result."""
        deleter = Deleter()
        result = deleter.delete_files([])

        assert result.deleted_files == []
        assert result.failed_files == []
        assert result.total_deleted == 0
        assert result.total_failed == 0
        assert result.space_saved == 0

    def test_delete_files_single_file(self) -> None:
        """Test delete_files with a single file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Given: A file exists
            file_path = Path(tmpdir) / "test_file.jpg"
            file_path.write_bytes(b"test content")
            file_size = file_path.stat().st_size

            file_meta = FileMeta(
                path=str(file_path),
                size=file_size,
                modified_time=datetime.now(),
            )

            # When: Delete the file
            deleter = Deleter()
            with patch("src.services.deleter.send2trash") as mock_send2trash:
                result = deleter.delete_files([file_meta])

            # Then: File is deleted successfully
            mock_send2trash.assert_called_once_with(str(file_path))
            assert result.total_deleted == 1
            assert result.total_failed == 0
            assert result.space_saved == file_size
            assert str(file_path) in result.deleted_files

    def test_delete_files_multiple_files(self) -> None:
        """Test delete_files with multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Given: Multiple files exist
            files: List[FileMeta] = []
            total_size = 0

            for i in range(3):
                file_path = Path(tmpdir) / f"test_file_{i}.jpg"
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
            deleter = Deleter()
            with patch("src.services.deleter.send2trash") as mock_send2trash:
                result = deleter.delete_files(files)

            # Then: All files are deleted
            assert mock_send2trash.call_count == 3
            assert result.total_deleted == 3
            assert result.total_failed == 0
            assert result.space_saved == total_size

    def test_delete_files_handles_error(self) -> None:
        """Test delete_files handles errors gracefully."""
        # Given: A file that will fail to delete
        file_meta = FileMeta(
            path="/nonexistent/file.jpg",
            size=1024,
            modified_time=datetime.now(),
        )

        # When: Try to delete the file
        deleter = Deleter()
        with patch(
            "src.services.deleter.send2trash",
            side_effect=OSError("File in use"),
        ):
            result = deleter.delete_files([file_meta])

        # Then: Error is recorded
        assert result.total_deleted == 0
        assert result.total_failed == 1
        assert result.space_saved == 0
        assert len(result.failed_files) == 1
        assert result.failed_files[0][0] == "/nonexistent/file.jpg"
        assert "File in use" in result.failed_files[0][1]

    def test_delete_files_partial_failure(self) -> None:
        """Test delete_files with some files failing."""
        # Given: Two files, one will fail
        file1 = FileMeta(
            path="/path/to/success.jpg",
            size=1024,
            modified_time=datetime.now(),
        )
        file2 = FileMeta(
            path="/path/to/fail.jpg",
            size=2048,
            modified_time=datetime.now(),
        )

        # When: Delete files with partial failure
        deleter = Deleter()

        def mock_send2trash(path: str) -> None:
            if "fail" in path:
                raise OSError("Permission denied")

        with patch(
            "src.services.deleter.send2trash",
            side_effect=mock_send2trash,
        ):
            result = deleter.delete_files([file1, file2])

        # Then: One success, one failure
        assert result.total_deleted == 1
        assert result.total_failed == 1
        assert result.space_saved == 1024
        assert "/path/to/success.jpg" in result.deleted_files
        assert result.failed_files[0][0] == "/path/to/fail.jpg"

    def test_delete_files_with_callback(self) -> None:
        """Test delete_files calls progress callback."""
        # Given: Files to delete with a callback
        files = [
            FileMeta(
                path=f"/path/to/file{i}.jpg",
                size=1024,
                modified_time=datetime.now(),
            )
            for i in range(3)
        ]

        callback = MagicMock()

        # When: Delete files with callback
        deleter = Deleter()
        with patch("src.services.deleter.send2trash"):
            result = deleter.delete_files(files, progress_callback=callback)

        # Then: Callback is called for each file
        assert callback.call_count == 3
        assert result.total_deleted == 3

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
