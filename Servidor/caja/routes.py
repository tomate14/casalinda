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

if __name__ == '__main__':
    app.run(debug=True)
