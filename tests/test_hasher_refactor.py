"""Hasherサービスのリファクタリング機能テスト"""

import hashlib
import tempfile
from pathlib import Path

import pytest

from src.services.hasher import Hasher


class TestHasherRefactor:
    """Hasherクラスのリファクタリング機能テスト"""

    def test_custom_chunk_size(self):
        """カスタムチャンクサイズのテスト"""
        # Given: 2KBチャンクサイズのHasher
        hasher = Hasher(chunk_size=2048)
        assert hasher.chunk_size == 2048

    def test_custom_hash_algorithm(self):
        """カスタムハッシュアルゴリズムのテスト"""
        # Given: MD5アルゴリズムのHasher
        hasher = Hasher(hash_algorithm="md5")
        assert hasher.hash_algorithm == "md5"

    def test_md5_hash_calculation(self):
        """MD5ハッシュ計算のテスト"""
        # Given: MD5アルゴリズムとテストファイル
        test_content = b"Test content for MD5"
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            hasher = Hasher(hash_algorithm="md5")

            # When: MD5ハッシュを計算
            result = hasher.calculate_full_hash(temp_file_path)

            # Then: 正しいMD5ハッシュ値が返される
            expected_hash = hashlib.md5(test_content).hexdigest()  # noqa: S324
            assert result == expected_hash
        finally:
            Path(temp_file_path).unlink()

    def test_partial_hash_with_custom_chunk_size(self):
        """カスタムチャンクサイズでの部分ハッシュ計算テスト"""
        # Given: 2KBチャンクサイズと6KBファイル
        hasher = Hasher(chunk_size=2048)
        first_2kb = b"A" * 2048
        middle_2kb = b"B" * 2048
        last_2kb = b"C" * 2048
        test_content = first_2kb + middle_2kb + last_2kb

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            # When: 部分ハッシュを計算
            result = hasher.calculate_partial_hash(temp_file_path)

            # Then: 6KBファイルは2*chunk_size(4KB)より大きいので、最初と最後の2KBを結合したハッシュ値が返される
            expected_content = first_2kb + last_2kb
            expected_hash = hashlib.sha256(expected_content).hexdigest()
            assert result == expected_hash
        finally:
            Path(temp_file_path).unlink()

    def test_os_error_handling(self):
        """FileNotFoundErrorハンドリングのテスト"""
        # Given: 存在しないディレクトリ内のファイルパス
        hasher = Hasher()
        invalid_path = "/nonexistent/directory/file.txt"

        # When & Then: FileNotFoundErrorが発生すること
        with pytest.raises(FileNotFoundError, match="File not found"):
            hasher.calculate_partial_hash(invalid_path)

        with pytest.raises(FileNotFoundError, match="File not found"):
            hasher.calculate_full_hash(invalid_path)

    def test_memory_efficiency_large_file(self):
        """大きなファイルでのメモリ効率テスト"""
        # Given: 1MBのファイル(チャンクサイズ4KBに対して十分に大きい)
        hasher = Hasher(chunk_size=4096)
        test_content = b"X" * (1024 * 1024)  # 1MB

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            # When: 部分ハッシュと完全ハッシュを計算
            partial_hash = hasher.calculate_partial_hash(temp_file_path)
            full_hash = hasher.calculate_full_hash(temp_file_path)

            # Then: ハッシュ値が生成され、部分ハッシュは完全ハッシュと異なる
            assert len(partial_hash) == 64  # SHA256 hex length
            assert len(full_hash) == 64  # SHA256 hex length
            assert partial_hash != full_hash  # 1MBファイルでは異なるはず
        finally:
            Path(temp_file_path).unlink()

    def test_edge_case_exact_chunk_size_file(self):
        """ちょうどチャンクサイズのファイルのテスト"""
        # Given: ちょうど4KBのファイル
        hasher = Hasher(chunk_size=4096)
        test_content = b"Y" * 4096

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            # When: 部分ハッシュを計算
            result = hasher.calculate_partial_hash(temp_file_path)

            # Then: ファイル全体のハッシュ値が返される
            expected_hash = hashlib.sha256(test_content).hexdigest()
            assert result == expected_hash
        finally:
            Path(temp_file_path).unlink()
