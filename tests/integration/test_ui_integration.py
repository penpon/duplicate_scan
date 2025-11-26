"""Integration tests for UI components with services.

Tests the integration of UI views with backend services
to verify the complete user workflow.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest

from src.models.file_meta import FileMeta
from src.services.deleter import DeleteResult, Deleter
from src.services.detector import DuplicateDetector
from src.services.hasher import Hasher
from src.ui.cleanup_view import CleanupView
from src.ui.results_view import ResultsView


def _create_test_file(path: Path, content: bytes) -> FileMeta:
    """Create a test file and return its FileMeta."""
    path.write_bytes(content)
    stat = path.stat()
    return FileMeta(
        path=str(path),
        size=stat.st_size,
        modified_time=datetime.fromtimestamp(stat.st_mtime),
    )


class TestResultsViewWithServices:
    """Integration tests for ResultsView with backend services."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def hasher(self) -> Hasher:
        """Create a Hasher instance."""
        return Hasher()

    @pytest.fixture
    def detector(self) -> DuplicateDetector:
        """Create a DuplicateDetector instance."""
        return DuplicateDetector()

    @pytest.fixture
    def results_view(self) -> ResultsView:
        """Create a ResultsView instance."""
        return ResultsView()

    def test_results_view_displays_detected_duplicates(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        results_view: ResultsView,
    ) -> None:
        """Test ResultsView correctly displays detected duplicates.

        Given: Duplicate files detected by services
        When: Setting duplicate groups on ResultsView
        Then: View correctly displays the groups
        """
        # Given: Create and detect duplicates
        content = b"Duplicate content" * 100
        file1 = _create_test_file(temp_dir / "file1.txt", content)
        file2 = _create_test_file(temp_dir / "file2.txt", content)

        for f in [file1, file2]:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        duplicates = detector.find_duplicates([file1, file2])

        # When: Set duplicates on view
        results_view.set_duplicate_groups(duplicates)

        # Then: View has the correct data
        assert len(results_view.duplicate_groups) == 1
        assert len(results_view.duplicate_groups[0].files) == 2

    def test_results_view_file_selection(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        results_view: ResultsView,
    ) -> None:
        """Test file selection in ResultsView.

        Given: Duplicate groups displayed in view
        When: Selecting files for deletion
        Then: Selected files are tracked correctly
        """
        # Given: Create and detect duplicates
        content = b"Test content" * 100
        file1 = _create_test_file(temp_dir / "file1.txt", content)
        file2 = _create_test_file(temp_dir / "file2.txt", content)

        for f in [file1, file2]:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        duplicates = detector.find_duplicates([file1, file2])
        results_view.set_duplicate_groups(duplicates)

        # When: Select a file
        file_to_select = duplicates[0].files[0]
        results_view.toggle_file_selection(file_to_select)

        # Then: File is in selected list
        selected = results_view.get_selected_files()
        assert len(selected) == 1
        assert file_to_select in selected

    def test_results_view_clear_selection(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        results_view: ResultsView,
    ) -> None:
        """Test clearing selection in ResultsView.

        Given: Files selected in view
        When: Clearing selection
        Then: No files are selected
        """
        # Given: Create duplicates and select files
        content = b"Test content" * 100
        file1 = _create_test_file(temp_dir / "file1.txt", content)
        file2 = _create_test_file(temp_dir / "file2.txt", content)

        for f in [file1, file2]:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        duplicates = detector.find_duplicates([file1, file2])
        results_view.set_duplicate_groups(duplicates)

        # Select both files
        for file in duplicates[0].files:
            results_view.toggle_file_selection(file)

        assert len(results_view.get_selected_files()) == 2

        # When: Clear selection
        results_view.clear_selection()

        # Then: No files selected
        assert len(results_view.get_selected_files()) == 0


class TestCleanupViewWithDeleter:
    """Integration tests for CleanupView with Deleter service."""

    @pytest.fixture
    def cleanup_view(self) -> CleanupView:
        """Create a CleanupView instance."""
        return CleanupView()

    @pytest.fixture
    def deleter(self) -> Deleter:
        """Create a Deleter instance."""
        return Deleter()

    def test_cleanup_view_displays_delete_results(
        self, cleanup_view: CleanupView
    ) -> None:
        """Test CleanupView correctly displays deletion results.

        Given: A DeleteResult from the Deleter service
        When: Setting result on CleanupView
        Then: View displays correct information
        """
        # Given: Create a delete result
        result = DeleteResult(
            deleted_files=["/path/to/file1.txt", "/path/to/file2.txt"],
            failed_files=[],
            total_deleted=2,
            total_failed=0,
            space_saved=2048,
        )

        # When: Set result on view
        cleanup_view.set_result(result)

        # Then: View has correct data
        assert cleanup_view.delete_result == result
        assert cleanup_view.deleted_count_text.value == "2"
        assert "2.0 KB" in cleanup_view.space_saved_text.value

    def test_cleanup_view_displays_failed_deletions(
        self, cleanup_view: CleanupView
    ) -> None:
        """Test CleanupView correctly displays failed deletions.

        Given: A DeleteResult with failures
        When: Setting result on CleanupView
        Then: Failed files are displayed
        """
        # Given: Create a delete result with failures
        result = DeleteResult(
            deleted_files=["/path/to/file1.txt"],
            failed_files=[("/path/to/file2.txt", "Permission denied")],
            total_deleted=1,
            total_failed=1,
            space_saved=1024,
        )

        # When: Set result on view
        cleanup_view.set_result(result)

        # Then: View shows failures
        assert cleanup_view.delete_result == result
        assert cleanup_view.failed_count_text.value == "1"
        assert cleanup_view.failed_section.visible is True

    def test_cleanup_view_done_callback(self, cleanup_view: CleanupView) -> None:
        """Test CleanupView done callback is triggered.

        Given: A done callback set on view
        When: Done button is clicked
        Then: Callback is invoked
        """
        # Given: Set up callback
        callback_called = []

        def on_done() -> None:
            callback_called.append(True)

        cleanup_view.set_done_callback(on_done)

        # When: Simulate done button click via the public button callback
        assert cleanup_view.done_button.on_click is not None
        cleanup_view.done_button.on_click(None)

        # Then: Callback was called
        assert len(callback_called) == 1


