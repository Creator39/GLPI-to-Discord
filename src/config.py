"""Lecture et validation du fichier .env.

Spécification : voir tests/test_config.py.
"""

from dataclasses import dataclass
from pathlib import Path

VARIABLES_OBLIGATOIRES = (
    "GLPI_BASE_URL",
    "GLPI_CLIENT_ID",
    "GLPI_CLIENT_SECRET",
    "DISCORD_WEBHOOK_URL",
)


class ConfigError(Exception):
    """Configuration absente ou incomplète."""


@dataclass(frozen=True)
class Config:
    glpi_base_url: str
    glpi_client_id: str
    glpi_client_secret: str
    discord_webhook_url: str

    def __repr__(self) -> str:
        # Ne jamais afficher les secrets, même dans un log ou une trace
        return f"Config(glpi_base_url={self.glpi_base_url!r}, glpi_client_id=***, glpi_client_secret=***, discord_webhook_url=***)"


def _lire_variables(chemin: Path) -> dict[str, str]:
    variables = {}
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, valeur = ligne.split("=", 1)
        variables[cle.strip()] = valeur.strip()
    return variables


def charger_config(chemin: Path) -> Config:
    chemin = Path(chemin)
    if not chemin.is_file():
        raise ConfigError(f"Fichier de configuration introuvable : {chemin}")

    variables = _lire_variables(chemin)

    manquantes = [nom for nom in VARIABLES_OBLIGATOIRES if not variables.get(nom)]
    if manquantes:
        # Seuls les noms des variables apparaissent, jamais leurs valeurs
        raise ConfigError("Variables manquantes ou vides : " + ", ".join(manquantes))

    return Config(
        glpi_base_url=variables["GLPI_BASE_URL"],
        glpi_client_id=variables["GLPI_CLIENT_ID"],
        glpi_client_secret=variables["GLPI_CLIENT_SECRET"],
        discord_webhook_url=variables["DISCORD_WEBHOOK_URL"],
    )
