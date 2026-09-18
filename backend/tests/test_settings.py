from app.infrastructure.config.settings import Settings


def test_settings_load_defaults_without_secrets_in_code() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "agro-asistente"
    assert settings.mysql_database == "agro_asistente"
    assert settings.embedding_provider == "local"
    assert settings.chroma_collection == "agro_knowledge_pmv1"
    assert settings.rag_top_k == 3
    assert settings.embedding_api_key == ""
    assert "sk-" not in settings.embedding_api_key
    assert "localhost:5173" in settings.cors_origin_list[0]
