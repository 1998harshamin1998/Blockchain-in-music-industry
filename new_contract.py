from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class ContractForm(FlaskForm):
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    """
    distributorAPI = StringField('Distributor API KEY', validators=[DataRequired()])
    producerID = StringField('Producer ID', validators=[DataRequired()])
    albumID = StringField('Album ID', validators=[DataRequired()])
    amount_per_access = StringField('Amount per usage', validators=[DataRequired()])
    submit = SubmitField('Submit')
