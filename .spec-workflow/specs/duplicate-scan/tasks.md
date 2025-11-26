# タスクドキュメント

## 開発プロセス
各タスクの実装は以下の標準ワークフローに従ってください：
1. **TDDサイクル (`/tdd-cycle`)**: `git worktree`作成、RGRサイクルでの実装
2. **品質チェック (`/quality-check`)**: 実装後の品質確認
3. **レビュー & PR (`/rabbit-rocket`)**: CodeRabbitレビューとPR作成
4. **クリーンアップ (`/sync`)**: マージ後のクリーンアップ

- [x] 1. プロジェクト初期化
  - File: pyproject.toml, src/main.py
  - uvプロジェクトの初期化と依存関係のインストール（flet, send2trash）
  - 基本的なプロジェクト構造の作成
  - Purpose: 開発環境のセットアップ
  - _Leverage: tech.md_
  - _Requirements: Non-functional_
  - _Prompt: **instruction** Role: Python Developer | Task: Initialize project with uv and install dependencies | Context: Setting up a new Flet project for Duplicate File Remover | Implementation Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md | Run `uv init` to initialize the project | Add dependencies: `flet`, `send2trash`, `pytest`, `ruff`, `mypy` | Create `src` directory structure | Ensure `pyproject.toml` is correctly configured | Restrictions: Use Python 3.10+ | Success Criteria: `uv run flet run src/main.py` runs successfully | After Implementation: Verify environment setup | Mark as completed ([x]) in tasks.md | Group changes by similarity and git commit. If pre-commit fails, fix issues and retry commit._

- [ ] 2. データモデルの実装
  - File: src/models/file_meta.py, src/models/duplicate_group.py
  - FileMetaとDuplicateGroupのデータクラスを定義
  - Purpose: ファイル処理用のデータ構造を定義
  - _Leverage: design.md (Data Models)_
  - _Requirements: All_
  - _Prompt: **instruction** Role: Python Developer | Task: Implement data models | Context: Structured data needed for file metadata and duplicate groups | Implementation Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md | Create `FileMeta` dataclass in `src/models/file_meta.py` with fields: path, size, modified_time, partial_hash, full_hash | Create `DuplicateGroup` dataclass in `src/models/duplicate_group.py` with fields: files (List[FileMeta]), total_size | Restrictions: Use `@dataclass` | Success Criteria: Models can be instantiated and pass type checking | After Implementation: Run mypy | Mark as completed ([x]) in tasks.md | Group changes by similarity and git commit. If pre-commit fails, fix issues and retry commit._

- [ ] 3. Scannerサービスの実装
  - File: src/services/scanner.py
  - 再帰的ディレクトリスキャンの実装
  - 画像/動画拡張子のフィルタリングを追加
  - Purpose: 対象ファイルを検出
  - _Leverage: design.md (Scanner Service)_
  - _Requirements: 1, 2_
  - _Prompt: **instruction** Role: Python Developer | Task: Implement Scanner Service | Context: Need to scan local and network drives for target files | Implementation Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md | Create `Scanner` class in `src/services/scanner.py` | Implement `scan_directories` method using `pathlib` | Add filtering for image/video extensions (jpg, png, mp4, mov, etc.) | Handle permission errors gracefully | Restrictions: Must handle network paths correctly | Success Criteria: Returns list of FileMeta objects for valid files | After Implementation: Create unit tests | Mark as completed ([x]) in tasks.md | Group changes by similarity and git commit. If pre-commit fails, fix issues and retry commit._

- [ ] 4. Hasherサービスの実装
  - File: src/services/hasher.py
  - 部分ハッシュと完全ハッシュのロジックを実装
  - Purpose: 効率的に重複を識別
  - _Leverage: design.md (Hasher Service)_
  - _Requirements: 3_
  - _Prompt: **instruction** Role: Python Developer | Task: Implement Hasher Service | Context: Optimized hashing for large files on network drives | Implementation Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md | Create `Hasher` class in `src/services/hasher.py` | Implement `calculate_partial_hash` (first/last 4KB) | Implement `calculate_full_hash` | Restrictions: Use `hashlib` (SHA256 recommended) | Optimize for large files | Success Criteria: Correct hash generation and good performance on large files | After Implementation: Create unit tests | Mark as completed ([x]) in tasks.md | Group changes by similarity and git commit. If pre-commit fails, fix issues and retry commit._

