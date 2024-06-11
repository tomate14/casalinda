import os
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS
from datetime import datetime
import pymongo
import logging


caja_bp = Blueprint('caja', __name__)

def obtener_conexion_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    logging.info('Conectando a %s', os.getenv("MONGO_URI"))
    db = client['pedidos']
    return db

@caja_bp.route('/caja/<string:fechaInicio>/<string:fechaFin>', methods=['GET'])
def get_caja_by_date(fechaInicio,fechaFin):
    try:
        logging.info('Fecha inicio: %s', fechaInicio)
        logging.info('Fecha fin: %s', fechaFin)
    except ValueError:
        return jsonify({"message": "Fecha no válida"}), 400
        
    db = obtener_conexion_db()
    cajas = list(db['caja'].find({
        "fecha": {
            "$gte": fechaInicio,
            "$lt": fechaFin
        }
    }).sort("fecha", pymongo.ASCENDING))

    for caja in cajas:
        caja['_id'] = str(caja['_id'])
    
    return jsonify(cajas), 200

@caja_bp.route('/caja-cierre/<string:fechaInicio>/<string:fechaFin>', methods=['GET'])
def cierre_caja(fechaInicio, fechaFin):
    try:
        # Parsear las fechas
        fecha_inicio = fechaInicio
        fecha_fin = fechaFin
    except ValueError:
        return jsonify({"message": "Fecha no válida"}), 400

    db = obtener_conexion_db()

    # Verificar si ya existe un cierre de caja con la misma fecha
    if db['caja'].find_one({"fecha": fechaInicio}):
        logging.info("La caja del dia %s ya fue cerrada", fechaInicio)
        return jsonify({"message": "Ya existe un cierre de caja para la fecha proporcionada " + fechaInicio}), 200

    try:
        pagos = list(db['pagos'].find({
            "fechaPago": {
                "$gte": fecha_inicio,
                "$lt": fecha_fin
            }
        }))
    except Exception as e:
        logging.error("Error al consultar la base de datos: %s", str(e))
        return jsonify({"message": "Error al consultar la base de datos"}), 500

    contado = 0
    tarjeta = 0
    transferencia = 0
    cuentaDni = 0
    ganancia = 0
    gastos = 0
    diferencia_caja = 0
    if not pagos:
        logging.info("Dia sin pagos para procesar: %s", fechaInicio)
        return jsonify({"message": "No hay entradas para cerrar la caja del dia "+fechaInicio}), 200
        
    for pago in pagos:
        valor = pago['valor']
        forma_pago = pago['formaPago']
        idPedido = pago['idPedido']
        if idPedido != '-2' and idPedido != '-3':
            if forma_pago == 1:
                contado += valor
            elif forma_pago == 2:
                tarjeta += valor
            elif forma_pago == 3:
                cuentaDni += valor
            elif forma_pago == 4:
                transferencia += valor
            
            if valor < 0:
                gastos += -valor
            else:
                ganancia += valor
        else:
            diferencia_caja += valor
            logging.info("No se contempla el movimiento de caja: %s", pago)

    cierre_caja_doc = {
        "fecha": fecha_inicio,
        "contado": contado,
        "tarjeta": tarjeta,
        "cuentaDni": cuentaDni,
        "transferencia": transferencia,
        "gastos": gastos,
        "ganancia": ganancia - gastos
    }

    try:
        # Insertar el documento en la colección 'caja'
        db['caja'].insert_one(cierre_caja_doc)
        cierre_caja_doc['_id'] = str(cierre_caja_doc['_id'])
    except Exception as e:
        logging.error("Error al insertar el documento en la colección 'caja': %s", str(e))
        return jsonify({"message": "Error al guardar el cierre de caja"}), 500

    cierre_caja_doc["diferencia_caja"] = diferencia_caja
    return jsonify(cierre_caja_doc), 200

@caja_bp.route('/caja/ultima-cerrada', methods=['GET'])
def get_caja_no_cerrada():
        
    db = obtener_conexion_db()

    # Consulta de agregación para obtener las últimas 10 fechas ordenadas de manera descendente
    pipeline = [
        {"$group": {"_id": "$fecha"}},
        {"$sort": {"_id": pymongo.DESCENDING}},
        {"$limit": 1}
    ]
    
    ultima_fecha = list(db['caja'].aggregate(pipeline))
    
    # Extraer solo las fechas del resultado
    ultima_fecha = [fecha["_id"] for fecha in ultima_fecha]

    return jsonify(ultima_fecha), 200

if __name__ == '__main__':
    app.run(debug=True)
