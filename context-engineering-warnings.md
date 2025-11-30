# ⚠️ 大量ファイルをプロンプトに入れる問題点

## 1. コンテキスト制限の壁

**悪い例:**
```python
# 例: 会話履歴とログをすべて読み込む（危険）
history_files = glob.glob("conversation_history/*.md")
log_files = glob.glob("execution_logs/*.md")

all_context = ""
for file in history_files + log_files:
    with open(file, 'r') as f:
        all_context += f.read()  # 数十万〜数百万文字になる可能性

# これをプロンプトに入れると...
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": all_context  # ❌ コンテキスト上限を超える
    }
)
```

**問題:**
- Claude APIのコンテキスト上限: 200,000トークン (約15万文字)
- 大量のログ/履歴はすぐに上限を超える
- 超えた部分は切り捨てられるか、エラーになる

---

## 2. コスト爆発

- 入力トークン数に比例して課金
- 毎回大量のコンテキストを送るとコストが莫大になる

---

## 3. レスポンス速度の低下

- コンテキストが大きいほど処理が遅くなる
- 実用的な速度で動作しなくなる

---

## 4. ノイズ問題

- 関係ない過去の会話やログも含まれる
- Claudeが混乱し、精度が低下する

---

# ✅ 正しいアプローチ

## アプローチ1: 必要な情報だけを動的に抽出

```python
from pathlib import Path
import json

def get_relevant_context(current_task):
    """現在のタスクに関連する情報だけを抽出"""

    # 1. キーワードベースで関連ファイルを検索
    relevant_files = search_relevant_logs(current_task)

    # 2. 最新N件だけを取得（古いものは除外）
    recent_conversations = get_recent_conversations(limit=5)

    # 3. サマリーを作成（全文ではなく要約）
    summary = create_summary(relevant_files, recent_conversations)

    return summary  # 数千文字程度に収める

# プロンプトに追加
with open("prompts-repo/Coding.md", 'r') as f:
    coding_prompt = f.read()

context = get_relevant_context(current_task="バグ修正")

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": f"{coding_prompt}\n\n## Recent Context\n{context}"
    }
)
```

---

## アプローチ2: RAG（Retrieval-Augmented Generation）

```python
from claude_agent_sdk import ClaudeAgentOptions

def retrieve_relevant_info(query):
    """ベクトル検索で関連情報を取得"""
    # 1. 過去のログ/会話をベクトルDBに格納（事前処理）
    # 2. クエリに類似した情報を検索
    # 3. トップK件を取得
    return top_k_results

# 実行時
query = "認証エラーの修正方法"
relevant_context = retrieve_relevant_info(query)

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": f"## Relevant Past Information\n{relevant_context}"
    }
)
```

---

## アプローチ3: 階層的サマリー

```python
def create_hierarchical_summary():
    """階層的に要約を作成"""

    # レベル1: 最新1週間のサマリー
    week_summary = summarize_logs(days=7)

    # レベル2: 最新1ヶ月の重要なイベントのみ
    month_highlights = extract_highlights(days=30)

    # レベル3: プロジェクト全体の主要な決定事項
    project_decisions = get_key_decisions()

    return f"""
# Recent Activity (Last 7 days)
{week_summary}

# Important Events (Last 30 days)
{month_highlights}

# Key Project Decisions
{project_decisions}
"""  # 合計でも数千文字に収まる
```

---

# 📊 実装例: スマートなコンテキスト管理

```python
from pathlib import Path
from datetime import datetime, timedelta
import json

class ContextManager:
    def __init__(self, max_context_chars=10000):
        self.max_context_chars = max_context_chars
        self.history_dir = Path("conversation_history")
        self.log_dir = Path("execution_logs")

    def get_context_for_task(self, task_type, task_description):
        """タスクに応じた最適なコンテキストを取得"""

        context_parts = []

        # 1. タスクタイプ別の重要情報
        if task_type == "bug_fix":
            context_parts.append(self._get_recent_errors())
            context_parts.append(self._get_similar_past_fixes(task_description))
        elif task_type == "feature":
            context_parts.append(self._get_architecture_decisions())
            context_parts.append(self._get_coding_patterns())

        # 2. 最近の会話（最新5件のみ）
        context_parts.append(self._get_recent_conversations(limit=5))

        # 3. 文字数制限内に収める
        full_context = "\n\n".join(context_parts)
        if len(full_context) > self.max_context_chars:
            full_context = full_context[:self.max_context_chars] + "\n...(truncated)"

        return full_context

    def _get_recent_errors(self):
        """直近のエラーログのみ取得"""
        cutoff = datetime.now() - timedelta(days=7)
        recent_logs = []

        for log_file in sorted(self.log_dir.glob("*.md"), reverse=True):
            if log_file.stat().st_mtime > cutoff.timestamp():
                recent_logs.append(log_file.read_text()[:500])  # 各ログ最大500文字
                if len(recent_logs) >= 3:  # 最新3件まで
                    break

        return "## Recent Errors\n" + "\n".join(recent_logs)

# 使用例
context_manager = ContextManager(max_context_chars=10000)

# Coding Agentの起動
with open("prompts-repo/Coding.md", 'r') as f:
    coding_prompt = f.read()

smart_context = context_manager.get_context_for_task(
    task_type="bug_fix",
    task_description="認証エラーの修正"
)

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": f"{coding_prompt}\n\n{smart_context}"
    }
)
```

---

# 💡 上司への提案

## 現状のアプローチの問題点を説明

1. **コスト**: 毎回大量コンテキスト送信 → 月額数十万円〜数百万円の可能性
2. **速度**: レスポンスが数分かかる可能性
3. **精度**: ノイズが多すぎて逆に性能低下
4. **制限**: APIの上限を超えてエラー

## 代替案の提案

**「スマートコンテキスト抽出システム」**
- 関連情報だけを動的に抽出
- 要約技術で情報密度を最大化
- コンテキスト上限内に収める
- コストを1/10以下に削減
- レスポンス速度を維持

---

# 結論

- 大量ファイルをそのまま入れる = ❌ **NG**
- 関連情報を賢く抽出して入れる = ✅ **OK**

必要であれば、スマートコンテキスト管理システムの実装例を詳しく作成できます。
