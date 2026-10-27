"""Serveur de capture des webhooks GLPI.

Phase de capture : accepte un POST sur le chemin configuré, vérifie le secret,
affiche le corps reçu. N'appelle jamais Discord.

Spécification : voir tests/test_server.py.
"""

import hmac
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

EN_TETE_SECRET = "X-Notifier-Secret"


def creer_serveur(secret: str, chemin: str, port: int, hote: str = "127.0.0.1") -> HTTPServer:
    class GestionnaireCapture(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != chemin:
                self.send_error(404)
                return

            recu = self.headers.get(EN_TETE_SECRET, "")
            if not hmac.compare_digest(recu.encode("utf-8"), secret.encode("utf-8")):
                # Aucune trace du secret ni du corps dans les sorties
                self.send_error(401)
                return

            taille = int(self.headers.get("Content-Length", 0))
            corps = self.rfile.read(taille).decode("utf-8", errors="replace")
            print(corps, flush=True)

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, format, *args):
            # Journal minimal : méthode et chemin seulement, sans en-têtes
            print(f"{self.command} {self.path}", flush=True)

    return HTTPServer((hote, port), GestionnaireCapture)


if __name__ == "__main__":
    secret = os.environ["NOTIFIER_SECRET"]
    chemin = os.environ.get("NOTIFIER_CHEMIN", "/glpi-ticket")
    # Port 80 : GLPI refuse les URL avec port dans sa liste d'URL autorisées
    port = int(os.environ.get("NOTIFIER_PORT", "80"))
    serveur = creer_serveur(secret=secret, chemin=chemin, port=port, hote="0.0.0.0")
    print(f"Capture en écoute sur le port {port}", flush=True)
    serveur.serve_forever()
