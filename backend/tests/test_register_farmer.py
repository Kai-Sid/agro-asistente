from pathlib import Path

from app.application.useCases.register_farmer import RegisterFarmer
from app.domain.entities.farmer import Farmer
from app.domain.exceptions import (
    DuplicateEmailError,
    InvalidEmailError,
    InvalidFarmerDataError,
    InvalidPasswordError,
)
from app.domain.ports.input.register_farmer_port import RegisterFarmerCommand
from app.domain.ports.output.farmer_repository_port import FarmerRepositoryPort
from app.domain.ports.output.password_hasher_port import PasswordHasherPort
from app.domain.valueObjects.email import Email
import pytest


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
    def hash_password(self, password: str) -> str:
        return f"$fake${password}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        return password_hash == f"$fake${password}"


def _use_case() -> tuple[RegisterFarmer, InMemoryFarmerRepository]:
    repository = InMemoryFarmerRepository()
    return RegisterFarmer(repository, FakePasswordHasher()), repository


def test_register_farmer_success() -> None:
    use_case, repository = _use_case()

    result = use_case.execute(
        RegisterFarmerCommand(
            names="Juan",
            last_names="Pérez",
            email="juan@example.com",
            password="Password123!",
        )
    )

    assert result.names == "Juan"
    assert result.last_names == "Pérez"
    assert result.email == "juan@example.com"
    assert result.id
    assert len(repository.farmers) == 1
    stored = repository.farmers[0]
    assert stored.password_hash.value == "$fake$Password123!"
    assert stored.password_hash.value != "Password123!"


def test_register_farmer_duplicate_email() -> None:
    use_case, _repository = _use_case()
    command = RegisterFarmerCommand(
        names="Juan",
        last_names="Pérez",
        email="juan@example.com",
        password="Password123!",
    )
    use_case.execute(command)

    with pytest.raises(DuplicateEmailError, match="ya está registrado"):
        use_case.execute(command)


def test_register_farmer_invalid_email() -> None:
    use_case, _repository = _use_case()
    with pytest.raises(InvalidEmailError):
        use_case.execute(
            RegisterFarmerCommand(
                names="Juan",
                last_names="Pérez",
                email="correo-invalido",
                password="Password123!",
            )
        )


def test_register_farmer_short_password() -> None:
    use_case, _repository = _use_case()
    with pytest.raises(InvalidPasswordError, match="8 caracteres"):
        use_case.execute(
            RegisterFarmerCommand(
                names="Juan",
                last_names="Pérez",
                email="juan@example.com",
                password="123",
            )
        )


def test_register_farmer_requires_names() -> None:
    use_case, _repository = _use_case()
    with pytest.raises(InvalidFarmerDataError, match="nombres"):
        use_case.execute(
            RegisterFarmerCommand(
                names="  ",
                last_names="Pérez",
                email="juan@example.com",
                password="Password123!",
            )
        )


def test_use_case_file_depends_on_ports_not_adapters() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "application"
        / "useCases"
        / "register_farmer.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    assert "farmerrepositoryport" in lowered
    assert "passwordhasherport" in lowered
    assert "mysqlfarmerrepository" not in lowered
    assert "bcryptpasswordhasher" not in lowered
    assert "fastapi" not in lowered
    assert "sqlalchemy" not in lowered
    assert "pydantic" not in lowered
    assert "import bcrypt" not in lowered
