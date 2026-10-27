"""Lecture et validation du fichier .env.

Spécification : voir tests/test_config.py.
Seule DISCORD_WEBHOOK_URL est obligatoire pour la notification.
Les variables GLPI_* sont lues si elles sont présentes (usage futur : authentification API),
mais leur absence n'empêche pas le démarrage.
"""

from dataclasses import dataclass
from pathlib import Path

VARIABLES_OBLIGATOIRES = ("DISCORD_WEBHOOK_URL",)


class ConfigError(Exception):
    """Configuration absente ou incomplète."""


@dataclass(frozen=True)
class Config:
    discord_webhook_url: str
    glpi_base_url: str = ""
    glpi_client_id: str = ""
    glpi_client_secret: str = ""

    def __repr__(self) -> str:
        # Ne jamais afficher les secrets, même dans un log ou une trace
        return (
            f"Config(glpi_base_url={self.glpi_base_url!r}, "
            "glpi_client_id=***, glpi_client_secret=***, discord_webhook_url=***)"
        )


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
        discord_webhook_url=variables["DISCORD_WEBHOOK_URL"],
        glpi_base_url=variables.get("GLPI_BASE_URL", ""),
        glpi_client_id=variables.get("GLPI_CLIENT_ID", ""),
        glpi_client_secret=variables.get("GLPI_CLIENT_SECRET", ""),
    )
