import importlib


def test_database_config_reads_environment(monkeypatch):
    from config import db_config

    with monkeypatch.context() as env:
        env.setenv("SERPLENO_DB_HOST", "db.internal")
        env.setenv("SERPLENO_DB_PORT", "3307")
        env.setenv("SERPLENO_DB_USER", "desktop_user")
        env.setenv("SERPLENO_DB_PASSWORD", "secret")
        env.setenv("SERPLENO_DB_NAME", "desktop_db")

        reloaded = importlib.reload(db_config)

        assert reloaded.DB_CONFIG == {
            "host": "db.internal",
            "user": "desktop_user",
            "password": "secret",
            "database": "desktop_db",
            "port": 3307,
        }

    importlib.reload(db_config)


def test_api_config_reads_environment(monkeypatch):
    from config import config

    with monkeypatch.context() as env:
        env.setenv("SERPLENO_API_URL", "https://api.example.test/")
        env.delenv("SERPLENO_DESKTOP_API_URL", raising=False)
        env.delenv("SERPLENO_MURAL_API_URL", raising=False)

        reloaded = importlib.reload(config)

        assert reloaded.API_ROOT_URL == "https://api.example.test"
        assert reloaded.DESKTOP_API_URL == "https://api.example.test/api/v1/desktop"
        assert reloaded.MURAL_API_URL == "https://api.example.test/api/mural"

    importlib.reload(config)
