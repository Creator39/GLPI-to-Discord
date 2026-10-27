"""Tests de src/discord_envoi.py : envoi du message vers le webhook Discord.

Aucun appel réseau réel : requests.post est remplacé par un faux.

Spécification :
- envoyer_vers_discord(webhook_url, message) envoie message en JSON, avec un délai maximal.
- Discord répond 204 (ou 200) : succès, rien n'est renvoyé.
- Tout autre code HTTP lève DiscordError avec le code et le corps de la réponse.
- Une erreur réseau lève DiscordError.
- L'URL du webhook est un secret : elle n'apparaît jamais dans un message d'erreur.
"""

import pytest
import requests

from src.discord_envoi import DiscordError, envoyer_vers_discord

WEBHOOK = "https://discord.com/api/webhooks/123/SECRET-TOKEN-XYZ"
MESSAGE = {"embeds": [{"title": "Nouveau ticket #108 : test"}]}


class FauxReponse:
    def __init__(self, status_code, texte=""):
        self.status_code = status_code
        self.text = texte


def test_succes_204_ne_leve_rien(monkeypatch):
    appels = []

    def faux_post(url, **kwargs):
        appels.append((url, kwargs))
        return FauxReponse(204)

    monkeypatch.setattr(requests, "post", faux_post)

    envoyer_vers_discord(WEBHOOK, MESSAGE)

    assert len(appels) == 1


def test_message_envoye_en_json_avec_delai(monkeypatch):
    appels = []

    def faux_post(url, **kwargs):
        appels.append((url, kwargs))
        return FauxReponse(204)

    monkeypatch.setattr(requests, "post", faux_post)

    envoyer_vers_discord(WEBHOOK, MESSAGE)

    url, kwargs = appels[0]
    assert url == WEBHOOK
    assert kwargs["json"] == MESSAGE
    assert "timeout" in kwargs


def test_succes_200_ne_leve_rien(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda url, **kw: FauxReponse(200))

    envoyer_vers_discord(WEBHOOK, MESSAGE)


def test_code_404_leve_discordError_avec_le_code(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda url, **kw: FauxReponse(404, "Unknown Webhook"))

    with pytest.raises(DiscordError) as erreur:
        envoyer_vers_discord(WEBHOOK, MESSAGE)

    assert "404" in str(erreur.value)
    assert "Unknown Webhook" in str(erreur.value)


def test_code_400_leve_discordError(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda url, **kw: FauxReponse(400, "Invalid payload"))

    with pytest.raises(DiscordError):
        envoyer_vers_discord(WEBHOOK, MESSAGE)


def test_erreur_reseau_leve_discordError(monkeypatch):
    def faux_post(url, **kwargs):
        raise requests.ConnectionError("connexion refusée")

    monkeypatch.setattr(requests, "post", faux_post)

    with pytest.raises(DiscordError):
        envoyer_vers_discord(WEBHOOK, MESSAGE)


def test_url_du_webhook_absente_des_erreurs_reseau(monkeypatch):
    def faux_post(url, **kwargs):
        raise requests.ConnectionError(f"échec sur {url}")

    monkeypatch.setattr(requests, "post", faux_post)

    with pytest.raises(DiscordError) as erreur:
        envoyer_vers_discord(WEBHOOK, MESSAGE)

    assert "SECRET-TOKEN-XYZ" not in str(erreur.value)


def test_url_du_webhook_absente_des_erreurs_http(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda url, **kw: FauxReponse(401, "Unauthorized"))

    with pytest.raises(DiscordError) as erreur:
        envoyer_vers_discord(WEBHOOK, MESSAGE)

    assert "SECRET-TOKEN-XYZ" not in str(erreur.value)
