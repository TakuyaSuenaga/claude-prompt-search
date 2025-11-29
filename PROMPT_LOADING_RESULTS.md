# プロンプト読み込み検証結果

## 🎯 検証の目的

Claude Agent SDKで、どのプロンプトファイルがどのように読み込まれるかを検証する。

## 📊 検証方法

Claudeに「あなたに与えられたシステムプロンプトの内容を報告してください」と質問し、実際に読み込まれた内容を確認する。

## ✅ 検証結果

### テスト1: 外部プロンプトファイル（`system_prompt`直接指定）

**設定**:
```python
# prompts-repo/Design.md を読み込む
with open("prompts-repo/Design.md", 'r') as f:
    external_prompt = f.read()  # 3,209文字

options = ClaudeAgentOptions(
    system_prompt=external_prompt,  # 直接指定
    allowed_tools=["Read"],
    permission_mode="acceptEdits"
)
```

**結果**: ✅ **成功 - 完全に読み込まれた**

Claudeの報告内容:

1. **プロンプトのソース**
   - タイトル: "Design Agent System Prompt"
   - ファイル名の明示はないが、内容は完全に読み込まれている

2. **役割の認識**
   - Design Agent（デザインエージェント）
   - ソフトウェアアーキテクチャ、UX/UI設計、システム設計の専門家

3. **使用可能なツール**
   - `Read`: 既存のコードとデザインファイルを読む
   - `Glob`: パターンに一致するファイルを見つける
   - `Grep`: コード内の特定のパターンを検索する

4. **出力形式**
   - Summary（要約）
   - Rationale（根拠）
   - Alternatives Considered（検討した代替案）
   - Implementation Notes（実装メモ）
   - Diagrams（図）

5. **主要な指示**
   - ユーザー中心設計
   - スケーラビリティ
   - 保守性

6. **プロンプトの冒頭**
   ```
   # Design Agent System Prompt

   You are an expert Design Agent specializing in...
   ```

**結論**:
- ✅ 外部プロンプトファイルは`system_prompt`に直接渡すことで**完全に読み込まれる**
- ✅ ファイル名は任意（Design.md、Coding.md など自由に命名可能）
- ✅ 他のリポジトリからの読み込みも可能

---

### テスト2: Claude Code プリセット + `setting_sources=["project"]`

**設定**:
```python
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code"
    },
    setting_sources=["project"],  # プロジェクト設定を読み込む
    allowed_tools=["Read"],
    permission_mode="acceptEdits"
)
```

**ファイル構成**:
```
claude-prompt-search/
├── CLAUDE.md                    # ルートディレクトリ
└── .claude/
    ├── system.md               # システムプロンプト
    └── instructions.md         # インストラクション
```

**結果**: ⚠️ **CLAUDE.md のみ読み込まれる**

Claudeの報告内容:

#### ✅ 読み込まれたファイル

**CLAUDE.md** のみ
```markdown
# Test CLAUDE.md File

This is a test CLAUDE.md file to investigate prompt loading order.

You are a helpful assistant for testing prompt loading order.

**File Location**: CLAUDE.md (root directory)
**Purpose**: Testing which prompt files are loaded and in what order
```

#### ❌ 読み込まれないファイル

1. **.claude/system.md**
   - ファイルは存在する
   - **現在のコンテキストには含まれていない**

2. **.claude/instructions.md**
   - ファイルは存在する
   - **現在のコンテキストには含まれていない**

**優先順位**:
1. **CLAUDE.md のみが有効** ✅
2. `.claude/system.md` は無視される ❌
3. `.claude/instructions.md` は無視される ❌

**結論**:
- ⚠️ `setting_sources=["project"]` では **CLAUDE.md のみ**が読み込まれる
- ❌ `.claude/` ディレクトリ内のファイルは読み込まれない
- ✅ CLAUDE.md が最優先で、他のファイルを上書きする

---

## 🔍 重要な発見

### 1. ファイル読み込みの仕組み

| 方法 | 読み込まれるファイル | 用途 |
|------|---------------------|------|
| `system_prompt="文字列"` | 任意の外部ファイル | マルチエージェントシステム（各エージェント専用プロンプト） |
| `setting_sources=["project"]` | **CLAUDE.mdのみ** | プロジェクト統一プロンプト |
| `setting_sources=["user"]` | `~/.claude/settings.json` | ユーザー個人設定 |
| `setting_sources=["local"]` | `.claude/settings.local.json` | ローカル設定 |

### 2. `.claude/system.md` と `.claude/instructions.md` の扱い

**重要**: これらのファイルは**Claude Code CLI（VSCode拡張）専用**の可能性が高い

- Python SDKの`setting_sources=["project"]`では読み込まれない
- CLAUDE.md が優先され、他は無視される
- CLI/VSCodeでは異なる動作をする可能性がある

