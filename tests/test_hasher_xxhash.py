"""Hasherサービスのxxhashサポートテスト"""

import tempfile
from pathlib import Path

import pytest

from src.models.scan_config import ScanConfig
from src.services.hasher import Hasher


class TestHasherXxhash:
    """Hasherクラスのxxhashサポートテスト"""

    def test_init_with_scan_config_default(self):
        """ScanConfigを使用した初期化テスト（デフォルト値）"""
        # Given: デフォルトのScanConfig
        config = ScanConfig()

        # When: ScanConfigでHasherを初期化
        hasher = Hasher(config)

        # Then: 設定が反映される
        assert hasher.chunk_size == 65536
        assert hasher.hash_algorithm == "xxhash64"

    def test_init_with_scan_config_custom(self):
        """ScanConfigを使用した初期化テスト（カスタム値）"""
        # Given: カスタムのScanConfig
        config = ScanConfig(
            chunk_size=32768, hash_algorithm="sha256", parallel_workers=2
        )

        # When: ScanConfigでHasherを初期化
        hasher = Hasher(config)

        # Then: 設定が反映される
        assert hasher.chunk_size == 32768
        assert hasher.hash_algorithm == "sha256"

    def test_init_backward_compatibility(self):
        """後方互換性テスト（従来のパラメータ）"""
        # When: 従来のパラメータで初期化
        hasher = Hasher(chunk_size=8192, hash_algorithm="md5")

        # Then: 設定が反映される
        assert hasher.chunk_size == 8192
        assert hasher.hash_algorithm == "md5"

    def test_init_no_parameters_backward_compatibility(self):
        """パラメータなし初期化の後方互換性テスト"""
        # When: パラメータなしで初期化
        hasher = Hasher()

        # Then: デフォルト値が設定される
        assert hasher.chunk_size == 4096
        assert hasher.hash_algorithm == "sha256"

    def test_xxhash64_partial_hash(self):
        """xxhash64による部分ハッシュ計算テスト"""
        # Given: テストファイルとxxhash64設定
        test_content = b"Test content for xxhash64 partial hash" * 100  # 約3KB
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            config = ScanConfig(hash_algorithm="xxhash64")
            hasher = Hasher(config)

            # When: xxhash64で部分ハッシュを計算
            result = hasher.calculate_partial_hash(temp_file_path)

            # Then: ハッシュ値が返される（xxhash64は64ビットハッシュ）
            assert isinstance(result, str)
            assert len(result) == 16  # xxhash64は16進数で16文字
            assert all(c in "0123456789abcdef" for c in result.lower())

        finally:
            Path(temp_file_path).unlink()

    def test_xxhash64_full_hash(self):
        """xxhash64による完全ハッシュ計算テスト"""
        # Given: テストファイルとxxhash64設定
        test_content = b"Test content for xxhash64 full hash" * 200  # 約6KB
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            config = ScanConfig(hash_algorithm="xxhash64")
            hasher = Hasher(config)

            # When: xxhash64で完全ハッシュを計算
            result = hasher.calculate_full_hash(temp_file_path)

            # Then: ハッシュ値が返される
            assert isinstance(result, str)
            assert len(result) == 16  # xxhash64は16進数で16文字
            assert all(c in "0123456789abcdef" for c in result.lower())

        finally:
            Path(temp_file_path).unlink()

    def test_xxhash64_vs_sha256_different_results(self):
        """xxhash64とSHA256で異なるハッシュ値が生成されることを確認"""
        # Given: テストファイル
        test_content = b"Test content for algorithm comparison"
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            # When: 異なるアルゴリズムでハッシュを計算
            sha256_hasher = Hasher(hash_algorithm="sha256")
            xxhash_hasher = Hasher(ScanConfig(hash_algorithm="xxhash64"))

            sha256_result = sha256_hasher.calculate_full_hash(temp_file_path)
            xxhash_result = xxhash_hasher.calculate_full_hash(temp_file_path)

            # Then: 異なるハッシュ値が生成される
            assert sha256_result != xxhash_result
            assert len(sha256_result) == 64  # SHA256は16進数で64文字
            assert len(xxhash_result) == 16  # xxhash64は16進数で16文字

        finally:
            Path(temp_file_path).unlink()

    def test_configurable_chunk_size_used_in_reading(self):
        """設定されたchunk_sizeがファイル読み込みに使用されることを確認"""
        # Given: 大きなテストファイルとカスタムchunk_size
        chunk_size = 4096  # 最小値の4KB
        test_content = b"A" * 16384  # 16KB

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name

        try:
            config = ScanConfig(chunk_size=chunk_size, hash_algorithm="sha256")
            hasher = Hasher(config)

            # When: 部分ハッシュを計算
            result = hasher.calculate_partial_hash(temp_file_path)

            # Then: 正しいハッシュ値が計算される（chunk_sizeが反映されている）
            # 16KBファイルなので最初と最後の4KBが読み込まれるはず
            import hashlib

            expected_content = test_content[:chunk_size] + test_content[-chunk_size:]
            expected_hash = hashlib.sha256(expected_content).hexdigest()
            assert result == expected_hash

        finally:
            Path(temp_file_path).unlink()

    def test_invalid_hash_algorithm_fallback(self):
        """無効なハッシュアルゴリズムの場合のフォールバックテスト"""
        # Given: 無効なハッシュアルゴリズムを指定
        config = ScanConfig(hash_algorithm="invalid_algorithm")

        # When & Then: エラーが発生すること
        with pytest.raises(ValueError):
            Hasher(config)
