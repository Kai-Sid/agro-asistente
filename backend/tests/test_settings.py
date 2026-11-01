from app.infrastructure.config.settings import Settings


def test_settings_load_defaults_without_secrets_in_code() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "agro-asistente"
    assert settings.mysql_database == "agro_asistente"
    assert settings.embedding_provider == "local"
    assert settings.chroma_collection == "agro_knowledge_pmv1"
    assert settings.rag_top_k == 3
    assert Settings.model_fields["generation_provider"].default == "ollama"
    assert Settings.model_fields["ollama_base_url"].default == "http://127.0.0.1:11434"
    assert Settings.model_fields["ollama_model"].default == "qwen2.5:1.5b"
    assert Settings.model_fields["ollama_timeout_seconds"].default == 90
    assert (
        Settings.model_fields["senamhi_wis2_base_url"].default
        == "https://wis.senamhi.gob.pe/oapi"
    )
    assert (
        Settings.model_fields["senamhi_wis2_collection"].default
        == "urn:wmo:md:pe-senamhi:synop-hourly"
    )
    assert Settings.model_fields["senamhi_wis2_timeout_seconds"].default == 20
    assert Settings.model_fields["clasificador_margen_minimo"].default == 0.17
    assert Settings.model_fields["clasificador_modelo_ruta"].default == ""
    assert settings.embedding_api_key == ""
    assert "sk-" not in settings.embedding_api_key
    assert "localhost:5173" in settings.cors_origin_list[0]
    assert "*" not in settings.cors_origin_list


def test_cors_acepta_el_origen_de_pages_sin_barra_final() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins=" https://agro-asistente.pages.dev/ ",
    )

    assert settings.cors_origin_list == ["https://agro-asistente.pages.dev"]


def test_cors_rechaza_comodines_y_conserva_el_origen_local() -> None:
    abierto = Settings(_env_file=None, cors_origins="*")
    assert abierto.cors_origin_list == [
        "http://localhost:5173",
        "https://agro-asistente.pages.dev",
    ]
    assert abierto.cors_origin_list != ["*"]

    mixto = Settings(
        _env_file=None,
        cors_origins="http://localhost:5173, *, https://*",
    )
    assert mixto.cors_origin_list == [
        "http://localhost:5173",
        "https://agro-asistente.pages.dev",
    ]
    assert "https://*" not in mixto.cors_origin_list


def test_cors_separa_el_dominio_principal_del_subdominio_de_despliegue() -> None:
    settings = Settings(
        _env_file=None,
        cors_origins=(
            "http://localhost:5173, "
            "https://agro-asistente.pages.dev/, "
            "https://*.agro-asistente.pages.dev"
        ),
    )

    assert settings.cors_origin_list == [
        "http://localhost:5173",
        "https://agro-asistente.pages.dev",
    ]
    assert "*" not in settings.cors_origin_list
    assert settings.cors_origin_regex == (
        r"^https://[A-Za-z0-9-]+\.agro-asistente\.pages\.dev$"
    )
