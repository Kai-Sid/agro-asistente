from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedIdentity:
    farmer_id: str


class TokenVerifierPort(ABC):
    @abstractmethod
    def verify(self, token: str) -> AuthenticatedIdentity:
        """Valida un token y devuelve la identidad del agricultor."""
