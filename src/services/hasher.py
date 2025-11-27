"""Hasherサービス - ファイルハッシュ計算"""

import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Union

from src.models.file_meta import FileMeta

logger = logging.getLogger(__name__)


class Hasher:
    """ファイルハッシュ計算を行うサービスクラス

    大きなファイルやネットワークドライブ上のファイルを効率的に処理するために、
    部分ハッシュと完全ハッシュの計算機能を提供する。
    """

    def __init__(self, chunk_size: int = 4096, hash_algorithm: str = "sha256") -> None:
        """Hasherを初期化する

        Args:
            chunk_size: ファイル読み込みのチャンクサイズ(バイト単位)。デフォルトは4096(4KB)
            hash_algorithm: 使用するハッシュアルゴリズム。デフォルトはSHA256
        """
        self.chunk_size = chunk_size
        self.hash_algorithm = hash_algorithm

    def _get_hash_object(self) -> Any:
        """ハッシュオブジェクトを取得する"""
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
