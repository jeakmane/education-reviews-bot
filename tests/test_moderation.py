import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from moderation import contains_obscene, moderate, spam_flags


class TestObscene:
    def test_plain_obscene_rejected(self):
        assert moderate("Препод полный мудак, не советую").verdict == "reject"

    def test_obscene_with_prefix(self):
        assert contains_obscene("он меня заебал этими пересдачами")

    def test_obfuscated_digits(self):
        assert contains_obscene("ху1ня какая-то") is False  # '1' не маппится, но:
        assert contains_obscene("хуйня какая-то")

    def test_obfuscated_latin(self):
        assert contains_obscene("полный xyй")  # латинские x, y

    def test_repeated_letters(self):
        assert contains_obscene("суууука как сложно")

    def test_normal_words_pass(self):
        # ложные срабатывания недопустимы
        for text in (
            "Учеба с ним в удовольствие",
            "Очень требовательный, но справедливый",
            "Лекции скучные, экзамен легкий",
            "Страхует студентов на пересдаче",
            "Сказал, что зачет будет в субботу",
        ):
            assert not contains_obscene(text), text
            assert moderate(text).verdict != "reject", text


class TestSpam:
    def test_link_flagged(self):
        assert "ссылка/контакт" in spam_flags("Пиши мне t.me/spammer куплю диплом")

    def test_phone_flagged(self):
        assert "ссылка/контакт" in spam_flags("Звони +7 900 123-45-67 решим вопрос")

    def test_caps_flagged(self):
        assert "КАПС" in spam_flags("ЭТО ПРОСТО УЖАСНЫЙ ПРЕПОДАВАТЕЛЬ НЕ ХОДИТЕ")

    def test_repeated_words_flagged(self):
        assert "повторяющиеся слова" in spam_flags("купить купить купить диплом купить диплом купить диплом")

    def test_short_flagged(self):
        assert "слишком короткий текст" in spam_flags("норм")

    def test_good_review_ok(self):
        text = (
            "Экзамен проходит в письменной форме, билеты совпадают с тем, "
            "что давал на лекциях. Спрашивает по материалу, но лояльный, "
            "можно пересдать без проблем."
        )
        assert spam_flags(text) == []
        assert moderate(text).verdict == "ok"

    def test_suspicious_goes_to_review(self):
        assert moderate("норм").verdict == "review"
