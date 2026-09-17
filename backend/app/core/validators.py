import re

from pydantic import ValidationInfo
from pydantic_core import PydanticCustomError


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
PLATE_RE = re.compile(r"^(?:[A-Z]{3}\d{4}|[A-Z]{3}\d[A-Z]\d{2})$")


def digits(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def normalize_email(value: str) -> str:
    return value.strip().lower()


def validate_email(value: str, info: ValidationInfo) -> str:
    normalized = normalize_email(value)
    if normalized and not EMAIL_RE.fullmatch(normalized):
        raise PydanticCustomError("value_error", "Informe um e-mail válido.")
    return normalized


def normalize_phone(value: str) -> str:
    return digits(value)


def validate_phone(value: str, info: ValidationInfo) -> str:
    normalized = normalize_phone(value)
    if normalized and len(normalized) not in (10, 11):
        raise PydanticCustomError(
            "value_error",
            "Informe um telefone válido com DDD (10 ou 11 dígitos).",
        )
    if normalized and len(set(normalized)) == 1:
        raise PydanticCustomError("value_error", "Informe um telefone válido.")
    return normalized


def _check_digit(value: str, weights: list[int]) -> int:
    total = sum(int(number) * weight for number, weight in zip(value, weights))
    digit = (total * 10) % 11
    return 0 if digit == 10 else digit


def _has_valid_cpf_check_digits(value: str) -> bool:
    body = value[:9]
    check = value[9:]
    if len(set(value)) == 1:
        return False
    if _check_digit(body, list(range(10, 1, -1))) != int(check[0]):
        return False
    return _check_digit(body + check[0], list(range(11, 1, -1))) == int(check[1])


def _has_valid_cnpj_check_digits(value: str) -> bool:
    body = value[:12]
    check = value[12:]
    if len(set(value)) == 1:
        return False
    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    if _check_digit(body, first_weights) != int(check[0]):
        return False
    return _check_digit(body + check[0], second_weights) == int(check[1])


def normalize_document(value: str) -> str:
    return digits(value)


def validate_document(value: str, info: ValidationInfo) -> str:
    normalized = normalize_document(value)
    if normalized and (
        (len(normalized) == 11 and not _has_valid_cpf_check_digits(normalized))
        or (len(normalized) == 14 and not _has_valid_cnpj_check_digits(normalized))
        or len(normalized) not in (11, 14)
    ):
        raise PydanticCustomError("value_error", "Informe um CPF ou CNPJ válido.")
    return normalized


def normalize_plate(value: str) -> str:
    return value.strip().upper().replace("-", "").replace(" ", "")


def validate_plate(value: str, info: ValidationInfo) -> str:
    normalized = normalize_plate(value)
    if not PLATE_RE.fullmatch(normalized):
        raise PydanticCustomError(
            "value_error",
            "Informe uma placa válida (ABC1234 ou ABC1D23).",
        )
    return normalized
