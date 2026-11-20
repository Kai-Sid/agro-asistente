from app.domain.ports.input.listar_consultas_port import (
    PuertoListarConsultas,
    ResultadoHistorialConsulta,
)
from app.domain.ports.output.repositorio_consulta_port import PuertoRepositorioConsulta


class ListarConsultas(PuertoListarConsultas):
    def __init__(self, repositorio_consulta: PuertoRepositorioConsulta) -> None:
        self._repositorio_consulta = repositorio_consulta

    def ejecutar(
        self, agricultor_id: str, limite: int = 20
    ) -> list[ResultadoHistorialConsulta]:
        tope = max(1, min(int(limite or 20), 50))
        items = self._repositorio_consulta.listar_por_agricultor(
            agricultor_id=agricultor_id,
            limite=tope,
        )
        return [
            ResultadoHistorialConsulta(
                id=item["id"],
                text=item["text"],
                answer=item["answer"],
                generation_method=item["generation_method"],
                created_at=item["created_at"],
            )
            for item in items
        ]
