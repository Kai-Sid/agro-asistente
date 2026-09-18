from pathlib import Path

import pytest

from app.application.useCases.create_agricultural_context import CreateAgriculturalContext
from app.application.useCases.list_agricultural_contexts import ListAgriculturalContexts
from app.application.useCases.select_agricultural_context import SelectAgriculturalContext
from app.domain.entities.agricultural_context import AgriculturalContext
from app.domain.exceptions import ContextNotFoundError, InvalidContextDataError
from app.domain.ports.input.manage_context_port import (
    CreateAgriculturalContextCommand,
    SelectAgriculturalContextCommand,
)
from app.domain.ports.output.agricultural_context_repository_port import (
    AgriculturalContextRepositoryPort,
)


class InMemoryContextRepository(AgriculturalContextRepositoryPort):
    def __init__(self) -> None:
        self.contexts: list[AgriculturalContext] = []

    def save(self, context: AgriculturalContext) -> None:
        self.contexts.append(context)

    def list_by_farmer(self, farmer_id: str) -> list[AgriculturalContext]:
        return [context for context in self.contexts if context.farmer_id == farmer_id]

    def find_by_id_for_farmer(self, context_id: str, farmer_id: str) -> AgriculturalContext | None:
        for context in self.contexts:
            if context.id == context_id and context.farmer_id == farmer_id:
                return context
        return None

    def select_for_farmer(self, context_id: str, farmer_id: str) -> AgriculturalContext | None:
        target = self.find_by_id_for_farmer(context_id, farmer_id)
        if target is None:
            return None
        for context in self.contexts:
            if context.farmer_id == farmer_id:
                context.mark_unselected()
        target.mark_selected()
        return target


FARMER_A = "farmer-a"
FARMER_B = "farmer-b"


def _create(
    repository: InMemoryContextRepository,
    farmer_id: str = FARMER_A,
    crop: str = "papa",
    region: str = "Huancayo",
) -> str:
    use_case = CreateAgriculturalContext(repository)
    result = use_case.execute(
        CreateAgriculturalContextCommand(
            farmer_id=farmer_id,
            plot_name="Parcela 1",
            crop=crop,
            region=region,
            notes="Riego por gravedad",
        )
    )
    return result.id


def test_create_agricultural_context() -> None:
    repository = InMemoryContextRepository()
    result = CreateAgriculturalContext(repository).execute(
        CreateAgriculturalContextCommand(
            farmer_id=FARMER_A,
            plot_name="Parcela 1",
            crop="papa",
            region="Huancayo",
            notes=None,
        )
    )
    assert result.farmer_id == FARMER_A
    assert result.crop == "papa"
    assert result.region == "Huancayo"
    assert result.is_selected is False
    assert len(repository.contexts) == 1


def test_list_contexts_only_returns_authenticated_farmer() -> None:
    repository = InMemoryContextRepository()
    _create(repository, FARMER_A, crop="papa")
    _create(repository, FARMER_B, crop="maiz")

    listed = ListAgriculturalContexts(repository).execute(FARMER_A)
    assert len(listed) == 1
    assert listed[0].crop == "papa"
    assert all(item.farmer_id == FARMER_A for item in listed)


def test_select_own_context() -> None:
    repository = InMemoryContextRepository()
    first = _create(repository, FARMER_A, crop="papa")
    second = _create(repository, FARMER_A, crop="maiz")

    selected = SelectAgriculturalContext(repository).execute(
        SelectAgriculturalContextCommand(farmer_id=FARMER_A, context_id=second)
    )
    assert selected.id == second
    assert selected.is_selected is True
    stored_first = repository.find_by_id_for_farmer(first, FARMER_A)
    stored_second = repository.find_by_id_for_farmer(second, FARMER_A)
    assert stored_first is not None and stored_first.is_selected is False
    assert stored_second is not None and stored_second.is_selected is True


def test_cannot_select_another_farmer_context() -> None:
    repository = InMemoryContextRepository()
    context_b = _create(repository, FARMER_B, crop="maiz")
    with pytest.raises(ContextNotFoundError):
        SelectAgriculturalContext(repository).execute(
            SelectAgriculturalContextCommand(farmer_id=FARMER_A, context_id=context_b)
        )


def test_create_requires_crop() -> None:
    repository = InMemoryContextRepository()
    with pytest.raises(InvalidContextDataError, match="cultivo"):
        CreateAgriculturalContext(repository).execute(
            CreateAgriculturalContextCommand(
                farmer_id=FARMER_A,
                plot_name=None,
                crop="  ",
                region="Huancayo",
                notes=None,
            )
        )


def test_context_use_cases_do_not_import_frameworks() -> None:
    use_cases = Path(__file__).resolve().parents[1] / "app" / "application" / "useCases"
    forbidden = ("fastapi", "sqlalchemy", "import jwt", "from jwt", "import bcrypt")
    for name in (
        "create_agricultural_context.py",
        "list_agricultural_contexts.py",
        "select_agricultural_context.py",
    ):
        source = (use_cases / name).read_text(encoding="utf-8").lower()
        for item in forbidden:
            assert item not in source
