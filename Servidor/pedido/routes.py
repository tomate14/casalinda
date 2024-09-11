import os
import sys

from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS
import pymongo

import logging

# Agrega el directorio del paquete cliente al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'cliente')))

# Importa la función get_all_clientes del archivo cliente.py
from cliente.routes import get_all_clientes


pedido_bp = Blueprint('pedido', __name__)

pedido = MongoClient(os.getenv("MONGO_URI"))
db = pedido['pedidos']
# Configuración de la base de datos
def obtener_conexion_db():
    #pedido = MongoClient('mongodb://mongodb:27017/')
    pedido = MongoClient(os.getenv("MONGO_URI"))
    db = pedido['pedidos']
    return db

# Servicio GET para /pedido
#@pedido_bp.route('/pedido/<int:pageNumber>/<int:pageLimit>', methods=['GET'])
#def obtener_pedidos(pageNumber, pageLimit):

# Servicio POST para /pedido
@pedido_bp.route('/pedido', methods=['POST'])
def crear_pedido():
    nuevo_pedido = request.get_json()
    if not nuevo_pedido:
        return jsonify({"message": "No se proporcionaron datos"}), 400
    
    if "dniCliente" not in nuevo_pedido:
        return jsonify({"message": "Datos incompletos"}), 400

        
    cliente = db['clientes'].find_one({"dni":nuevo_pedido["dniCliente"]})
    
    if not cliente:
        error = "Cliente no encontrado con el numero "+str(nuevo_pedido["dniCliente"])+". Darlo de alta"
        return jsonify({"message": error}), 400

    #db = obtener_conexion_db()
    coleccion_pedidos = db['pedidos']

    numerador = obtener_siguiente_numeracion(db)
    index = numerador["numeroComprobante"]
    nuevo_pedido["numeroComprobante"] = formatear_numero(index)

    resultado = coleccion_pedidos.insert_one(nuevo_pedido)
    
    cliente['_id'] = str(cliente['_id'])

    nuevo_pedido["_id"] = str(resultado.inserted_id)
    nuevo_pedido["nombreCliente"] = cliente["nombre"]
    nuevo_pedido["telefonoCliente"] = cliente["telefono"]

    logging.info('nuevo_pedido: %s', nuevo_pedido)

    actualizar_numeracion(db, numerador, index+1)

    return jsonify(nuevo_pedido), 201

# Servicio DELETE para eliminar envíos por idpedido
@pedido_bp.route('/pedido/<string:idPedido>', methods=['DELETE'])
def eliminar_pedidos_por_idpedido(idPedido):
    #db = obtener_conexion_db()
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
    #db = obtener_conexion_db()
    coleccion_pedidos = db['pedidos']

    # Eliminar el campo _id del diccionario de datos si está presente
    if '_id' in data:
        del data['_id']

    # Actualizar el envío por idPedido
    resultado = coleccion_pedidos.update_one({"_id": object_id}, {"$set": data})
    logging.info('resultado: %s', resultado)
    # Verificar si se encontró y se actualizó el envío
    if resultado.modified_count > 0:
        pedido = coleccion_pedidos.find_one({"_id": object_id})
        pedido['_id'] = str(pedido['_id'])
        return jsonify({"message": f"Se actualizó el envío con idPedido {idPedido}"}), 200
    else:
        return jsonify({"message": f"No se encontró el envío con idPedido {idPedido}"}), 404

@pedido_bp.route('/pedido/pedidos-vencidos/<string:fechaDesde>/<int:tipoPedido>', methods=['GET'])
def get_pedidos_vencidos(fechaDesde, tipoPedido):
    
    #db = obtener_conexion_db()
    logging.info(f"Fecha desde {fechaDesde}")
    pedidos = list(db['pedidos'].find({"fechaPedido": {"$lt": fechaDesde}, "estado":"PENDIENTE", "tipoPedido": tipoPedido }).sort("fechaPedido", pymongo.ASCENDING))
    logging.info("pedidos {pedidos}")
    # Obtener todos los clientes
    response = get_all_clientes()
    clientes = list(db['clientes'].find().sort("dni", pymongo.ASCENDING))
    
    for cliente in clientes:
        cliente['_id'] = str(cliente['_id'])

    for pedido in pedidos:
        pedido['_id'] = str(pedido['_id'])
        cliente = next((c for c in clientes if c['dni'] == pedido['dniCliente']), None)
        if cliente:
            pedido['nombreCliente'] = cliente['nombre']

    return jsonify(pedidos), 200

