"""Tests des mises à jour de ticket (event "update") dans src/discord.py.

Spécification :
- event "update" est notifié seulement si date_mod est différente de date_creation.
  Un ticket qui vient d'être créé peut déclencher un "update" sans modification réelle :
  il ne doit pas être notifié une seconde fois.
- Titre : "Ticket mis à jour #<id> : <nom>".
- Un champ "Mis à jour le" affiche date_mod en heure de Madagascar.
- Un "new" n'a pas de champ "Mis à jour le".
"""

import copy

from src.discord import formater_message

PAYLOAD_UPDATE = {
    "item": {
        "id": 108,
        "name": "test 3 discord",
        "content": "<p>test</p>",
        "urgency": 3,
        "priority": 3,
        "date_creation": "2026-10-27T05:46:37+00:00",
        "date_mod": "2026-10-27T06:10:00+00:00",
        "status": {"id": 5, "name": "Résolu"},
        "user_recipient": {"id": 2, "name": "toto"},
        "entity": {"id": 0, "completename": "Root entity"},
        "category": None,
    },
    "event": "update",
}

URL_GLPI = "https://ticketing.42antananarivo.mg"


def payload_modifie(**modifications):
    donnees = copy.deepcopy(PAYLOAD_UPDATE)
    for chemin, valeur in modifications.items():
        cible = donnees
        *parents, dernier = chemin.split("__")
        for parent in parents:
            cible = cible[parent]
        cible[dernier] = valeur
    return donnees


def champs_par_nom(message):
    return {champ["name"]: champ["value"] for champ in message["embeds"][0]["fields"]}


def test_update_avec_modification_reelle_est_notifie():
    message = formater_message(PAYLOAD_UPDATE, URL_GLPI)

    assert message is not None
    assert message["embeds"][0]["title"] == "Ticket mis à jour #108 : test 3 discord"


def test_update_sans_modification_reelle_est_ignore():
    # Cas de la création par formulaire : date_mod égale date_creation
    donnees = payload_modifie(item__date_mod="2026-10-27T05:46:37+00:00")

    assert formater_message(donnees, URL_GLPI) is None


def test_update_sans_date_mod_est_ignore():
    donnees = payload_modifie(item__date_mod=None)

    assert formater_message(donnees, URL_GLPI) is None


def test_update_affiche_la_date_de_modification_en_heure_de_madagascar():
    # 06:10 UTC = 09:10 à Madagascar
    champs = champs_par_nom(formater_message(PAYLOAD_UPDATE, URL_GLPI))

    assert champs["Mis à jour le"] == "2026-10-27 09:10 (Madagascar)"


def test_new_na_pas_de_champ_mis_a_jour_le():
    donnees = payload_modifie(event="new")

    champs = champs_par_nom(formater_message(donnees, URL_GLPI))

    assert "Mis à jour le" not in champs
