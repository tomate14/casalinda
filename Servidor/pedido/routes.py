import os
import sys

from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS
import pymongo

import logging
# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agrega el directorio del paquete cliente al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'cliente')))

# Importa la función get_all_clientes del archivo cliente.py
from cliente.routes import get_all_clientes


pedido_bp = Blueprint('pedido', __name__)

# Configuración de la base de datos
def obtener_conexion_db():
    #pedido = MongoClient('mongodb://mongodb:27017/')
    pedido = MongoClient(os.getenv("MONGO_URI"))
    db = pedido['pedidos']
    return db

# Servicio GET para /pedido
#@pedido_bp.route('/pedido/<int:pageNumber>/<int:pageLimit>', methods=['GET'])
#def obtener_pedidos(pageNumber, pageLimit):
@pedido_bp.route('/pedido', methods=['GET'])
def obtener_pedidos():
    db = obtener_conexion_db()
    coleccion_pedidos = db['pedidos']
    coleccion_clientes = db['clientes']

    pedidos = list(coleccion_pedidos.find().sort("fechaPedido", pymongo.DESCENDING))
    clientes = list(coleccion_clientes.find().sort("dni", pymongo.ASCENDING))
    for cliente in clientes:
        cliente['_id'] = str(cliente['_id'])
    for pedido in pedidos:
        pedido['_id'] = str(pedido['_id'])
        cliente = next((c for c in clientes if c['dni'] == pedido['dniCliente']), None)
        if cliente:
            pedido['nombreCliente'] = cliente['nombre']
    
    return jsonify(pedidos), 200

@pedido_bp.route('/pedido/<int:dniCliente>', methods=['GET'])
def get_pedidos_por_dniCliente(dniCliente):
    db = obtener_conexion_db()
    pedidos = list(db['pedidos'].find({"dniCliente": dniCliente}).sort("fechaPedido", pymongo.DESCENDING))
    
    for pedido in pedidos:
        pedido['_id'] = str(pedido['_id'])
    return jsonify(pedidos), 200

@pedido_bp.route('/pedido/tipo-pedido/<int:tipoPedido>', methods=['GET'])
def get_pedidos_por_tipo_pedido(tipoPedido):
    db = obtener_conexion_db()
    pedidos = list(db['pedidos'].find({"tipoPedido": tipoPedido}).sort("fechaPedido", pymongo.DESCENDING))
    clientes = list(db['clientes'].find().sort("dni", pymongo.ASCENDING))
    
    for cliente in clientes:
        cliente['_id'] = str(cliente['_id'])

    for pedido in pedidos:
        pedido['_id'] = str(pedido['_id'])
        logging.info('Pedido  %s', pedido)
        cliente = next((c for c in clientes if c['dni'] == pedido['dniCliente']), None)
        logging.info('Cliente  %s', cliente)
        if cliente:
            pedido['nombreCliente'] = cliente['nombre']

    return jsonify(pedidos), 200

# Servicio POST para /pedido
@pedido_bp.route('/pedido', methods=['POST'])
def crear_pedido():
    nuevo_pedido = request.get_json()
    if not nuevo_pedido:
        return jsonify({"error": "No se proporcionaron datos"}), 400
    
    if "dniCliente" not in nuevo_pedido:
        return jsonify({"error": "Datos incompletos"}), 400

    db = obtener_conexion_db()
    coleccion_pedidos = db['pedidos']
    resultado = coleccion_pedidos.insert_one(nuevo_pedido)
    nuevo_pedido["_id"] = str(resultado.inserted_id)
    return jsonify(nuevo_pedido), 201

# Servicio DELETE para eliminar envíos por idpedido
@pedido_bp.route('/pedido/<string:idPedido>', methods=['DELETE'])
def eliminar_pedidos_por_idpedido(idPedido):
    db = obtener_conexion_db()
    coleccion_pedidos = db['pedidos']
    resultado = coleccion_pedidos.delete_many({"idPedido": idPedido, "estado":"COMPLETO"})
    if resultado.deleted_count > 0:
        return jsonify({"message": f"Se eliminaron {resultado.deleted_count} envíos con idPedido {idPedido}"}), 200
    else:
        return jsonify({"message": f"No se encontraron envíos con idPedido {idPedido}"}), 404

# Servicio PUT para actualizar el envío por idPedido
@pedido_bp.route('/pedido/<string:idPedido>', methods=['PUT'])
def actualizar_pedido(idPedido):
    # Obtener los datos del cuerpo de la solicitud
    data = request.get_json()

    try:
        # Convertir idPago a ObjectId
        object_id = ObjectId(idPedido)
    except:
        return jsonify({"message": f"ID de pago no válido: {idPedido}"}), 400

    # Conectar a la base de datos
    db = obtener_conexion_db()
    coleccion_pedidos = db['pedidos']

    # Eliminar el campo _id del diccionario de datos si está presente
    if '_id' in data:
        del data['_id']

    # Actualizar el envío por idPedido
    resultado = coleccion_pedidos.update_one({"_id": object_id}, {"$set": data})

    # Verificar si se encontró y se actualizó el envío
    if resultado.modified_count > 0:
        return jsonify({"message": f"Se actualizó el envío con idPedido {idPedido}"}), 200
    else:
        return jsonify({"message": f"No se encontró el envío con idPedido {idPedido}"}), 404

# Esto permit
if __name__ == 'pedidoservice':
    app.run(debug=True)