@pedido_bp.route('/pedido/informe-deuda', methods=['GET'])
def get_deuda_pedido():
    #db = obtener_conexion_db()
    coleccion_pedidos = db['pedidos']
    coleccion_pagos = db['pagos']
    coleccion_cliente = db['clientes']

    # Construir el filtro de consulta basado en los parámetros de consulta proporcionados

    logging.info('Query params: %s', request.args)
    if 'id' in request.args:
       try:
          object_id = ObjectId(request.args['id'])
       except Exception as e:
          logging.warning('ID no válido: %s', request.args['id'])
          return jsonify({'message': 'ID no válido'}), 400
    
    pedido = coleccion_pedidos.find_one({"_id": object_id})
    if not pedido:
        logging.error('El pedido %s no existe.', object_id)
        return jsonify({'message': 'ID no válido'}), 400
    
    pedido['_id'] = str(pedido['_id'])
    logging.info('Pedido a procesar: %s', pedido)

    
    cliente = coleccion_cliente.find_one({"dni": pedido["dniCliente"]})

    if not cliente:
        logging.error('El cliente %s no existe.', pedido["dniCliente"])
        return jsonify({'message': 'No se puede realizar la accion'}), 400
    logging.info('Cliente: %s', cliente)

    deuda_cliente = {        
        "nombreCliente": cliente["nombre"],
        "telefonoCliente": cliente["telefono"],
        "emailCliente": cliente["email"],
        "idPedido": request.args['id'],
        "pedido": pedido        
    }

    pagos = list(coleccion_pagos.find({"idPedido": request.args['id']}).sort("fechaPago", pymongo.DESCENDING))
    logging.info('Pagos encontrados: %s', pagos)
    suma_pagos = 0
    for pago in pagos:
        pago['_id'] = str(pago['_id'])
        suma_pagos += pago['valor']

    deuda_cliente["saldoRestante"] = pedido["total"] - suma_pagos
    
    if pagos:
        deuda_cliente["fechaUltimoPago"] = pagos[0]["fechaPago"]
        deuda_cliente["montoUltimoPago"] = pagos[0]["valor"]

    
    return jsonify(deuda_cliente), 200

