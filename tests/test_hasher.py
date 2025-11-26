"""Hasherサービスのテスト"""

import hashlib
import tempfile
from pathlib import Path

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

        from datetime import datetime

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