class TestEndToEndWorkflow:
    """End-to-end tests simulating complete user workflows."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_complete_user_workflow(self, temp_dir: Path) -> None:
        """Test complete user workflow from scan to cleanup.

        Given: A directory with duplicate files
        When: User scans, selects, and deletes duplicates
        Then: Workflow completes successfully
        """
        # Setup: Create services and views
        hasher = Hasher()
        detector = DuplicateDetector()
        deleter = Deleter()
        results_view = ResultsView()
        cleanup_view = CleanupView()

        # Step 1: Create test files (simulating scan)
        content = b"Duplicate content for E2E test" * 100
        original = _create_test_file(temp_dir / "original.txt", content)
        dup1 = _create_test_file(temp_dir / "duplicate1.txt", content)
        dup2 = _create_test_file(temp_dir / "duplicate2.txt", content)

        # Step 2: Hash files
        files = [original, dup1, dup2]
        for f in files:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Step 3: Detect duplicates
        duplicates = detector.find_duplicates(files)
        assert len(duplicates) == 1, "Should find one duplicate group"

        # Step 4: Display in ResultsView
        results_view.set_duplicate_groups(duplicates)
        assert len(results_view.duplicate_groups) == 1

        # Step 5: User selects files to delete (keep original)
        for file in duplicates[0].files:
            if "duplicate" in file.path:
                results_view.toggle_file_selection(file)

        selected = results_view.get_selected_files()
        assert len(selected) == 2, "Should have 2 files selected"

        # Step 6: Delete selected files
        with patch("src.services.deleter.send2trash") as mock_trash:
            result = deleter.delete_files(selected)

            assert result.total_deleted == 2
            assert result.total_failed == 0
            assert mock_trash.call_count == 2

        # Step 7: Display results in CleanupView
        cleanup_view.set_result(result)
        assert cleanup_view.deleted_count_text.value == "2"

    def test_workflow_with_partial_failures(self, temp_dir: Path) -> None:
        """Test workflow handles partial deletion failures.

        Given: Files where some deletions will fail
        When: User attempts to delete
        Then: Failures are reported correctly
        """
        # Setup
        hasher = Hasher()
        detector = DuplicateDetector()
        deleter = Deleter()
        cleanup_view = CleanupView()

        # Create test files
        content = b"Test content" * 100
        file1 = _create_test_file(temp_dir / "file1.txt", content)
        file2 = _create_test_file(temp_dir / "file2.txt", content)

        for f in [file1, file2]:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        duplicates = detector.find_duplicates([file1, file2])
        files_to_delete = duplicates[0].files

        # Simulate partial failure
        def mock_send2trash(path: str) -> None:
            if "file1" in path:
                raise PermissionError("File locked")

        with patch("src.services.deleter.send2trash", side_effect=mock_send2trash):
            result = deleter.delete_files(files_to_delete)

        # Verify results
        assert result.total_deleted == 1
        assert result.total_failed == 1

        # Display in CleanupView
        cleanup_view.set_result(result)
        assert cleanup_view.failed_section.visible is True
        assert cleanup_view.failed_count_text.value == "1"

    def test_workflow_empty_selection(self, temp_dir: Path) -> None:
        """Test workflow with no files selected.

        Given: Duplicate files detected
        When: User doesn't select any files
        Then: Delete button should be disabled
        """
        # Setup
        hasher = Hasher()
        detector = DuplicateDetector()
        results_view = ResultsView()

        # Create and detect duplicates
        content = b"Test content" * 100
        file1 = _create_test_file(temp_dir / "file1.txt", content)
        file2 = _create_test_file(temp_dir / "file2.txt", content)

        for f in [file1, file2]:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        duplicates = detector.find_duplicates([file1, file2])
        results_view.set_duplicate_groups(duplicates)

        # Verify no selection
        assert len(results_view.get_selected_files()) == 0
        assert results_view.delete_button.disabled is True

    def test_workflow_no_duplicates_found(self, temp_dir: Path) -> None:
        """Test workflow when no duplicates are found.

        Given: Directory with unique files only
        When: Scanning for duplicates
        Then: No duplicate groups are returned
        """
        # Setup
        hasher = Hasher()
        detector = DuplicateDetector()
        results_view = ResultsView()

        # Create unique files
        file1 = _create_test_file(temp_dir / "file1.txt", b"Content 1" * 100)
        file2 = _create_test_file(temp_dir / "file2.txt", b"Content 2" * 100)
        file3 = _create_test_file(temp_dir / "file3.txt", b"Content 3" * 100)

        for f in [file1, file2, file3]:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Detect duplicates
        duplicates = detector.find_duplicates([file1, file2, file3])

        # Verify no duplicates
        assert len(duplicates) == 0

        # Display in view
        results_view.set_duplicate_groups(duplicates)
        assert len(results_view.duplicate_groups) == 0
