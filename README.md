# Image preparator
Webová aplikace pro Kroměříž

## Jak spustit
stačí rozjet docker-compose


## Jak připravit pro vývoj
- Je potřeba mít připojený MZK disk, budeme zatím počítat s obecným /mnt/MZK. Je jedno jestli je připojený přes NFS nebo CIFS.
- Je potřeba mít definované tyto proměnné
  | Proměnná  | Hodnota    |
  |-----------|------------|
  | FLASK_APP | preparator |
  | FLASK_DEBUG | 1 | 
  | SRC_FOLDER | cesta, kde leží Kroměřížská data|
  | DST_FOLDER | /mnt/MZK (nebo kde se nachází MZK mount) |
      
1. Vytvořit python venv prostředí
2. Nainstalovat moduly z requirements.txt
3. Rozjet Postgres a Redis (stačí jako kontejner image)
4. Rozjet Celery `celery -A preparator:celery_app worker --loglevel=debug`
6. Rozjet Flask `flask run
