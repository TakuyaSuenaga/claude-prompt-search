#!/usr/bin/env python3
"""
Claude Agent SDK Prompt Loading Order Investigation

This script runs a simple Claude Agent SDK query and logs
the order in which prompt files are loaded.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('prompt_loading.log')
    ]
)

logger = logging.getLogger(__name__)

# Monkey-patch file reading functions to trace prompt loading
original_open = open
file_read_order = []

def traced_open(file, *args, **kwargs):
    """Wrapper around open() to trace file reads"""
    result = original_open(file, *args, **kwargs)

    # Check if this looks like a prompt file being read
    if isinstance(file, (str, Path)):
        file_str = str(file)
        # Track reads of .md files and system prompt files
        if any(pattern in file_str.lower() for pattern in [
            'claude.md', '.claude', '.md', 'system', 'prompt', 'instruction', 'settings'
        ]) and not any(exclude in file_str.lower() for exclude in [
            'site-packages', 'node_modules', '__pycache__'
        ]):
            file_read_order.append(file_str)
            logger.info(f"📄 FILE READ: {file_str}")

    return result

# Apply the monkey-patch
import builtins
builtins.open = traced_open

async def main():
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions

        logger.info("=" * 80)
        logger.info("Starting Claude Agent SDK Prompt Loading Investigation")
        logger.info("=" * 80)

        # Create options to load project settings (including CLAUDE.md)
        logger.info("Creating query with setting_sources=['project']...")
        options = ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code"
            },
            setting_sources=["project"],  # This will load CLAUDE.md and .claude/ files
            allowed_tools=["Read", "Write"],
            permission_mode="acceptEdits"
        )

        logger.info("=" * 80)
        logger.info("Prompt Files Read During Setup (in order):")
        logger.info("=" * 80)

        for i, file_path in enumerate(file_read_order, 1):
            logger.info(f"{i}. {file_path}")

        logger.info("=" * 80)

        # Run a simple task
        logger.info("Running a simple test query...")
        async for message in query(
            prompt="Hello! Please respond with a simple greeting and tell me what files you can see.",
            options=options
        ):
            logger.info(f"Message received: {type(message).__name__}")

        logger.info("=" * 80)
        logger.info("All Prompt Files Read (in order):")
        logger.info("=" * 80)

        for i, file_path in enumerate(file_read_order, 1):
            logger.info(f"{i}. {file_path}")

        logger.info("=" * 80)
        logger.info("Investigation complete! Check prompt_loading.log for full details.")

    except ImportError as e:
        logger.error("=" * 80)
        logger.error("ERROR: Claude Agent SDK not installed")
        logger.error("=" * 80)
        logger.error(f"Import error: {e}")
        logger.error("\nPlease install the Claude Agent SDK:")
        logger.error("  pip install claude-agent-sdk")
        logger.error("\nThen set your API key:")
        logger.error("  export ANTHROPIC_API_KEY=your_api_key")
        sys.exit(1)

    except Exception as e:
        logger.error("=" * 80)
        logger.error("ERROR: An error occurred")
        logger.error("=" * 80)
        logger.error(f"Error: {e}", exc_info=True)

        # Still show files that were read
        if file_read_order:
            logger.info("=" * 80)
            logger.info("Files Read Before Error:")
            logger.info("=" * 80)
            for i, file_path in enumerate(file_read_order, 1):
                logger.info(f"{i}. {file_path}")

        sys.exit(1)
    finally:
        # Restore original open
        builtins.open = original_open

if __name__ == "__main__":
    asyncio.run(main())
