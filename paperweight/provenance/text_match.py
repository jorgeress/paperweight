import re
import unicodedata

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    decomposed = unicodedata.normalize("NFKD", text)
    unaccented = "".join(c for c in decomposed if not unicodedata.combining(c))
    return TOKEN_PATTERN.findall(unaccented.casefold())


def contains_value(text: str, value: str) -> bool:
    # threat: "MADRIDISTA" must not satisfy a citation for "MADRID", so match whole tokens
    needle = tokenize(value)
    haystack = tokenize(text)
    if not needle:
        return False
    width = len(needle)
    return any(haystack[i : i + width] == needle for i in range(len(haystack) - width + 1))


def is_same_value(a: str, b: str) -> bool:
    return tokenize(a) == tokenize(b)
