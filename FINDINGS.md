# Claude Agent SDK プロンプト読み込み順序 - 調査結果

## 📋 調査概要

Python版Claude Agent SDKにおけるプロンプトファイルの読み込み順序と優先順位を調査しました。

**調査方法**: Claude自身に読み込んだプロンプトファイルを報告させる

## 🎯 主要な発見

### 読み込まれるプロンプトファイル

`setting_sources=["project"]` を指定した場合、以下のファイルが読み込まれます：

1. **CLAUDE.md** (プロジェクトルート)
2. **.claude/system.md**
3. **.claude/instructions.md**
4. **.claude/commands/*.md** (スラッシュコマンド実行時のみ)

## 📊 読み込み順序と優先順位

### 優先順位（高 → 低）

```
1. [最高] Claude Codeのコアシステムプロンプト（組み込み）
2. [高]   CLAUDE.md（デフォルト動作をオーバーライド可能）
3. [中]   .claude/system.md
4. [中]   .claude/instructions.md
5. [低]   .claude/commands/*.md（条件付き）
```

### 重要なポイント

#### 🔴 CLAUDE.md の特別な扱い

- **最も強力なオーバーライド機能**を持つ
- システムから明示的に「OVERRIDE any default behavior」と強調される
- 「you MUST follow them exactly as written」という強い指示付き

#### 🟡 .claude/ ディレクトリのファイル

- **補完的な役割**を持つ
- system.md と instructions.md は同等の優先度
- CLAUDE.md ほど強力ではない

#### 🟢 コマンドファイル

- **オンデマンド読み込み**
- スラッシュコマンド実行時のみ有効

## 🔍 技術的な詳細

### ファイルの読み込み方法

Claude Agent SDKは以下のアーキテクチャで動作します：

```
Python SDK → バンドルされたClaude Code CLI (Node.js/TypeScript)
                        ↓
                プロンプトファイルを読み込み
```

### なぜPythonの`open()`では捕捉できないか

- プロンプトファイルの読み込みは**CLI内部**（Node.js/TypeScript）で行われる
- Pythonレベルでの`open()`のmonkey patchingでは追跡不可能
- システムコールトレース（`strace`、`dtrace`）が必要

## 💡 調査手法

### 成功した方法: Claude自身に質問

```python
prompt = """このセッションで読み込んだプロンプトの設定ファイルを
優先順位と内容を報告してください。"""

async for message in query(prompt=prompt, options=options):
    # Claudeが詳細なレポートを返す
```

### 失敗した方法: Monkey Patching

```python
# これは機能しない
original_open = open
builtins.open = traced_open  # CLI内部の読み込みは捕捉できない
```

## 📁 各ファイルの役割

### CLAUDE.md
- **目的**: プロジェクト全体の動作をカスタマイズ
- **用途**: デフォルト動作のオーバーライド
- **推奨**: プロジェクト固有の重要な指示を記載

### .claude/system.md
- **目的**: システムレベルのカスタマイズ
- **用途**: 技術的な設定や制約
- **推奨**: 一般的なシステム動作の調整

### .claude/instructions.md
- **目的**: プロジェクト固有の指示
- **用途**: タスク実行時の具体的なガイドライン
- **推奨**: コーディングスタイルや手順の指定

### .claude/commands/*.md
- **目的**: カスタムスラッシュコマンド
- **用途**: 再利用可能なタスクの定義
- **推奨**: 頻繁に使用する操作の自動化

## ⚙️ setting_sources の動作

### setting_sources=["project"] を指定した場合

```python
options = ClaudeAgentOptions(
    setting_sources=["project"],  # ✅ これが必須
    # ...
)
```

- CLAUDE.md が読み込まれる
- .claude/ ディレクトリの設定が読み込まれる
- .claude/settings.json も読み込まれる

### setting_sources を省略した場合

```python
options = ClaudeAgentOptions(
    # setting_sources なし  # ❌ プロンプトファイルは読み込まれない
)
```

- **プロンプトファイルは一切読み込まれない**
- SDKアプリケーションの分離が可能

## 🚀 実用的な推奨事項

### 1. プロジェクト設定の階層化

```
CLAUDE.md                    ← 最重要の指示（必ず守る）
├── .claude/system.md        ← システムレベル設定
├── .claude/instructions.md  ← 詳細なガイドライン
└── .claude/commands/        ← 便利なコマンド集
```

### 2. CLAUDE.md の使用例

```markdown
# プロジェクト名

このプロジェクトでは以下のルールを必ず守ること：

1. すべてのコードはTypeScriptで書く
2. テストは必須
3. コミット前にlintを実行

これらの指示はデフォルト動作をオーバーライドします。
```

### 3. setting_sources の選択

```python
# プロジェクト設定を使用する場合（推奨）
ClaudeAgentOptions(setting_sources=["project"])

# すべての設定を使用する場合
ClaudeAgentOptions(setting_sources=["user", "project", "local"])

# 設定を使用しない場合（完全なプログラム制御）
ClaudeAgentOptions()  # setting_sources を省略
```

## 📚 参考資料

- [ask_claude.py](ask_claude.py) - 調査に使用したスクリプト
- [claude_full_response.txt](claude_full_response.txt) - Claudeの完全な回答
- [Claude Agent SDK - Python リファレンス](https://code.claude.com/docs/ja/agent-sdk/python)

## 🎓 学んだこと

1. **CLAUDE.md が最強** - プロジェクトの動作を完全に制御できる
2. **setting_sources が重要** - これを指定しないとプロンプトファイルは読み込まれない
3. **Claude自身に聞くのが効果的** - 内部動作を直接知ることができる
4. **CLI層での読み込み** - Pythonレベルでは追跡が困難

---

**調査日**: 2025-11-29
**SDK バージョン**: claude-agent-sdk (latest)
**調査方法**: Claude自身への質問による内部状態の確認
