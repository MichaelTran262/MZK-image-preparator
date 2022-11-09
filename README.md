# Image preparator
Webová aplikace pro Kroměříž

## Jak nainstalovat a spustit na linuxu
Python 3 a [libvips](https://www.libvips.org/install.html) musí být k dispozici.
Je nutné definovat kořenovou složku s obrázky v proměnné BASE_DIR.

```yaml
python3 -m venv <nazev_venv> # např. python3 -m venv venv, vytvoří se složka venv
source <nazev_venv>/bin/activate # např. source venv/bin/activate, aktivace nového lokálního Pythonu místo globálního
pip install flask pyvips # instalace flask a pyvips
python3 app.py
```
Bravo! Aplikace běží na [localhost:5000](http://localhost:5000).

Pro deaktivaci lokálního Pythonu:
```yaml
source <nazev_venv>/bin/deactivate
```
