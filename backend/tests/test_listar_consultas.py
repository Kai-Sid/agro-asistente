from datetime import datetime, timezone

from app.application.useCases.listar_consultas import ListarConsultas
from app.domain.entities.consulta import Consulta
from app.domain.entities.respuesta import Respuesta
from app.domain.valueObjects.texto_consulta import TextoConsulta
from tests.test_submit_query import RepositorioConsultaEnMemoria


def test_listar_consultas_devuelve_historial_del_agricultor() -> None:
    repo = RepositorioConsultaEnMemoria()
    consulta = Consulta(
        consulta_id="1",
        agricultor_id="farmer-a",
        contexto_id="ctx-1",
        texto=TextoConsulta("¿Cómo riego la papa?"),
        creado_en=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    respuesta = Respuesta(
        respuesta_id="r1",
        consulta_id="1",
        texto_respuesta="Riego frecuente en floración.",
        metodo_generacion="template",
        creado_en=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    repo.guardar_interaccion(consulta, respuesta, [])

    resultado = ListarConsultas(repo).ejecutar("farmer-a", limite=10)

    assert len(resultado) == 1
    assert resultado[0].text == "¿Cómo riego la papa?"
    assert resultado[0].answer.startswith("Riego")
    assert ListarConsultas(repo).ejecutar("otro") == []
