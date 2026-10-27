"""Tests de src/discord.py : transformation du webhook GLPI en message Discord.

Spécification :
- formater_message(payload, url_glpi) ne traite que event == "new" ; sinon renvoie None.
- Renvoie un corps Discord : {"embeds": [ {...} ]}.
- Titre : "Nouveau ticket #<id> : <nom>", tronqué à 256 caractères.
- Description : contenu HTML converti en texte brut, tronqué à 4096 caractères.
- Champs : demandeur, statut, urgence et priorité (libellés 1 à 5), entité, date (heure de Madagascar, UTC+3).
- Lien vers le ticket seulement si url_glpi est fourni.
- Les noms des intervenants (realname, firstname) n'apparaissent jamais.
- Les champs null ou absents ne font pas planter la fonction.
"""

import copy
import json

from src.discord import formater_message

PAYLOAD = {
    "item": {
        "id": 108,
        "name": "test 3 discord",
        "content": "<p><strong>test</strong></p>",
        "urgency": 3,
        "impact": 3,
        "priority": 3,
        "date_creation": "2026-10-27T05:46:37+00:00",
        "status": {"id": 2, "name": "En cours (Attribué)"},
        "user_recipient": {"id": 2, "name": "toto"},
        "entity": {"id": 0, "name": "Root entity", "completename": "Root entity"},
        "category": None,
        "team": [
            {
                "role": "requester",
                "name": "toto",
                "realname": "sauron",
                "firstname": None,
                "display_name": "sauron",
                "id": 2,
            }
        ],
    },
    "event": "new",
}

URL_GLPI = "https://ticketing.42antananarivo.mg"


def payload_modifie(**modifications):
    donnees = copy.deepcopy(PAYLOAD)
    for chemin, valeur in modifications.items():
        cible = donnees
        *parents, dernier = chemin.split("__")
        for parent in parents:
            cible = cible[parent]
        cible[dernier] = valeur
    return donnees


def premier_embed(message):
    return message["embeds"][0]


def champs_par_nom(message):
    return {champ["name"]: champ["value"] for champ in premier_embed(message)["fields"]}


def test_evenement_new_produit_un_embed():
    message = formater_message(PAYLOAD, URL_GLPI)

    assert message is not None
    assert len(message["embeds"]) == 1


def test_autre_evenement_est_ignore():
    message = formater_message(payload_modifie(event="update"), URL_GLPI)

    assert message is None


def test_titre_contient_id_et_nom():
    embed = premier_embed(formater_message(PAYLOAD, URL_GLPI))

    assert embed["title"] == "Nouveau ticket #108 : test 3 discord"


def test_description_convertit_le_html_en_texte():
    embed = premier_embed(formater_message(PAYLOAD, URL_GLPI))

    assert "test" in embed["description"]
    assert "<" not in embed["description"]
    assert ">" not in embed["description"]


def test_champs_statut_demandeur_entite_et_date():
    champs = champs_par_nom(formater_message(PAYLOAD, URL_GLPI))

    assert champs["Statut"] == "En cours (Attribué)"
    assert champs["Demandeur"] == "toto"
    assert champs["Entité"] == "Root entity"
    assert champs["Créé le"] == "2026-10-27 08:46 (Madagascar)"


def test_date_convertie_en_heure_de_madagascar_au_changement_de_jour():
    donnees = payload_modifie(item__date_creation="2026-10-27T22:30:00+00:00")

    champs = champs_par_nom(formater_message(donnees, URL_GLPI))

    assert champs["Créé le"] == "2026-10-28 01:30 (Madagascar)"


def test_date_absente_donne_un_tiret():
    donnees = payload_modifie(item__date_creation=None)

    champs = champs_par_nom(formater_message(donnees, URL_GLPI))

    assert champs["Créé le"] == "—"


def test_rubriques_du_formulaire_sur_des_lignes_separees():
    donnees = payload_modifie(
        item__content="<p>1) Titre : test 2) Description : test 3) Pièce jointe : photo.jpeg</p>"
    )

    description = premier_embed(formater_message(donnees, URL_GLPI))["description"]

    assert description.split("\n") == [
        "1) Titre : test",
        "2) Description : test",
        "3) Pièce jointe : photo.jpeg",
    ]


def test_texte_sans_rubriques_garde_ses_retours_et_reduit_les_espaces():
    donnees = payload_modifie(item__content="<p>Panne   réseau\n au bureau</p>")

    description = premier_embed(formater_message(donnees, URL_GLPI))["description"]

    assert description == "Panne réseau\nau bureau"


def test_categorie_affichee_si_renseignee():
    donnees = payload_modifie(item__category={"id": 3, "name": "Réseau"})

    champs = champs_par_nom(formater_message(donnees, URL_GLPI))

    assert champs["Catégorie"] == "Réseau"


def test_categorie_absente_affiche_aucune():
    champs = champs_par_nom(formater_message(PAYLOAD, URL_GLPI))

    assert champs["Catégorie"] == "Aucune"


def test_urgence_et_priorite_sont_traduites():
    champs = champs_par_nom(formater_message(PAYLOAD, URL_GLPI))

    assert champs["Urgence"] == "Moyenne"
    assert champs["Priorité"] == "Moyenne"


def test_valeur_urgence_inconnue_ne_plante_pas():
    message = formater_message(payload_modifie(item__urgency=9), URL_GLPI)

    assert champs_par_nom(message)["Urgence"] == "Inconnue"


def test_lien_vers_le_ticket_si_url_fournie():
    champs = champs_par_nom(formater_message(PAYLOAD, URL_GLPI))

    assert champs["Lien"] == f"{URL_GLPI}/front/ticket.form.php?id=108"


def test_pas_de_lien_si_url_absente():
    champs = champs_par_nom(formater_message(PAYLOAD, None))

    assert "Lien" not in champs


def test_noms_des_intervenants_absents_du_message():
    message = formater_message(PAYLOAD, URL_GLPI)

    assert "sauron" not in json.dumps(message)


def test_titre_et_description_sont_tronques():
    donnees = payload_modifie(
        item__name="x" * 300,
        item__content="<p>" + "a" * 5000 + "</p>",
    )

    embed = premier_embed(formater_message(donnees, URL_GLPI))

    assert len(embed["title"]) <= 256
    assert len(embed["description"]) <= 4096


def test_champs_null_ou_absents_ne_plantent_pas():
    donnees = payload_modifie(item__content=None, item__user_recipient=None)

    message = formater_message(donnees, URL_GLPI)

    assert premier_embed(message)["description"] == "(pas de description)"
    assert champs_par_nom(message)["Demandeur"] == "—"
