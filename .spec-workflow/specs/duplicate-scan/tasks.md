# タスクドキュメント

## 開発プロセス
各タスクの実装は以下の標準ワークフローに従ってください：
1. **TDDサイクル (`/tdd-cycle`)**: `git worktree`作成、RGRサイクルでの実装
2. **品質チェック (`/quality-check`)**: 実装後の品質確認
3. **レビュー & PR (`/rabbit-rocket`)**: CodeRabbitレビューとPR作成
4. **クリーンアップ (`/sync`)**: マージ後のクリーンアップ

- [ ] 1. プロジェクト初期化
  - File: pyproject.toml, src/main.py
  - uvプロジェクトの初期化と依存関係のインストール（flet, send2trash）
  - 基本的なプロジェクト構造の作成
  - Purpose: 開発環境のセットアップ
  - _Leverage: tech.md_
  - _Requirements: Non-functional_
  - _Prompt: **instruction** Role: Python開発者 | Task: uvでプロジェクトを初期化し依存関係をインストール | Context: 新規Fletプロジェクト | Implementation Instructions: `uv init`を実行 | `flet` `send2trash` `pytest` `ruff` `mypy`を追加 | `src`ディレクトリを作成 | Restrictions: Python 3.10+を使用 | Success Criteria: `uv run flet run src/main.py`が動作する | After Implementation: 環境を検証_

- [ ] 2. データモデルの実装
  - File: src/models/file_meta.py, src/models/duplicate_group.py
  - FileMetaとDuplicateGroupのデータクラスを定義
  - Purpose: ファイル処理用のデータ構造を定義
  - _Leverage: design.md (Data Models)_
  - _Requirements: All_
  - _Prompt: **instruction** Role: Python開発者 | Task: データモデルを実装 | Context: ファイルメタデータ用の構造化データが必要 | Implementation Instructions: design.mdで定義された`FileMeta`と`DuplicateGroup`データクラスを作成 | Restrictions: `@dataclass`を使用 | Success Criteria: モデルをインスタンス化でき型チェックが通る | After Implementation: mypyを実行_

- [ ] 3. Scannerサービスの実装
  - File: src/services/scanner.py
  - 再帰的ディレクトリスキャンの実装
  - 画像/動画拡張子のフィルタリングを追加
  - Purpose: 対象ファイルを検出
  - _Leverage: design.md (Scanner Service)_
  - _Requirements: 1, 2_
  - _Prompt: **instruction** Role: Python開発者 | Task: Scannerサービスを実装 | Context: ローカルおよびネットワークドライブをスキャンする必要がある | Implementation Instructions: `scan_directories`メソッドを持つ`Scanner`クラスを作成 | `pathlib`を使用 | 拡張子でフィルタリング（jpg, png, mp4など） | Restrictions: 権限エラーを適切に処理 | Success Criteria: 有効なファイルのFileMetaリストを返す | After Implementation: ユニットテストを作成_

- [ ] 4. Hasherサービスの実装
  - File: src/services/hasher.py
  - 部分ハッシュと完全ハッシュのロジックを実装
  - Purpose: 効率的に重複を識別
  - _Leverage: design.md (Hasher Service)_
  - _Requirements: 3_
  - _Prompt: **instruction** Role: Python開発者 | Task: Hasherサービスを実装 | Context: ネットワークドライブ上の大きなファイルに最適化 | Implementation Instructions: `Hasher`クラスを作成 | `calculate_hash`は部分ハッシュ（先頭/末尾4KB）をサポート | Restrictions: `hashlib`を使用 | Success Criteria: 正しいハッシュ生成、大きなファイルでのパフォーマンス | After Implementation: ユニットテストを作成_

- [ ] 5. Duplicate Detectorの実装
  - File: src/services/detector.py
  - 重複をグループ化するロジックを実装
  - Purpose: ハッシュでファイルをグループ化
  - _Leverage: design.md (Duplicate Detector)_
  - _Requirements: 3_
  - _Prompt: **instruction** Role: Python開発者 | Task: Duplicate Detectorを実装 | Context: サイズとハッシュに基づいてファイルをグループ化 | Implementation Instructions: `DuplicateDetector`クラスを作成 | ロジック: サイズでグループ化 → 部分ハッシュでグループ化 → 完全ハッシュでグループ化 | Restrictions: 効率的なメモリ使用 | Success Criteria: 重複を正しく識別 | After Implementation: ユニットテストを作成_

