"""Фильтрация отзывов: нецензурная лексика и признаки спама.

Вердикты:
    "ok"     — отзыв чистый, публикуем сразу;
    "review" — есть подозрительные признаки, отправляем админу на проверку;
    "reject" — нецензурная лексика, отклоняем автоматически.
"""

import re
from dataclasses import dataclass

# Обфускация: похожие латинские буквы и цифры -> кириллица
HOMOGLYPHS = str.maketrans({
    "a": "а", "e": "е", "o": "о", "p": "р", "c": "с", "x": "х", "y": "у",
    "k": "к", "m": "м", "t": "т", "b": "в", "h": "н", "u": "и",
    "0": "о", "3": "з", "6": "б", "@": "а", "$": "с",
})

# Приставки, которые отрезаем от начала слова перед проверкой корня
PREFIXES = (
    "пере", "разо", "раз", "рас", "взо", "возо", "воз", "вос", "восо",
    "вы", "до", "за", "из", "ис", "на", "над", "нед", "недо", "об", "обо",
    "обез", "обес", "ото", "от", "по", "под", "подо", "пре", "пред", "при",
    "про", "со", "с", "в", "у", "о", "не",
)

# Корни нецензурных слов (проверяются по началу слова после снятия приставок)
OBSCENE_ROOTS = (
    "хуй", "хуя", "хуе", "хуё", "пизд", "пижд", "еб", "ёб",
    "бляд", "блят", "блядь",
    "мудак", "мудил", "мудозвон", "говн", "гавн", "залуп",
    "пидор", "пидар", "педера", "шлюх", "шалав", "сук",
)

URL_RE = re.compile(r"(https?://|www\.|t\.me/|@[a-z0-9_]{4,})", re.IGNORECASE)
PHONE_RE = re.compile(r"[+]?[\d\s()\-]{10,}")
REPEAT_CHAR_RE = re.compile(r"(.)\1{4,}", re.IGNORECASE)


@dataclass
class ModerationResult:
    verdict: str  # "ok" | "review" | "reject"
    reason: str = ""


def _normalize(text: str) -> str:
    text = text.lower().replace("ё", "е").translate(HOMOGLYPHS)
    return text


def _strip_prefix(word: str) -> str:
    for prefix in PREFIXES:
        if word.startswith(prefix) and len(word) - len(prefix) >= 2:
            return word[len(prefix):]
    return word


def contains_obscene(text: str) -> bool:
    """Есть ли в тексте нецензурная лексика (с учётом обфускации)."""
    normalized = _normalize(text)
    for raw_word in re.findall(r"[а-я]+", normalized):
        word = re.sub(r"(.)\1{1,}", r"\1", raw_word)  # сууука -> сука
        candidates = {word, _strip_prefix(word)}
        for candidate in candidates:
            for root in OBSCENE_ROOTS:
                root = root.replace("ё", "е")
                if candidate.startswith(root):
                    return True
    return False


def spam_flags(text: str) -> list[str]:
    """Список спам-признаков (пустой = признаков нет)."""
    flags = []
    if URL_RE.search(text) or PHONE_RE.search(text):
        flags.append("ссылка/контакт")
    if REPEAT_CHAR_RE.search(text):
        flags.append("много повторяющихся символов")
    letters = [c for c in text if c.isalpha()]
    if len(letters) >= 15:
        caps = sum(1 for c in letters if c.isupper())
        if caps / len(letters) > 0.7:
            flags.append("КАПС")
    words = text.lower().split()
    if len(words) >= 6 and len(set(words)) / len(words) < 0.4:
        flags.append("повторяющиеся слова")
    if len(text.strip()) < 15:
        flags.append("слишком короткий текст")
    return flags


def moderate(text: str) -> ModerationResult:
    if contains_obscene(text):
        return ModerationResult("reject", "нецензурная лексика")
    flags = spam_flags(text)
    if flags:
        return ModerationResult("review", ", ".join(flags))
    return ModerationResult("ok")
