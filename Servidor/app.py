import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
# Configuración de la base de datos
def obtener_conexion_db():
    #client = MongoClient('mongodb://mongodb:27017/')
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client['envios']
    return db

# Servicio GET para /envio
@app.route('/envio', methods=['GET'])
def obtener_envios():
    db = obtener_conexion_db()
    coleccion_envios = db['envios']
    envios = list(coleccion_envios.find())
    for envio in envios:
        envio['_id'] = str(envio['_id'])
    return jsonify(envios), 200

# Servicio POST para /envio
@app.route('/envio', methods=['POST'])
def crear_envio():
    nuevo_envio = request.get_json()
    if not nuevo_envio:
        return jsonify({"error": "No se proporcionaron datos"}), 400
    
    if "dni" not in nuevo_envio:
        return jsonify({"error": "Datos incompletos"}), 400

    db = obtener_conexion_db()
    coleccion_envios = db['envios']
    resultado = coleccion_envios.insert_one(nuevo_envio)
    nuevo_envio["_id"] = str(resultado.inserted_id)
    return jsonify(nuevo_envio), 201

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)