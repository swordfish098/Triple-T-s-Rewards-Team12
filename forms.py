from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired

class AboutForm(FlaskForm):
    team_num = IntegerField('Team Number', validators=[DataRequired()])
    version_num = IntegerField('Version Number', validators=[DataRequired()])
    product_name = StringField('Product Name', validators=[DataRequired()])
    product_desc = TextAreaField('Product Description', validators=[DataRequired()])