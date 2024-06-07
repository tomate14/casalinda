# casalinda Subir cambios

## Para crear un tag 
docker tag casalinda-flask maxiroselli/casalinda:casalinda-flask
docker tag casalinda-angular maxiroselli/casalinda:casalinda-angular
docker tag mongo maxiroselli/casalinda:mongo
docker tag casalinda-backup maxiroselli/casalinda:casalinda-backup

## Para pushearlo
docker push maxiroselli/casalinda:casalinda-flask


# Bajar cambios

## Darle acceso al usuario para mi repo
## Hacer un pull de las imagenes
## Sobre la carpeta con el docker compose:
docker-compose up --build 




# Nueva version
## Buildear local con el docker-compose-local.yaml
## Darle un alias (referencia a Para crear un tag)
## Pushear ese alias (referencia a Para pushearlo)