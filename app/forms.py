from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class ListingValidatorForm(FlaskForm):
    # Desactivamos el CSRF interno de WTForms porque tú ya tienes un input manual en tu HTML
    class Meta:
        csrf = False

    title = StringField('Título', validators=[
        DataRequired(message="El título es obligatorio."),
        Length(min=5, max=100, message="El título debe tener entre 5 y 100 caracteres.")
    ])
    category_id = IntegerField('Categoría', validators=[
        DataRequired(message="Debes seleccionar una categoría válida.")
    ])
    description = TextAreaField('Descripción', validators=[
        DataRequired(message="La descripción es obligatoria."),
        Length(min=15, max=5000, message="La descripción debe ser más detallada (mínimo 15 letras).")
    ])
    price = FloatField('Precio', validators=[
        DataRequired(message="El precio es obligatorio."),
        NumberRange(min=0.01, max=10000000, message="El precio debe ser un número válido mayor a 0.")
    ])
    province = StringField('Provincia', validators=[
        DataRequired(message="Debes seleccionar una provincia.")
    ])
    district = StringField('Distrito', validators=[
        DataRequired(message="El distrito es obligatorio."),
        Length(max=100, message="El nombre del distrito es demasiado largo.")
    ])
    duration_days = IntegerField('Duración', validators=[
        Optional(),
        NumberRange(min=20, max=60, message="Manipulación detectada: La duración de la campaña es inválida.")
    ])