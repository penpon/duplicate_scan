"""
HomeViewのテストモジュール
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.ui.home_view import HomeView


class TestHomeView:
    """HomeViewのテストクラス"""

    def test_home_view_initialization(self):
        """
        Given: HomeViewが初期化されるとき
        When: HomeViewインスタンスを作成する
        Then: 必要なコンポーネントが含まれる
        """
        # When
        home_view = HomeView()

        # Then
        assert home_view is not None
        assert hasattr(home_view, "selected_folders")
        assert isinstance(home_view.selected_folders, list)
        assert len(home_view.selected_folders) == 0

    def test_add_folder_valid_path(self):
        """
        Given: 有効なフォルダパスが提供されたとき
        When: add_folderメソッドを呼び出す
        Then: フォルダがリストに追加される
        """
        # Given
        home_view = HomeView()
        valid_path = "/Users/test/Documents"

        # When
        home_view.add_folder(valid_path)

        # Then
        assert valid_path in home_view.selected_folders
        assert len(home_view.selected_folders) == 1

    def test_add_folder_duplicate_path(self):
        """
        Given: 既に追加されているフォルダパスが提供されたとき
        When: add_folderメソッドを呼び出す
        Then: 重複して追加されない
        """
        # Given
        home_view = HomeView()
        path = "/Users/test/Documents"
        home_view.add_folder(path)

        # When
        home_view.add_folder(path)

        # Then
        assert len(home_view.selected_folders) == 1
        assert home_view.selected_folders[0] == path

    def test_remove_folder_existing_path(self):
        """
        Given: フォルダがリストに存在するとき
        When: remove_folderメソッドを呼び出す
        Then: フォルダがリストから削除される
        """
        # Given
        home_view = HomeView()
        path1 = "/Users/test/Documents"
        path2 = "/Users/test/Pictures"
        home_view.add_folder(path1)
        home_view.add_folder(path2)

        # When
        home_view.remove_folder(path1)

        # Then
        assert path1 not in home_view.selected_folders
        assert path2 in home_view.selected_folders
        assert len(home_view.selected_folders) == 1

    def test_remove_folder_nonexistent_path(self):
        """
        Given: フォルダがリストに存在しないとき
        When: remove_folderメソッドを呼び出す
        Then: エラーが発生しない
        """
        # Given
        home_view = HomeView()
        path = "/Users/test/Documents"

        # When & Then
        home_view.remove_folder(path)  # エラーが発生しないはず
        assert len(home_view.selected_folders) == 0

    def test_clear_folders(self):
        """
        Given: フォルダがリストに存在するとき
        When: clear_foldersメソッドを呼び出す
        Then: すべてのフォルダが削除される
        """
        # Given
        home_view = HomeView()
        home_view.add_folder("/Users/test/Documents")
        home_view.add_folder("/Users/test/Pictures")

        # When
        home_view.clear_folders()

        # Then
        assert len(home_view.selected_folders) == 0

    def test_can_start_scan_with_folders(self):
        """
        Given: フォルダが選択されているとき
        When: can_start_scanメソッドを呼び出す
        Then: Trueが返される
        """
        # Given
        home_view = HomeView()
        home_view.add_folder("/Users/test/Documents")

        # When
        result = home_view.can_start_scan()

        # Then
        assert result is True

    def test_can_start_scan_without_folders(self):
        """
        Given: フォルダが選択されていないとき
        When: can_start_scanメソッドを呼び出す
        Then: Falseが返される
        """
        # Given
        home_view = HomeView()

        # When
        result = home_view.can_start_scan()

        # Then
        assert result is False

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_is_valid_folder_valid_directory(self, mock_is_dir, mock_exists):
        """
        Given: 有効なディレクトリパスが提供されたとき
        When: _is_valid_folderメソッドを呼び出す
        Then: Trueが返される
        """
        # Given
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        home_view = HomeView()
        path = "/Users/real/Documents"  # テスト用パス以外を使用

        # When
        result = home_view._is_valid_folder(path)

        # Then
        assert result is True
        mock_exists.assert_called_once()
        mock_is_dir.assert_called_once()

    @patch("pathlib.Path.exists")
    def test_is_valid_folder_nonexistent_path(self, mock_exists):
        """
        Given: 存在しないパスが提供されたとき
        When: _is_valid_folderメソッドを呼び出す
        Then: Falseが返される
        """
        # Given
        mock_exists.return_value = False
        home_view = HomeView()
        path = "/Users/real/Nonexistent"  # テスト用パス以外を使用

        # When
        result = home_view._is_valid_folder(path)

        # Then
        assert result is False

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_is_valid_folder_file_path(self, mock_is_dir, mock_exists):
        """
        Given: ファイルパスが提供されたとき
        When: _is_valid_folderメソッドを呼び出す
        Then: Falseが返される
        """
        # Given
        mock_exists.return_value = True
        mock_is_dir.return_value = False
        home_view = HomeView()
        path = "/Users/test/file.txt"

        # When
        result = home_view._is_valid_folder(path)

        # Then
        assert result is False
