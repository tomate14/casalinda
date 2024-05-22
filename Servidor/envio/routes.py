import os
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS
import pymongo

envio_bp = Blueprint('envio', __name__)

# Configuración de la base de datos
def obtener_conexion_db():
    #envio = MongoClient('mongodb://mongodb:27017/')
    envio = MongoClient(os.getenv("MONGO_URI"))
    db = envio['envios']
    return db

# Servicio GET para /envio
@envio_bp.route('/envio', methods=['GET'])
def obtener_envios():
    db = obtener_conexion_db()
    coleccion_envios = db['envios']
    coleccion_clientes = db['clientes']

    envios = list(coleccion_envios.find().sort("fechaPedido", pymongo.DESCENDING))
    clientes = list(coleccion_clientes.find().sort("dni", pymongo.ASCENDING))
    for cliente in clientes:
        cliente['_id'] = str(cliente['_id'])
    for envio in envios:
        envio['_id'] = str(envio['_id'])
        cliente = next((c for c in clientes if c['dni'] == envio['dniCliente']), None)
        if cliente:
            envio['nombreCliente'] = cliente['nombre']
    
    return jsonify(envios), 200

@envio_bp.route('/envio/<int:dniCliente>', methods=['GET'])
def get_envios_por_dniCliente(dniCliente):
    db = obtener_conexion_db()
    envios = list(db['envios'].find({"dniCliente": dniCliente}).sort("fechaPedido", pymongo.DESCENDING))
    
    for envio in envios:
        envio['_id'] = str(envio['_id'])
    return jsonify(envios), 200

# Servicio POST para /envio
@envio_bp.route('/envio', methods=['POST'])
def crear_envio():
    nuevo_envio = request.get_json()
    if not nuevo_envio:
        return jsonify({"error": "No se proporcionaron datos"}), 400
    
    if "dniCliente" not in nuevo_envio:
        return jsonify({"error": "Datos incompletos"}), 400

    db = obtener_conexion_db()
    coleccion_envios = db['envios']
    resultado = coleccion_envios.insert_one(nuevo_envio)
    nuevo_envio["_id"] = str(resultado.inserted_id)
    return jsonify(nuevo_envio), 201

# Servicio DELETE para eliminar envíos por idEnvio
@envio_bp.route('/envio/<string:idEnvio>', methods=['DELETE'])
def eliminar_envios_por_idEnvio(idEnvio):
    db = obtener_conexion_db()
    coleccion_envios = db['envios']
    resultado = coleccion_envios.delete_many({"idEnvio": idEnvio, "estado":"COMPLETO"})
    if resultado.deleted_count > 0:
        return jsonify({"message": f"Se eliminaron {resultado.deleted_count} envíos con idEnvio {idEnvio}"}), 200
    else:
        return jsonify({"message": f"No se encontraron envíos con idEnvio {idEnvio}"}), 404

# Servicio PUT para actualizar el envío por idEnvio
@envio_bp.route('/envio/<string:idPedido>', methods=['PUT'])
def actualizar_envio(idPedido):
    # Obtener los datos del cuerpo de la solicitud
    data = request.get_json()

    try:
        # Convertir idPago a ObjectId
        object_id = ObjectId(idPedido)
    except:
        return jsonify({"message": f"ID de pago no válido: {idPedido}"}), 400

    # Conectar a la base de datos
    db = obtener_conexion_db()
    coleccion_envios = db['envios']

    # Eliminar el campo _id del diccionario de datos si está presente
    if '_id' in data:
        del data['_id']

    # Actualizar el envío por idPedido
    resultado = coleccion_envios.update_one({"_id": object_id}, {"$set": data})

    # Verificar si se encontró y se actualizó el envío
    if resultado.modified_count > 0:
        return jsonify({"message": f"Se actualizó el envío con idPedido {idPedido}"}), 200
    else:
        return jsonify({"message": f"No se encontró el envío con idPedido {idPedido}"}), 404

# Esto permit
if __name__ == 'envioService':
    app.run(debug=True)