"""ProgressViewのテスト"""

from unittest.mock import Mock
import flet as ft

from src.ui.progress_view import ProgressView


class TestProgressView:
    """ProgressViewのテストクラス"""

    def test_init(self) -> None:
        """初期化のテスト"""
        progress_view = ProgressView()

        assert progress_view.page is None
        assert progress_view.stage_label.value == "Preparing..."
        assert progress_view.progress_bar.value == 0.0
        assert progress_view.count_label.value == "0/0"

    def test_build(self) -> None:
        """UI構築のテスト"""
        progress_view = ProgressView()
        ui = progress_view.build()

        assert isinstance(ui, ft.Column)
        assert (
            len(ui.controls) == 6
        )  # title, divider, stage_label, progress_bar_container, count_label, cancel_button_container

        # コンポーネントの確認
        assert isinstance(progress_view.stage_label, ft.Text)
        assert isinstance(progress_view.progress_bar, ft.ProgressBar)
        assert isinstance(progress_view.count_label, ft.Text)
        assert isinstance(progress_view.cancel_button, ft.ElevatedButton)

    def test_update_progress(self) -> None:
        """進捗更新のテスト"""
        progress_view = ProgressView()
        mock_page = Mock()
        progress_view.page = mock_page

        # 進捗更新
        progress_view.update_progress("Scanning files", 25, 100)

        assert progress_view.stage_label.value == "Scanning files"
        assert progress_view.progress_bar.value == 0.25
        assert progress_view.count_label.value == "25/100"
        mock_page.update.assert_called_once()

    def test_update_progress_zero_total(self) -> None:
        """totalが0の場合の進捗更新テスト"""
        progress_view = ProgressView()
        mock_page = Mock()
        progress_view.page = mock_page

        # totalが0の場合
        progress_view.update_progress("Processing", 0, 0)

        assert progress_view.stage_label.value == "Processing"
        assert progress_view.progress_bar.value == 0.0
        assert progress_view.count_label.value == "0/0"
        mock_page.update.assert_called_once()

    def test_set_indeterminate(self) -> None:
        """不定モード設定のテスト"""
        progress_view = ProgressView()
        mock_page = Mock()
        progress_view.page = mock_page

        # 不定モードに設定
        progress_view.set_indeterminate("Initializing...")

        assert progress_view.stage_label.value == "Initializing..."
        # Fletはvalue=Noneを内部的に空文字として保持するため、属性を直接確認する
        assert progress_view.progress_bar._get_attr("value", data_type="string") == ""
        assert progress_view.count_label.value == "Processing..."
        mock_page.update.assert_called_once()

    def test_set_cancel_callback(self) -> None:
        """キャンセルコールバック設定のテスト"""
        progress_view = ProgressView()
        mock_callback = Mock()

        progress_view.set_cancel_callback(mock_callback)

        # キャンセルボタンをクリック
        progress_view._on_cancel_clicked(None)

        mock_callback.assert_called_once()

    def test_reset(self) -> None:
        """リセットのテスト"""
        progress_view = ProgressView()
        mock_page = Mock()
        progress_view.page = mock_page

        # 進捗を更新してからリセット
        progress_view.update_progress("Test", 50, 100)
        progress_view.reset()

        assert progress_view.stage_label.value == "Preparing..."
        assert progress_view.progress_bar.value == 0.0
        assert progress_view.count_label.value == "0/0"
        mock_page.update.assert_called()

    def test_cancel_callback_without_page_update(self) -> None:
        """ページ更新なしでキャンセルコールバックが呼ばれるテスト"""
        progress_view = ProgressView()
        mock_callback = Mock()

        progress_view.set_cancel_callback(mock_callback)
        progress_view._on_cancel_clicked(None)

        # コールバックが呼ばれるがページ更新はされない
        mock_callback.assert_called_once()
