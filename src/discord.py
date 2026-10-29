"""Transformation du webhook GLPI en message Discord (embed).

Spécification : voir tests/test_discord.py.
Cette fonction ne fait aucun appel réseau : l'envoi est une étape séparée.
"""

import html
import re
from datetime import datetime, timedelta, timezone

EVENEMENTS_NOTIFIES = ("new", "update")
LONGUEUR_MAX_TITRE = 256
LONGUEUR_MAX_DESCRIPTION = 4096
LONGUEUR_MAX_VALEUR_CHAMP = 1024
COULEUR_EMBED = 0x2F80ED  # bleu
# Madagascar : UTC+3 toute l'année, sans heure d'été
FUSEAU_MADAGASCAR = timezone(timedelta(hours=3))

NIVEAUX = {1: "Très basse", 2: "Basse", 3: "Moyenne", 4: "Haute", 5: "Très haute"}

# Emoji par catégorie GLPI ; les catégories inconnues reçoivent EMOJI_CATEGORIE_PAR_DEFAUT
EMOJIS_CATEGORIES = {
    "IT": "💻",
    "Pédagogie": "🎓",
    "Employabilité": "💼",
    "Communication": "📣",
    "Office Management": "🏢",
    "Direction": "👔",
}
EMOJI_CATEGORIE_PAR_DEFAUT = "📌"


def html_vers_texte(contenu: str | None) -> str:
    texte = re.sub(r"<[^>]+>", " ", contenu or "")
    texte = html.unescape(texte)
    # Les réponses de formulaire sont enregistrées sur une seule ligne : "1) ... 2) ..."
    # Un saut de ligne est inséré avant chaque rubrique numérotée (1) à 99))
    texte = re.sub(r"\s+(?=\d{1,2}\)\s)", "\n", texte)
    lignes = (" ".join(ligne.split()) for ligne in texte.split("\n"))
    return "\n".join(ligne for ligne in lignes if ligne)


def formater_date(date_brute: str | None) -> str:
    if not date_brute:
        return "—"
    try:
        date = datetime.fromisoformat(date_brute)
    except ValueError:
        return "—"
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    locale = date.astimezone(FUSEAU_MADAGASCAR)
    return locale.strftime("%Y-%m-%d %H:%M") + " (Madagascar)"


def _tronquer(texte: str, longueur: int) -> str:
    if len(texte) <= longueur:
        return texte
    return texte[: longueur - 1] + "…"


def _sous_champ(item: dict, cle: str, sous_cle: str, defaut: str) -> str:
    objet = item.get(cle) or {}
    return objet.get(sous_cle) or defaut


def libelle_categorie(item: dict) -> str:
    nom = _sous_champ(item, "category", "name", "")
    if not nom:
        return "Aucune"
    return f"{EMOJIS_CATEGORIES.get(nom, EMOJI_CATEGORIE_PAR_DEFAUT)} {nom}"


def _modification_reelle(item: dict) -> bool:
    # Un ticket créé par formulaire peut déclencher un "update" sans modification réelle
    date_mod = item.get("date_mod")
    return bool(date_mod) and date_mod != item.get("date_creation")


def formater_message(payload: dict, url_glpi: str | None = None) -> dict | None:
    evenement = payload.get("event")
    if evenement not in EVENEMENTS_NOTIFIES:
        return None

    item = payload["item"]
    if evenement == "update" and not _modification_reelle(item):
        return None

    ticket_id = item["id"]

    if evenement == "new":
        titre = f"Nouveau ticket #{ticket_id} : {item.get('name') or 'sans titre'}"
    else:
        titre = f"Ticket mis à jour #{ticket_id} : {item.get('name') or 'sans titre'}"
    corps = html_vers_texte(item.get("content")) or "(pas de description)"
    # La catégorie est la première ligne de la description : elle s'affiche juste sous le titre, en titre markdown (## = plus grand)
    description = f"### {libelle_categorie(item)}\n{corps}"

    champs = [
        {"name": "Demandeur", "value": _sous_champ(item, "user_recipient", "name", "—"), "inline": True},
        {"name": "Statut", "value": _sous_champ(item, "status", "name", "Inconnu"), "inline": True},
        {"name": "Urgence", "value": NIVEAUX.get(item.get("urgency"), "Inconnue"), "inline": True},
        {"name": "Priorité", "value": NIVEAUX.get(item.get("priority"), "Inconnue"), "inline": True},
        {"name": "Entité", "value": _sous_champ(item, "entity", "completename", "—"), "inline": True},
        {"name": "Créé le", "value": formater_date(item.get("date_creation")), "inline": True},
    ]

    if evenement == "update":
        champs.append({"name": "Mis à jour le", "value": formater_date(item.get("date_mod")), "inline": True})

    if url_glpi:
        lien = f"{url_glpi.rstrip('/')}/front/ticket.form.php?id={ticket_id}"
        champs.append({"name": "Lien", "value": lien, "inline": False})

    for champ in champs:
        champ["value"] = _tronquer(str(champ["value"]), LONGUEUR_MAX_VALEUR_CHAMP)

    embed = {
        "title": _tronquer(titre, LONGUEUR_MAX_TITRE),
        "description": _tronquer(description, LONGUEUR_MAX_DESCRIPTION),
        "color": COULEUR_EMBED,
        "fields": champs,
    }

    return {"embeds": [embed]}
