# app.py
import logging
from flask import Flask
from flask_cors import CORS
from cliente.routes import cliente_bp
from pedido.routes import pedido_bp
from pagos.routes import pagos_bp
from caja.routes import caja_bp

# Configuración del registro de logs
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

# Registrar los Blueprints
app.register_blueprint(cliente_bp)
app.register_blueprint(pedido_bp)
app.register_blueprint(pagos_bp)
app.register_blueprint(caja_bp)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)