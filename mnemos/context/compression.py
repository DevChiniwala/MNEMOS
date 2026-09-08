# -*- coding: utf-8 -*-
"""Text compression utilities for context packaging."""

import re

class TextCompressor:
    """Utility to compress text without semantic loss."""

    @staticmethod
    def compress(text: str) -> str:
        """Remove redundant whitespace and formatting."""
        # Replace multiple spaces with single space
        text = re.sub(r"[ \t]+", " ", text)
        # Replace multiple newlines with a single newline
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
