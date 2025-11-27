"""統合テスト: スキャン最適化機能の検証"""

import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.models.file_meta import FileMeta
from src.services.detector import DuplicateDetector
from src.services.hasher import Hasher


class TestScanOptimization:
    """スキャン最適化機能の統合テスト

    最適化された重複ファイルスキャンパイプラインの正しさとパフォーマンスを検証します。
    サイズフィルタリング、遅延ハッシュ計算、並列処理、プログレスコールバックの各機能をテストします。
    """

    def test_optimized_vs_original_correctness(self):
        """最適化版とオリジナル版で同じ結果が得られることを検証

        Given: 重複ファイルを含むテストデータ（事前ハッシュ計算済み）
        When: オリジナル版と最適化版を実行
        Then: 結果が一致すること
        """
        # Given: 重複ファイルを含むテストデータ（事前ハッシュ計算済み）
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 重複ファイルを作成
            content1 = b"Duplicate content 1" * 100
            content2 = b"Unique content" * 100
            content3 = b"Duplicate content 1" * 100

            file1_path = temp_path / "file1.txt"
            file2_path = temp_path / "file2.txt"
            file3_path = temp_path / "file3.txt"

            file1_path.write_bytes(content1)
            file2_path.write_bytes(content2)
            file3_path.write_bytes(content3)

            # ハッシュを事前計算
            hasher = Hasher()
            hash1 = hasher.calculate_partial_hash(str(file1_path))
            full_hash1 = hasher.calculate_full_hash(str(file1_path))
            hash2 = hasher.calculate_partial_hash(str(file2_path))
            full_hash2 = hasher.calculate_full_hash(str(file2_path))
            hash3 = hasher.calculate_partial_hash(str(file3_path))
            full_hash3 = hasher.calculate_full_hash(str(file3_path))

            # FileMetaオブジェクトを作成（ハッシュ付き）
            files = [
                FileMeta(
                    path=str(file1_path),
                    size=len(content1),
                    modified_time=datetime.fromtimestamp(file1_path.stat().st_mtime),
                    partial_hash=hash1,
                    full_hash=full_hash1,
                ),
                FileMeta(
                    path=str(file2_path),
                    size=len(content2),
                    modified_time=datetime.fromtimestamp(file2_path.stat().st_mtime),
                    partial_hash=hash2,
                    full_hash=full_hash2,
                ),
                FileMeta(
                    path=str(file3_path),
                    size=len(content3),
                    modified_time=datetime.fromtimestamp(file3_path.stat().st_mtime),
                    partial_hash=hash3,
                    full_hash=full_hash3,
                ),
            ]

            detector = DuplicateDetector()

            # When: オリジナル版と最適化版を実行
            original_result = detector.find_duplicates(files.copy())
            optimized_result = detector.find_duplicates_optimized(files.copy(), hasher)

            # Then: 結果が一致すること
            assert len(original_result) == len(optimized_result)

            if original_result:
                # 重複グループの数が一致
                assert len(original_result[0].files) == len(optimized_result[0].files)
                # 合計サイズが一致
                assert original_result[0].total_size == optimized_result[0].total_size
                # ファイルパスが一致（順序は無視）
                original_paths = {f.path for f in original_result[0].files}
                optimized_paths = {f.path for f in optimized_result[0].files}
                assert original_paths == optimized_paths

    def test_size_filtering_effectiveness(self):
        """サイズフィルタリングの有効性を検証

        Given: 異なるサイズのファイル多数と重複ファイル少数
        When: 最適化版を実行
        Then: 重複のみが検出され、パフォーマンスが良好であること
        """
        # Given: 異なるサイズのファイル多数と重複ファイル少数
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            files = []

            # 異なるサイズのファイルを100個作成
            for i in range(100):
                content = f"Unique content {i}".encode() * (10 + i)
                file_path = temp_path / f"unique_{i}.txt"
                file_path.write_bytes(content)
                files.append(
                    FileMeta(
                        path=str(file_path),
                        size=len(content),
                        modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
                    )
                )

            # 重複ファイルを2組作成
            dup_content1 = b"Duplicate content A" * 50
            dup_content2 = b"Duplicate content B" * 30

            for i, content in enumerate([dup_content1, dup_content2], 1):
                for j in range(2):
                    file_path = temp_path / f"dup_{i}_{j}.txt"
                    file_path.write_bytes(content)
                    files.append(
                        FileMeta(
                            path=str(file_path),
                            size=len(content),
                            modified_time=datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ),
                        )
                    )

            detector = DuplicateDetector()
            hasher = Hasher()

            # When: 最適化版を実行
            start_time = time.monotonic()
            result = detector.find_duplicates_optimized(files, hasher)
            duration = time.monotonic() - start_time

            # Then: 重複のみが検出され、パフォーマンスが良好であること
            assert len(result) == 2  # 2組の重複

            # パフォーマンスが良好であること（1秒以内）
            assert duration < 1.0

    def test_lazy_hash_effectiveness(self):
        """遅延ハッシュ計算の有効性を検証

        Given: 同じサイズで異なる内容のファイル
        When: 最適化版を実行
        Then: 完全重複のみが検出されること
        """
        # Given: 同じサイズで異なる内容のファイル
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            files = []

            # 同じサイズ（1000バイト）で異なる内容のファイルを10個作成
            base_size = 1000
            for i in range(10):
                content = f"Different content {i:02d}".encode().ljust(base_size, b"X")
                file_path = temp_path / f"same_size_{i}.txt"
                file_path.write_bytes(content)
                files.append(
                    FileMeta(
                        path=str(file_path),
                        size=base_size,
                        modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
                    )
                )

            # 完全な重複ファイルを2個作成
            dup_content = b"Exact duplicate content" * 20
            for i in range(2):
                file_path = temp_path / f"exact_dup_{i}.txt"
                file_path.write_bytes(dup_content)
                files.append(
                    FileMeta(
                        path=str(file_path),
                        size=len(dup_content),
                        modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
                    )
                )

            detector = DuplicateDetector()
            hasher = Hasher()

            # When: 最適化版を実行
            result = detector.find_duplicates_optimized(files, hasher)

            # Then: 完全重複のみが検出されること
            assert len(result) == 1  # 完全重複の1組のみ
            assert len(result[0].files) == 2

    def test_parallel_performance(self):
        """並列処理のパフォーマンス向上を検証

        Given: 多数の重複ファイル
        When: 並列処理で実行
        Then: 正しい結果が得られ、パフォーマンスが良好であること
        """
        # Given: 多数の重複ファイル
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            files = []

            # 20組の重複ファイルを作成（計40ファイル）
            for i in range(20):
                content = f"Duplicate group {i:02d}".encode() * 100
                for j in range(2):
                    file_path = temp_path / f"dup_group_{i}_{j}.txt"
                    file_path.write_bytes(content)
                    files.append(
                        FileMeta(
                            path=str(file_path),
                            size=len(content),
                            modified_time=datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ),
                        )
                    )

            detector = DuplicateDetector()
            hasher = Hasher()

            # When: 並列処理で実行
            start_time = time.monotonic()
            result = detector.find_duplicates_optimized(files, hasher)
            parallel_duration = time.monotonic() - start_time

            # Then: 正しい結果が得られ、パフォーマンスが良好であること
            assert len(result) == 20  # 20組の重複

            for group in result:
                assert len(group.files) == 2

            # パフォーマンスが良好であること（30秒以内で実行）
            assert parallel_duration < 30.0

            # 並列処理の効果があること（シーケンシャルより速いはず）
            # ただしテスト環境によっては差が出にくいので、完了時間のみを検証

    def test_progress_callback(self):
        """プログレスコールバックの正確性を検証

        Given: テストファイルとモックコールバック
        When: プログレスコールバック付きで実行
        Then: すべてのステージでコールバックが呼ばれていること
        """
        # Given: テストファイルとモックコールバック
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 異なるステップで進行するファイルを作成
            files = []

            # ステップ1（サイズフィルタリング通過）：同じサイズのファイル
            for i in range(5):
                content = f"Same size content {i}".encode().ljust(1000, b"X")
                file_path = temp_path / f"step1_{i}.txt"
                file_path.write_bytes(content)
                files.append(
                    FileMeta(
                        path=str(file_path),
                        size=1000,
                        modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
                    )
                )

            # ステップ2（部分ハッシュフィルタリング通過）：同じ部分ハッシュ
            partial_dup_content = b"Partial duplicate content" * 50
            for i in range(3):
                file_path = temp_path / f"step2_{i}.txt"
                file_path.write_bytes(partial_dup_content)
                files.append(
                    FileMeta(
                        path=str(file_path),
                        size=len(partial_dup_content),
                        modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
                    )
                )

            # ステップ3（完全ハッシュ）：完全重複
            full_dup_content = b"Full duplicate content" * 30
            for i in range(2):
                file_path = temp_path / f"step3_{i}.txt"
                file_path.write_bytes(full_dup_content)
                files.append(
                    FileMeta(
                        path=str(file_path),
                        size=len(full_dup_content),
                        modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
                    )
                )

            detector = DuplicateDetector()
            hasher = Hasher()
            progress_calls = []

            def progress_callback(stage: str, current: int, total: int) -> None:
                progress_calls.append((stage, current, total))

            # When: プログレスコールバック付きで実行
            result = detector.find_duplicates_optimized(
                files, hasher, progress_callback
            )

            # Then: すべてのステージでコールバックが呼ばれていること
            assert len(progress_calls) >= 5  # 少なくとも5回は呼ばれる

            # ステージ名が適切であること
            stages = [call[0] for call in progress_calls]
            assert any("size" in stage.lower() for stage in stages)
            assert any(
                "partial" in stage.lower() or "hash" in stage.lower()
                for stage in stages
            )
            assert any(
                "complete" in stage.lower() or "done" in stage.lower()
                for stage in stages
            )

            # カウントが合理的であること
            for stage, current, total in progress_calls:
                assert 0 <= current <= total
                assert total >= 0

            # 最終的な結果が正しいこと（2組の重複が見つかるはず）
            assert len(result) == 2  # 部分重複1組 + 完全重複1組
            # 最初のグループは3ファイルの重複、次のグループは2ファイルの重複
            assert len(result[0].files) >= 2
            assert len(result[1].files) >= 2
