"""Tests de src/server.py : serveur de capture des webhooks GLPI.

Spécification :
- creer_serveur(secret, chemin, port) renvoie un serveur HTTP (non démarré).
- Seul un POST sur `chemin` avec l'en-tête `X-Notifier-Secret` égal à `secret`
  est accepté : réponse 200.
- Sans en-tête, ou avec un mauvais secret : réponse 401, rien n'est affiché.
- Le corps JSON valide est affiché tel quel sur la sortie standard.
- La valeur du secret n'apparaît jamais dans la sortie.
- Aucun appel vers Discord (requests.post) n'est fait pendant la capture.
"""

import json
import threading
import urllib.request

import pytest
import requests

from src.server import creer_serveur

SECRET = "secret-de-test-123"
CHEMIN = "/glpi-ticket-test"
EN_TETE = "X-Notifier-Secret"
CORPS = {"test": "ok", "id": 42}


@pytest.fixture
def serveur():
    srv = creer_serveur(secret=SECRET, chemin=CHEMIN, port=0)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def url(srv):
    _, port = srv.server_address
    return f"http://127.0.0.1:{port}{CHEMIN}"


def test_post_avec_bon_secret_renvoie_200(serveur):
    reponse = requests.post(url(serveur), json=CORPS, headers={EN_TETE: SECRET})

    assert reponse.status_code == 200


def test_post_sans_en_tete_renvoie_401(serveur):
    reponse = requests.post(url(serveur), json=CORPS)

    assert reponse.status_code == 401


def test_post_avec_mauvais_secret_renvoie_401(serveur):
    reponse = requests.post(url(serveur), json=CORPS, headers={EN_TETE: "faux"})

    assert reponse.status_code == 401


def test_corps_recu_est_affiche_tel_quel(serveur, capsys):
    requests.post(url(serveur), json=CORPS, headers={EN_TETE: SECRET})

    sortie = capsys.readouterr().out

    assert json.dumps(CORPS) in sortie


def test_secret_absent_de_la_sortie(serveur, capsys):
    requests.post(url(serveur), json=CORPS, headers={EN_TETE: SECRET})
    requests.post(url(serveur), json=CORPS, headers={EN_TETE: "faux"})

    sortie = capsys.readouterr()

    assert SECRET not in sortie.out
    assert SECRET not in sortie.err


def test_aucun_appel_discord_pendant_la_capture(serveur, monkeypatch):
    appels = []

    def faux_post(url, **kwargs):
        appels.append(url)
        raise AssertionError("Discord ne doit pas être appelé pendant la capture")

    # On remplace requests.post pour détecter tout appel vers Discord.
    # Le client de test utilise urllib, sinon il serait lui-même intercepté.
    monkeypatch.setattr(requests, "post", faux_post)

    requete = urllib.request.Request(
        url(serveur),
        data=json.dumps(CORPS).encode("utf-8"),
        headers={"Content-Type": "application/json", EN_TETE: SECRET},
        method="POST",
    )
    with urllib.request.urlopen(requete) as reponse:
        assert reponse.status == 200

    assert appels == []
