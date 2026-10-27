"""Envoi du message vers le webhook Discord.

Spécification : voir tests/test_discord_envoi.py.
L'URL du webhook est un secret : elle n'apparaît jamais dans un message d'erreur.
"""

import requests

DELAI_MAX_SECONDES = 10
CODES_SUCCES = (200, 204)
LONGUEUR_MAX_CORPS_ERREUR = 200


class DiscordError(Exception):
    """Échec de l'envoi du message vers Discord."""


def envoyer_vers_discord(webhook_url: str, message: dict) -> None:
    try:
        reponse = requests.post(webhook_url, json=message, timeout=DELAI_MAX_SECONDES)
    except requests.RequestException as erreur:
        # Le message ne contient ni l'URL du webhook ni le détail brut de l'exception
        raise DiscordError(f"Connexion à Discord impossible : {type(erreur).__name__}") from None

    if reponse.status_code not in CODES_SUCCES:
        corps = (reponse.text or "")[:LONGUEUR_MAX_CORPS_ERREUR]
        raise DiscordError(f"Discord a refusé le message (HTTP {reponse.status_code}) : {corps}")
