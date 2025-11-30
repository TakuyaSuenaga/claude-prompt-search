#!/usr/bin/env python3
"""
Claude Agent SDK プロンプト読み込み検証スクリプト

このスクリプトは3つのパターンでプロンプトファイルの読み込みを検証します：
1. CLAUDE.md のみ
2. 外部プロンプトファイル（Design.md）のみ
3. 両方を同時に使用

各パターンで、Claudeに読み込んだプロンプトの内容を報告させて検証します。
"""

import asyncio
import logging
import sys
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('prompt_loading.log')
    ]
)

logger = logging.getLogger(__name__)


async def test_pattern_1_claude_md():
    """パターン1: CLAUDE.md のみを読み込む"""

    logger.info("=" * 80)
    logger.info("パターン1: CLAUDE.md のみ")
    logger.info("=" * 80)

    options = ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code"
        },
        setting_sources=["project"],  # CLAUDE.mdを読み込む
        allowed_tools=["Read"],
        permission_mode="acceptEdits"
    )

    verification_prompt = """
読み込まれたプロンプトファイルについて報告してください：

1. どのファイルが読み込まれましたか？
2. プロンプトの冒頭部分（最初の100文字）を引用してください
3. あなたの役割は何ですか？
"""

    print("\n" + "=" * 80)
    print("【パターン1】CLAUDE.md のみ - 検証結果")
    print("=" * 80 + "\n")

    async for message in query(prompt=verification_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                    logger.info(f"Response: {block.text[:200]}...")


async def test_pattern_2_external_prompt():
    """パターン2: 外部プロンプトファイル（Design.md）のみを読み込む"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("パターン2: 外部プロンプトファイル（Design.md）のみ")
    logger.info("=" * 80)

    # 外部プロンプトを読み込む
    prompt_path = Path("prompts-repo/Design.md")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        external_prompt = f.read()

    logger.info(f"外部プロンプト読み込み: {len(external_prompt)} 文字")

    options = ClaudeAgentOptions(
        system_prompt=external_prompt,  # 外部プロンプトを直接指定
        allowed_tools=["Read"],
        permission_mode="acceptEdits"
    )

    verification_prompt = """
読み込まれたプロンプトについて報告してください：

1. プロンプトのタイトルは何ですか？
2. あなたの役割は何ですか？
3. 使用可能なツールは何ですか？
4. プロンプトの冒頭部分（最初の100文字）を引用してください
"""

    print("\n" + "=" * 80)
    print("【パターン2】外部プロンプト（Design.md）のみ - 検証結果")
    print("=" * 80 + "\n")

    async for message in query(prompt=verification_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                    logger.info(f"Response: {block.text[:200]}...")


async def test_pattern_3_combined():
    """パターン3: CLAUDE.md + 外部プロンプトを同時に使用"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("パターン3: CLAUDE.md + 外部プロンプト（両方を使用）")
    logger.info("=" * 80)

    # 外部プロンプトを読み込む
    prompt_path = Path("prompts-repo/Design.md")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        external_prompt = f.read()

    logger.info(f"外部プロンプト読み込み: {len(external_prompt)} 文字")

    options = ClaudeAgentOptions(
        system_prompt=external_prompt,   # 外部プロンプト
        setting_sources=["project"],      # CLAUDE.md も読み込む
        allowed_tools=["Read"],
        permission_mode="acceptEdits"
    )

    verification_prompt = """
両方のプロンプトファイルについて報告してください：

1. **読み込まれたファイル**:
   - CLAUDE.md は読み込まれましたか？
   - Design.md は読み込まれましたか？

2. **優先順位**:
   - どちらのプロンプトが主要な役割を定義していますか？
   - もう一方はどのように扱われていますか？

3. **あなたの役割**:
   - 現在、あなたの主要な役割は何ですか？
"""

    print("\n" + "=" * 80)
    print("【パターン3】CLAUDE.md + 外部プロンプト（両方）- 検証結果")
    print("=" * 80 + "\n")

    async for message in query(prompt=verification_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                    logger.info(f"Response: {block.text[:200]}...")


async def test_pattern_4_append():
    """パターン4: Claude Codeプリセット + 外部プロンプト（append）+ CLAUDE.md"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("パターン4: Claude Code + 外部プロンプト（append）+ CLAUDE.md")
    logger.info("=" * 80)

    # 外部プロンプトを読み込む
    prompt_path = Path("prompts-repo/Design.md")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        external_prompt = f.read()

    logger.info(f"外部プロンプト読み込み: {len(external_prompt)} 文字")

    options = ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",  # Claude Code標準プロンプト（ベース）
            "append": external_prompt  # Design.mdを追加
        },
        setting_sources=["project"],  # CLAUDE.md も読み込む
        allowed_tools=["Read"],
        permission_mode="acceptEdits"
    )

    verification_prompt = """
3つのプロンプトソースについて報告してください：

1. **読み込まれたプロンプト**:
   - Claude Code標準プロンプトは読み込まれていますか？
   - Design.md（appendで追加）は読み込まれていますか？
   - CLAUDE.md（setting_sources）は読み込まれていますか？

2. **優先順位と統合状況**:
   - それぞれがどのように統合されていますか？
   - 主要な役割を定義しているのはどれですか？

3. **あなたの役割**:
   - 現在、あなたの主要な役割は何ですか？
   - どのプロンプトの影響を最も受けていますか？
"""

    print("\n" + "=" * 80)
    print("【パターン4】Claude Code + append + CLAUDE.md - 検証結果")
    print("=" * 80 + "\n")

    async for message in query(prompt=verification_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                    logger.info(f"Response: {block.text[:200]}...")


async def main():
    print("\n" + "=" * 80)
    print("Claude Agent SDK プロンプト読み込み検証")
    print("=" * 80)
    print("\n4つのパターンで検証します：")
    print("1. CLAUDE.md のみ")
    print("2. 外部プロンプト（Design.md）のみ")
    print("3. 外部プロンプト + CLAUDE.md（両方を同時に使用）")
    print("4. Claude Code + 外部プロンプト（append）+ CLAUDE.md")
    print("\n" + "=" * 80)

    try:
        # パターン1: CLAUDE.md のみ
        await test_pattern_1_claude_md()

        # パターン2: 外部プロンプトのみ
        await test_pattern_2_external_prompt()

        # パターン3: 両方を使用
        await test_pattern_3_combined()

        # パターン4: append を使用
        await test_pattern_4_append()

        print("\n" + "=" * 80)
        print("全ての検証が完了しました")
        print("詳細なログは prompt_loading.log を参照してください")
        print("=" * 80 + "\n")

    except FileNotFoundError as e:
        logger.error(f"ファイルが見つかりません: {e}")
        logger.error("prompts-repo/Design.md が存在することを確認してください")
        sys.exit(1)

    except ImportError as e:
        logger.error(f"インポートエラー: {e}")
        logger.error("pip install claude-agent-sdk を実行してください")
        sys.exit(1)

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
