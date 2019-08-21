from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    """ Represents a login form """

    email = StringField('Email', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])

    def __str__(self):
        return self.email.data + ', ' + self.password.data
