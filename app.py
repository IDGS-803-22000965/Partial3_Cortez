from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from models import db, Usuario, Pedido, DetallePedido
from forms import FormularioLogin, FormularioRegistro, ClienteForm, PizzaForm
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
app.secret_key = 'tu_clave_secreta_aqui'
csrf = CSRFProtect(app)

gestor_login = LoginManager()
gestor_login.init_app(app)
gestor_login.login_view = 'iniciar_sesion'
gestor_login.login_message = "Por favor, inicia sesión para acceder a esta página."  
gestor_login.login_message_category = "info"  

db.init_app(app)

ARCHIVO_TEMPORAL = 'pizzas_temp.json'

def guardar_pizza_temp(pizza):
    if os.path.exists(ARCHIVO_TEMPORAL):
        with open(ARCHIVO_TEMPORAL, 'r') as file:
            pizzas = json.load(file)
    else:
        pizzas = []
    pizzas.append(pizza)
    with open(ARCHIVO_TEMPORAL, 'w') as file:
        json.dump(pizzas, file)

def obtener_pizzas_temp():
    if os.path.exists(ARCHIVO_TEMPORAL):
        with open(ARCHIVO_TEMPORAL, 'r') as file:
            return json.load(file)
    return []

def eliminar_pizzas_temp():
    if os.path.exists(ARCHIVO_TEMPORAL):
        os.remove(ARCHIVO_TEMPORAL)

@gestor_login.user_loader
def cargar_usuario(id_usuario):
    # Modificación para manejar tanto IDs numéricos como nombres de usuario
    try:
        # Primero intenta con el ID numérico
        return Usuario.query.get(int(id_usuario))
    except (ValueError, TypeError):
        # Si falla, busca por nombre de usuario
        return Usuario.query.filter_by(username=id_usuario).first()

@app.route('/')
@login_required
def inicio():
    return redirect(url_for('index'))

