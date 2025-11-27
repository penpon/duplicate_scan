"""Hasherサービス - ファイルハッシュ計算"""

import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Optional, Union, overload

import xxhash

from src.models.file_meta import FileMeta
from src.models.scan_config import ScanConfig

logger = logging.getLogger(__name__)


class Hasher:
    """ファイルハッシュ計算を行うサービスクラス

    大きなファイルやネットワークドライブ上のファイルを効率的に処理するために、
    部分ハッシュと完全ハッシュの計算機能を提供する。
    """

    @overload
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        hash_algorithm: Optional[str] = None,
        *,
        config: Optional[ScanConfig] = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        chunk_size: ScanConfig,
        hash_algorithm: None = None,
        *,
        config: Optional[ScanConfig] = None,
    ) -> None: ...

    def __init__(
        self,
        chunk_size: Optional[Union[ScanConfig, int]] = None,
        hash_algorithm: Optional[str] = None,
        *,
        config: Optional[ScanConfig] = None,
    ) -> None:
        """Hasherを初期化する

        Args:
            chunk_size: ファイル読み込みのチャンクサイズ(バイト単位) または ScanConfig。
                旧API互換のため位置引数で指定可能。
            hash_algorithm: 使用するハッシュアルゴリズム。デフォルトはSHA256。
            config: ScanConfigオブジェクト。指定された場合は他のパラメータを無視。
        """
        if config is not None:
            if not isinstance(config, ScanConfig):
                raise ValueError("config must be a ScanConfig object")
            self.chunk_size = config.chunk_size
            self.hash_algorithm = config.hash_algorithm
        elif isinstance(chunk_size, ScanConfig):
            if hash_algorithm is not None:
                raise ValueError(
                    "Cannot specify hash_algorithm when passing ScanConfig as the first argument"
                )
            self.chunk_size = chunk_size.chunk_size
            self.hash_algorithm = chunk_size.hash_algorithm
        elif isinstance(chunk_size, int):
            self.chunk_size = chunk_size
            self.hash_algorithm = (
                hash_algorithm if hash_algorithm is not None else "sha256"
            )
        elif chunk_size is not None:
            raise ValueError("chunk_size must be an int or ScanConfig")
        else:
            self.chunk_size = 4096
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

    def _calculate_hashes_parallel(
        self,
        files: list[FileMeta],
        max_workers: int,
        hash_func: Callable[[Union[str, Path]], str],
        attr_name: str,
        log_prefix: str,
    ) -> None:
        """並列でハッシュを計算するための共通処理。"""
        if not files:
            return

        def _worker(
            file_meta: FileMeta,
        ) -> tuple[FileMeta, str | None, Exception | None]:
            try:
                hash_value = hash_func(file_meta.path)
                return (file_meta, hash_value, None)
            except Exception as exc:  # noqa: BLE001
                return (file_meta, None, exc)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_worker, file_meta) for file_meta in files]
            for future in as_completed(futures):
                file_meta, hash_value, exc = future.result()
                if exc is not None:
                    logger.warning("%s %s: %s", log_prefix, file_meta.path, exc)
                    continue

                setattr(file_meta, attr_name, hash_value)

    def calculate_partial_hashes_parallel(
        self,
        files: list[FileMeta],
        max_workers: int = 4,
    ) -> None:
        """複数ファイルの部分ハッシュを並列に計算する。

        FileMeta の ``partial_hash`` をインプレースで更新する。
        1ファイルでエラーが発生しても処理を継続し、警告ログのみを出力する。
        """
        self._calculate_hashes_parallel(
            files=files,
            max_workers=max_workers,
            hash_func=self.calculate_partial_hash,
            attr_name="partial_hash",
            log_prefix="Failed to calculate partial hash for",
        )

    def calculate_full_hashes_parallel(
        self,
        files: list[FileMeta],
        max_workers: int = 4,
    ) -> None:
        """複数ファイルの完全ハッシュを並列に計算する。

        FileMeta の ``full_hash`` をインプレースで更新する。
        1ファイルでエラーが発生しても処理を継続し、警告ログのみを出力する。
        """
        self._calculate_hashes_parallel(
            files=files,
            max_workers=max_workers,
            hash_func=self.calculate_full_hash,
            attr_name="full_hash",
            log_prefix="Failed to calculate full hash for",
        )

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
