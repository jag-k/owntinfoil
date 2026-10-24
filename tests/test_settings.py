import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from app.config import BASE_PATH, Settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_default_paths_are_relative_to_repository(self):
        self.assertEqual(BASE_PATH, Path(__file__).resolve().parents[1])
        settings = Settings(_env_file=None)
        self.assertEqual(settings.nps_dir, BASE_PATH / "NPSdir")
        self.assertEqual(settings.torrent_dir, BASE_PATH / "TORRENTdir")

    def test_environment_values_have_types(self):
        with patch.dict(os.environ, {"PORT": "9090", "NPS_DIR": "fixture-shop", "BOT_KEY": " fixture-secret "}):
            settings = Settings(_env_file=None)
        self.assertEqual(settings.port, 9090)
        self.assertEqual(settings.nps_dir, Path("fixture-shop"))
        self.assertEqual(settings.bot_key.get_secret_value(), "fixture-secret")
        self.assertNotIn("fixture-secret", repr(settings))
        self.assertNotIn("fixture-secret", settings.model_dump_json())

    def test_invalid_port_is_rejected_without_echoing_input(self):
        for value in ("fixture-secret", "0", "65536"):
            with self.subTest(value=value), patch.dict(os.environ, {"PORT": value}):
                with self.assertRaises(ValidationError) as error:
                    Settings(_env_file=None)
                self.assertNotIn("input_value", str(error.exception))

    def test_dotenv_and_environment_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("PORT=8090\nBOT_KEY=fixture-key\nUNRELATED=value\n", encoding="utf-8")
            with patch.dict(os.environ, {"PORT": "9090"}):
                settings = Settings(_env_file=env_file)
        self.assertEqual(settings.port, 9090)
        self.assertEqual(settings.bot_key.get_secret_value(), "fixture-key")

    def test_legacy_auth_from_environment(self):
        with patch.dict(os.environ, {"HTTP_AUTH_USER_1": "tester:pass:word", "HTTP_AUTH_USER_2": "malformed"}):
            settings = Settings(_env_file=None)
        self.assertEqual(settings.http_auth_users["tester"].get_secret_value(), "pass:word")
        self.assertEqual(len(settings.http_auth_users), 1)

    def test_legacy_auth_from_dotenv(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("HTTP_AUTH_USER_1=tester:from-file\n", encoding="utf-8")
            with patch.dict(os.environ, {"HTTP_AUTH_USER_1": "tester:from-env"}):
                settings = Settings(_env_file=env_file)
        self.assertEqual(settings.http_auth_users["tester"].get_secret_value(), "from-env")

    def test_auth_json_overrides_legacy(self):
        with patch.dict(
            os.environ,
            {
                "HTTP_AUTH_USERS": '{"tester":"canonical"}',
                "HTTP_AUTH_USER_1": "tester:legacy",
            },
        ):
            settings = Settings(_env_file=None)
        self.assertEqual(settings.http_auth_users["tester"].get_secret_value(), "canonical")

    def test_no_bot_credentials_required_and_no_directories_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "new"
            settings = Settings(_env_file=None, nps_dir=path / "shop", torrent_dir=path / "watch")
            self.assertEqual(settings.bot_key.get_secret_value(), "")
            self.assertFalse(path.exists())
            settings.ensure_directories()
            self.assertTrue(settings.nps_dir.is_dir())
            self.assertTrue(settings.torrent_dir.is_dir())
