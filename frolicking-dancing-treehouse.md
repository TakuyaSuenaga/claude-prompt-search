# エージェント起動時の会話履歴・実行ログ再現のためのコンテキストエンジニアリング手法

## 調査結果サマリー

Web検索と現在のプロジェクト（Claude Agent SDK プロンプト読み込み検証）の分析から、RAG以外のコンテキストエンジニアリング手法を特定しました。

---

## RAG以外の主要なコンテキストエンジニアリング手法（2025年最新）

### 1. **Pruning/Trimming（刈り込み）**
**概要**: 会話が長くなった際に、最も古いメッセージを削除する手法

**実装方法（Claude Agent SDK）**:
```python
def load_trimmed_context(max_messages=10):
    """最新N件のメッセージのみを保持"""
    all_messages = load_all_conversation_history()
    recent_messages = all_messages[-max_messages:]  # 最新10件

    context = "\n".join([f"- {msg}" for msg in recent_messages])

    return f"## Recent Conversation History\n{context}"

# 使用例
with open("prompts-repo/Coding.md", 'r') as f:
    coding_prompt = f.read()

trimmed_context = load_trimmed_context(max_messages=10)

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": f"{coding_prompt}\n\n{trimmed_context}"
    }
)
```

**メリット**: シンプル、実装が容易
**デメリット**: 重要な古い情報が失われる可能性

---

### 2. **Compaction/Summarization（要約）**
**概要**: 古い会話部分をLLMに要約させ、トークン数を削減

**実装方法（Claude Agent SDK）**:
```python
def create_hierarchical_summary():
    """階層的要約を作成"""
    # レベル1: 直近1週間の詳細ログ
    week_logs = get_logs(days=7)

    # レベル2: 先月の要約（事前にLLMで要約生成）
    month_summary = """
    ## November Summary
    - 主要決定事項: マイクロサービスアーキテクチャ採用
    - 解決した問題: 認証エラー3件
    - 進行中タスク: APIゲートウェイ実装
    """

    # レベル3: プロジェクト全体の重要なマイルストーン
    project_milestones = """
    ## Project Milestones
    - Phase 1: 設計完了（10/15）
    - Phase 2: 実装中（11/01 - 進行中）
    """

    return f"{project_milestones}\n\n{month_summary}\n\n## This Week\n{week_logs}"

# 使用例
summary_context = create_hierarchical_summary()

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": summary_context
    },
    setting_sources=["project"]  # CLAUDE.mdにメタ情報
)
```

**メリット**: 重要情報を保持しつつトークン削減
**デメリット**: 要約生成にコストがかかる

---

### 3. **Structured Note-Taking（構造化メモ）**
**概要**: 会話履歴とは別のドキュメントに重要情報を記録

**実装方法（Claude Agent SDK）**:
```python
# ディレクトリ構造
# prompts-repo/
# ├── agent-notes/
# │   ├── decisions.md      # 決定事項
# │   ├── open-issues.md    # 未解決の問題
# │   └── code-patterns.md  # コーディングパターン
# └── session-logs/
#     └── current.md         # 現在のセッション

def load_structured_notes():
    """構造化されたメモを読み込む"""
    notes_dir = Path("prompts-repo/agent-notes")

    decisions = (notes_dir / "decisions.md").read_text()
    issues = (notes_dir / "open-issues.md").read_text()
    patterns = (notes_dir / "code-patterns.md").read_text()

    return f"{decisions}\n\n{issues}\n\n{patterns}"

# 使用例
structured_notes = load_structured_notes()

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": structured_notes
    }
)
```

**メリット**: 情報の構造化、検索性向上
**デメリット**: メンテナンスコスト

---

### 4. **Context Caching（コンテキストキャッシュ）**
**概要**: 繰り返し使用されるコンテキストをキャッシュしてコスト削減

#### 4-A. Anthropic API Prompt Caching（ネイティブ）

