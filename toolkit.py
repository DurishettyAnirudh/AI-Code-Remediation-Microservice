"""Utility helpers for code-manipulation workflows."""

from __future__ import annotations

import csv
import logging
from datetime import datetime
from pathlib import Path
from difflib import unified_diff
from typing import Iterable, Sequence


def diff_code(old_code: str, new_code: str, *, context: int = 3) -> str:
	"""Return a unified diff between the old and new code snippets.

	Args:
		old_code: Previous version of the code.
		new_code: Updated version to compare against ``old_code``.
		context: Number of surrounding unchanged lines to include.

	Returns:
		A unified diff string that can be displayed or logged.
	"""

	old_lines: Sequence[str] = old_code.splitlines(keepends=True)
	new_lines: Sequence[str] = new_code.splitlines(keepends=True)

	diff: Iterable[str] = unified_diff(
		old_lines,
		new_lines,
		fromfile="old",
		tofile="new",
		n=context,
	)

	return "".join(diff)


LOGGER = logging.getLogger("local_fix")
if not LOGGER.handlers:
	handler = logging.StreamHandler()
	handler.setFormatter(
		logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
	)
	LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)


def log_metrics(
	input_tokens: int,
	output_tokens: int,
	latency_ms: int,
	*,
	csv_path: str | Path | None = "logs.csv",
) -> None:
	"""Log token usage and latency to console and an optional CSV file."""
	LOGGER.info(
		"Tokens in: %s | Tokens out: %s | Latency: %sms",
		input_tokens,
		output_tokens,
		latency_ms,
	)
	if not csv_path:
		return
	path = Path(csv_path)
	file_exists = path.exists()
	with path.open("a", newline="", encoding="utf-8") as csvfile:
		writer = csv.DictWriter(
			csvfile,
			fieldnames=[
				"timestamp",
				"input_tokens",
				"output_tokens",
				"latency_ms",
			],
		)
		if not file_exists:
			writer.writeheader()
		writer.writerow(
			{
				"timestamp": datetime.utcnow().isoformat(timespec="seconds"),
				"input_tokens": int(input_tokens),
				"output_tokens": int(output_tokens),
				"latency_ms": int(latency_ms),
			}
		)
