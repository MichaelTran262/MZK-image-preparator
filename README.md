# Image preparator
Webová aplikace pro Kroměříž

## Jak nainstalovat a spustit v Dockeru
Rozjet `build.sh`<br>
Rozjet `docker-compose`

```yaml
version: '3'
services:
  app:
    image: krom-app
    container_name: krom-app
    ports:
      - "8080:80"
    volumes:
      - ./:/app
      - ./testFolder:/mnt/testFolder
    command: "python3 /app/app.py"
    depends_on:
      - db
    restart: always
  db:
    image: postgres:15
    container_name: db
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=baseddata
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
```