@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    # Inicialización de formularios
    cliente_form = ClienteForm()
    pizza_form = PizzaForm()
    
    # Establecer valor por defecto para cantidad
    pizza_form.cantidad.data = 0
    
    # Obtener pizzas temporales y calcular total
    pizzas = obtener_pizzas_temp()
    total = sum(p['subtotal'] for p in pizzas) if pizzas else 0
    
    # Configuración de filtros de fecha
    hoy = datetime.now()
    periodo = request.args.get('periodo', 'dia')
    mes_seleccionado = request.args.get('mes', str(hoy.month))
    dia_seleccionado = request.args.get('dia', str(hoy.day))
    
    meses = [(str(i), datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    dias = [(str(i), str(i)) for i in range(1, 32)]
    
    # Consulta de pedidos filtrados
    if periodo == 'dia':
        pedidos_filtrados = Pedido.query.filter(
            db.func.month(Pedido.fecha) == int(mes_seleccionado),
            db.func.day(Pedido.fecha) == int(dia_seleccionado)
        ).all()
        titulo_periodo = f"{datetime(2000, int(mes_seleccionado), int(dia_seleccionado)).strftime('%d de %B')}"
    else:  
        pedidos_filtrados = Pedido.query.filter(
            db.func.month(Pedido.fecha) == int(mes_seleccionado)
        ).all()
        titulo_periodo = f"{datetime(2000, int(mes_seleccionado), 1).strftime('%B')}"
    
    total_ventas_periodo = sum(pedido.total for pedido in pedidos_filtrados) if pedidos_filtrados else 0
    
    # Aplicar filtros si es necesario
    if 'aplicar_filtro' in request.args:
        return redirect(url_for('index', 
                            periodo=request.args.get('periodo', 'dia'),
                            mes=request.args.get('mes', '1'),
                            dia=request.args.get('dia', '1')))
    
    # Cargar datos del cliente desde sesión si existen
    if 'cliente_data' in session:
        cliente_form.nombre.data = session['cliente_data'].get('nombre', '')
        cliente_form.direccion.data = session['cliente_data'].get('direccion', '')
        cliente_form.telefono.data = session['cliente_data'].get('telefono', '')
    
    # Procesamiento de formularios POST
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Guardar/actualizar datos del cliente en sesión
        session['cliente_data'] = {
            'nombre': request.form.get('nombre', ''),
            'direccion': request.form.get('direccion', ''),
            'telefono': request.form.get('telefono', '')
        }
        
        if action == 'agregar_pizza':
            if pizza_form.validate():
                # Cálculo de precios sin validación de cantidad
                precios_tamano = {'Chica': 40, 'Mediana': 80, 'Grande': 120}
                precio_tamano = precios_tamano.get(pizza_form.tamano.data, 0)
                precio_ingredientes = 10
                subtotal = (precio_tamano + precio_ingredientes) * pizza_form.cantidad.data

                nueva_pizza = {
                    'tamano': pizza_form.tamano.data,
                    'ingredientes': pizza_form.ingredientes.data,
                    'cantidad': pizza_form.cantidad.data,
                    'subtotal': subtotal
                }
                guardar_pizza_temp(nueva_pizza)
                flash('Pizza agregada correctamente', 'success')
            else:
                for field, errors in pizza_form.errors.items():
                    for error in errors:
                        flash(f'Error en pizza: {getattr(pizza_form, field).label.text}: {error}', 'error')
            return redirect(url_for('index'))

        elif action == 'quitar_pizza':
            index = int(request.form.get('quitar_pizza', -1))
            if 0 <= index < len(pizzas):
                pizzas.pop(index)
                with open(ARCHIVO_TEMPORAL, 'w') as file:
                    json.dump(pizzas, file)
                flash('Pizza eliminada correctamente', 'success')
            return redirect(url_for('index'))

        elif action == 'terminar_pedido':
            if cliente_form.validate():
                if not pizzas:
                    flash('El pedido debe contener al menos una pizza', 'error')
                    return redirect(url_for('index'))
                
                try:
                    # Crear nuevo pedido
                    nuevo_pedido = Pedido(
                        nombre=cliente_form.nombre.data,
                        direccion=cliente_form.direccion.data,
                        telefono=cliente_form.telefono.data,
                        total=total,
                        fecha=datetime.now()
                    )
                    db.session.add(nuevo_pedido)
                    db.session.commit()

                    # Añadir detalles del pedido
                    for pizza in pizzas:
                        detalle = DetallePedido(
                            pedido_id=nuevo_pedido.id,
                            tamano=pizza['tamano'],
                            ingredientes=pizza['ingredientes'],
                            cantidad=pizza['cantidad'],
                            subtotal=pizza['subtotal']
                        )
                        db.session.add(detalle)
                    
                    db.session.commit()
                    eliminar_pizzas_temp()
                    session.pop('cliente_data', None)
                    flash(f'Pedido realizado con éxito. Total: ${total:.2f}', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error al realizar el pedido: {str(e)}', 'error')
                return redirect(url_for('index'))
            else:
                for field, errors in cliente_form.errors.items():
                    for error in errors:
                        flash(f'{getattr(cliente_form, field).label.text}: {error}', 'error')
                return redirect(url_for('index'))

    # Renderizar plantilla
    return render_template(
        'index.html',
        cliente_form=cliente_form,
        pizza_form=pizza_form,
        pizzas=pizzas,
        total=total,
        pedidos_filtrados=pedidos_filtrados,
        total_ventas_periodo=total_ventas_periodo,
        titulo_periodo=titulo_periodo,
        periodo=periodo,
        mes_seleccionado=mes_seleccionado,
        dia_seleccionado=dia_seleccionado,
        meses=meses,
        dias=dias
    )
@app.route('/iniciar_sesion', methods=['GET', 'POST'])
def iniciar_sesion():
    formulario = FormularioLogin()
    if formulario.validate_on_submit():
        username = formulario.username.data
        password = formulario.password.data

        usuario = Usuario.query.filter_by(username=username).first()

        if usuario and usuario.verificar_password(password):
            login_user(usuario)
            flash('Inicio de sesión exitoso.', 'éxito')
            return redirect(url_for('index'))  
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'error')

    return render_template('iniciar_sesion.html', formulario=formulario)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    formulario = FormularioRegistro()
    if formulario.validate_on_submit():
        username = formulario.username.data
        password = formulario.password.data
        rol = formulario.rol.data

        usuario_existente = Usuario.query.filter_by(username=username).first()
        if usuario_existente:
            flash('El nombre de usuario ya está en uso.', 'error')
            return redirect(url_for('registro'))

        nuevo_usuario = Usuario(username=username, rol=rol)
        nuevo_usuario.establecer_password(password)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Usuario registrado exitosamente. Por favor, inicia sesión.', 'éxito')
        return redirect(url_for('iniciar_sesion'))

    return render_template('registro.html', formulario=formulario)

@app.route('/cerrar_sesion')
@login_required
def cerrar_sesion():
    logout_user()
    return redirect(url_for('iniciar_sesion'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)