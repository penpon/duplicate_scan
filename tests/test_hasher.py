"""Hasherサービスのテスト"""

import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
import time

import pytest

from src.models.file_meta import FileMeta
from src.services.hasher import Hasher


class TestHasher:
    """Hasherクラスのテスト"""

    def test_calculate_partial_hash_small_file(self):
        """小さなファイルの部分ハッシュ計算テスト"""
        # Given: 小さなテストファイル (8KB)
        test_content = b"A" * 8192  # 8KBの'A'
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            hasher = Hasher()

            # When: 部分ハッシュを計算
            result = hasher.calculate_partial_hash(temp_file_path)

            # Then: 正しいハッシュ値が返される
            # 最初の4KB + 最後の4KB (8KBファイルなので全体)
            expected_hash = hashlib.sha256(test_content).hexdigest()
            assert result == expected_hash
        finally:
            Path(temp_file_path).unlink()

    def test_calculate_partial_hashes_parallel_updates_filemeta(self):
        """複数ファイルの部分ハッシュがインプレースで更新されることを確認する。"""
        contents = [b"A" * 1024, b"B" * 2048, b"C" * 4096]
        temp_files: list[Path] = []
        files: list[FileMeta] = []

        for content in contents:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                path = Path(temp_file.name)
            temp_files.append(path)
            files.append(
                FileMeta(
                    path=str(path),
                    size=len(content),
                    modified_time=datetime.fromtimestamp(path.stat().st_mtime),
                )
            )

        try:
            hasher = Hasher()

            # When: 並列で部分ハッシュを計算
            hasher.calculate_partial_hashes_parallel(files, max_workers=4)

            # Then: FileMeta.partial_hash が設定され、単体計算と一致する
            for file_meta, path in zip(files, temp_files):
                assert file_meta.partial_hash is not None
                expected = hasher.calculate_partial_hash(str(path))
                assert file_meta.partial_hash == expected
        finally:
            for path in temp_files:
                path.unlink()

    def test_calculate_full_hashes_parallel_updates_filemeta(self):
        """複数ファイルの完全ハッシュがインプレースで更新されることを確認する。"""
        contents = [b"X" * 1024, b"Y" * 2048, b"Z" * 4096]
        temp_files: list[Path] = []
        files: list[FileMeta] = []

        for content in contents:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                path = Path(temp_file.name)
            temp_files.append(path)
            files.append(
                FileMeta(
                    path=str(path),
                    size=len(content),
                    modified_time=datetime.fromtimestamp(path.stat().st_mtime),
                )
            )

        try:
            hasher = Hasher()

            # When: 並列で完全ハッシュを計算
            hasher.calculate_full_hashes_parallel(files, max_workers=4)

            # Then: FileMeta.full_hash が設定され、単体計算と一致する
            for file_meta, path in zip(files, temp_files):
                assert file_meta.full_hash is not None
                expected = hasher.calculate_full_hash(str(path))
                assert file_meta.full_hash == expected
        finally:
            for path in temp_files:
                path.unlink()

    def test_calculate_partial_hashes_parallel_handles_errors(self, caplog):
        """存在しないファイルが含まれても他のファイルの処理は継続される。"""
        # Given: 2つの有効ファイルと1つの存在しないファイル
        temp_files: list[Path] = []
        files: list[FileMeta] = []
        content = b"E" * 1024

        for _ in range(2):
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                path = Path(temp_file.name)
            temp_files.append(path)
            files.append(
                FileMeta(
                    path=str(path),
                    size=len(content),
                    modified_time=datetime.fromtimestamp(path.stat().st_mtime),
                )
            )

        missing_path = "/path/to/nonexistent/file-for-parallel-test.txt"
        missing_meta = FileMeta(
            path=missing_path,
            size=0,
            modified_time=datetime.fromtimestamp(0),
        )
        files.append(missing_meta)

        try:
            hasher = Hasher()

            # When: 並列部分ハッシュ計算を実行（警告ログのみで処理継続）
            with caplog.at_level("WARNING"):
                hasher.calculate_partial_hashes_parallel(files, max_workers=4)

            # Then: 有効ファイルはハッシュが設定され、存在しないファイルは None のまま
            for file_meta, path in zip(files[:2], temp_files):
                assert file_meta.partial_hash is not None
                expected = hasher.calculate_partial_hash(str(path))
                assert file_meta.partial_hash == expected

            assert missing_meta.partial_hash is None

            # 警告ログが出力されていること
            messages = [record.getMessage() for record in caplog.records]
            assert any(
                "Failed to calculate partial hash for" in message
                and missing_path in message
                for message in messages
            )
        finally:
            for path in temp_files:
                path.unlink()

    def test_full_hashes_parallel_is_faster_than_sequential(self, monkeypatch):
        """完全ハッシュの並列計算がシーケンシャルより高速であることを緩やかに確認する。"""
        temp_files: list[Path] = []
        files: list[FileMeta] = []

        for i in range(8):
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                content = f"file-{i}".encode("utf-8") * 2048
                temp_file.write(content)
                path = Path(temp_file.name)
            temp_files.append(path)
            files.append(
                FileMeta(
                    path=str(path),
                    size=path.stat().st_size,
                    modified_time=datetime.fromtimestamp(path.stat().st_mtime),
                )
            )

        hasher = Hasher()
        original_full_hash = hasher.calculate_full_hash

        def slow_full_hash(path: str) -> str:
            time.sleep(0.02)
            return original_full_hash(path)

        monkeypatch.setattr(hasher, "calculate_full_hash", slow_full_hash)

        try:
            # シーケンシャル計測
            start_seq = time.monotonic()
            for file_meta in files:
                file_meta.full_hash = hasher.calculate_full_hash(file_meta.path)
            seq_duration = time.monotonic() - start_seq

            # 並列計測
            for file_meta in files:
                file_meta.full_hash = None

            start_par = time.monotonic()
            hasher.calculate_full_hashes_parallel(files, max_workers=4)
            par_duration = time.monotonic() - start_par

            # 並列の方が速いことを確認（マージンは緩め）
            assert par_duration < seq_duration
        finally:
            for path in temp_files:
                path.unlink()

    def test_calculate_partial_hash_large_file(self):
        """大きなファイルの部分ハッシュ計算テスト"""
        # Given: 大きなテストファイル (16KB)
        first_4kb = b"B" * 4096
        middle_8kb = b"C" * 8192
        last_4kb = b"D" * 4096
        test_content = first_4kb + middle_8kb + last_4kb

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            hasher = Hasher()

            # When: 部分ハッシュを計算
            result = hasher.calculate_partial_hash(temp_file_path)

            # Then: 最初と最後の4KBを結合したハッシュ値が返される
            expected_content = first_4kb + last_4kb
            expected_hash = hashlib.sha256(expected_content).hexdigest()
            assert result == expected_hash
        finally:
            Path(temp_file_path).unlink()

    def test_calculate_partial_hash_exact_4kb(self):
        """ちょうど4KBのファイルの部分ハッシュ計算テスト"""
        # Given: ちょうど4KBのファイル
        test_content = b"E" * 4096
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            hasher = Hasher()

            # When: 部分ハッシュを計算
            result = hasher.calculate_partial_hash(temp_file_path)

            # Then: ファイル全体のハッシュ値が返される
            expected_hash = hashlib.sha256(test_content).hexdigest()
            assert result == expected_hash
        finally:
            Path(temp_file_path).unlink()

    def test_calculate_partial_hash_less_than_4kb(self):
        """4KB未満のファイルの部分ハッシュ計算テスト"""
        # Given: 2KBのファイル
        test_content = b"F" * 2048
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            hasher = Hasher()

            # When: 部分ハッシュを計算
            result = hasher.calculate_partial_hash(temp_file_path)

            # Then: ファイル全体のハッシュ値が返される
            expected_hash = hashlib.sha256(test_content).hexdigest()
            assert result == expected_hash
        finally:
            Path(temp_file_path).unlink()

    def test_calculate_full_hash(self):
        """完全ハッシュ計算テスト"""
        # Given: テストファイル
        test_content = b"Test content for full hash calculation"
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            hasher = Hasher()

            # When: 完全ハッシュを計算
            result = hasher.calculate_full_hash(temp_file_path)

            # Then: 正しいハッシュ値が返される
            expected_hash = hashlib.sha256(test_content).hexdigest()
            assert result == expected_hash
        finally:
            Path(temp_file_path).unlink()

    def test_calculate_full_hash_empty_file(self):
        """空ファイルの完全ハッシュ計算テスト"""
        # Given: 空のファイル
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            hasher = Hasher()

            # When: 完全ハッシュを計算
            result = hasher.calculate_full_hash(temp_file_path)

            # Then: 空のコンテンツのハッシュ値が返される
            expected_hash = hashlib.sha256(b"").hexdigest()
            assert result == expected_hash
        finally:
            Path(temp_file_path).unlink()

    def test_hash_nonexistent_file(self):
        """存在しないファイルのハッシュ計算テスト"""
        # Given: 存在しないファイルパス
        nonexistent_path = "/path/to/nonexistent/file.txt"
        hasher = Hasher()

        # When & Then: FileNotFoundErrorが発生すること
        with pytest.raises(FileNotFoundError):
            hasher.calculate_partial_hash(nonexistent_path)

        with pytest.raises(FileNotFoundError):
            hasher.calculate_full_hash(nonexistent_path)

    def test_hash_file_meta_integration(self):
        """FileMetaとの連携テスト"""
        # Given: FileMetaオブジェクトとテストファイル
        test_content = b"Integration test content"
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        file_meta = FileMeta(
            path=temp_file_path,
            size=len(test_content),
            modified_time=datetime.fromtimestamp(Path(temp_file_path).stat().st_mtime),
            partial_hash="",
            full_hash="",
        )

        try:
            hasher = Hasher()

            # When: FileMetaからハッシュを計算
            partial_hash = hasher.calculate_partial_hash(str(file_meta.path))
            full_hash = hasher.calculate_full_hash(str(file_meta.path))

            # Then: ハッシュ値が正しく計算される
            expected_partial = hashlib.sha256(
                test_content
            ).hexdigest()  # 4KB未満なので全体
            expected_full = hashlib.sha256(test_content).hexdigest()

            assert partial_hash == expected_partial
            assert full_hash == expected_full
        finally:
            Path(temp_file_path).unlink()