- [ ] 6. UI実装 - ホームビュー
  - File: src/ui/home_view.py, src/main.py
  - フォルダ選択画面を作成
  - Purpose: ユーザーがスキャン対象を選択できるようにする
  - _Leverage: design.md (UI Manager)_
  - _Requirements: 1_
  - _Prompt: **instruction** Role: Flet開発者 | Task: ホームビューを実装 | Context: フォルダ選択 | Implementation Instructions: `HomeView`コントロールを作成 | フォルダを選択するボタン（`FilePicker`を使用）を追加 | 選択されたフォルダをリスト表示 | 「スキャン開始」ボタンを追加 | Restrictions: Fletコントロールを使用 | Success Criteria: フォルダを選択して次に進める | After Implementation: 手動UIチェック_

- [ ] 7. UI実装 - スキャンビュー
  - File: src/ui/scanning_view.py
  - 進捗表示を作成
  - Purpose: 長時間操作中のフィードバックを表示
  - _Leverage: design.md (UI Manager)_
  - _Requirements: Non-functional (Usability)_
  - _Prompt: **instruction** Role: Flet開発者 | Task: スキャンビューを実装 | Context: 進捗を表示 | Implementation Instructions: `ScanningView`を作成 | `ProgressBar`、ステータステキストを追加 | Scanner/Hasherの更新と統合 | Restrictions: レスポンシブなUI | Success Criteria: スキャン中に更新される | After Implementation: 手動UIチェック_

- [ ] 8. UI実装 - 結果ビュー
  - File: src/ui/results_view.py
  - 重複リストと選択インターフェースを作成
  - Purpose: 削除するファイルをレビューして選択
  - _Leverage: design.md (UI Manager)_
  - _Requirements: 4_
  - _Prompt: **instruction** Role: Flet開発者 | Task: 結果ビューを実装 | Context: 重複をレビュー | Implementation Instructions: `ResultsView`を作成 | `DuplicateGroup`をリスト表示 | ファイル詳細/プレビューを表示 | 選択用のチェックボックス | 「選択を削除」ボタン | Restrictions: 大きなリストを効率的に処理 | Success Criteria: ファイルを選択できる | After Implementation: 手動UIチェック_

- [ ] 9. 削除ロジック & クリーンアップビューの実装
  - File: src/services/deleter.py, src/ui/cleanup_view.py
  - 安全な削除と結果サマリーを実装
  - Purpose: ファイルを削除してレポートを表示
  - _Leverage: design.md (Deletion Service)_
  - _Requirements: 4_
  - _Prompt: **instruction** Role: Python開発者 | Task: 削除とクリーンアップビューを実装 | Context: 安全な削除 | Implementation Instructions: `send2trash`を使用 | 結果を表示する`CleanupView`を作成（削除数、節約容量） | Restrictions: エラーを処理（例: ファイルが使用中） | Success Criteria: ファイルがゴミ箱に移動される | After Implementation: ゴミ箱の内容を確認_

- [ ] 10. 統合 & E2Eテスト
  - File: tests/integration/test_flow.py
  - 完全なワークフローを検証
  - Purpose: すべてのコンポーネントが連携して動作することを確認
  - _Leverage: design.md (Testing Strategy)_
  - _Requirements: All_
  - _Prompt: **instruction** Role: QAエンジニア | Task: 統合テストを実施 | Context: アプリ全体のフロー | Implementation Instructions: Scanner、Hasher、Detectorを組み合わせた統合テストを作成 | ローカル/ネットワークドライブ上のダミーファイルで手動E2Eテストを実施 | Restrictions: なし | Success Criteria: すべてのテストが合格、アプリが期待通りに動作 | After Implementation: 最終レポート_

