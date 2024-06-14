import os
import re
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS
from datetime import datetime, timedelta

import pymongo
import logging
# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pagos_bp = Blueprint('pagos', __name__)

def obtener_conexion_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    logging.info('Conectando a %s', os.getenv("MONGO_URI"))
    db = client['pedidos']
    return db

@pagos_bp.route('/pago/<string:idPedido>', methods=['GET'])
def get_pagos(idPedido):
    db = obtener_conexion_db()
    pagos = list(db['pagos'].find({"idPedido": idPedido}).sort("fechaPago", pymongo.DESCENDING))
    
    for pago in pagos:
        pago['_id'] = str(pago['_id'])
    
    respuesta = {
        "pagos": pagos
    }

    try:
        object_id = ObjectId(idPedido)
    except Exception as e:
        logging.warning('ID no válido: %s', idPedido)
        return jsonify({'message': 'ID no válido'}), 400
    
    pedido = db['pedidos'].find_one({"_id": object_id})
    if not pedido:
        logging.error('El pedido %s no existe.', object_id)
        return jsonify({'message': 'ID no válido'}), 400
    
    pedido['_id'] = str(pedido['_id'])
    logging.info('Pedido a procesar: %s', pedido)

    cliente = db['clientes'].find_one({"dni": pedido["dniCliente"]})

    if not cliente:
        logging.error('El cliente %s no existe.', pedido["dniCliente"])
        return jsonify({'message': 'No se puede realizar la accion'}), 400

    logging.info('Cliente: %s', cliente)

    respuesta["nombreCliente"] = cliente["nombre"]
    respuesta["telefonoCliente"] = cliente["telefono"]
    respuesta["emailCliente"] = cliente["email"]

    return jsonify(respuesta), 200

# Servicios de caja
@pagos_bp.route('/pago/caja/<string:fechaInicio>/<string:fechaFin>', methods=['GET'])
def get_pagos_por_fecha(fechaInicio, fechaFin):
    try:
       
        logger.info('Fecha inicio: %s', fechaInicio)
        logger.info('Fecha fin: %s', fechaFin)
    except ValueError:
        return jsonify({"message": "Fecha no válida"}), 400

    db = obtener_conexion_db()
    pagos = list(db['pagos'].find({
        "fechaPago": {
            "$gte": fechaInicio,
            "$lt": fechaFin
        }
    }).sort("fechaPago", pymongo.DESCENDING))

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

##@pagos_bp.route('/pago/<string:idpedido>', methods=['DELETE'])
def delete_pagos_by_idpedido(idpedido):
    db = obtener_conexion_db()
    result = db['pagos'].delete_many({"idpedido": idpedido})
    if result.deleted_count > 0:
        return jsonify({"message": f"Se eliminaron {result.deleted_count} pagos con idpedido {idpedido}"}), 200
    else:
        return jsonify({"message": f"No se encontraron pagos con idpedido {idpedido}"}), 404

@pagos_bp.route('/pago', methods=['POST'])
def create_pago():
    nuevo_pago = request.get_json()
    if not nuevo_pago:
        return jsonify({"message": "No se proporcionaron datos"}), 400
    
    if "idPedido" not in nuevo_pago :
        return jsonify({"message": "Datos incompletos"}), 400

    db = obtener_conexion_db()

    nueva_fecha = reemplazar_t(nuevo_pago["fechaPago"])

    # Consulta de agregación para obtener la última fecha de caja cerrada
    pipeline = [
        {"$group": {"_id": "$fecha"}},
        {"$sort": {"_id": pymongo.DESCENDING}},
        {"$limit": 1}
    ]
    
    ultima_fecha = db['caja'].aggregate(pipeline)
    ultima_fecha = next(ultima_fecha, None)
    if ultima_fecha:
        ultima_fecha = ultima_fecha['_id']

    logging.info('Ultima fecha: %s', ultima_fecha)
    logging.info('Fecha Pago: %s', nueva_fecha)

    if ultima_fecha == nueva_fecha :
        return jsonify({"message": f"No se pueden agregar datos porque la caja del dia ya fue cerrada"}), 404
    else:
        coleccion_pagos = db['pagos']
        resultado = coleccion_pagos.insert_one(nuevo_pago)
        nuevo_pago["_id"] = str(resultado.inserted_id)
        return jsonify(nuevo_pago), 201
        
@pagos_bp.route('/pago/<string:idPago>', methods=['PUT'])
def update_pago(idPago):
    pago_actualizado = request.get_json()

    if not pago_actualizado:
        return jsonify({"message": "No se proporcionaron datos"}), 400

    db = obtener_conexion_db()
    coleccion_pagos = db['pagos']
    
    pago_existente = coleccion_pagos.find_one({"_id": ObjectId(idPago)})
    if pago_existente is None:
        return jsonify({'message': 'pago no encontrado'}), 404

    # Actualizar pago existente con los nuevos datos
    coleccion_pagos.update_one({"_id": ObjectId(idPago)}, {"$set": pago_actualizado})

    # Obtener el pago actualizado
    pago_actualizado = coleccion_pagos.find_one({"_id": ObjectId(idPago)})
    pago_actualizado['_id'] = str(pago_actualizado['_id'])  # Convertir ObjectId a string antes de devolver la respuesta
    
    return jsonify(pago_actualizado), 200


def reemplazar_t(fecha):
    # Utilizar una expresión regular para buscar la parte derecha de la T
    nueva_fecha = re.sub(r'T\d{2}:\d{2}:\d{2}.\d{3}-\d{2}:\d{2}$', 'T00:00:00.000-03:00', fecha)
    logging.info('Nueva fecha a checkear %s', nueva_fecha)
    return nueva_fecha

if __name__ == 'pagosService':
    app.run(debug=True)
