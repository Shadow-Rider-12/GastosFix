import os
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, g, flash
from datetime import datetime, date

app = Flask(__name__)

# ── 1. CONFIGURACIÓN SEGURA DE BASE DE DATOS (SEMANA 13) ──────
DB_CONFIG = {
    'host':     os.environ.get('DB_HOST', '127.0.0.1'),
    'port':     int(os.environ.get('DB_PORT', 3306)),
    'user':     os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),  # Vacío por defecto en XAMPP
    'database': os.environ.get('DB_NAME', 'gastos_db'),
    'charset':  'utf8mb4',
    'converter_class': mysql.connector.conversion.MySQLConverter
}

# REQUERIDO: La clave secreta es OBLIGATORIA para usar flash (Mensajes cifrados en sesión)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cft_maule_key_secreta_98765')


# ── 2. HELPERS DE CONEXIÓN REUTILIZABLES (SEMANA 12) ──────────
def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(**DB_CONFIG)
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query(sql, params=(), one=False):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(sql, params)
    result = cursor.fetchone() if one else cursor.fetchall()
    cursor.close()
    return result

def execute(sql, params=()):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(sql, params)
    db.commit()
    lastrowid = cursor.lastrowid
    cursor.close()
    return lastrowid


# ── 3. LÓGICA DE VALIDACIÓN ROBUSTA (HITO 3) ──────────────────
def validar_gasto(data):
    try:
        monto = float(data.get('monto', 0))
        if monto <= 0:
            return "El monto del gasto debe ser un número mayor a cero."
    except (ValueError, TypeError):
        return "El monto ingresado no es un número válido."
    
    fecha_str = data.get('fecha', '')
    try:
        if isinstance(fecha_str, (date, datetime)):
            fecha_str = str(fecha_str)
        fecha_gasto = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        if fecha_gasto > datetime.now().date():
            return "La fecha del gasto no puede ser posterior al día de hoy."
    except ValueError:
        return "Formato de fecha inválido. Use el calendario (YYYY-MM-DD)."
    
    return None


# ── 4. CONTROLADORES Y RUTAS WEB (CON EMISIÓN DE FLASH) ────────

@app.route('/')
def inicio():
    resumen = query("SELECT SUM(monto) AS total, COUNT(id) AS cantidad FROM gastos", one=True)
    total = resumen['total'] if resumen['total'] else 0
    cantidad = resumen['cantidad']
    return render_template('inicio.html', total=total, cantidad=cantidad)

@app.route('/gastos/')
def lista_gastos():
    cat_id = request.args.get('categoria_id', type=int)
    categorias = query("SELECT * FROM categorias ORDER BY nombre")
    
    if cat_id:
        gastos_filtrados = query("SELECT * FROM gastos WHERE categoria_id = %s ORDER BY fecha DESC", (cat_id,))
    else:
        gastos_filtrados = query("SELECT * FROM gastos ORDER BY fecha DESC")
        
    return render_template('lista.html', gastos=gastos_filtrados, categorias=categorias, cat_id=cat_id)

@app.route('/gastos/<int:id>/')
def detalle_gasto(id):
    gasto = query("SELECT * FROM gastos WHERE id = %s", (id,), one=True)
    if not gasto:
        abort(404)
        
    cat = query("SELECT * FROM categorias WHERE id = %s", (gasto['categoria_id'],), one=True)
    mp = query("SELECT * FROM metodos_pago WHERE id = %s", (gasto['metodo_pago_id'],), one=True)
    return render_template('detalle.html', gasto=gasto, categoria=cat, metodo_pago=mp)

@app.route('/gastos/nuevo/', methods=['GET', 'POST'])
def crear_gasto_html():
    categorias = query("SELECT * FROM categorias ORDER BY nombre")
    metodos_pago = query("SELECT * FROM metodos_pago ORDER BY nombre")
    
    if request.method == 'POST':
        data = {
            "descripcion": request.form.get('descripcion'),
            "monto": request.form.get('monto'),
            "fecha": request.form.get('fecha'),
            "categoria_id": request.form.get('categoria_id'),
            "metodo_pago_id": request.form.get('metodo_pago_id')
        }
        
        error = validar_gasto(data)
        if error:
            return render_template('form_crear.html', categorias=categorias, metodos_pago=metodos_pago, error=error, datos=data)
        
        execute(
            "INSERT INTO gastos (descripcion, monto, fecha, categoria_id, metodo_pago_id) VALUES (%s, %s, %s, %s, %s)",
            (data['descripcion'], float(data['monto']), data['fecha'], int(data['categoria_id']), int(data['metodo_pago_id']))
        )
        # MEJORA: Emitimos mensaje de éxito
        flash("¡Transacción registrada con éxito en MySQL!", "success")
        return redirect(url_for('lista_gastos'))
        
    return render_template('form_crear.html', categorias=categorias, metodos_pago=metodos_pago, error=None, datos={})

