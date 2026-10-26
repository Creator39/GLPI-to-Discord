# glpi-discord-notifier

Notification Discord à la création d'un ticket GLPI (tickets créés via le formulaire).

## Structure

- `src/` : code du projet (authentification GLPI, lecture des tickets, envoi Discord)
- `tests/` : tests écrits avant l'implémentation
- `.env.example` : variables d'environnement à copier dans `.env`
- `.gitignore` : exclut les secrets (`.env`) et l'état local (`state.json`)

## Étape en cours

Obtenir un jeton d'accès via OAuth2 `client_credentials` depuis l'API v2 de GLPI.
