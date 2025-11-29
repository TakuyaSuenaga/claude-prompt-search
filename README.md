# Claude Agent SDK プロンプト読み込み検証

Python版Claude Agent SDKで、プロンプトファイルがどのように読み込まれるかを検証するプロジェクト。

---

## 📁 プロジェクト構成

```
claude-prompt-search/
├── main.py                  # 検証スクリプト（3つのパターンをテスト）
├── requirements.txt         # Python依存関係
├── CLAUDE.md               # プロジェクト統一プロンプト
├── prompts-repo/
│   └── Design.md           # 外部プロンプトファイル（例）
├── .env.example            # 環境変数のサンプル
└── README.md               # このファイル
```

---

## 🚀 セットアップ

### 1. 依存関係のインストール

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# パッケージのインストール
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
# APIキーを設定
export ANTHROPIC_API_KEY=your_actual_api_key_here
```

または `.env` ファイルを作成：

```bash
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

---

## 🔧 実行方法

```bash
# 仮想環境内で実行
source venv/bin/activate
python main.py
```

スクリプトは3つのパターンを順番にテストします：
1. CLAUDE.md のみ
2. 外部プロンプト（Design.md）のみ
3. 両方を同時に使用

実行結果は画面とログファイル（`prompt_loading.log`）に出力されます。

---

## 📊 プロンプトファイル設定パターンと結果

### パターン1: CLAUDE.md のみ

**設定コード:**
```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code"
    },
    setting_sources=["project"]  # CLAUDE.mdを読み込む
)
```

**ファイル配置:**
```
your-project/
└── CLAUDE.md    # プロジェクトルートに配置
```

**結果:**
- ✅ CLAUDE.md が完全に読み込まれる
- ✅ ファイルの全内容がClaudeに認識される
- 📌 プロジェクト全体で統一したプロンプトを使う場合に適している

---

### パターン2: 外部プロンプトファイルのみ

**設定コード:**
```python
from claude_agent_sdk import ClaudeAgentOptions
from pathlib import Path

# 外部ファイルを読み込む
with open("prompts-repo/Design.md", 'r', encoding='utf-8') as f:
    prompt_content = f.read()

options = ClaudeAgentOptions(
    system_prompt=prompt_content  # 読み込んだ内容を直接指定
)
```

**ファイル配置:**
```
your-project/
└── prompts-repo/
    └── Design.md    # 任意の場所に配置可能
```

**結果:**
- ✅ 外部プロンプトファイルが完全に読み込まれる（例: Design.md 3,209文字）
- ✅ ファイル名は自由（Design.md、Coding.md など）
- ✅ 配置場所も自由（prompts-repo/ など任意のディレクトリ）
- 📌 マルチエージェントシステムで各エージェント専用プロンプトを使う場合に適している

---

### パターン3: 両方を同時に使用

**設定コード:**
```python
from claude_agent_sdk import ClaudeAgentOptions
from pathlib import Path

# 外部ファイルを読み込む
with open("prompts-repo/Design.md", 'r', encoding='utf-8') as f:
    external_prompt = f.read()

options = ClaudeAgentOptions(
    system_prompt=external_prompt,   # 外部プロンプト（メイン）
    setting_sources=["project"]       # CLAUDE.md も読み込む（補足）
)
```

**ファイル配置:**
```
your-project/
├── CLAUDE.md                # プロジェクト固有の情報
└── prompts-repo/
    └── Design.md            # メインのプロンプト
```

**結果:**
- ✅ 両方のファイルが読み込まれる
- ✅ `system_prompt`（外部プロンプト）が主要な役割を定義
- ✅ `setting_sources`（CLAUDE.md）は `<system-reminder>` タグ内に配置され、補足コンテキストとして扱われる
- 📌 エージェントの役割は外部リポジトリで管理し、プロジェクト固有のルールはCLAUDE.mdで管理する場合に適している

---

## 📋 3つのパターンの比較

| 項目 | CLAUDE.md のみ | 外部ファイルのみ | 両方を使用 |
|------|----------------|-----------------|-----------|
| **設定方法** | `setting_sources=["project"]` | `system_prompt=読み込んだ内容` | 両方を指定 |
| **ファイル名** | 固定（CLAUDE.md） | 自由（任意の名前） | 両方 |
| **配置場所** | プロジェクトルート | 任意の場所 | 両方 |
| **読み込み確認** | ✅ 完全に読み込まれる | ✅ 完全に読み込まれる | ✅ 両方読み込まれる |
| **優先順位** | 単独使用時は最優先 | 単独使用時は最優先 | `system_prompt`が優先 |
| **用途** | プロジェクト統一プロンプト | マルチエージェント | エージェント+プロジェクト情報 |

---

## ⚠️ 注意点

### 1. 両方を使用する場合の優先順位

両方を指定した場合：
- **`system_prompt`（外部プロンプト）が主要プロンプト**として機能
- **`setting_sources`（CLAUDE.md）は補足コンテキスト**として `<system-reminder>` 内に配置される
- CLAUDE.mdと外部プロンプトで矛盾する指示がある場合、混乱を招く可能性がある

