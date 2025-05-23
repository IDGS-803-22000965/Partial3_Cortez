from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError

class FormularioLogin(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Contraseña', validators=[DataRequired()])

class FormularioRegistro(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    rol = SelectField('Rol', choices=[('alumno', 'Alumno'), ('profesor', 'Profesor')], validators=[DataRequired()])

class ClienteForm(FlaskForm):
    nombre = StringField('Nombre Completo', validators=[DataRequired(), Length(min=4, max=100)])
    direccion = TextAreaField('Dirección', validators=[DataRequired(), Length(min=10, max=200)])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(min=8, max=15)])

class PizzaForm(FlaskForm):
    tamano = SelectField('Tamaño', choices=[
        ('Chica', 'Chica ($40)'), 
        ('Mediana', 'Mediana ($80)'), 
        ('Grande', 'Grande ($120)')
    ], validators=[DataRequired()])
    
    ingredientes = SelectField('Ingredientes', choices=[
        ('Jamón', 'Jamón ($10)'), 
        ('Piña', 'Piña ($10)'), 
        ('Champiñones', 'Champiñones ($10)')
    ], validators=[DataRequired()])
    
    cantidad = IntegerField('Cantidad', validators=[DataRequired()], default=1)
    
    def validate_cantidad(self, field):
        if field.data is None or field.data < 1:
            raise ValidationError('La cantidad debe ser al menos 1')