from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Length, InputRequired
from werkzeug.security import generate_password_hash, check_password_hash

class AddForm(FlaskForm):
    task = StringField('Сделать:', validators=[InputRequired(),Length(min=5, max=100)])
    submit = SubmitField('Записать') 