**実装方法（Claude Agent SDK）**:
```python
# Anthropic APIのPrompt Caching機能を活用
def load_cached_context():
    """キャッシュ可能なコンテキストを準備"""
    # 静的な部分（変更されない）をキャッシュ対象に
    static_context = """
    ## Project Background
    [プロジェクトの基本情報 - 変更されない]

    ## Coding Standards
    [コーディング規約 - 変更されない]

    ## Architecture Decisions
    [確定したアーキテクチャ決定 - 変更されない]
    """

    # 動的な部分（セッションごとに変わる）
    dynamic_context = get_recent_session_logs()

    return static_context, dynamic_context

# 使用例
static, dynamic = load_cached_context()

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": f"{static}\n\n{dynamic}"  # staticがキャッシュされる
    }
)
```

**メリット**:
- コスト大幅削減（最大90%）
- レスポンス速度向上
- 実装が簡単

**デメリット**:
- Anthropic API依存
- キャッシュ期間が5分に限定
- 細かい制御ができない

---

#### 4-B. Redis/Memcached による外部キャッシュ（推奨）

**概要**:
- より長期間のキャッシュ（時間、日、週単位）
- 複数のエージェントインスタンス間で共有可能
- キャッシュの細かい制御が可能

**実装方法（Redis使用）**:

