import re
import unicodedata


class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""

        # Normalize unicode characters
        text = unicodedata.normalize("NFKC", text)

        # Remove zero-width & non-printable control characters (except newline, tab)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200b]", "", text)

        # Replace 3 or more consecutive newlines with double newline
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Replace horizontal tabs and multiple consecutive spaces with a single space
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()
