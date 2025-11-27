"""ProgressViewのテスト"""

from unittest.mock import Mock
import flet as ft

from src.ui.progress_view import ProgressView


class TestProgressView:
    """ProgressViewのテストクラス"""

    def test_init(self) -> None:
        """初期化のテスト"""
        # Given: ProgressViewを新規作成する
        progress_view = ProgressView()

        # When: 初期状態を確認する

        # Then: デフォルト値が設定されている
        assert progress_view.page is None
        assert progress_view.stage_label.value == "Preparing..."
        assert progress_view.progress_bar.value == 0.0
        assert progress_view.count_label.value == "0/0"

    def test_build(self) -> None:
        """UI構築のテスト"""
        # Given: ProgressViewを用意する
        progress_view = ProgressView()

        # When: UIを構築する
        ui = progress_view.build()

        # Then: 期待するコンポーネントが含まれる
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
        # Given: ページを持つProgressViewを準備
        progress_view = ProgressView()
        mock_page = Mock()
        progress_view.page = mock_page

        # When: 進捗を更新する
        progress_view.update_progress("Scanning files", 25, 100)

        # Then: 表示が更新される
        assert progress_view.stage_label.value == "Scanning files"
        assert progress_view.progress_bar.value == 0.25
        assert progress_view.count_label.value == "25/100"
        mock_page.update.assert_called_once()

    def test_update_progress_zero_total(self) -> None:
        """totalが0の場合の進捗更新テスト"""
        # Given: totalが0のケース
        progress_view = ProgressView()
        mock_page = Mock()
        progress_view.page = mock_page

        # When: 進捗を更新する
        progress_view.update_progress("Processing", 0, 0)

        # Then: プログレス値は0のまま
        assert progress_view.stage_label.value == "Processing"
        assert progress_view.progress_bar.value == 0.0
        assert progress_view.count_label.value == "0/0"
        mock_page.update.assert_called_once()

    def test_update_progress_clamps_value(self) -> None:
        """currentがtotalを超えても値がクランプされるテスト"""
        # Given: current > total の条件
        progress_view = ProgressView()
        mock_page = Mock()
        progress_view.page = mock_page

        # When: 進捗を更新する
        progress_view.update_progress("Processing", 150, 100)

        # Then: 値が1.0にクランプされる
        assert progress_view.progress_bar.value == 1.0
        assert progress_view.count_label.value == "150/100"
        mock_page.update.assert_called_once()

    def test_set_indeterminate(self) -> None:
        """不定モード設定のテスト"""
        # Given: ProgressViewとページ
        progress_view = ProgressView()
        mock_page = Mock()
        progress_view.page = mock_page

        # When: 不定モードを設定する
        progress_view.set_indeterminate("Initializing...")

        # Then: インデターミネート表示になる
        assert progress_view.stage_label.value == "Initializing..."
        # Fletはvalue=Noneを内部的に空文字として保持するため、属性を直接確認する
        assert progress_view.progress_bar._get_attr("value", data_type="string") == ""
        assert progress_view.count_label.value == "Processing..."
        mock_page.update.assert_called_once()

    def test_set_cancel_callback(self) -> None:
        """キャンセルコールバック設定のテスト"""
        # Given: モックコールバックを設定
        progress_view = ProgressView()
        mock_callback = Mock()

        # When: コールバックを登録し、ボタンを押す
        progress_view.set_cancel_callback(mock_callback)

        progress_view._on_cancel_clicked(None)

        # Then: コールバックが呼ばれる
        mock_callback.assert_called_once()

    def test_reset(self) -> None:
        """リセットのテスト"""
        # Given: 一度進捗を更新した状態
        progress_view = ProgressView()
        mock_page = Mock()
        progress_view.page = mock_page

        # When: リセットを呼び出す
        progress_view.update_progress("Test", 50, 100)
        progress_view.reset()

        # Then: 初期値に戻る
        assert progress_view.stage_label.value == "Preparing..."
        assert progress_view.progress_bar.value == 0.0
        assert progress_view.count_label.value == "0/0"
        mock_page.update.assert_called()

    def test_cancel_callback_without_page_update(self) -> None:
        """ページ更新なしでキャンセルコールバックが呼ばれるテスト"""
        # Given: コールバックのみ設定
        progress_view = ProgressView()
        mock_callback = Mock()

        # When: コールバックを呼び出す
        progress_view.set_cancel_callback(mock_callback)
        progress_view._on_cancel_clicked(None)

        # Then: コールバックのみが呼ばれる
        mock_callback.assert_called_once()
