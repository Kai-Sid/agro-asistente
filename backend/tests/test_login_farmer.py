from pathlib import Path

import pytest

from app.application.useCases.login_farmer import LoginFarmer
from app.domain.entities.farmer import Farmer
from app.domain.exceptions import InvalidCredentialsError, InvalidEmailError
from app.domain.ports.input.login_farmer_port import LoginFarmerCommand
from app.domain.ports.output.farmer_repository_port import FarmerRepositoryPort
from app.domain.ports.output.password_hasher_port import PasswordHasherPort
from app.domain.ports.output.token_issuer_port import TokenIssuerPort
from app.domain.valueObjects.email import Email
from app.domain.valueObjects.password_hash import PasswordHash


class InMemoryFarmerRepository(FarmerRepositoryPort):
    def __init__(self) -> None:
        self.farmers: list[Farmer] = []

    def exists_by_email(self, email: Email) -> bool:
        return any(farmer.email == email for farmer in self.farmers)

    def find_by_email(self, email: Email) -> Farmer | None:
        for farmer in self.farmers:
            if farmer.email == email:
                return farmer
        return None

    def save(self, farmer: Farmer) -> None:
        self.farmers.append(farmer)


class FakePasswordHasher(PasswordHasherPort):
    def __init__(self) -> None:
        self.verify_calls: list[tuple[str, str]] = []

    def hash_password(self, password: str) -> str:
        return f"$fake${password}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        self.verify_calls.append((password, password_hash))
        return password_hash == f"$fake${password}"


class FakeTokenIssuer(TokenIssuerPort):
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str]]] = []

    def issue_token(self, subject: str, claims: dict[str, str]) -> str:
        self.calls.append((subject, claims))
        return f"token-for-{subject}"


def _registered_use_case(
    password: str = "Password123!",
) -> tuple[LoginFarmer, Farmer, FakePasswordHasher, FakeTokenIssuer]:
    repository = InMemoryFarmerRepository()
    hasher = FakePasswordHasher()
    tokens = FakeTokenIssuer()
    farmer = Farmer.register(
        names="Juan",
        last_names="Pérez",
        email=Email("juan@example.com"),
        password_hash=PasswordHash(hasher.hash_password(password)),
    )
    repository.save(farmer)
    return LoginFarmer(repository, hasher, tokens), farmer, hasher, tokens


def test_login_farmer_success() -> None:
    use_case, farmer, hasher, tokens = _registered_use_case()

    result = use_case.execute(
        LoginFarmerCommand(email="juan@example.com", password="Password123!")
    )

    assert result.access_token == f"token-for-{farmer.id}"
    assert result.token_type == "bearer"
    assert result.farmer.id == farmer.id
    assert result.farmer.email == "juan@example.com"
    assert result.farmer.names == "Juan"
    assert "password" not in result.__dict__
    assert not hasattr(result.farmer, "password_hash")
    assert hasher.verify_calls == [("Password123!", farmer.password_hash.value)]
    assert tokens.calls == [(farmer.id, {"email": "juan@example.com"})]


def test_login_unknown_email_returns_generic_error() -> None:
    use_case, _farmer, hasher, tokens = _registered_use_case()

    with pytest.raises(InvalidCredentialsError, match="Credenciales inválidas"):
        use_case.execute(
            LoginFarmerCommand(email="otro@example.com", password="Password123!")
        )
    assert hasher.verify_calls == []
    assert tokens.calls == []


def test_login_wrong_password_returns_generic_error() -> None:
    use_case, _farmer, hasher, tokens = _registered_use_case()

    with pytest.raises(InvalidCredentialsError, match="Credenciales inválidas"):
        use_case.execute(
            LoginFarmerCommand(email="juan@example.com", password="WrongPass1")
        )
    assert len(hasher.verify_calls) == 1
    assert tokens.calls == []


def test_login_invalid_email() -> None:
    use_case, _farmer, _hasher, _tokens = _registered_use_case()
    with pytest.raises(InvalidEmailError):
        use_case.execute(LoginFarmerCommand(email="no-es-correo", password="Password123!"))


def test_login_result_does_not_leak_password_hash() -> None:
    use_case, _farmer, _hasher, _tokens = _registered_use_case()
    result = use_case.execute(
        LoginFarmerCommand(email="juan@example.com", password="Password123!")
    )
    dumped = str(result)
    assert "password_hash" not in dumped
    assert "$fake$" not in dumped


def test_login_use_case_depends_on_ports_not_libraries() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "application"
        / "useCases"
        / "login_farmer.py"
    ).read_text(encoding="utf-8").lower()
    assert "farmerrepositoryport" in source
    assert "passwordhasherport" in source
    assert "tokenissuerport" in source
    assert "import jwt" not in source
    assert "from jwt" not in source
    assert "import bcrypt" not in source
    assert "from bcrypt" not in source
    assert "fastapi" not in source
    assert "sqlalchemy" not in source
    assert "pydantic" not in source
    assert "jwttokenissuer" not in source
    assert "bcryptpasswordhasher" not in source
