"""Serveur de réception des webhooks GLPI.

Deux modes :
- capture (traiter=None) : affiche le corps reçu, n'envoie rien. Sert à découvrir le format.
- notification (traiter=fonction) : décode le JSON et délègue le traitement à la fonction.

Spécification : voir tests/test_server.py et tests/test_server_notification.py.
Les erreurs ne journalisent jamais le secret ni le corps reçu.
"""

import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.notifier import traiter_ticket

EN_TETE_SECRET = "X-Notifier-Secret"


def creer_serveur(secret: str, chemin: str, port: int, hote: str = "127.0.0.1", traiter=None) -> HTTPServer:
    class GestionnaireWebhook(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != chemin:
                self.send_error(404)
                return

            recu = self.headers.get(EN_TETE_SECRET, "")
            if not hmac.compare_digest(recu.encode("utf-8"), secret.encode("utf-8")):
                self.send_error(401)
                return

            taille = int(self.headers.get("Content-Length", 0))
            corps = self.rfile.read(taille).decode("utf-8", errors="replace")

            if traiter is None:
                print(corps, flush=True)
                self._repondre(200)
                return

            try:
                payload = json.loads(corps)
            except ValueError:
                self.send_error(400)
                return

            try:
                traiter(payload)
            except Exception as erreur:
                # Seul le type de l'erreur est journalisé : pas de détail pouvant contenir un secret
                print(f"Échec du traitement : {type(erreur).__name__}", flush=True)
                self.send_error(502)
                return

            self._repondre(200)

        def _repondre(self, code: int):
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, format, *args):
            # Journal minimal : méthode et chemin seulement, sans en-têtes ni corps
            print(f"{self.command} {self.path}", flush=True)

    return HTTPServer((hote, port), GestionnaireWebhook)


if __name__ == "__main__":
    secret = os.environ["NOTIFIER_SECRET"]
    chemin = os.environ.get("NOTIFIER_CHEMIN", "/glpi-ticket")
    port = int(os.environ.get("NOTIFIER_PORT", "80"))
    mode = os.environ.get("NOTIFIER_MODE", "notification")

    if mode == "capture":
        traiter = None
    else:
        webhook_discord = os.environ["DISCORD_WEBHOOK_URL"]
        url_glpi = os.environ.get("GLPI_PUBLIC_URL") or None

        def traiter(payload):
            traiter_ticket(payload, url_glpi, webhook_discord)

    serveur = creer_serveur(secret=secret, chemin=chemin, port=port, hote="0.0.0.0", traiter=traiter)
    print(f"Notifier en écoute sur le port {port} (mode {mode})", flush=True)
    serveur.serve_forever()
