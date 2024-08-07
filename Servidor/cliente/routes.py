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
    db = client['pedidos']
    return db

@cliente_bp.route('/cliente/<int:dni>', methods=['GET'])
def get_cliente(dni):
    db = obtener_conexion_db()
    logging.info('dni a buscar %s', dni)
    cliente = db['clientes'].find_one({"dni": dni})
    
    if cliente is None:
        logging.warning('Cliente con DNI %s no encontrado', dni)
        return jsonify({'message': 'Cliente no encontrado'}), 404
    cliente['_id'] = str(cliente['_id'])  # Convertir ObjectId a string antes de devolver la respuesta
    return jsonify(cliente)

@cliente_bp.route('/cliente', methods=['GET'])
def get_all_clientes():
    db = obtener_conexion_db()

    filtros = {}
    logging.info('Query params: %s', request.args)

    if 'dni' in request.args:
        filtros['dni'] = int(request.args['dni'])
    if 'nombre' in request.args:
        regex = {'$regex': request.args['nombre'], '$options': 'i'}  # 'i' para insensible a mayúsculas/minúsculas
        filtros = {'nombre': regex}
    if 'tipoUsuario' in request.args:
        filtros['tipoUsuario'] = int(request.args['tipoUsuario'])

    clientes = list(db['clientes'].find(filtros))

    # Obtener lista de deudores
    dni_deudores = get_clientes_deudores()
    logging.info('Get deudores: %s', dni_deudores)
    for cliente in clientes:
        cliente['_id'] = str(cliente['_id'])
        cliente['esDeudor'] = cliente['dni'] in dni_deudores
    return jsonify(clientes), 200

@cliente_bp.route('/cliente', methods=['POST'])
def create_cliente():
    nuevo_cliente = request.get_json()
    if not nuevo_cliente:
        return jsonify({"message": "No se proporcionaron datos"}), 400
    
    if "dni" not in nuevo_cliente:
        return jsonify({"message": "Datos incompletos"}), 400

    db = obtener_conexion_db()
    coleccion_clientes = db['clientes']
    cliente = coleccion_clientes.find_one({"dni": nuevo_cliente['dni']})

    if cliente:
        logging.info("Cliente ya existe")
        cliente['_id'] = str(cliente['_id'])
        return jsonify(cliente), 404

    resultado = coleccion_clientes.insert_one(nuevo_cliente)
    nuevo_cliente["_id"] = str(resultado.inserted_id)

    # Obtener lista de deudores
    dni_deudores = get_clientes_deudores()

    nuevo_cliente['esDeudor'] = nuevo_cliente['dni'] in dni_deudores

    return jsonify(nuevo_cliente), 201

@cliente_bp.route('/cliente/<string:idCliente>', methods=['PUT'])
def update_cliente(idCliente):
    cliente_actualizado = request.get_json()
    if not cliente_actualizado:
        return jsonify({"message": "No se proporcionaron datos"}), 400
    
    db = obtener_conexion_db()
    coleccion_clientes = db['clientes']
    
    cliente_existente = coleccion_clientes.find_one({"_id": ObjectId(idCliente)})
    if cliente_existente is None:
        return jsonify({'message': 'Cliente no encontrado'}), 404

    # Actualizar cliente existente con los nuevos datos
    coleccion_clientes.update_one({"_id": ObjectId(idCliente)}, {"$set": cliente_actualizado})

    # Obtener el cliente actualizado
    cliente_actualizado = coleccion_clientes.find_one({"_id": ObjectId(idCliente)})
    cliente_actualizado['_id'] = str(cliente_actualizado['_id'])  # Convertir ObjectId a string antes de devolver la respuesta

    # Obtener lista de deudores
    dni_deudores = get_clientes_deudores()

    cliente_actualizado['esDeudor'] = cliente_actualizado['dni'] in dni_deudores

    return jsonify(cliente_actualizado), 200
    
def get_clientes_deudores():
    db = obtener_conexion_db()
    pedidos = db['pedidos']
    
    # Buscar pedidos pendientes
    pedidos_pendientes = pedidos.find({'estado': 'PENDIENTE'})
    # Obtener los DNI de los clientes deudores
    dni_deudores = [pedido['dniCliente'] for pedido in pedidos_pendientes]
    
    return dni_deudores

if __name__ == 'clienteService':
    app.run(debug=True)
