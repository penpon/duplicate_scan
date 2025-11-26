"""
ResultsViewのテスト
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

import flet as ft

from src.models.file_meta import FileMeta
from src.models.duplicate_group import DuplicateGroup
from src.ui.results_view import ResultsView


class TestResultsView:
    """ResultsViewのテストクラス"""

    @pytest.fixture
    def sample_files(self) -> list[FileMeta]:
        """テスト用のサンプルファイルデータ"""
        return [
            FileMeta(
                path="/path/to/file1.jpg",
                size=1024,
                modified_time=datetime(2024, 1, 1, 10, 0, 0),
                full_hash="hash123",
            ),
            FileMeta(
                path="/path/to/file2.jpg",
                size=1024,
                modified_time=datetime(2024, 1, 2, 11, 0, 0),
                full_hash="hash123",
            ),
            FileMeta(
                path="/path/to/file3.png",
                size=2048,
                modified_time=datetime(2024, 1, 3, 12, 0, 0),
                full_hash="hash456",
            ),
        ]

    @pytest.fixture
    def sample_duplicate_groups(self, sample_files) -> list[DuplicateGroup]:
        """テスト用のサンプル重複グループデータ"""
        return [
            DuplicateGroup(files=sample_files[:2]),  # file1.jpgとfile2.jpgが重複
            DuplicateGroup(files=[sample_files[2]]),  # file3.pngのみ（重複なし）
        ]

    def test_init(self) -> None:
        """
        Given: なし
        When: ResultsViewを初期化する
        Then: 正しく初期化されること
        """
        # When
        view = ResultsView()

        # Then
        assert view.duplicate_groups == []
        assert view.selected_files == set()
        assert view.page is None
        assert view.delete_button is not None
        assert view.delete_button.disabled is True

    def test_build_ui(self) -> None:
        """
        Given: 初期化されたResultsView
        When: UIを構築する
        Then: 正しいUIコンポーネントが含まれること
        """
        # Given
        view = ResultsView()

        # When
        ui = view.build()

        # Then
        assert isinstance(ui, ft.Column)
        assert len(ui.controls) >= 3  # Header, groups list, delete button

        # ヘッダーの確認
        header_text = None
        for control in ui.controls:
            if isinstance(control, ft.Text) and "Results" in str(control.value):
                header_text = control
                break
        assert header_text is not None

    def test_set_duplicate_groups(self, sample_duplicate_groups) -> None:
        """
        Given: ResultsViewと重複グループリスト
        When: 重複グループを設定する
        Then: 重複グループが正しく設定され、UIが更新されること
        """
        # Given
        view = ResultsView()
        view.page = Mock()

        # When
        view.set_duplicate_groups(sample_duplicate_groups)

        # Then
        assert view.duplicate_groups == sample_duplicate_groups
        assert view.page.update.called

    def test_toggle_file_selection(self, sample_duplicate_groups) -> None:
        """
        Given: ResultsViewと重複グループ
        When: ファイルの選択状態を切り替える
        Then: 選択状態が正しく変更されること
        """
        # Given
        view = ResultsView()
        view.set_duplicate_groups(sample_duplicate_groups)
        target_file = sample_duplicate_groups[0].files[0]

        # When - 選択
        view.toggle_file_selection(target_file)

        # Then - 選択されていること
        assert target_file in view.selected_files

        # When - 選択解除
        view.toggle_file_selection(target_file)

        # Then - 選択解除されていること
        assert target_file not in view.selected_files

    def test_toggle_file_selection_updates_delete_button(
        self, sample_duplicate_groups
    ) -> None:
        """
        Given: ResultsViewと重複グループ、モックページ
        When: ファイルを選択する
        Then: 削除ボタンの状態が更新されること
        """
        # Given
        view = ResultsView()
        view.page = Mock()
        view.set_duplicate_groups(sample_duplicate_groups)
        target_file = sample_duplicate_groups[0].files[0]

        # When
        view.toggle_file_selection(target_file)

        # Then
        assert view.delete_button.disabled is False
        assert view.page.update.called

    def test_get_selected_files(self, sample_duplicate_groups) -> None:
        """
        Given: ResultsViewと重複グループ
        When: ファイルを選択して取得する
        Then: 選択されたファイルリストが正しく返されること
        """
        # Given
        view = ResultsView()
        view.set_duplicate_groups(sample_duplicate_groups)
        target_file1 = sample_duplicate_groups[0].files[0]
        target_file2 = sample_duplicate_groups[0].files[1]

        # When
        view.toggle_file_selection(target_file1)
        view.toggle_file_selection(target_file2)
        selected = view.get_selected_files()

        # Then
        assert len(selected) == 2
        assert target_file1 in selected
        assert target_file2 in selected

    def test_clear_selection(self, sample_duplicate_groups) -> None:
        """
        Given: ResultsViewと選択されたファイル
        When: 選択をクリアする
        Then: すべての選択が解除されること
        """
        # Given
        view = ResultsView()
        view.page = Mock()
        view.set_duplicate_groups(sample_duplicate_groups)
        target_file = sample_duplicate_groups[0].files[0]
        view.toggle_file_selection(target_file)

        # When
        view.clear_selection()

        # Then
        assert len(view.selected_files) == 0
        assert view.delete_button.disabled is True
        assert view.page.update.called

    def test_on_delete_clicked_with_callback(self, sample_duplicate_groups) -> None:
        """
        Given: ResultsViewと選択されたファイル、削除コールバック
        When: 削除ボタンがクリックされる
        Then: コールバックが選択されたファイルで呼ばれること
        """
        # Given
        view = ResultsView()
        view.set_duplicate_groups(sample_duplicate_groups)
        target_file = sample_duplicate_groups[0].files[0]
        view.toggle_file_selection(target_file)

        delete_callback = Mock()
        view.set_delete_callback(delete_callback)

        # When
        view._on_delete_clicked(None)

        # Then
        delete_callback.assert_called_once_with([target_file])

    def test_on_delete_clicked_without_selection(self) -> None:
        """
        Given: ResultsView（選択なし）
        When: 削除ボタンがクリックされる
        Then: コールバックが呼ばれないこと
        """
        # Given
        view = ResultsView()
        delete_callback = Mock()
        view.set_delete_callback(delete_callback)

        # When
        view._on_delete_clicked(None)

        # Then
        delete_callback.assert_not_called()

    def test_create_group_item_ui(self, sample_duplicate_groups) -> None:
        """
        Given: ResultsViewと重複グループ
        When: グループアイテムUIを作成する
        Then: 正しいUIコンポーネントが作成されること
        """
        # Given
        view = ResultsView()
        group = sample_duplicate_groups[0]  # 重複のあるグループ

        # When
        group_ui = view._create_group_item(group)

        # Then
        assert isinstance(group_ui, ft.Card)
        # グループ内のファイル数が表示されていることを確認
        # 各ファイルにチェックボックスがあることを確認

    def test_create_file_item_ui(self, sample_files) -> None:
        """
        Given: ResultsViewとファイル
        When: ファイルアイテムUIを作成する
        Then: 正しいUIコンポーネントが作成されること
        """
        # Given
        view = ResultsView()
        file = sample_files[0]

        # When
        file_ui = view._create_file_item(file)

        # Then
        assert isinstance(file_ui, ft.ListTile)
        # チェックボックス、ファイル名、サイズが表示されていることを確認

    def test_format_file_size(self) -> None:
        """
        Given: ResultsView
        When: ファイルサイズをフォーマットする
        Then: 正しくフォーマットされること
        """
        # Given
        view = ResultsView()

        # When & Then
        assert view._format_file_size(1024) == "1.0 KB"
        assert view._format_file_size(1024 * 1024) == "1.0 MB"
        assert view._format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert view._format_file_size(500) == "500 B"

    def test_set_delete_callback(self) -> None:
        """
        Given: ResultsView
        When: 削除コールバックを設定する
        Then: コールバックが正しく設定されること
        """
        # Given
        view = ResultsView()
        callback = Mock()

        # When
        view.set_delete_callback(callback)

        # Then
        assert view.delete_callback == callback