```python
import redis
import hashlib
import json
from datetime import timedelta
from pathlib import Path

class RedisContextCache:
    """Redisを使用したコンテキストキャッシュシステム"""

    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = timedelta(hours=24)  # デフォルト24時間

    def _generate_cache_key(self, key_data):
        """キャッシュキーを生成"""
        # ファイルパス、バージョン、タイプなどからハッシュ生成
        key_str = json.dumps(key_data, sort_keys=True)
        return f"context:{hashlib.md5(key_str.encode()).hexdigest()}"

    def get_cached_context(self, context_id, version=None):
        """キャッシュからコンテキストを取得"""
        cache_key = self._generate_cache_key({
            "id": context_id,
            "version": version or "latest"
        })

        cached = self.redis_client.get(cache_key)
        if cached:
            return cached.decode('utf-8')
        return None

    def set_cached_context(self, context_id, content, ttl=None, version=None):
        """コンテキストをキャッシュに保存"""
        cache_key = self._generate_cache_key({
            "id": context_id,
            "version": version or "latest"
        })

        ttl = ttl or self.default_ttl
        self.redis_client.setex(
            cache_key,
            ttl,
            content.encode('utf-8')
        )

    def get_or_load_context(self, context_id, loader_func, ttl=None):
        """キャッシュから取得、なければloader_funcで生成してキャッシュ"""
        cached = self.get_cached_context(context_id)

        if cached:
            return cached, True  # (content, from_cache)

        # キャッシュミス - 生成してキャッシュ
        content = loader_func()
        self.set_cached_context(context_id, content, ttl)
        return content, False

    def invalidate_cache(self, context_id, version=None):
        """キャッシュを無効化"""
        cache_key = self._generate_cache_key({
            "id": context_id,
            "version": version or "latest"
        })
        self.redis_client.delete(cache_key)

    def get_cached_file_context(self, file_path, check_modification=True):
        """ファイルベースのキャッシュ（変更検出機能付き）"""
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        # ファイルの最終更新時刻をバージョンとして使用
        mtime = file_path.stat().st_mtime if check_modification else None

        cache_key = self._generate_cache_key({
            "file": str(file_path),
            "mtime": mtime
        })

        cached = self.redis_client.get(cache_key)
        if cached:
            return cached.decode('utf-8')

        # キャッシュミス - ファイルを読み込んでキャッシュ
        content = file_path.read_text(encoding='utf-8')
        self.redis_client.setex(
            cache_key,
            self.default_ttl,
            content.encode('utf-8')
        )
        return content

# 使用例1: 基本的なキャッシュ
cache = RedisContextCache()

def load_project_info():
    """プロジェクト情報を読み込む（重い処理）"""
    return Path("prompts-repo/context/project-info.md").read_text()

# キャッシュから取得、なければ生成
project_info, from_cache = cache.get_or_load_context(
    context_id="project_info",
    loader_func=load_project_info,
    ttl=timedelta(days=7)  # 1週間キャッシュ
)

print(f"From cache: {from_cache}")

# 使用例2: ファイルベースのキャッシュ
coding_standards = cache.get_cached_file_context(
    "prompts-repo/context/coding-standards.md",
    check_modification=True  # ファイル変更を自動検出
)

# 使用例3: Claude Agent SDKとの統合
with open("prompts-repo/Coding.md", 'r') as f:
    coding_prompt = f.read()

# 複数の静的コンテキストをキャッシュから取得
static_contexts = []

# プロジェクト情報（1週間キャッシュ）
project_info, _ = cache.get_or_load_context(
    "project_info",
    lambda: Path("prompts-repo/context/project-info.md").read_text(),
    ttl=timedelta(days=7)
)
static_contexts.append(project_info)

# コーディング規約（1ヶ月キャッシュ）
coding_standards, _ = cache.get_or_load_context(
    "coding_standards",
    lambda: Path("prompts-repo/context/coding-standards.md").read_text(),
    ttl=timedelta(days=30)
)
static_contexts.append(coding_standards)

# アーキテクチャ決定（1週間キャッシュ）
architecture, _ = cache.get_or_load_context(
    "architecture_decisions",
    lambda: Path("prompts-repo/context/architecture.md").read_text(),
    ttl=timedelta(days=7)
)
static_contexts.append(architecture)

# 静的コンテキストを結合
static_context = "\n\n".join(static_contexts)

# 動的コンテキスト（キャッシュしない）
dynamic_context = get_recent_session_logs()

# Claude Agent SDKで使用
options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": f"{coding_prompt}\n\n{static_context}\n\n{dynamic_context}"
    }
)

# 使用例4: セッション要約のキャッシュ
def generate_session_summary(session_id):
    """セッション要約を生成（LLM使用 - コストが高い）"""
    # LLMで要約生成（省略）
    return "Session summary..."

session_summary, from_cache = cache.get_or_load_context(
    context_id=f"session_summary_{session_id}",
    loader_func=lambda: generate_session_summary(session_id),
    ttl=timedelta(days=30)  # 1ヶ月保持
)

if not from_cache:
    print("要約を新規生成（コストがかかった）")
else:
    print("要約をキャッシュから取得（コスト削減）")

# 使用例5: キャッシュの無効化
# コーディング規約が更新された場合
cache.invalidate_cache("coding_standards")
```

**より高度な実装例（階層キャッシュ）**:

```python
class HierarchicalRedisCache(RedisContextCache):
    """階層的キャッシュシステム"""

    def get_hierarchical_context(self, task_type):
        """タスクタイプに応じた階層的コンテキスト"""

        layers = {}

        # Layer 1: グローバル（全タスク共通）- 長期キャッシュ
        layers['global'] = self.get_or_load_context(
            "global_context",
            lambda: self._load_global_context(),
            ttl=timedelta(days=30)
        )[0]

        # Layer 2: プロジェクト固有 - 中期キャッシュ
        layers['project'] = self.get_or_load_context(
            "project_context",
            lambda: self._load_project_context(),
            ttl=timedelta(days=7)
        )[0]

        # Layer 3: タスクタイプ固有 - 短期キャッシュ
        layers[f'task_{task_type}'] = self.get_or_load_context(
            f"task_context_{task_type}",
            lambda: self._load_task_context(task_type),
            ttl=timedelta(hours=6)
        )[0]

        return layers

    def _load_global_context(self):
        """グローバルコンテキスト"""
        return Path("prompts-repo/context/global.md").read_text()

    def _load_project_context(self):
        """プロジェクトコンテキスト"""
        return Path("prompts-repo/context/project.md").read_text()

    def _load_task_context(self, task_type):
        """タスク固有コンテキスト"""
        file_map = {
            "bug_fix": "prompts-repo/context/bug-fix-patterns.md",
            "feature": "prompts-repo/context/feature-patterns.md",
            "refactor": "prompts-repo/context/refactor-patterns.md"
        }
        file_path = file_map.get(task_type, "")
        if file_path and Path(file_path).exists():
            return Path(file_path).read_text()
        return ""

# 使用例
hierarchical_cache = HierarchicalRedisCache()

layers = hierarchical_cache.get_hierarchical_context(task_type="bug_fix")

# レイヤーを結合
full_context = f"""
## Global Context
{layers['global']}

## Project Context
{layers['project']}

## Bug Fix Patterns
{layers['task_bug_fix']}
"""

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": full_context
    }
)
```