@app.route('/gastos/editar/<int:id>/', methods=['GET', 'POST'])
def editar_gasto_html(id):
    gasto = query("SELECT * FROM gastos WHERE id = %s", (id,), one=True)
    if not gasto:
        abort(404)
        
    categorias = query("SELECT * FROM categorias ORDER BY nombre")
    metodos_pago = query("SELECT * FROM metodos_pago ORDER BY nombre")
        
    if request.method == 'POST':
        data = {
            "descripcion": request.form.get('descripcion'),
            "monto": request.form.get('monto'),
            "fecha": request.form.get('fecha'),
            "categoria_id": request.form.get('categoria_id'),
            "metodo_pago_id": request.form.get('metodo_pago_id')
        }
        
        error = validar_gasto(data)
        if error:
            data['id'] = id
            return render_template('form_editar.html', categorias=categorias, metodos_pago=metodos_pago, error=error, gasto=data)
            
        execute(
            "UPDATE gastos SET descripcion=%s, monto=%s, fecha=%s, categoria_id=%s, metodo_pago_id=%s WHERE id=%s",
            (data['descripcion'], float(data['monto']), data['fecha'], int(data['categoria_id']), int(data['metodo_pago_id']), id)
        )
        # MEJORA: Emitimos mensaje de actualización con estilo informativo
        flash(f"¡El registro #{id} ha sido modificado exitosamente!", "info")
        return redirect(url_for('lista_gastos'))
        
    return render_template('form_editar.html', categorias=categorias, metodos_pago=metodos_pago, error=None, gasto=gasto)

@app.route('/gastos/eliminar/<int:id>/', methods=['GET', 'POST'])
def eliminar_gasto_html(id):
    gasto = query("SELECT * FROM gastos WHERE id = %s", (id,), one=True)
    if not gasto:
        abort(404)
        
    if request.method == 'POST':
        execute("DELETE FROM gastos WHERE id = %s", (id,))
        # MEJORA: Emitimos un mensaje de peligro/advertencia para el borrado
        flash("El gasto ha sido eliminado de manera permanente de la base de datos.", "danger")
        return redirect(url_for('lista_gastos'))
    return render_template('confirmar_eliminar.html', gasto=gasto)


# ── 5. ENDPOINTS DE LA API REST ───────────────────────────────

@app.route('/api/gastos/', methods=['GET'])
def api_get_gastos():
    cat_id = request.args.get('categoria_id', type=int)
    if cat_id:
        filtrados = query("SELECT * FROM gastos WHERE categoria_id = %s", (cat_id,))
        return jsonify(filtrados), 200
    todos = query("SELECT * FROM gastos")
    return jsonify(todos), 200

@app.route('/api/gastos/<int:id>/', methods=['GET'])
def api_get_gasto_detalle(id):
    gasto = query("SELECT * FROM gastos WHERE id = %s", (id,), one=True)
    if not gasto:
        abort(404)
    return jsonify(gasto), 200

@app.route('/api/gastos/', methods=['POST'])
def api_create_gasto():
    data = request.get_json() or {}
    error = validar_gasto(data)
    if error:
        return jsonify({"error": error}), 400
        
    nuevo_id = execute(
        "INSERT INTO gastos (descripcion, monto, fecha, categoria_id, metodo_pago_id) VALUES (%s, %s, %s, %s, %s)",
        (data['descripcion'], float(data['monto']), data['fecha'], int(data['categoria_id']), int(data['metodo_pago_id']))
    )
    nuevo_gasto = query("SELECT * FROM gastos WHERE id = %s", (nuevo_id,), one=True)
    return jsonify(nuevo_gasto), 201

@app.route('/api/gastos/resumen/', methods=['GET'])
def api_resumen_gastos():
    resumen = query("SELECT SUM(monto) AS total, COUNT(id) AS cantidad FROM gastos", one=True)
    total = resumen['total'] if resumen['total'] else 0
    return jsonify({
        "total_acumulado": total,
        "cantidad_gastos": resumen['cantidad']
    }), 200


# ── 6. CONTROLADORES GLOBALES DE EXCEPCIONES HTTP ─────────────

@app.errorhandler(400)
def peticion_incorrecta(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Petición incorrecta o parámetros inválidos"}), 400
    return render_template('base.html', contenido_error="Los datos enviados no tienen un formato válido."), 400

@app.errorhandler(404)
def pagina_no_encontrada(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "El recurso solicitado no fue encontrado"}), 404
    return render_template('base.html', contenido_error="La sección o el gasto que estás intentando buscar no existe."), 404

@app.errorhandler(500)
def error_interno_servidor(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Error interno crítico en el servidor de base de datos"}), 500
    return render_template('base.html', contenido_error="Disculpe las molestias. Ocurrió un error interno en nuestro servidor."), 500


if __name__ == '__main__':
    DEBUG_MODE = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    app.run(debug=DEBUG_MODE)