@pedido_bp.route('/pedido', methods=['GET'])
def get_pedidos_filtrados():
    #db = obtener_conexion_db()
    coleccion_pedidos = db['pedidos']

    # Construir el filtro de consulta basado en los parámetros de consulta proporcionados
    filtros = {}
    logging.info('Query params: %s', request.args)
    if 'id' in request.args:
       try:
          filtros['_id'] = ObjectId(request.args['id'])
       except Exception as e:
          logging.warning('ID no válido: %s', request.args['id'])
          return jsonify({'message': 'ID no válido'}), 400

    if 'estadoEnvio' in request.args:
        filtros['estadoEnvio'] = int(request.args['estadoEnvio'])
    
    if 'tipoPedido' in request.args:
        filtros['tipoPedido'] = int(request.args['tipoPedido'])
    
    if 'estado' in request.args:
        filtros['estado'] = request.args['estado']
    
    if 'dniCliente' in request.args:
        filtros['dniCliente'] = int(request.args['dniCliente'])

    if 'numeroComprobante' in request.args:
        numero_comprobante = request.args['numeroComprobante']
        filtros['numeroComprobante'] = {'$regex': numero_comprobante, '$options': 'i'}

    if 'fechaDesde' in request.args or 'fechaHasta' in request.args:
        try:
            fecha_filtro = {}
            if 'fechaDesde' in request.args:
                fecha_filtro['$gte'] = request.args['fechaDesde']
            if 'fechaHasta' in request.args:
                fecha_filtro['$lt'] = request.args['fechaHasta']
            filtros['fechaPedido'] = fecha_filtro
        except Exception as e:
            logging.warning('Fecha no válida: %s', e)
            return jsonify({'message': 'Fecha no válida'}), 400

    # Verificar el parámetro de ordenación
    orden_fecha = pymongo.DESCENDING
    if 'ordenFecha' in request.args and request.args['ordenFecha'] == '1':
        orden_fecha = pymongo.ASCENDING

    logging.info('Filtros a aplicar: %s', filtros)
    pedidos = list(coleccion_pedidos.find(filtros).sort("fechaPedido", orden_fecha))
    
    if not pedidos:
        return jsonify({'message': 'No se encontraron pedidos con los filtros proporcionados'}), 404
    
    filtroCliente = {}
    if 'nombreCliente' in request.args:
        regex = {'$regex': request.args['nombreCliente'], '$options': 'i'}  # 'i' para insensible a mayúsculas/minúsculas
        filtroCliente = {'nombre': regex}

    logging.info('filtroCliente: %s', filtroCliente)
    clientes = list(db['clientes'].find(filtroCliente).sort("dni", pymongo.ASCENDING))
    
    for cliente in clientes:
        cliente['_id'] = str(cliente['_id'])
    
    logging.info('Clientes: %s', clientes)

    if 'nombreCliente' in request.args:
        pedidos = [pedido for pedido in pedidos if any(cliente['dni'] == pedido['dniCliente'] for cliente in clientes)]

    for pedido in pedidos:
        pedido['_id'] = str(pedido['_id'])
        logging.info('Pedido  %s', pedido)
        cliente = next((c for c in clientes if c['dni'] == pedido['dniCliente']), None)
        logging.info('Cliente  %s', cliente)
        if cliente:
            pedido['nombreCliente'] = cliente['nombre']
            pedido['telefonoCliente'] = cliente['telefono']
    
    return jsonify(pedidos), 200

@pedido_bp.route('/pedido/sin-numero', methods=['GET'])
def obtener_sin_nroPedido():
    #db = obtener_conexion_db()
    coleccion_pedidos = db['pedidos']
    logging.info('Iniciando Sin numero ...')
    # Query para obtener documentos sin el atributo 'nroPedido'
    documentos = list(coleccion_pedidos.find())
    logging.info('After find ... %s', documentos)
    
    numerador = obtener_siguiente_numeracion(db)
    index = numerador["numeroComprobante"]
    
    for documento in documentos:
        #documento['_id'] = str(documento['_id'])
        documento['numeroComprobante'] = formatear_numero(index)
        # Eliminar el campo _id del diccionario de datos si está presente
        object_id = ObjectId(documento['_id'])
        if '_id' in documento:
            del documento['_id']
        # Actualizar el envío por idPedido
        resultado = db['pedidos'].update_one({"_id": object_id}, {"$set": documento})
       
        # Verificar si se encontró y se actualizó el envío
        if resultado.modified_count > 0:
            logging.info('Pedido actualizado %s', documento)
        else:
            logging.info('No se pudo actualizar %s', documento)
        index += 1

    actualizar_numeracion(db, numerador, index)
    logging.info('documentos  %s', documentos)
    return jsonify(documentos)

def obtener_siguiente_numeracion(db):
    coleccion_comprobantes = db['numeracion']
    contador = coleccion_comprobantes.find_one({"tipoComprobante": 1})
    logging.info('After find contador ... %s', contador)
    return contador

def actualizar_numeracion(db, numerador, index):
    numerador["numeroComprobante"] = index
    db['numeracion'].update_one({"_id": numerador["_id"]}, {"$set": numerador})

def formatear_numero(numero):
    """Formatea un número en el formato XXXX-XXXX con ceros a la izquierda."""
    logging.info('Formateando numeros ...')
    return f"{numero:08}"

# Esto permit
if __name__ == 'pedidoservice':
    app.run(debug=True)