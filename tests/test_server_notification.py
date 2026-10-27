"""Tests du serveur en mode notification (traiter != None).

Spécification :
- Un JSON valide avec bon secret : traiter(payload) est appelé, réponse 200.
- Un corps qui n'est pas du JSON : réponse 400, traiter n'est pas appelé.
- Si traiter lève une exception : réponse 502, le secret n'apparaît dans aucune sortie.
- Sans bon secret : 401, traiter n'est pas appelé.
"""

import json
import threading

import pytest
import requests

from src.server import creer_serveur

SECRET = "secret-de-test-123"
CHEMIN = "/glpi-ticket"
EN_TETE = "X-Notifier-Secret"
PAYLOAD = {"item": {"id": 1}, "event": "new"}


def demarrer(traiter):
    srv = creer_serveur(secret=SECRET, chemin=CHEMIN, port=0, traiter=traiter)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def url(srv):
    _, port = srv.server_address
    return f"http://127.0.0.1:{port}{CHEMIN}"


@pytest.fixture
def appels():
    return []


@pytest.fixture
def serveur_ok(appels):
    srv = demarrer(lambda payload: appels.append(payload))
    yield srv
    srv.shutdown()
    srv.server_close()


def test_json_valide_appelle_traiter_et_renvoie_200(serveur_ok, appels):
    reponse = requests.post(url(serveur_ok), json=PAYLOAD, headers={EN_TETE: SECRET})

    assert reponse.status_code == 200
    assert appels == [PAYLOAD]


def test_corps_non_json_renvoie_400_sans_appeler_traiter(serveur_ok, appels):
    reponse = requests.post(
        url(serveur_ok),
        data=b"ceci n'est pas du json",
        headers={EN_TETE: SECRET, "Content-Type": "text/plain"},
    )

    assert reponse.status_code == 400
    assert appels == []


def test_mauvais_secret_renvoie_401_sans_appeler_traiter(serveur_ok, appels):
    reponse = requests.post(url(serveur_ok), json=PAYLOAD, headers={EN_TETE: "faux"})

    assert reponse.status_code == 401
    assert appels == []


def test_erreur_de_traitement_renvoie_502_sans_fuite_du_secret(capsys):
    def traiter_en_echec(payload):
        raise RuntimeError("Discord injoignable")

    srv = demarrer(traiter_en_echec)
    try:
        reponse = requests.post(url(srv), json=PAYLOAD, headers={EN_TETE: SECRET})
    finally:
        srv.shutdown()
        srv.server_close()

    sortie = capsys.readouterr()
    assert reponse.status_code == 502
    assert SECRET not in sortie.out
    assert SECRET not in sortie.err
