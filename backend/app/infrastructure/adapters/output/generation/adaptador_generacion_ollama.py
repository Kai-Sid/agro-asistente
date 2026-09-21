import httpx

from app.domain.exceptions import ErrorGeneracionTexto
from app.domain.ports.output.text_generation_port import (
    PasajeRecuperado,
    PuertoGeneracionTexto,
    RespuestaGenerada,
)

INSTRUCCION_SISTEMA = (
    "Eres un asistente técnico agrícola para la agricultura familiar de Junín, Perú. "
    "Responde siempre en español, con lenguaje claro y práctico. "
    "Usa únicamente la información de los fragmentos recuperados de la base de conocimiento. "
    "No inventes dosis, productos, fechas ni recomendaciones que no estén respaldadas "
    "por esos fragmentos. Si la información es insuficiente, dilo de forma explícita "
    "y no completes el vacío con conocimiento general."
)


def construir_prompt_agricola(
    texto_consulta: str,
    cultivo: str,
    region: str,
    pasajes: list[PasajeRecuperado] | None = None,
) -> str:
    """Arma el prompt de usuario. No invoca el modelo."""
    consulta = (texto_consulta or "").strip()
    cultivo_limpio = (cultivo or "").strip() or "no indicado"
    region_limpia = (region or "").strip() or "no indicada"
    relevantes = [item for item in (pasajes or []) if (item.extracto or "").strip()]

    lineas = [
        f"Cultivo: {cultivo_limpio}",
        f"Región: {region_limpia}",
        f"Consulta del agricultor: {consulta}",
        "",
        "Fragmentos recuperados de la base de conocimiento:",
    ]
    if not relevantes:
        lineas.append(
            "(No se recuperó ningún fragmento relevante. "
            "Indica que no hay información suficiente en la base de conocimiento.)"
        )
    else:
        for indice, pasaje in enumerate(relevantes, start=1):
            titulo = (pasaje.titulo or "").strip() or "documento agrícola"
            lineas.append(f"{indice}. {titulo}: {pasaje.extracto.strip()}")
    lineas.append("")
    lineas.append("Redacta la respuesta técnica en español.")
    return "\n".join(lineas)


class AdaptadorGeneracionOllama(PuertoGeneracionTexto):
    """Adaptador de infraestructura hacia Ollama. El dominio no importa este módulo."""

    METHOD = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: int = 90,
        cliente_http: object | None = None,
    ) -> None:
        self._base_url = (base_url or "").rstrip("/")
        self._model = (model or "").strip()
        self._timeout_seconds = timeout_seconds
        self._cliente = cliente_http

    def generar(
        self,
        texto_consulta: str,
        cultivo: str,
        region: str,
        pasajes: list[PasajeRecuperado] | None = None,
    ) -> RespuestaGenerada:
        if not self._model:
            raise ErrorGeneracionTexto(
                "No se pudo generar la respuesta: falta configurar el modelo local (OLLAMA_MODEL)."
            )
        if not self._base_url:
            raise ErrorGeneracionTexto(
                "No se pudo generar la respuesta: falta la URL del servicio de generación (OLLAMA_BASE_URL)."
            )

        prompt = construir_prompt_agricola(texto_consulta, cultivo, region, pasajes)
        payload = {
            "model": self._model,
            "system": INSTRUCCION_SISTEMA,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        try:
            respuesta_http = self._post(payload)
        except httpx.TimeoutException as error:
            raise ErrorGeneracionTexto(
                "No se pudo generar la respuesta: el modelo local excedió el tiempo de espera."
            ) from error
        except httpx.RequestError as error:
            raise ErrorGeneracionTexto(
                "No se pudo generar la respuesta: el servicio de generación local no está disponible. "
                "Comprueba que Ollama esté en ejecución."
            ) from error

        return RespuestaGenerada(
            texto_respuesta=_texto_desde_respuesta(respuesta_http, self._model),
            metodo_generacion=self.METHOD,
        )

    def _post(self, payload: dict[str, object]) -> object:
        url = f"{self._base_url}/api/generate"
        if self._cliente is not None:
            return self._cliente.post(url, json=payload, timeout=self._timeout_seconds)
        with httpx.Client(timeout=self._timeout_seconds) as cliente:
            return cliente.post(url, json=payload)


def _texto_desde_respuesta(respuesta_http: object, modelo: str) -> str:
    status_code = int(getattr(respuesta_http, "status_code", 0) or 0)
    cuerpo = _json_seguro(respuesta_http)
    error_remoto = ""
    if isinstance(cuerpo, dict):
        error_remoto = str(cuerpo.get("error") or "").strip()

    if status_code == 404 or _es_modelo_ausente(error_remoto, status_code):
        raise ErrorGeneracionTexto(
            f"No se pudo generar la respuesta: el modelo '{modelo}' no está disponible en Ollama. "
            "Revisa OLLAMA_MODEL e instálalo con `ollama pull`."
        )
    if status_code >= 400:
        detalle = error_remoto or f"el servicio respondió HTTP {status_code}"
        raise ErrorGeneracionTexto(
            f"No se pudo generar la respuesta: {detalle}."
        )

    texto = ""
    if isinstance(cuerpo, dict):
        texto = str(cuerpo.get("response") or "").strip()
    if not texto:
        raise ErrorGeneracionTexto(
            "No se pudo generar la respuesta: el modelo devolvió un texto vacío."
        )
    return texto


def _json_seguro(respuesta_http: object) -> object:
    lector = getattr(respuesta_http, "json", None)
    if not callable(lector):
        return {}
    try:
        return lector()
    except ValueError:
        return {}


def _es_modelo_ausente(error_remoto: str, status_code: int) -> bool:
    lowered = error_remoto.lower()
    if "not found" in lowered or "no such file" in lowered:
        return True
    return status_code == 404
