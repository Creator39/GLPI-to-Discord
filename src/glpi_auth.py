"""Obtention du jeton d'accès GLPI (OAuth2 client_credentials).

Spécification : voir tests/test_glpi_auth.py.
La vérification TLS reste active : le certificat de GLPI doit être valide.
"""

import requests

from src.config import Config

DELAI_MAX_SECONDES = 10


class AuthError(Exception):
    """Échec d'obtention du jeton GLPI."""


def obtenir_jeton(config: Config) -> str:
    if not (config.glpi_base_url and config.glpi_client_id and config.glpi_client_secret):
        # Sans ces trois valeurs, aucune requête n'est tentée
        raise AuthError("Variables GLPI_* absentes : authentification impossible")

    url = f"{config.glpi_base_url}/api.php/v2/token"
    donnees = {
        "grant_type": "client_credentials",
        "client_id": config.glpi_client_id,
        "client_secret": config.glpi_client_secret,
    }

    try:
        reponse = requests.post(url, data=donnees, timeout=DELAI_MAX_SECONDES)
    except requests.RequestException as erreur:
        # Le message ne contient pas les identifiants envoyés
        raise AuthError(f"Connexion à GLPI impossible : {type(erreur).__name__}") from None

    if reponse.status_code != 200:
        raise AuthError(
            f"GLPI a refusé la demande de jeton (HTTP {reponse.status_code}) : {reponse.text}"
        )

    try:
        jeton = reponse.json().get("access_token")
    except ValueError:
        jeton = None

    if not jeton:
        raise AuthError("Réponse de GLPI sans access_token")

    return jeton
