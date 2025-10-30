from flask_wtf import FlaskForm
from extensions import db
from wtforms import BooleanField, SelectMultipleField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length
from models import Role, User

# Assuming your User model has USERNAME, FNAME, and LNAME attributes
class SendNotificationForm(FlaskForm):
    recipients = SelectMultipleField("Recipients", coerce=int) 
    
    message = TextAreaField('Message', validators=[DataRequired()])
    
    submit = SubmitField('Send Message')
    send_all = BooleanField('Send to All Drivers')
    
    def __init__(self, current_user_code=None, *args, **kwargs):
        super(SendNotificationForm, self).__init__(*args, **kwargs)
        
        # 1. Fetch all active users, ordered by Username
        users = (User.query.filter(User.IS_ACTIVE == 1)
         .with_entities(User.USER_CODE, User.USERNAME, User.USER_TYPE)
         .order_by(User.USERNAME)
         .all())
        
        rows = (User.query
                .with_entities(
                    User.USER_CODE,   # index 0
                    User.USERNAME,    # index 1
                    User.FNAME,       # index 2
                    User.LNAME        # index 3
                )
                .filter(User.IS_ACTIVE == 1)
                .order_by(User.USERNAME.asc())
                .all())

        if current_user_code is not None:
            rows = [r for r in rows if r[0] != int(current_user_code)]
        
        # 4. Set the final choices list
        self.recipients.choices = [
            (user_code, f"{username} ({(fname or '').strip()} {(lname or '').strip()})".strip())
            for (user_code, username, fname, lname) in rows
        ]