**Redisキャッシュのメリット**:
- ✅ 長期間のキャッシュ（時間、日、週、月単位）
- ✅ 複数のエージェントインスタンス間で共有可能
- ✅ ファイル変更の自動検出
- ✅ 階層的キャッシュ管理
- ✅ TTL（有効期限）の柔軟な設定
- ✅ 手動でのキャッシュ無効化が可能
- ✅ キャッシュヒット率の監視が可能
- ✅ 分散システムに対応

**Redisキャッシュのデメリット**:
- ❌ Redisサーバーのセットアップが必要
- ❌ 実装が複雑
- ❌ メモリ管理が必要
- ❌ ネットワークレイテンシ

**代替キャッシュシステム**:

1. **Memcached**: Redisと同様の使い方、よりシンプル
2. **DiskCache**: ファイルベースのキャッシュ、サーバー不要
3. **SQLite**: 構造化データのキャッシュに適している

**DiskCache実装例（サーバー不要）**:

```python
from diskcache import Cache
from pathlib import Path

class DiskContextCache:
    """ディスクベースのキャッシュ（Redis不要）"""

    def __init__(self, cache_dir=".context_cache"):
        self.cache = Cache(cache_dir)

    def get_or_load_context(self, context_id, loader_func, ttl=86400):
        """キャッシュから取得、なければ生成"""
        cached = self.cache.get(context_id)

        if cached is not None:
            return cached, True

        content = loader_func()
        self.cache.set(context_id, content, expire=ttl)
        return content, False

# 使用例
cache = DiskContextCache()

project_info, from_cache = cache.get_or_load_context(
    "project_info",
    lambda: Path("prompts-repo/context/project-info.md").read_text(),
    ttl=86400 * 7  # 7日間
)
```

**requirements.txt への追加**:
```
# Redis使用の場合
redis>=5.0.0

# DiskCache使用の場合
diskcache>=5.6.3
```

---

### 5. **Selective Context Injection（選択的コンテキスト注入）**
**概要**: タスクに関連する情報だけを動的に選択して注入

**実装方法（Claude Agent SDK）**:
```python
def get_relevant_context(current_task, task_type):
    """タスクタイプに応じた関連コンテキストを抽出"""

    context_parts = []

    if task_type == "bug_fix":
        # バグ修正には: エラーログ + 過去の類似修正
        context_parts.append(get_recent_errors(limit=3))
        context_parts.append(get_similar_past_fixes(current_task))

    elif task_type == "feature":
        # 新機能には: アーキテクチャ決定 + コーディングパターン
        context_parts.append(get_architecture_decisions())
        context_parts.append(get_coding_patterns())

    elif task_type == "refactor":
        # リファクタリングには: コード品質基準 + 過去のリファクタリング例
        context_parts.append(get_code_quality_standards())
        context_parts.append(get_refactoring_examples())

    return "\n\n".join(context_parts)

# 使用例
relevant_context = get_relevant_context(
    current_task="認証エラーの修正",
    task_type="bug_fix"
)

with open("prompts-repo/Coding.md", 'r') as f:
    coding_prompt = f.read()

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": f"{coding_prompt}\n\n{relevant_context}"
    }
)
```

