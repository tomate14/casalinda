import os
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS
import pymongo
import logging

caja_bp = Blueprint('caja', __name__)

def obtener_conexion_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    logging.info('Conectando a %s', os.getenv("MONGO_URI"))
    db = client['pedidos']
    return db

@caja_bp.route('/caja', methods=['POST'])
def create_caja():
    db = obtener_conexion_db()
    data = request.get_json()
    if not data:
        return jsonify({"error": "No se proporcionaron datos"}), 400
    
    required_fields = ["fecha", "contado", "tarjeta", "cuentaDni"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Datos incompletos"}), 400

    db['caja'].insert_one(data)
    return jsonify({"message": "Registro creado exitosamente"}), 201

@caja_bp.route('/caja/<string:fechaInicio>/<string:fechaFin>', methods=['GET'])
def get_caja_by_date(fechaInicio,fechaFin):
    try:
        logging.info('Fecha inicio: %s', fechaInicio)
        logging.info('Fecha fin: %s', fechaFin)
    except ValueError:
        return jsonify({"error": "Fecha no válida"}), 400
        
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
        return jsonify({"error": "Fecha no válida"}), 400

    db = obtener_conexion_db()

    # Verificar si ya existe un cierre de caja con la misma fecha
    if db['caja'].find_one({"fecha": fecha_fin}):
        return jsonify({"error": "Ya existe un cierre de caja para la fecha proporcionada"}), 400

    try:
        pagos = list(db['pagos'].find({
            "fechaPago": {
                "$gte": fecha_inicio,
                "$lt": fecha_fin
            }
        }))
    except Exception as e:
        logger.error("Error al consultar la base de datos: %s", str(e))
        return jsonify({"error": "Error al consultar la base de datos"}), 500

    contado = 0
    tarjeta = 0
    cuentaDni = 0
    ingresos = 0
    gastos = 0

    for pago in pagos:
        valor = pago['valor']
        forma_pago = pago['formaPago']
        
        if forma_pago == 1:
            contado += valor
        elif forma_pago == 2:
            tarjeta += valor
        elif forma_pago == 3:
            cuentaDni += valor
        
        if valor < 0:
            gastos += -valor
        else:
            ingresos += valor

    cierre_caja_doc = {
        "fecha": fecha_fin,
        "contado": contado,
        "tarjeta": tarjeta,
        "cuentaDni": cuentaDni,
        "gastos": gastos,
        "ingresos": ingresos - gastos
    }

    try:
        # Insertar el documento en la colección 'caja'
        db['caja'].insert_one(cierre_caja_doc)
        cierre_caja_doc['_id'] = str(cierre_caja_doc['_id'])
    except Exception as e:
        logger.error("Error al insertar el documento en la colección 'caja': %s", str(e))
        return jsonify({"error": "Error al guardar el cierre de caja"}), 500


    return jsonify({"message": f"Cierre de caja exitoso para el dia {fechaInicio}"}), 200
if __name__ == '__main__':
    app.run(debug=True)
