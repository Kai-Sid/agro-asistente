from abc import ABC, abstractmethod


class TokenIssuerPort(ABC):
    @abstractmethod
    def issue_token(self, subject: str, claims: dict[str, str]) -> str:
        """Emite un token de acceso para el sujeto autenticado."""
