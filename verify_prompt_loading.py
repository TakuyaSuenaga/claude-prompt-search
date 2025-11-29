#!/usr/bin/env python3
"""
Verify Prompt Loading - 読み込んだプロンプトファイルの確認

外部プロンプトファイルが正しく読み込まれているかを確認するスクリプト。
Claudeに読み込んだファイルと内容を報告させます。
"""

import asyncio
import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('verify_prompt_loading.log')
    ]
)

logger = logging.getLogger(__name__)

async def verify_external_prompt():
    """外部プロンプトファイルの読み込みを確認"""
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

        # 1. 外部プロンプトファイルを読み込む
        prompt_path = Path("prompts-repo/Design.md")
        logger.info("=" * 80)
        logger.info(f"Reading external prompt from: {prompt_path}")
        logger.info("=" * 80)

        with open(prompt_path, 'r', encoding='utf-8') as f:
            external_prompt = f.read()

        logger.info(f"✓ Loaded prompt: {len(external_prompt)} characters")
        logger.info(f"✓ First 200 chars: {external_prompt[:200]}...")
        logger.info("")

        # 2. プロンプトをsystem_promptに設定
        options = ClaudeAgentOptions(
            system_prompt=external_prompt,  # 外部プロンプトを直接指定
            allowed_tools=["Read"],
            permission_mode="acceptEdits"
        )

        # 3. Claudeに読み込んだプロンプトの内容を報告させる
        verification_prompt = """
あなたに与えられたシステムプロンプトについて、以下の情報を報告してください：

1. **プロンプトのソース**: どこから読み込まれたプロンプトか（ファイル名が記載されているか）
2. **あなたの役割**: システムプロンプトで定義されているあなたの役割は何ですか？
3. **使用可能なツール**: システムプロンプトで指定されているツールは何ですか？
4. **出力形式**: システムプロンプトで指定されている出力形式は何ですか？
5. **主要な指示**: システムプロンプトの主要な指示を3つ挙げてください
6. **プロンプトの冒頭部分**: システムプロンプトの最初の100文字程度を引用してください

この情報を明確に、箇条書きで報告してください。
"""

        logger.info("=" * 80)
        logger.info("Asking Claude to report loaded prompt content...")
        logger.info("=" * 80)
        print("\n" + "=" * 80)
        print("Claude's Report on Loaded Prompt:")
        print("=" * 80 + "\n")

        async for message in query(prompt=verification_prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                        logger.info(f"Response: {block.text}")

        print("\n" + "=" * 80)
        print("Verification Complete")
        print("=" * 80)

        logger.info("")
        logger.info("=" * 80)
        logger.info("Verification completed successfully")
        logger.info(f"Full log saved to: verify_prompt_loading.log")
        logger.info("=" * 80)

    except FileNotFoundError as e:
        logger.error(f"Error: Prompt file not found - {e}")
        logger.error("Please ensure prompts-repo/Design.md exists")
        sys.exit(1)

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Please install: pip install claude-agent-sdk")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        sys.exit(1)

async def verify_claude_code_preset():
    """Claude Codeプリセット + setting_sourcesの読み込みを確認"""
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

        logger.info("")
        logger.info("=" * 80)
        logger.info("Testing Claude Code Preset + setting_sources")
        logger.info("=" * 80)

        options = ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code"
            },
            setting_sources=["project"],  # CLAUDE.md と .claude/ を読み込む
            allowed_tools=["Read"],
            permission_mode="acceptEdits"
        )

        verification_prompt = """
setting_sources=["project"] を使用した場合に読み込まれるプロンプトファイルについて報告してください：

1. **読み込まれたファイル**: どのプロンプトファイルが読み込まれましたか？
   - CLAUDE.md の内容
   - .claude/system.md の内容
   - .claude/instructions.md の内容

2. **ファイルの優先順位**: これらのファイルの優先順位はどうなっていますか？

3. **各ファイルの最初の一文**: 各ファイルの冒頭部分を引用してください

明確に報告してください。
"""

        print("\n" + "=" * 80)
        print("Claude's Report on setting_sources=['project'] Files:")
        print("=" * 80 + "\n")

        async for message in query(prompt=verification_prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                        logger.info(f"Response: {block.text}")

        print("\n" + "=" * 80)
        print("setting_sources Verification Complete")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Error in preset verification: {e}", exc_info=True)

async def main():
    print("\n" + "=" * 80)
    print("Prompt Loading Verification Tool")
    print("=" * 80)
    print("\nThis tool verifies:")
    print("1. External prompt file loading (prompts-repo/Design.md)")
    print("2. Claude Code preset + setting_sources loading")
    print("=" * 80 + "\n")

    # Test 1: 外部プロンプトファイル
    logger.info("TEST 1: External Prompt File Loading")
    await verify_external_prompt()

    # Test 2: Claude Code プリセット + setting_sources
    logger.info("")
    logger.info("TEST 2: Claude Code Preset + setting_sources")
    await verify_claude_code_preset()

    print("\n" + "=" * 80)
    print("All Verification Tests Completed")
    print("Check verify_prompt_loading.log for details")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
