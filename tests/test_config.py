"""Tests de src/config.py : lecture et validation du fichier .env.

Spécification :
- charger_config(chemin) lit un fichier .env et renvoie un objet Config.
- Les lignes vides et les commentaires (#) sont ignorés.
- DISCORD_WEBHOOK_URL est obligatoire : absente ou vide, elle lève ConfigError.
- Les variables GLPI_* sont optionnelles.
- Le message d'erreur nomme la variable manquante, jamais sa valeur.
"""

import pytest

from src.config import ConfigError, charger_config

ENV_VALIDE = """\
# commentaire ignoré
GLPI_BASE_URL=https://ticketing.42antananarivo.mg
GLPI_CLIENT_ID=abc123

GLPI_CLIENT_SECRET=s3cr3t
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1/xyz
"""


def test_charge_les_variables_valides(tmp_path):
    fichier = tmp_path / ".env"
    fichier.write_text(ENV_VALIDE)

    config = charger_config(fichier)

    assert config.discord_webhook_url == "https://discord.com/api/webhooks/1/xyz"
    assert config.glpi_base_url == "https://ticketing.42antananarivo.mg"
    assert config.glpi_client_id == "abc123"
    assert config.glpi_client_secret == "s3cr3t"


def test_ignore_commentaires_et_lignes_vides(tmp_path):
    fichier = tmp_path / ".env"
    fichier.write_text(ENV_VALIDE)

    config = charger_config(fichier)

    assert config.glpi_client_id == "abc123"


def test_webhook_discord_seul_suffit(tmp_path):
    fichier = tmp_path / ".env"
    fichier.write_text("DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1/xyz\n")

    config = charger_config(fichier)

    assert config.discord_webhook_url == "https://discord.com/api/webhooks/1/xyz"
    assert config.glpi_client_id == ""
    assert config.glpi_client_secret == ""


def test_variables_glpi_absentes_ne_leve_pas_erreur(tmp_path):
    fichier = tmp_path / ".env"
    fichier.write_text("DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1/xyz\n")

    # Ne doit pas lever d'exception : GLPI_* sont optionnelles
    charger_config(fichier)


def test_webhook_discord_absent_leve_erreur(tmp_path):
    fichier = tmp_path / ".env"
    fichier.write_text("GLPI_BASE_URL=https://exemple.mg\nGLPI_CLIENT_ID=abc\n")

    with pytest.raises(ConfigError) as erreur:
        charger_config(fichier)

    assert "DISCORD_WEBHOOK_URL" in str(erreur.value)


def test_webhook_discord_vide_leve_erreur(tmp_path):
    fichier = tmp_path / ".env"
    fichier.write_text("DISCORD_WEBHOOK_URL=\n")

    with pytest.raises(ConfigError) as erreur:
        charger_config(fichier)

    assert "DISCORD_WEBHOOK_URL" in str(erreur.value)


def test_message_derreur_ne_contient_jamais_le_secret(tmp_path):
    fichier = tmp_path / ".env"
    fichier.write_text(
        "GLPI_CLIENT_SECRET=s3cr3t-tres-sensible\n"
        "DISCORD_WEBHOOK_URL=\n"
    )

    with pytest.raises(ConfigError) as erreur:
        charger_config(fichier)

    assert "s3cr3t-tres-sensible" not in str(erreur.value)


def test_fichier_inexistant_leve_erreur(tmp_path):
    with pytest.raises(ConfigError):
        charger_config(tmp_path / "absent.env")
