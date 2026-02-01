from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    model: str = os.getenv("OPENAI_MODEL", "gpt-5.2")
    temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))
    max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
    run_dir: Path = Path(os.getenv("AUDIT_RUN_DIR", "runs"))
    max_file_bytes: int = int(os.getenv("AUDIT_MAX_FILE_BYTES", "20000"))
    max_total_bytes: int = int(os.getenv("AUDIT_MAX_TOTAL_BYTES", "200000"))


settings = Settings()