**メリット**: ノイズ削減、タスク特化
**デメリット**: 関連性判定ロジックの実装が必要

---

### 6. **Multi-Agent Isolation（マルチエージェント分離）**
**概要**: 複数のエージェントにタスクを分割し、各エージェントが独立したコンテキストを持つ

**実装方法（Claude Agent SDK）**:
```python
# 現在のプロジェクトのパターン2を応用
# 各エージェントが専用のプロンプトファイルとコンテキストを持つ

# Design Agent
with open("prompts-repo/Design.md", 'r') as f:
    design_prompt = f.read()

design_context = get_design_specific_context()

design_agent = ClaudeAgentOptions(
    system_prompt=f"{design_prompt}\n\n{design_context}"
)

# Coding Agent
with open("prompts-repo/Coding.md", 'r') as f:
    coding_prompt = f.read()

coding_context = get_coding_specific_context()

coding_agent = ClaudeAgentOptions(
    system_prompt=f"{coding_prompt}\n\n{coding_context}"
)

# Testing Agent
with open("prompts-repo/Testing.md", 'r') as f:
    testing_prompt = f.read()

testing_context = get_testing_specific_context()

testing_agent = ClaudeAgentOptions(
    system_prompt=f"{testing_prompt}\n\n{testing_context}"
)
```

**メリット**: コンテキスト汚染を防ぐ、専門性の向上
**デメリット**: エージェント間の調整コスト

---

### 7. **Session-Based Memory（セッションベースメモリ）**
**概要**: セッション単位でコンテキストを管理し、セッション終了時に要約を保存

**実装方法（Claude Agent SDK）**:
```python
class SessionManager:
    def __init__(self, session_id):
        self.session_id = session_id
        self.session_dir = Path(f"prompts-repo/sessions/{session_id}")
        self.session_dir.mkdir(exist_ok=True, parents=True)

    def start_session(self, task_description):
        """セッション開始"""
        # 前セッションの要約を読み込む
        previous_summary = self.load_previous_summary()

        # 新しいセッションのコンテキストを初期化
        session_context = f"""
## Previous Sessions Summary
{previous_summary}

## Current Session
Task: {task_description}
Started: {datetime.now()}
"""

        (self.session_dir / "current.md").write_text(session_context)
        return session_context

    def end_session(self):
        """セッション終了時に要約を生成"""
        # LLMに要約を生成させる（別途実装）
        summary = generate_session_summary()
        (self.session_dir / "summary.md").write_text(summary)

    def load_previous_summary(self):
        """前セッションの要約を読み込む"""
        summaries = list(Path("prompts-repo/sessions").glob("*/summary.md"))
        if summaries:
            # 最新の要約を取得
            latest = max(summaries, key=lambda p: p.stat().st_mtime)
            return latest.read_text()
        return "No previous sessions"

# 使用例
session = SessionManager(session_id="20251130_bug_fix")
session_context = session.start_session("認証エラーの修正")

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": session_context
    }
)

# タスク完了後
session.end_session()
```

**メリット**: セッション間の継続性、自動要約
**デメリット**: セッション管理の複雑さ

---

### 8. **Dynamic Prompting（動的プロンプティング）**
**概要**: 会話の進行に応じてプロンプトをリアルタイムで調整

