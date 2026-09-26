"""
Aura Writer — Protection Package
"""

from tools.protection.aura_protect import (
    compute_manuscript_sha256,
    extract_watermark_from_text,
    extract_watermark_from_file,
    create_protection_signature,
    strip_zero_width_chars,
)

__all__ = [
    "compute_manuscript_sha256",
    "extract_watermark_from_text",
    "extract_watermark_from_file",
    "create_protection_signature",
    "strip_zero_width_chars",
]
