#!/usr/bin/env python3
"""
Design Agent - Single Agent Instance with External Prompt

This script demonstrates running a single Design Agent that loads
its prompt from an external repository (prompts-repo/Design.md).

This simulates an orchestrator creating a single agent instance on AWS.
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
        logging.FileHandler('design_agent.log')
    ]
)

logger = logging.getLogger(__name__)

class DesignAgent:
    """Design Agent that loads prompt from external repository"""

    def __init__(self, prompt_repo_path: str = "prompts-repo"):
        self.prompt_repo = Path(prompt_repo_path)
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load Design.md prompt from external repository"""
        prompt_path = self.prompt_repo / "Design.md"

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Design prompt not found at: {prompt_path}\n"
                f"Please ensure {prompt_path} exists."
            )

        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info(f"Loaded prompt from: {prompt_path}")
        logger.info(f"Prompt length: {len(content)} characters")

        return content

    async def run(self, task: str):
        """Run the Design Agent with a specific task"""
        from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

        # Create options with custom prompt from Design.md
        options = ClaudeAgentOptions(
            system_prompt=self.prompt,  # Use Design.md content directly
            allowed_tools=["Read", "Glob", "Grep"],  # Design agent tools
            permission_mode="acceptEdits"
        )

        logger.info("=" * 80)
        logger.info("Design Agent Starting")
        logger.info("=" * 80)
        logger.info(f"Task: {task}")
        logger.info("=" * 80)

        # Execute the task
        async for message in query(prompt=task, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                        logger.info(f"Response: {block.text[:200]}...")

        logger.info("=" * 80)
        logger.info("Design Agent Completed")
        logger.info("=" * 80)

async def main():
    try:
        # Initialize Design Agent
        logger.info("Initializing Design Agent...")
        agent = DesignAgent(prompt_repo_path="prompts-repo")

        # Example task for Design Agent
        task = """
Please review and provide design recommendations for a user authentication system.

Consider:
1. Architecture patterns (MVC, microservices, etc.)
2. Security best practices
3. User experience flow
4. Component structure
5. Scalability considerations

Provide your analysis in the ADR format specified in your guidelines.
"""

        # Run the agent
        await agent.run(task)

    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Please install: pip install claude-agent-sdk")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
