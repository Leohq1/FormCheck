from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Protocol

from formcheck_video.errors import VideoTechnicalError


@dataclass(frozen=True)
class ProcessResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class ProcessRunner(Protocol):
    def run(self, args: list[str], *, timeout_seconds: float) -> ProcessResult: ...


class SubprocessRunner:
    def run(self, args: list[str], *, timeout_seconds: float) -> ProcessResult:
        try:
            completed = subprocess.run(
                list(args),
                shell=False,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise VideoTechnicalError("The video tool timed out.") from exc
        return ProcessResult(
            args=tuple(args),
            returncode=completed.returncode,
            stdout=completed.stdout.decode("utf-8", errors="replace"),
            stderr=completed.stderr.decode("utf-8", errors="replace"),
        )
