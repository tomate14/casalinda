import os
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS

import logging

pagos_bp = Blueprint('pagos', __name__)

def obtener_conexion_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    logging.info('Conectando a %s', os.getenv("MONGO_URI"))
    db = client['envios']
    return db

@pagos_bp.route('/pago/<string:idEnvio>', methods=['GET'])
def get_pagos(idEnvio):
    db = obtener_conexion_db()
    pagos = list(db['pagos'].find({"idEnvio": idEnvio}))
    
    for pago in pagos:
        pago['_id'] = str(pago['_id'])
    return jsonify(pagos), 200
@pagos_bp.route('/pago/<string:idPago>', methods=['DELETE'])
def delete_pagos(idPago):
    db = obtener_conexion_db()
    try:
        # Convertir idPago a ObjectId
        object_id = ObjectId(idPago)
    except:
        return jsonify({"message": f"ID de pago no válido: {idPago}"}), 400

    result = db['pagos'].delete_one({"_id": object_id})
    if result.deleted_count > 0:
        return jsonify({"message": f"Se elimo el pago con id {idPago}"}), 200
    else:
        return jsonify({"message": f"No se elimino el pago con id {idPago}"}), 404

##@pagos_bp.route('/pago/<string:idEnvio>', methods=['DELETE'])
def delete_pagos_by_idenvio(idEnvio):
    db = obtener_conexion_db()
    result = db['pagos'].delete_many({"idEnvio": idEnvio})
    if result.deleted_count > 0:
        return jsonify({"message": f"Se eliminaron {result.deleted_count} pagos con idEnvio {idEnvio}"}), 200
    else:
        return jsonify({"message": f"No se encontraron pagos con idEnvio {idEnvio}"}), 404

@pagos_bp.route('/pago', methods=['POST'])
def create_cliente():
    nuevo_pago = request.get_json()
    if not nuevo_pago:
        return jsonify({"error": "No se proporcionaron datos"}), 400
    
    if "idEnvio" not in nuevo_pago :
        return jsonify({"error": "Datos incompletos"}), 400

    db = obtener_conexion_db()
    coleccion_pagos = db['pagos']
    resultado = coleccion_pagos.insert_one(nuevo_pago)
    nuevo_pago["_id"] = str(resultado.inserted_id)
    return jsonify(nuevo_pago), 201

if __name__ == 'pagosService':
    app.run(debug=True)
