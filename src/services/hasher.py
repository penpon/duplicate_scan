"""Hasherサービス - ファイルハッシュ計算"""

import hashlib
from pathlib import Path
from typing import Any, Optional, Union, cast

import xxhash

from src.models.scan_config import ScanConfig


class Hasher:
    """ファイルハッシュ計算を行うサービスクラス

    大きなファイルやネットワークドライブ上のファイルを効率的に処理するために、
    部分ハッシュと完全ハッシュの計算機能を提供する。
    """

    def __init__(
        self,
        config: Optional[Union[ScanConfig, int]] = None,
        chunk_size: Optional[int] = None,
        hash_algorithm: Optional[str] = None,
    ) -> None:
        """Hasherを初期化する

        Args:
            config: ScanConfigオブジェクト。指定された場合は他のパラメータを無視
            chunk_size: ファイル読み込みのチャンクサイズ(バイト単位)。デフォルトは4096(4KB)
            hash_algorithm: 使用するハッシュアルゴリズム。デフォルトはSHA256
        """
        # 後方互換性のための処理
        if config is not None and not hasattr(config, "chunk_size"):
            # configがScanConfigオブジェクトでない場合（古い形式）
            # この場合、configはint（chunk_size）として扱われる
            if isinstance(config, int):
                self.chunk_size = config
                self.hash_algorithm = (
                    hash_algorithm if hash_algorithm is not None else "sha256"
                )
            else:
                raise ValueError(
                    "config must be a ScanConfig object or integer (chunk_size)"
                )
        elif config is not None:
            # 新しい形式：ScanConfigオブジェクト
            scan_config = cast(ScanConfig, config)
            self.chunk_size = scan_config.chunk_size
            self.hash_algorithm = scan_config.hash_algorithm
        else:
            # デフォルト値または個別パラメータ
            self.chunk_size = chunk_size if chunk_size is not None else 4096
            self.hash_algorithm = (
                hash_algorithm if hash_algorithm is not None else "sha256"
            )

        # ハッシュアルゴリズムの検証
        self._validate_hash_algorithm()

    def _validate_hash_algorithm(self) -> None:
        """ハッシュアルゴリズムが有効か検証する"""
        if self.hash_algorithm == "xxhash64":
            return  # xxhash64は常に有効
        elif self.hash_algorithm in hashlib.algorithms_available:
            return  # hashlibでサポートされているアルゴリズム
        else:
            raise ValueError(f"Unsupported hash algorithm: {self.hash_algorithm}")

    def _get_hash_object(self) -> Any:
        """ハッシュオブジェクトを取得する"""
        if self.hash_algorithm == "xxhash64":
            return xxhash.xxh64()
        else:
            return hashlib.new(self.hash_algorithm)

    def calculate_partial_hash(self, file_path: Union[str, Path]) -> str:
        """ファイルの部分ハッシュを計算する(最初と最後のチャンク)

        ネットワークドライブ上の大きなファイルを効率的に処理するために、
        ファイル全体ではなく最初と最後のチャンクのみを読み込んでハッシュを計算する。

        Args:
            file_path: ファイルパス

        Returns:
            ハッシュ値(16進数文字列)

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            OSError: ファイル読み込みエラーの場合
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            file_size = path.stat().st_size

            # ファイルが2*chunk_size未満の場合は全体を読み込む
            if file_size <= 2 * self.chunk_size:
                with open(path, "rb") as f:
                    content = f.read()
                hash_obj = self._get_hash_object()
                hash_obj.update(content)
                return hash_obj.hexdigest()

            # 最初のチャンクと最後のチャンクを読み込む
            hash_obj = self._get_hash_object()
            with open(path, "rb") as f:
                # 最初のチャンク
                first_chunk = f.read(self.chunk_size)
                hash_obj.update(first_chunk)

                # 最後のチャンク
                f.seek(-self.chunk_size, 2)
                last_chunk = f.read(self.chunk_size)
                hash_obj.update(last_chunk)

            return hash_obj.hexdigest()

        except OSError as e:
            raise OSError(f"Failed to read file {file_path}: {e}") from e

    def calculate_full_hash(self, file_path: Union[str, Path]) -> str:
        """ファイルの完全ハッシュを計算する

        大きなファイルのメモリ使用量を抑えるために、チャンク単位で読み込んで
        ハッシュを計算する。

        Args:
            file_path: ファイルパス

        Returns:
            ハッシュ値(16進数文字列)

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            OSError: ファイル読み込みエラーの場合
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            hash_obj = self._get_hash_object()

            with open(path, "rb") as f:
                # 大きなファイルのためにチャンクで読み込む
                while chunk := f.read(self.chunk_size):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()

        except OSError as e:
            raise OSError(f"Failed to read file {file_path}: {e}") from e
