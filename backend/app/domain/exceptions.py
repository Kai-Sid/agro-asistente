class DomainError(Exception):
    """Error de regla de negocio."""


class InvalidFarmerDataError(DomainError):
    """Datos obligatorios del agricultor inválidos o ausentes."""


class InvalidEmailError(DomainError):
    """El correo electrónico no cumple el formato del dominio."""


class InvalidPasswordError(DomainError):
    """La contraseña no cumple las reglas del dominio."""


class DuplicateEmailError(DomainError):
    """Ya existe un agricultor con el mismo correo."""


class InvalidCredentialsError(DomainError):
    """Email o contraseña incorrectos. El mensaje debe ser genérico."""


class InvalidTokenError(DomainError):
    """Token ausente, inválido o expirado."""


class InvalidContextDataError(DomainError):
    """Datos del contexto agrícola inválidos."""


class ContextNotFoundError(DomainError):
    """El contexto no existe o no pertenece al agricultor autenticado."""


class InvalidQueryTextError(DomainError):
    """El texto de la consulta agrícola es inválido."""


class InvalidQueryDataError(DomainError):
    """Datos de la consulta agrícola inválidos o ausentes."""


class SelectedContextNotFoundError(DomainError):
    """El agricultor no tiene un contexto agrícola seleccionado."""


class InvalidQueryTextError(DomainError):
    """El texto de la consulta agrícola es inválido."""


class InvalidQueryDataError(DomainError):
    """Datos de la consulta agrícola inválidos."""


class SelectedContextNotFoundError(DomainError):
    """El agricultor no tiene un contexto agrícola seleccionado."""


class InvalidKnowledgeDocumentError(DomainError):
    """Datos del documento de conocimiento inválidos o ausentes."""


class DuplicateKnowledgeDocumentError(DomainError):
    """Ya existe un documento con el mismo contenido."""


class InvalidEvidenceError(DomainError):
    """Datos de evidencia recuperada inválidos o ausentes."""


class KnowledgeFileNotFoundError(DomainError):
    """El archivo Markdown del documento de conocimiento no existe."""
