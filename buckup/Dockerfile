# Dockerfile.backup
FROM mongo:latest

# Instala cron
RUN apt-get update && apt-get install -y cron

# Añade el script de inicio
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]