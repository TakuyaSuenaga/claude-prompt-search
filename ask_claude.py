#!/usr/bin/env python3
"""
Ask Claude directly about loaded prompt files

This script asks Claude to report which prompt configuration files
were loaded in the session.
"""

import asyncio
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('claude_response.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

        logger.info("=" * 80)
        logger.info("Asking Claude about loaded prompt files")
        logger.info("=" * 80)

        # Create options to load project settings
        options = ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code"
            },
            setting_sources=["project"],  # Load CLAUDE.md and .claude/ files
            allowed_tools=["Read"],
            permission_mode="acceptEdits"
        )

        # Ask Claude about loaded prompt files
        prompt = """このセッションで読み込んだプロンプトの設定ファイルを優先順位と内容を報告してください。

具体的には、以下の情報を教えてください：
1. どのプロンプトファイルが読み込まれましたか？（例: CLAUDE.md, .claude/system.md など）
2. それらのファイルはどの順番で読み込まれましたか？
3. 各ファイルの内容や目的は何ですか？
4. プロンプトの優先順位はどうなっていますか？

可能な限り詳しく説明してください。"""

        logger.info(f"Prompt sent to Claude:\n{prompt}")
        logger.info("=" * 80)
        logger.info("Claude's Response:")
        logger.info("=" * 80)

        # Collect all text responses
        full_response = []

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                        full_response.append(block.text)

        logger.info("=" * 80)
        logger.info("Response complete! Check claude_response.log for full details.")

        # Save the full response to a separate file
        with open('claude_full_response.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(full_response))

        logger.info("Full response saved to: claude_full_response.txt")

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Please install: pip install claude-agent-sdk")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
