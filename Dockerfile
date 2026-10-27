# syntax=docker/dockerfile:1

# Image Python officielle, version alignée sur .python-version
FROM python:3.14-slim

# Binaires uv (Astral), copiés depuis leur image officielle
COPY --from=ghcr.io/astral-sh/uv:debian-slim /usr/local/bin/uv /usr/local/bin/uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Couche 1 : fichiers de dépendances seuls.
# Cette couche n'est reconstruite que si pyproject.toml, uv.lock ou .python-version changent.
COPY .python-version pyproject.toml uv.lock ./

# Couche 2 : installation des dépendances (sans le projet lui-même, sans les dépendances de dev comme pytest)
RUN uv sync --locked --no-dev --no-install-project

# Couche 3 : code applicatif, copié en dernier pour ne pas invalider le cache des dépendances
COPY src/ ./src/

# Utilisateur non privilégié
RUN useradd --system --no-create-home notifier \
    && chown -R notifier:notifier /app
USER notifier

# Port interne uniquement : rien n'est publié vers l'hôte dans le compose
EXPOSE 80

CMD ["python", "-m", "src.server"]
