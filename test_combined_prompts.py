#!/usr/bin/env python3
"""
Combined Prompts Test - CLAUDE.md + External Prompt 同時使用の検証

setting_sources=["project"] と system_prompt を同時に使った場合、
どちらが優先されるか、または両方が読み込まれるかを確認する。
"""

import asyncio
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_combined_prompts.log')
    ]
)

logger = logging.getLogger(__name__)

async def test_combined_prompts():
    """CLAUDE.md + 外部プロンプトを同時に使用した場合のテスト"""
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

        # 1. 外部プロンプトを読み込む
        prompt_path = Path("prompts-repo/Design.md")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            external_prompt = f.read()

        logger.info("=" * 80)
        logger.info("Test: CLAUDE.md + External Prompt Combined")
        logger.info("=" * 80)
        logger.info(f"External prompt loaded: {len(external_prompt)} characters")
        logger.info("")

        # 2. 両方を同時に指定
        options = ClaudeAgentOptions(
            system_prompt=external_prompt,  # 外部プロンプト
            setting_sources=["project"],     # CLAUDE.md も読み込む
            allowed_tools=["Read"],
            permission_mode="acceptEdits"
        )

        # 3. Claudeに質問して優先順位を確認
        verification_prompt = """
あなたに与えられたシステムプロンプトについて報告してください：

1. **読み込まれたプロンプトファイル**:
   - CLAUDE.md の内容が含まれていますか？
   - Design.md の内容が含まれていますか？

2. **あなたの役割**:
   - CLAUDE.md で定義されている役割は何ですか？
   - Design.md で定義されている役割は何ですか？
   - どちらの役割が優先されていますか？

3. **プロンプトの冒頭部分**:
   - システムプロンプトの最初の部分（100文字程度）を引用してください

4. **優先順位**:
   - どちらのプロンプトが優先されていますか？
   - 両方のプロンプトが統合されていますか？それとも片方だけですか？

明確に報告してください。
"""

        print("\n" + "=" * 80)
        print("Claude's Report on Combined Prompts:")
        print("=" * 80 + "\n")

        async for message in query(prompt=verification_prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                        logger.info(f"Response: {block.text}")

        print("\n" + "=" * 80)
        print("Test Complete")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

async def main():
    print("\n" + "=" * 80)
    print("Testing Combined Prompt Sources")
    print("=" * 80)
    print("\nThis test verifies what happens when both:")
    print("1. setting_sources=['project'] (loads CLAUDE.md)")
    print("2. system_prompt=external_content (loads Design.md)")
    print("are used simultaneously.")
    print("=" * 80 + "\n")

    await test_combined_prompts()

if __name__ == "__main__":
    asyncio.run(main())
