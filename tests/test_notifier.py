"""Tests de src/notifier.py : traitement d'un webhook GLPI (formatage puis envoi Discord).

Spécification :
- traiter_ticket(payload, url_glpi, webhook_discord) envoie un message pour event "new".
- Un autre événement n'envoie rien.
- Sans url_glpi, le message ne contient pas de lien.
"""

from src import notifier

WEBHOOK = "https://discord.com/api/webhooks/123/SECRET"
PAYLOAD_NEW = {
    "item": {
        "id": 108,
        "name": "test 3 discord",
        "content": "<p>test</p>",
        "urgency": 3,
        "priority": 3,
        "date_creation": "2026-10-27T05:46:37+00:00",
    },
    "event": "new",
}


def test_evenement_new_envoie_un_message(monkeypatch):
    envois = []
    monkeypatch.setattr(notifier, "envoyer_vers_discord", lambda url, msg: envois.append((url, msg)))

    notifier.traiter_ticket(PAYLOAD_NEW, "https://ticketing.example", WEBHOOK)

    assert len(envois) == 1
    url, message = envois[0]
    assert url == WEBHOOK
    assert message["embeds"][0]["title"] == "Nouveau ticket #108 : test 3 discord"


def test_evenement_autre_que_new_n_envoie_rien(monkeypatch):
    envois = []
    monkeypatch.setattr(notifier, "envoyer_vers_discord", lambda url, msg: envois.append(msg))

    payload_update = {**PAYLOAD_NEW, "event": "update"}
    notifier.traiter_ticket(payload_update, "https://ticketing.example", WEBHOOK)

    assert envois == []


def test_sans_url_glpi_pas_de_lien(monkeypatch):
    envois = []
    monkeypatch.setattr(notifier, "envoyer_vers_discord", lambda url, msg: envois.append(msg))

    notifier.traiter_ticket(PAYLOAD_NEW, None, WEBHOOK)

    noms_champs = [champ["name"] for champ in envois[0]["embeds"][0]["fields"]]
    assert "Lien" not in noms_champs