### 2. ファイル名と配置場所

- **CLAUDE.md**: プロジェクトルートに固定（`setting_sources=["project"]`を使う場合）
- **外部プロンプト**: ファイル名、配置場所ともに自由（`system_prompt`に直接指定）

### 3. 検証方法

プロンプトが正しく読み込まれているか確認する最も確実な方法：

```python
# Claudeに読み込んだ内容を報告させる
verification_prompt = """
あなたに与えられたシステムプロンプトについて報告してください：

1. プロンプトの冒頭部分（最初の100文字）
2. あなたの役割は何ですか？
3. 主要な指示を3つ挙げてください
"""
```

Claudeに質問すれば、読み込んだプロンプトの内容を正確に報告してくれます。

---

## 🔍 検証結果の例

### パターン1の実行結果

```
【パターン1】CLAUDE.md のみ - 検証結果
================================================================================

読み込まれたファイル: CLAUDE.md

内容の冒頭:
"# Test CLAUDE.md File

This is a test CLAUDE.md file to investigate prompt loading order.

You are a helpful assistant for testing prompt loading order."

あなたの役割: プロンプト読み込み順序をテストするためのアシスタント
```

### パターン2の実行結果

```
【パターン2】外部プロンプト（Design.md）のみ - 検証結果
================================================================================

プロンプトのタイトル: "Design Agent System Prompt"

あなたの役割:
- ソフトウェアアーキテクチャの専門家
- UX/UI設計の専門家
- システムデザインの専門家

使用可能なツール:
- Read: 既存のコードとデザインファイルを読む
- Glob: パターンに一致するファイルを見つける
- Grep: コード内の特定のパターンを検索する
```

### パターン3の実行結果

```
【パターン3】CLAUDE.md + 外部プロンプト（両方）- 検証結果
================================================================================

読み込まれたファイル:
✅ CLAUDE.md: 読み込まれている（<system-reminder> 内に配置）
✅ Design.md: 読み込まれている（メインのシステムプロンプト）

優先順位:
1. Design.md が主要プロンプトとして機能
2. CLAUDE.md は補足コンテキストとして扱われる

あなたの役割:
Design Agent（ソフトウェアアーキテクチャ、UX/UI設計の専門家）
```

---

## 📚 使用例

### プロジェクト全体で統一プロンプト

```python
# CLAUDE.md を使用
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code"
    },
    setting_sources=["project"]
)
```

### マルチエージェントシステム

```python
# 各エージェント用の外部プロンプトファイル
prompt_files = {
    "design": "prompts-repo/Design.md",
    "coding": "prompts-repo/Coding.md",
    "testing": "prompts-repo/Testing.md"
}

# 使いたいプロンプトを選択
selected = "design"
with open(prompt_files[selected], 'r', encoding='utf-8') as f:
    prompt = f.read()

options = ClaudeAgentOptions(
    system_prompt=prompt
)
```

### エージェント + プロジェクト情報

```python
# エージェントの役割は外部リポジトリで管理
# プロジェクト固有のルールはCLAUDE.mdで管理
with open("prompts-repo/Design.md", 'r', encoding='utf-8') as f:
    design_prompt = f.read()

options = ClaudeAgentOptions(
    system_prompt=design_prompt,      # メイン: エージェントの役割
    setting_sources=["project"]        # 補足: プロジェクト固有の情報
)
```

---

## 🎓 まとめ

### 確認できたこと

1. **CLAUDE.md の読み込み**
   - `setting_sources=["project"]` で読み込まれる
   - ファイルの全内容が認識される
   - プロジェクトルートに配置する必要がある

2. **外部ファイルの読み込み**
   - `system_prompt` に文字列として渡すことで読み込まれる
   - ファイルの全内容が認識される
   - ファイル名、配置場所は自由

3. **両方を同時に使用**
   - 両方が読み込まれる
   - `system_prompt` が優先される（メインの役割を定義）
   - `setting_sources` は補足情報として扱われる（`<system-reminder>` 内）

### 検証方法

Claudeに「読み込んだプロンプトを報告して」と質問すれば、正確に内容が反映されていることを確認できます。

---

## 📝 ログファイル

実行すると以下のログファイルが生成されます：

- **`prompt_loading.log`**: 詳細なログ（各パターンの実行結果、エラー情報など）

---

## 🔧 トラブルシューティング

### Claude Agent SDKが見つからない

```bash
pip install claude-agent-sdk
```

### APIキーのエラー

```bash
# 環境変数を確認
echo $ANTHROPIC_API_KEY

# 環境変数を設定
export ANTHROPIC_API_KEY=your_api_key
```

### ファイルが見つからない

```bash
# ファイル構成を確認
ls -la
ls -la prompts-repo/
```

---

**調査日**: 2025-11-29
**検証方法**: Claude自身に読み込んだプロンプトの内容を報告させる
**結論**: CLAUDE.md、外部プロンプトファイル、両方の組み合わせ、すべてのパターンで完全に読み込まれることを確認
