"""Traitement d'un webhook GLPI : formatage puis envoi vers Discord.

Spécification : voir tests/test_notifier.py.
"""

from src.discord import formater_message
from src.discord_envoi import envoyer_vers_discord


def traiter_ticket(payload: dict, url_glpi: str | None, webhook_discord: str) -> None:
    message = formater_message(payload, url_glpi)
    if message is None:
        # Événement non traité (seul "new" déclenche une notification)
        return
    envoyer_vers_discord(webhook_discord, message)
