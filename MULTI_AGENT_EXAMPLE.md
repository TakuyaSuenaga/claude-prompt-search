# マルチエージェントシステム実装例

外部リポジトリからプロンプトを読み込んで、単独のエージェントインスタンスを実行する方法の実装例です。

## 🎯 ユースケース

**シナリオ**: オーケストレーターが各エージェント用のAWSインスタンスを作成し、それぞれ専用のプロンプトファイルで動作させる

## 📁 プロジェクト構成

```
claude-prompt-search/
├── prompts-repo/              # 外部プロンプトリポジトリ
│   ├── Design.md             # Design Agent用プロンプト
│   ├── Coding.md             # Coding Agent用プロンプト（例）
│   └── Testing.md            # Testing Agent用プロンプト（例）
├── design_agent.py           # Design Agent実装
└── MULTI_AGENT_EXAMPLE.md    # このファイル
```

## ✅ 実装完了: Design Agent

### プロンプトファイル

[prompts-repo/Design.md](prompts-repo/Design.md) - Design Agent専用のシステムプロンプト

**内容**:
- 役割: ソフトウェアアーキテクチャ、UX/UI設計の専門家
- 原則: ユーザー中心設計、スケーラビリティ、保守性
- ツール: Read, Glob, Grep（コード分析用）
- 出力形式: ADR (Architecture Decision Record)

### 実装コード

[design_agent.py](design_agent.py) - 外部プロンプトを読み込む単独エージェント

**主要機能**:

```python
class DesignAgent:
    def __init__(self, prompt_repo_path: str = "prompts-repo"):
        self.prompt_repo = Path(prompt_repo_path)
        self.prompt = self._load_prompt()  # Design.mdを読み込み

    async def run(self, task: str):
        options = ClaudeAgentOptions(
            system_prompt=self.prompt,  # 外部プロンプトを直接使用
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="acceptEdits"
        )

        async for message in query(prompt=task, options=options):
            # ... 処理
```

### 実行方法

```bash
# 仮想環境内で実行
source venv/bin/activate
python design_agent.py
```

### 実行結果

Design Agentは以下を実行しました：

1. ✅ `prompts-repo/Design.md` から3,209文字のプロンプトを読み込み
2. ✅ プロンプトで指定されたADR形式で詳細な設計ドキュメントを生成
3. ✅ ユーザー認証システムの包括的な設計提案を作成
4. ✅ セキュリティ、スケーラビリティ、UXのベストプラクティスを適用

**出力サンプル**:
- アーキテクチャ図（ASCII）
- セキュリティフロー
- コンポーネント構造
- データベーススキーマ
- 実装フェーズ計画

## 🔑 重要なポイント

### 1. ファイル名の制約

❌ **できないこと**:
```python
# .claude/ ディレクトリのファイル名は変更不可
# これらはClaude Codeの規約で固定されている
.claude/system.md        # 固定
.claude/instructions.md  # 固定
.claude/commands/*.md    # 固定
```

✅ **できること**:
```python
# 外部ファイルから自由に読み込める
prompts-repo/Design.md   # 任意の名前
prompts-repo/Coding.md   # 任意の名前
prompts-repo/Testing.md  # 任意の名前

# system_promptに直接渡す
options = ClaudeAgentOptions(
    system_prompt=load_prompt("Design.md")  # ファイル名自由
)
```

### 2. setting_sources は使わない

```python
# ❌ これは使わない（.claude/ディレクトリ用）
options = ClaudeAgentOptions(
    setting_sources=["project"]  # CLAUDE.mdなどを読み込む
)

# ✅ 外部プロンプトを使う場合はこれ
options = ClaudeAgentOptions(
    system_prompt=external_prompt,  # 文字列で直接指定
    allowed_tools=[...],
    permission_mode="acceptEdits"
)
```

### 3. 単独エージェントの実装パターン

```python
class SingleAgent:
    """単独エージェントの基本パターン"""

    def __init__(self, prompt_file: str):
        # 1. 外部プロンプトを読み込む
        self.prompt = self._load_prompt(prompt_file)

    def _load_prompt(self, filename: str) -> str:
        # 2. プロンプトリポジトリから読み込み
        prompt_path = Path("prompts-repo") / filename
        with open(prompt_path, 'r') as f:
            return f.read()

    async def run(self, task: str):
        # 3. プロンプトを直接system_promptに渡す
        options = ClaudeAgentOptions(
            system_prompt=self.prompt,
            allowed_tools=self._get_tools(),
            permission_mode="acceptEdits"
        )

        # 4. タスクを実行
        async for message in query(prompt=task, options=options):
            self._process_message(message)
```

## 🚀 他のエージェントの実装例

### Coding Agent

```python
#!/usr/bin/env python3
"""Coding Agent - Implementation specialist"""

import asyncio
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions

class CodingAgent:
    def __init__(self):
        # prompts-repo/Coding.md を読み込む
        prompt_path = Path("prompts-repo/Coding.md")
        with open(prompt_path, 'r') as f:
            self.prompt = f.read()

    async def run(self, task: str):
        options = ClaudeAgentOptions(
            system_prompt=self.prompt,
            allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
            permission_mode="acceptEdits"
        )

        async for message in query(prompt=task, options=options):
            # 実装コードを生成
            pass

async def main():
    agent = CodingAgent()
    await agent.run("Implement the user authentication API endpoints")

if __name__ == "__main__":
    asyncio.run(main())
```

### Testing Agent

