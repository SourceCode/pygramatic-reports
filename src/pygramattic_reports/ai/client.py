"""ClaudeClient - subprocess-based wrapper for Claude CLI.

Provides headless Claude CLI invocations with retry logic,
timeout handling, and structured error management.
"""

from __future__ import annotations

import subprocess
import time
from typing import TYPE_CHECKING

from pygramattic_reports.exceptions import AIError
from pygramattic_reports.logging import get_logger

if TYPE_CHECKING:
    from pygramattic_reports.config.settings import ClaudeConfig

logger = get_logger("ai")


class ClaudeClient:
    """Client for Claude CLI headless invocations.

    Wraps subprocess calls to the Claude CLI with retry logic,
    timeout handling, and structured error management.

    Design principles:
    - Every AI call is optional. The system works without it.
    - Failures are logged and result in fallback content, not crashes.
    - All prompts are templated and deterministic (given the same input).

    Usage:
        client = ClaudeClient(config)
        result = client.generate(
            prompt="Summarize this data...",
            context="Revenue: US $1500, EU $2300...",
            max_tokens=512,
        )
    """

    def __init__(self, config: ClaudeConfig) -> None:
        """Initialize with Claude CLI configuration."""
        self.config = config
        self.enabled = config.enabled

    def generate(
        self,
        prompt: str,
        context: str = "",
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> str:
        """Generate content using Claude CLI.

        Args:
            prompt: The user prompt.
            context: Additional context (data, previous sections, etc.).
            max_tokens: Override max tokens.
            system_prompt: Override system prompt.

        Returns:
            Generated text content.

        Raises:
            AIError: If all retries fail.
        """
        if not self.enabled:
            logger.info("AI disabled, returning empty string")
            return ""

        full_prompt = self._build_prompt(prompt, context, system_prompt)
        max_tok = max_tokens or self.config.default_max_tokens

        last_error: AIError | None = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                result = self._invoke_cli(full_prompt, max_tok)
            except AIError as exc:
                last_error = exc
                if attempt < self.config.max_retries:
                    wait = self.config.retry_backoff_factor**attempt
                    logger.warning(
                        "AI call failed, retrying",
                        attempt=attempt,
                        wait_seconds=wait,
                        error=str(exc),
                    )
                    time.sleep(wait)
            else:
                logger.info(
                    "AI generation succeeded",
                    attempt=attempt,
                    prompt_len=len(full_prompt),
                )
                return result

        raise AIError(
            f"Claude CLI failed after {self.config.max_retries} attempts: {last_error}",
        )

    def _invoke_cli(self, prompt: str, max_tokens: int) -> str:
        """Execute a single Claude CLI subprocess call."""
        cmd = [
            self.config.executable,
            "--print",
            "--max-tokens",
            str(max_tokens),
            prompt,
        ]

        try:
            result = subprocess.run(  # noqa: S603
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AIError(
                f"Claude CLI timed out after {self.config.timeout_seconds}s",
            ) from exc
        except FileNotFoundError as exc:
            raise AIError(
                f"Claude CLI not found at: {self.config.executable}",
            ) from exc

        if result.returncode != 0:
            raise AIError(
                f"Claude CLI returned exit code {result.returncode}: {result.stderr}",
            )
        return result.stdout.strip()

    def _build_prompt(
        self,
        prompt: str,
        context: str,
        system_prompt: str | None,
    ) -> str:
        """Build the full prompt string for the CLI."""
        parts: list[str] = []
        if system_prompt:
            parts.append(f"System: {system_prompt}\n\n")
        if context:
            parts.append(f"Context:\n{context}\n\n")
        parts.append(prompt)
        return "".join(parts)

    def is_available(self) -> bool:
        """Check if Claude CLI is available and functioning."""
        if not self.enabled:
            return False
        try:
            result = subprocess.run(  # noqa: S603
                [self.config.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        else:
            return result.returncode == 0
