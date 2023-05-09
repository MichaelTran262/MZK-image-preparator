# Image preparator
Webová aplikace pro Kroměříž

## Jak spustit
stačí rozjet docker-compose


## Jak připravit pro vývoj
1. Vytvořit python venv prostředí
2. Nainstalovat moduly z requirements.txt
3. Rozjet Postgres a Redis (stačí jako kontejner image)
4. Rozjet Celery
5. Rozjet Flask `celery -A preparator:celery_app worker --loglevel=debug`