**実装方法（Claude Agent SDK）**:
```python
def get_adaptive_context(conversation_state):
    """会話の状態に応じてコンテキストを調整"""

    if conversation_state["phase"] == "planning":
        return """
## Current Phase: Planning
Focus on: Architecture decisions, design patterns, requirements
Avoid: Implementation details
"""

    elif conversation_state["phase"] == "implementation":
        return """
## Current Phase: Implementation
Focus on: Code quality, best practices, error handling
Refer to: Approved design from planning phase
"""

    elif conversation_state["phase"] == "testing":
        return """
## Current Phase: Testing
Focus on: Test coverage, edge cases, performance
Validate against: Implementation and design specifications
"""

    return ""

# 使用例
conversation_state = {
    "phase": "implementation",
    "progress": 60,
    "current_file": "src/auth.py"
}

adaptive_context = get_adaptive_context(conversation_state)

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": adaptive_context
    }
)
```

**メリット**: 会話の文脈に適応、効率的
**デメリット**: 状態管理の実装が必要

---

## Claude Agent SDKでの推奨実装パターン

現在のプロジェクト（4つのパターン検証）を踏まえた推奨構成:

### **パターンA: 階層的コンテキスト管理（推奨）**

```python
from pathlib import Path
from datetime import datetime, timedelta

class HierarchicalContextManager:
    """階層的コンテキスト管理システム"""

    def __init__(self, max_context_tokens=10000):
        self.max_context_tokens = max_context_tokens
        self.context_dir = Path("prompts-repo/context")
        self.context_dir.mkdir(exist_ok=True, parents=True)

    def build_context(self, task_type, task_description):
        """タスクに応じた最適なコンテキストを構築"""

        layers = []

        # Layer 1: Static Project Info (キャッシュ可能)
        static = self.get_static_context()
        layers.append(("static", static, "high_priority"))

        # Layer 2: Session Summary (要約)
        summary = self.get_session_summary()
        layers.append(("summary", summary, "medium_priority"))

        # Layer 3: Recent Context (最新情報)
        recent = self.get_recent_context(days=7)
        layers.append(("recent", recent, "high_priority"))

        # Layer 4: Task-Specific (タスク特化)
        task_specific = self.get_task_specific_context(task_type, task_description)
        layers.append(("task_specific", task_specific, "highest_priority"))

        # トークン予算内に収める
        return self.optimize_layers(layers)

    def get_static_context(self):
        """静的コンテキスト（プロジェクト情報）"""
        static_file = self.context_dir / "static.md"
        if static_file.exists():
            return static_file.read_text()
        return ""

    def get_session_summary(self):
        """セッション要約"""
        summary_file = self.context_dir / "session_summary.md"
        if summary_file.exists():
            return summary_file.read_text()
        return ""

    def get_recent_context(self, days=7):
        """最近のコンテキスト"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_logs = []

        logs_dir = self.context_dir / "logs"
        if logs_dir.exists():
            for log_file in sorted(logs_dir.glob("*.md"), reverse=True):
                if datetime.fromtimestamp(log_file.stat().st_mtime) > cutoff:
                    recent_logs.append(log_file.read_text()[:1000])  # 各ログ最大1000文字
                    if len(recent_logs) >= 5:  # 最新5件まで
                        break

        return "\n\n".join(recent_logs)

    def get_task_specific_context(self, task_type, task_description):
        """タスク特化コンテキスト"""
        # Selective Context Injectionの実装
        if task_type == "bug_fix":
            return self.get_bug_fix_context(task_description)
        elif task_type == "feature":
            return self.get_feature_context(task_description)
        else:
            return ""

    def optimize_layers(self, layers):
        """トークン予算内にレイヤーを最適化"""
        # 優先度順にソート
        priority_order = {
            "highest_priority": 0,
            "high_priority": 1,
            "medium_priority": 2,
            "low_priority": 3
        }

        sorted_layers = sorted(layers, key=lambda x: priority_order[x[2]])

        result = []
        total_tokens = 0

        for name, content, priority in sorted_layers:
            content_tokens = len(content.split())  # 簡易トークン計算

            if total_tokens + content_tokens <= self.max_context_tokens:
                result.append(f"## {name.title()}\n{content}")
                total_tokens += content_tokens
            else:
                # トークン制限に達した場合は切り詰め
                remaining = self.max_context_tokens - total_tokens
                if remaining > 100:  # 最低100トークンは確保
                    truncated = " ".join(content.split()[:remaining])
                    result.append(f"## {name.title()}\n{truncated}...[truncated]")
                break

        return "\n\n".join(result)

# 使用例
context_manager = HierarchicalContextManager(max_context_tokens=10000)

# Coding Agentの起動
with open("prompts-repo/Coding.md", 'r') as f:
    coding_prompt = f.read()

optimized_context = context_manager.build_context(
    task_type="bug_fix",
    task_description="認証エラーの修正"
)

options = ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": f"{coding_prompt}\n\n{optimized_context}"
    },
    setting_sources=["project"]  # CLAUDE.mdにプロジェクトメタ情報
)
```

