# Usar una imagen base de Python
FROM python:3.9

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos requeridos a la imagen del contenedor
#COPY . /app
COPY requirements.txt .

#ENV FLASK_RUN_HOST=0.0.0.0

# Instalar las dependencias
RUN pip install -r requirements.txt

COPY . .
# Exponer el puerto en el que correrá la aplicación Flask
# EXPOSE 5000

# Definir el comando por defecto para correr la aplicación
CMD ["python", "app.py"]
