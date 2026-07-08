from app.ai.pii_patterns import ACCOUNT_OR_NUMBER_RE, EMAIL_RE, NAME_RE

_NAME_POOL = [
    "John Doe",
    "Jane Roe",
    "Alex Smith",
    "Morgan Lee",
    "Taylor Brown",
    "Jordan Clark",
    "Casey Wright",
    "Riley Adams",
]


class Pseudonymizer:
    """Swaps person names, emails, and account numbers for consistent fake
    stand-ins before case text is sent to a third-party AI provider, and
    restores the real values in the provider's response afterward. State is
    scoped to a single analyze_case() call so the same real value always maps
    to the same fake value across the context/description/evidence texts of
    that call, keeping the AI's entity correlation intact."""

    def __init__(self):
        self._real_to_fake: dict[str, str] = {}
        self._fake_to_real: dict[str, str] = {}
        self._name_count = 0
        self._email_count = 0
        self._account_count = 0

    def _fake_name(self, real: str) -> str:
        if real in self._real_to_fake:
            return self._real_to_fake[real]
        cycle, index = divmod(self._name_count, len(_NAME_POOL))
        fake = _NAME_POOL[index] if cycle == 0 else f"{_NAME_POOL[index]} {cycle + 1}"
        self._name_count += 1
        self._register(real, fake)
        return fake

    def _fake_email(self, real: str) -> str:
        if real in self._real_to_fake:
            return self._real_to_fake[real]
        self._email_count += 1
        fake = f"person{self._email_count}@example.com"
        self._register(real, fake)
        return fake

    def _fake_account(self, real_digits: str) -> str:
        if real_digits in self._real_to_fake:
            return self._real_to_fake[real_digits]
        self._account_count += 1
        fake = str(self._account_count).rjust(len(real_digits), "9")
        self._register(real_digits, fake)
        return fake

    def _register(self, real: str, fake: str) -> None:
        self._real_to_fake[real] = fake
        self._fake_to_real[fake] = real

    def _replace_number(self, match) -> str:
        digits = match.group(1) or match.group(2)
        return match.group(0).replace(digits, self._fake_account(digits))

    def pseudonymize(self, text: str) -> str:
        if not text:
            return text
        text = EMAIL_RE.sub(lambda m: self._fake_email(m.group(0)), text)
        text = ACCOUNT_OR_NUMBER_RE.sub(self._replace_number, text)
        text = NAME_RE.sub(lambda m: self._fake_name(m.group(0)), text)
        return text

    def restore(self, text: str) -> str:
        if not text:
            return text
        for fake in sorted(self._fake_to_real, key=len, reverse=True):
            if fake in text:
                text = text.replace(fake, self._fake_to_real[fake])
        return text