---

## 手法の比較表

| 手法 | 実装難度 | トークン効率 | 情報保持率 | コスト | 推奨用途 |
|------|---------|------------|-----------|--------|---------|
| **Pruning** | 低 | 高 | 低 | 低 | 短期タスク |
| **Summarization** | 中 | 高 | 中 | 中 | 長期プロジェクト |
| **Structured Notes** | 中 | 中 | 高 | 低 | ナレッジ管理 |
| **Context Caching** | 低 | 最高 | 高 | 最低 | 繰り返しタスク |
| **Selective Injection** | 高 | 高 | 高 | 低 | タスク特化 |
| **Multi-Agent** | 高 | 中 | 高 | 中 | 複雑なワークフロー |
| **Session Memory** | 中 | 高 | 中 | 中 | 会話型アプリ |
| **Dynamic Prompting** | 高 | 高 | 高 | 中 | 適応型システム |

---

## 実装推奨

現在の業務要件（コーディングエージェントに過去の会話履歴・ログを提供）に対して:

### 推奨アプローチ: **ハイブリッド方式**

1. **Context Caching** (静的な部分)
   - プロジェクト情報、コーディング規約など変更されない部分をキャッシュ
   - コスト削減効果が最大

2. **Hierarchical Summarization** (動的な部分)
   - 過去のセッションを階層的に要約
   - 重要情報を保持しつつトークン削減

3. **Selective Context Injection** (タスク特化)
   - バグ修正、新機能開発など、タスクタイプに応じた関連情報のみ注入
   - ノイズ削減

4. **Structured Notes** (ナレッジベース)
   - 重要な決定事項、コーディングパターンを別ファイルで管理
   - 長期的な知識蓄積

### 実装ステップ

1. ディレクトリ構造の準備
2. `HierarchicalContextManager`クラスの実装
3. 各種コンテキスト抽出関数の実装
4. Claude Agent SDKとの統合
5. テストとトークン使用量の検証

---

## 参考資料

### Web検索結果からの主要ソース

- [Effective context engineering for AI agents - Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Context Engineering in LLM-Based Agents - Medium](https://jtanruan.medium.com/context-engineering-in-llm-based-agents-d670d6b439bc)
- [Context Engineering - LlamaIndex](https://www.llamaindex.ai/blog/context-engineering-what-it-is-and-techniques-to-consider)
- [LLM Context Management Guide - 16x Engineer](https://eval.16x.engineer/blog/llm-context-management-guide)
- [Context Window Management for AI Agents - Maxim](https://www.getmaxim.ai/articles/context-window-management-strategies-for-long-context-ai-agents-and-chatbots/)
- [Managing Context in Conversational AI - Zoice](https://zoice.ai/blog/managing-context-in-conversational-ai/)

### 追加リソース

- ACE (Agentic Context Engineering) Framework - [arXiv:2510.04618](https://arxiv.org/abs/2510.04618)
- OpenAI Cookbook - [Context Engineering Guide](https://cookbook.openai.com/examples/agents_sdk/session_memory)
- Microsoft AI Agents Guide - [Context Engineering](https://microsoft.github.io/ai-agents-for-beginners/12-context-engineering/)