### 3. マルチエージェントシステムの実装方法

#### ✅ 推奨: `system_prompt`直接指定

```python
# 各エージェント用の外部プロンプトファイル
prompts = {
    "design": "prompts-repo/Design.md",
    "coding": "prompts-repo/Coding.md",
    "testing": "prompts-repo/Testing.md"
}

# 各エージェントに専用プロンプトを読み込む
def create_agent(agent_type: str):
    with open(prompts[agent_type], 'r') as f:
        prompt = f.read()

    return ClaudeAgentOptions(
        system_prompt=prompt,  # 外部プロンプトを直接指定
        allowed_tools=get_tools_for_agent(agent_type),
        permission_mode="acceptEdits"
    )
```

**メリット**:
- ✅ ファイル名が自由
- ✅ 他のリポジトリからも読み込み可能
- ✅ 完全なプログラム制御
- ✅ 各エージェントが独立したプロンプトを持てる

#### ❌ 非推奨: `setting_sources`

```python
# これでは .claude/ 内のファイルは読み込まれない
options = ClaudeAgentOptions(
    setting_sources=["project"],  # CLAUDE.md のみ
    # .claude/system.md は無視される
    # .claude/instructions.md は無視される
)
```

**デメリット**:
- ❌ CLAUDE.md のみが読み込まれる
- ❌ `.claude/` 内のファイルは無視される
- ❌ ファイル名が固定（CLAUDE.md）
- ❌ マルチエージェントには不向き

---

## 📝 実装例の比較

### 方法1: 外部プロンプト（推奨）

```python
#!/usr/bin/env python3
"""Design Agent - 外部プロンプトを使用"""

from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions

# prompts-repo/Design.md を読み込む
prompt_path = Path("prompts-repo/Design.md")
with open(prompt_path, 'r') as f:
    design_prompt = f.read()

options = ClaudeAgentOptions(
    system_prompt=design_prompt,  # ✅ 完全に読み込まれる
    allowed_tools=["Read", "Glob", "Grep"]
)

# Claudeに質問
async for message in query(
    prompt="読み込んだプロンプトの役割を報告してください",
    options=options
):
    print(message)
```

**結果**: ✅ Design.mdの内容が完全に反映される

### 方法2: setting_sources（制限あり）

```python
#!/usr/bin/env python3
"""setting_sources を使用"""

from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code"
    },
    setting_sources=["project"]  # ⚠️ CLAUDE.mdのみ
)

# Claudeに質問
async for message in query(
    prompt="読み込んだプロンプトファイルを報告してください",
    options=options
):
    print(message)
```

**結果**: ⚠️ CLAUDE.md のみが読み込まれる（.claude/ は無視）

---

## 🎓 まとめ

### ✅ できること

1. **外部プロンプトファイルの自由な使用**
   - 任意のファイル名（Design.md、Coding.md など）
   - 他のリポジトリからの読み込み
   - `system_prompt`に直接渡す

2. **完全なプログラム制御**
   - ファイルの読み込みタイミング
   - 内容の確認・検証
   - 動的な切り替え

### ❌ できないこと

1. **`.claude/` ディレクトリの活用（Python SDKでは）**
   - `setting_sources=["project"]` では無視される
   - CLAUDE.md が優先される
   - VSCode拡張とは動作が異なる

2. **複数プロンプトファイルの自動統合**
   - CLAUDE.md 以外は読み込まれない
   - 手動で統合する必要がある

### 💡 ベストプラクティス

**マルチエージェントシステムの場合**:

```python
# ✅ 推奨: 各エージェント用の専用プロンプトファイル
prompts-repo/
├── Design.md      # Design Agent用
├── Coding.md      # Coding Agent用
└── Testing.md     # Testing Agent用

# 各エージェントで読み込み
options = ClaudeAgentOptions(
    system_prompt=load_prompt("Design.md")  # 直接指定
)
```

**単一プロジェクトの場合**:

```python
# ✅ CLAUDE.mdを使用
CLAUDE.md  # プロジェクト統一プロンプト

# setting_sourcesで読み込み
options = ClaudeAgentOptions(
    setting_sources=["project"]  # CLAUDE.mdのみ
)
```

---

## 📚 関連ファイル

- [verify_prompt_loading.py](verify_prompt_loading.py) - 検証スクリプト
- [prompts-repo/Design.md](prompts-repo/Design.md) - 外部プロンプト例
- [CLAUDE.md](CLAUDE.md) - プロジェクトプロンプト
- [.claude/system.md](.claude/system.md) - システムプロンプト（読み込まれない）
- [.claude/instructions.md](.claude/instructions.md) - インストラクション（読み込まれない）

---

**検証日**: 2025-11-29
**検証ツール**: [verify_prompt_loading.py](verify_prompt_loading.py)
**方法**: Claude自身に読み込んだプロンプトの内容を報告させる
