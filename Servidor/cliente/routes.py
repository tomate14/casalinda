import os
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS

import logging

cliente_bp = Blueprint('cliente', __name__)

def obtener_conexion_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    logging.info('Conectando a %s', os.getenv("MONGO_URI"))
    db = client['envios']
    return db

@cliente_bp.route('/cliente/<int:dni>', methods=['GET'])
def get_cliente(dni):
    db = obtener_conexion_db()
    logging.info('dni a buscar %s', dni)
    cliente = db['clientes'].find_one({"dni": dni})
    
    if cliente is None:
        logging.warning('Cliente con DNI %s no encontrado', dni)
        return jsonify({'error': 'Cliente no encontrado'}), 404
    cliente['_id'] = str(cliente['_id'])  # Convertir ObjectId a string antes de devolver la respuesta
    return jsonify(cliente)

@cliente_bp.route('/cliente', methods=['GET'])
def get_all_clientes():
    db = obtener_conexion_db()
    clientes = list(db['clientes'].find())
    for cliente in clientes:
        cliente['_id'] = str(cliente['_id'])
    return jsonify(clientes), 200

@cliente_bp.route('/cliente', methods=['POST'])
def create_cliente():
    nuevo_cliente = request.get_json()
    if not nuevo_cliente:
        return jsonify({"error": "No se proporcionaron datos"}), 400
    
    if "dni" not in nuevo_cliente:
        return jsonify({"error": "Datos incompletos"}), 400

    db = obtener_conexion_db()
    coleccion_clientes = db['clientes']
    resultado = coleccion_clientes.insert_one(nuevo_cliente)
    nuevo_cliente["_id"] = str(resultado.inserted_id)
    return jsonify(nuevo_cliente), 201

@cliente_bp.route('/cliente/<string:idCliente>', methods=['PUT'])
def update_cliente(idCliente):
    cliente_actualizado = request.get_json()
    if not cliente_actualizado:
        return jsonify({"error": "No se proporcionaron datos"}), 400
    
    db = obtener_conexion_db()
    coleccion_clientes = db['clientes']
    
    cliente_existente = coleccion_clientes.find_one({"_id": ObjectId(idCliente)})
    if cliente_existente is None:
        return jsonify({'error': 'Cliente no encontrado'}), 404

    # Actualizar cliente existente con los nuevos datos
    coleccion_clientes.update_one({"_id": ObjectId(idCliente)}, {"$set": cliente_actualizado})

    # Obtener el cliente actualizado
    cliente_actualizado = coleccion_clientes.find_one({"_id": ObjectId(idCliente)})
    cliente_actualizado['_id'] = str(cliente_actualizado['_id'])  # Convertir ObjectId a string antes de devolver la respuesta
    
    return jsonify(cliente_actualizado), 200
    
if __name__ == 'clienteService':
    app.run(debug=True)
