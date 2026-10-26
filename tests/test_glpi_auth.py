"""Tests de src/glpi_auth.py : obtention du jeton OAuth2 client_credentials.

Aucun appel réseau réel : requests.post est remplacé par un faux.

Spécification :
- obtenir_jeton(config) envoie grant_type=client_credentials, client_id et client_secret.
- Si la réponse est 200 avec un access_token, la fonction renvoie ce jeton.
- Si le code HTTP n'est pas 200, lève AuthError contenant le code et le corps.
- Si la requête échoue au niveau réseau, lève AuthError.
- Ni le secret ni le jeton n'apparaissent dans un message d'erreur.
"""

import pytest
import requests

from src.config import Config
from src.glpi_auth import AuthError, obtenir_jeton

CONFIG = Config(
    glpi_base_url="https://ticketing.42antananarivo.mg",
    glpi_client_id="abc123",
    glpi_client_secret="s3cr3t-tres-sensible",
    discord_webhook_url="https://discord.com/api/webhooks/1/xyz",
)


class FauxReponse:
    def __init__(self, status_code, corps):
        self.status_code = status_code
        self._corps = corps
        self.text = str(corps)

    def json(self):
        return self._corps


def test_renvoie_le_jeton_si_reponse_200(monkeypatch):
    def faux_post(url, **kwargs):
        return FauxReponse(200, {"access_token": "jeton-valide", "expires_in": 3600})

    monkeypatch.setattr(requests, "post", faux_post)

    assert obtenir_jeton(CONFIG) == "jeton-valide"


def test_envoie_grant_type_client_credentials_et_identifiants(monkeypatch):
    appels = {}

    def faux_post(url, **kwargs):
        appels["url"] = url
        appels["kwargs"] = kwargs
        return FauxReponse(200, {"access_token": "jeton"})

    monkeypatch.setattr(requests, "post", faux_post)

    obtenir_jeton(CONFIG)

    # Le format (data= ou json=, corps ou Basic Auth) est à confirmer
    # dans la documentation de l'instance : on vérifie ici les valeurs.
    envoye = str(appels["kwargs"])
    assert "client_credentials" in envoye
    assert "abc123" in envoye
    assert "s3cr3t-tres-sensible" in envoye
    assert appels["url"].startswith(CONFIG.glpi_base_url)


def test_code_http_non_200_leve_authError_avec_code_et_corps(monkeypatch):
    def faux_post(url, **kwargs):
        return FauxReponse(401, {"status": "ERROR_UNAUTHENTICATED"})

    monkeypatch.setattr(requests, "post", faux_post)

    with pytest.raises(AuthError) as erreur:
        obtenir_jeton(CONFIG)

    message = str(erreur.value)
    assert "401" in message
    assert "ERROR_UNAUTHENTICATED" in message


def test_erreur_reseau_leve_authError(monkeypatch):
    def faux_post(url, **kwargs):
        raise requests.ConnectionError("connexion refusée")

    monkeypatch.setattr(requests, "post", faux_post)

    with pytest.raises(AuthError):
        obtenir_jeton(CONFIG)


def test_message_derreur_ne_contient_pas_le_secret(monkeypatch):
    def faux_post(url, **kwargs):
        return FauxReponse(500, {"detail": "erreur interne"})

    monkeypatch.setattr(requests, "post", faux_post)

    with pytest.raises(AuthError) as erreur:
        obtenir_jeton(CONFIG)

    assert "s3cr3t-tres-sensible" not in str(erreur.value)


def test_reponse_200_sans_access_token_leve_authError(monkeypatch):
    def faux_post(url, **kwargs):
        return FauxReponse(200, {"expires_in": 3600})

    monkeypatch.setattr(requests, "post", faux_post)

    with pytest.raises(AuthError):
        obtenir_jeton(CONFIG)
