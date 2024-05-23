#!/bin/sh

# Añade la tarea cron
echo '5 20 * * * mongodump --host mongodb --out /backup/$(date +\%Y-\%m-\%d)' > /etc/cron.d/mongobackup

# Da los permisos adecuados
chmod 0644 /etc/cron.d/mongobackup

# Aplica la configuración de cron
crontab /etc/cron.d/mongobackup

# Corre el daemon de cron en primer plano
cron -f