```python
#!/usr/bin/env python3
"""Testing Agent - QA specialist"""

import asyncio
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions

class TestingAgent:
    def __init__(self):
        # prompts-repo/Testing.md を読み込む
        prompt_path = Path("prompts-repo/Testing.md")
        with open(prompt_path, 'r') as f:
            self.prompt = f.read()

    async def run(self, task: str):
        options = ClaudeAgentOptions(
            system_prompt=self.prompt,
            allowed_tools=["Read", "Write", "Bash"],
            permission_mode="acceptEdits"
        )

        async for message in query(prompt=task, options=options):
            # テストを生成・実行
            pass

async def main():
    agent = TestingAgent()
    await agent.run("Write comprehensive tests for the authentication system")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🏗️ オーケストレーターの実装イメージ

```python
#!/usr/bin/env python3
"""Orchestrator - Manages multiple agent instances"""

import asyncio
from typing import Literal

AgentType = Literal["design", "coding", "testing"]

class Orchestrator:
    """Manages agent lifecycle on AWS instances"""

    async def create_agent_instance(self, agent_type: AgentType, task: str):
        """
        AWSインスタンスを作成して単独エージェントを実行

        実際の実装では:
        1. EC2インスタンスを作成
        2. エージェントスクリプトをデプロイ
        3. 適切なプロンプトファイルを配置
        4. エージェントを実行
        5. 結果を収集
        """

        # 疑似コード
        instance = await self.launch_ec2_instance()
        await self.deploy_agent(instance, agent_type)
        result = await self.run_agent(instance, task)
        await self.terminate_instance(instance)

        return result

    async def run_workflow(self):
        """複数エージェントを順次実行"""

        # 1. Design Agent で設計
        design_result = await self.create_agent_instance(
            "design",
            "Design the authentication system"
        )

        # 2. Coding Agent で実装
        coding_result = await self.create_agent_instance(
            "coding",
            f"Implement based on this design: {design_result}"
        )

        # 3. Testing Agent でテスト
        testing_result = await self.create_agent_instance(
            "testing",
            f"Test this implementation: {coding_result}"
        )

        return {
            "design": design_result,
            "coding": coding_result,
            "testing": testing_result
        }
```

## 📊 アーキテクチャ図

```
┌─────────────────────────────────────────────────────────┐
│                    Orchestrator                         │
│         (Manages agent lifecycle on AWS)                │
└───────────┬────────────────┬──────────────┬─────────────┘
            │                │              │
            ▼                ▼              ▼
    ┌───────────┐    ┌───────────┐  ┌───────────┐
    │ Design    │    │ Coding    │  │ Testing   │
    │ Agent     │    │ Agent     │  │ Agent     │
    │ Instance  │    │ Instance  │  │ Instance  │
    └─────┬─────┘    └─────┬─────┘  └─────┬─────┘
          │                │              │
          ▼                ▼              ▼
    ┌──────────┐     ┌──────────┐   ┌──────────┐
    │Design.md │     │Coding.md │   │Testing.md│
    │(External)│     │(External)│   │(External)│
    └──────────┘     └──────────┘   └──────────┘
```

## 💡 ベストプラクティス

### 1. プロンプトファイルの管理

```bash
# 別リポジトリとして管理
prompts-repo/
├── README.md           # プロンプトのドキュメント
├── Design.md           # バージョン管理
├── Coding.md           # レビュー可能
├── Testing.md          # チーム共有
└── templates/          # テンプレート
    └── base_agent.md
```

### 2. エージェントの設定

```python
# 各エージェントに適したツールを指定
AGENT_CONFIGS = {
    "design": {
        "tools": ["Read", "Glob", "Grep"],  # 分析のみ
        "model": "opus"  # 深い思考が必要
    },
    "coding": {
        "tools": ["Read", "Write", "Edit", "Bash"],  # 実装
        "model": "sonnet"  # バランス重視
    },
    "testing": {
        "tools": ["Read", "Write", "Bash"],  # テスト実行
        "model": "sonnet"
    }
}
```

### 3. エラーハンドリング

```python
async def run_with_retry(self, task: str, max_retries: int = 3):
    """リトライ機能付きエージェント実行"""
    for attempt in range(max_retries):
        try:
            return await self.run(task)
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## 🎓 まとめ

### ✅ できること

1. **外部プロンプトファイルから自由に読み込み**
   - ファイル名は任意
   - 他のリポジトリからも可能
   - バージョン管理が容易

2. **単独エージェントインスタンスの実行**
   - AWSインスタンス上で独立動作
   - 専用プロンプトで特化した動作
   - オーケストレーターによる管理

3. **完全なプログラム制御**
   - `system_prompt` に直接渡す
   - `setting_sources` は使用しない
   - ツールや権限をカスタマイズ

### ❌ できないこと

1. **`.claude/` ディレクトリのファイル名変更**
   - `system.md`、`instructions.md` は固定
   - Claude Codeの規約

2. **`setting_sources` との併用**
   - 外部プロンプトを使う場合は不要
   - どちらか一方を選択

## 📚 関連ファイル

- [design_agent.py](design_agent.py) - Design Agent実装
- [prompts-repo/Design.md](prompts-repo/Design.md) - Design Agent用プロンプト
- [design_agent.log](design_agent.log) - 実行ログ
- [FINDINGS.md](FINDINGS.md) - プロンプト読み込み順序の調査結果

---

このアプローチにより、オーケストレーターが各エージェント専用のAWSインスタンスを作成し、それぞれ異なるプロンプトファイルで特化した動作をさせることができます。