- [ ] 5. Duplicate Detectorの実装
  - File: src/services/detector.py
  - 重複をグループ化するロジックを実装
  - Purpose: ハッシュでファイルをグループ化
  - _Leverage: design.md (Duplicate Detector)_
  - _Requirements: 3_
  - _Prompt: **instruction** Role: Python Developer | Task: Implement Duplicate Detector | Context: Group files based on size and hash to identify duplicates | Implementation Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md | Create `DuplicateDetector` class in `src/services/detector.py` | Implement logic: Group by size -> Group by partial hash -> Group by full hash | Restrictions: Efficient memory usage | Success Criteria: Correctly identifies duplicates | After Implementation: Create unit tests | Mark as completed ([x]) in tasks.md | Group changes by similarity and git commit. If pre-commit fails, fix issues and retry commit._

- [ ] 6. UI実装 - ホームビュー
  - File: src/ui/home_view.py, src/main.py
  - フォルダ選択画面を作成
  - Purpose: ユーザーがスキャン対象を選択できるようにする
  - _Leverage: design.md (UI Manager)_
  - _Requirements: 1_
  - _Prompt: **instruction** Role: Flet Developer | Task: Implement Home View | Context: User needs to select folders to scan | Implementation Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md | Create `HomeView` control in `src/ui/home_view.py` | Implement folder selection using `FilePicker` | Display list of selected folders | Add "Start Scan" button | Restrictions: Use Flet controls | Success Criteria: User can select folders and proceed to scan | After Implementation: Manual UI check | Mark as completed ([x]) in tasks.md | Group changes by similarity and git commit. If pre-commit fails, fix issues and retry commit._

- [ ] 7. UI実装 - スキャンビュー
  - File: src/ui/scanning_view.py
  - 進捗表示を作成
  - Purpose: 長時間操作中のフィードバックを表示
  - _Leverage: design.md (UI Manager)_
  - _Requirements: Non-functional (Usability)_
  - _Prompt: **instruction** Role: Flet Developer | Task: Implement Scanning View | Context: Display progress during long-running scan operations | Implementation Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md | Create `ScanningView` in `src/ui/scanning_view.py` | Add `ProgressBar` and status text | Integrate with Scanner/Hasher updates | Restrictions: Responsive UI | Success Criteria: UI updates in real-time during scan | After Implementation: Manual UI check | Mark as completed ([x]) in tasks.md | Group changes by similarity and git commit. If pre-commit fails, fix issues and retry commit._

- [ ] 8. UI実装 - 結果ビュー
  - File: src/ui/results_view.py
  - 重複リストと選択インターフェースを作成
  - Purpose: 削除するファイルをレビューして選択
  - _Leverage: design.md (UI Manager)_
  - _Requirements: 4_
  - _Prompt: **instruction** Role: Flet Developer | Task: Implement Results View | Context: Review and select duplicates for deletion | Implementation Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md | Create `ResultsView` in `src/ui/results_view.py` | Display list of `DuplicateGroup`s | Show file details and previews | Add checkboxes for selection | Add "Delete Selected" button | Restrictions: Handle large lists efficiently | Success Criteria: User can select files for deletion | After Implementation: Manual UI check | Mark as completed ([x]) in tasks.md | Group changes by similarity and git commit. If pre-commit fails, fix issues and retry commit._

- [ ] 9. 削除ロジック & クリーンアップビューの実装
  - File: src/services/deleter.py, src/ui/cleanup_view.py
  - 安全な削除と結果サマリーを実装
  - Purpose: ファイルを削除してレポートを表示
  - _Leverage: design.md (Deletion Service)_
  - _Requirements: 4_
  - _Prompt: **instruction** Role: Python Developer | Task: Implement Deletion Logic and Cleanup View | Context: Safe deletion of selected files | Implementation Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md | Implement deletion using `send2trash` in `src/services/deleter.py` | Create `CleanupView` in `src/ui/cleanup_view.py` to show results (deleted count, space saved) | Restrictions: Handle errors (e.g., file in use) | Success Criteria: Files are moved to trash, summary is correct | After Implementation: Verify trash contents | Mark as completed ([x]) in tasks.md | Group changes by similarity and git commit. If pre-commit fails, fix issues and retry commit._

- [ ] 10. 統合 & E2Eテスト
  - File: tests/integration/test_flow.py
  - 完全なワークフローを検証
  - Purpose: すべてのコンポーネントが連携して動作することを確認
  - _Leverage: design.md (Testing Strategy)_
  - _Requirements: All_
  - _Prompt: **instruction** Role: QA Engineer | Task: Perform Integration and E2E Tests | Context: Verify the entire application flow | Implementation Instructions: Before starting implementation, mark this task as in-progress ([-]) in tasks.md | Create integration tests combining Scanner, Hasher, and Detector | Perform manual E2E tests with dummy files on local/network drives | Restrictions: None | Success Criteria: All tests pass, app works as expected | After Implementation: Final Report | Mark as completed ([x]) in tasks.md | Group changes by similarity and git commit. If pre-commit fails, fix issues and retry commit._

