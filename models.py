from datetime import datetime, timedelta
from extensions import db, login_manager
from extensions import bcrypt
import secrets
from english_words import english_words_set
import random
import string
from flask_login import UserMixin
import pyotp
from itsdangerous import URLSafeTimedSerializer

LOCKOUT_ATTEMPTS = 3
WORDS = list(english_words_set)

class AuditLog(db.Model):
    __tablename__ = 'AUDIT_LOG'
    EVENT_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EVENT_TYPE = db.Column(db.String(50), nullable=False)
    DETAILS = db.Column(db.Text, nullable=True)
    CREATED_AT = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Role:
    DRIVER = 'driver'
    SPONSOR = 'sponsor'
    ADMINISTRATOR = 'administrator'

    @staticmethod
    def choices():
        return [Role.DRIVER, Role.SPONSOR, Role.ADMINISTRATOR]

class AboutInfo(db.Model):
    __tablename__ = 'ABOUT_INFO'
    entry_id = db.Column(db.Integer, primary_key=True)
    team_num = db.Column(db.Integer)
    version_num = db.Column(db.Integer)
    release_date = db.Column(db.DateTime, default=datetime)
    product_name = db.Column(db.String(255))
    product_desc = db.Column(db.Text)

class User(db.Model, UserMixin):
    __tablename__ = 'USERS'
    #User PI
    USER_CODE = db.Column(db.Integer, primary_key=True, autoincrement=True)
    USERNAME = db.Column(db.String(50), unique=True, nullable=False)
    PASS = db.Column(db.String(255), nullable=True)
    USER_TYPE = db.Column(db.String(20), nullable=False)
    FNAME = db.Column(db.String(50), nullable=False)
    LNAME = db.Column(db.String(50), nullable=False)
    EMAIL = db.Column(db.String(100), nullable=False)
    CREATED_AT = db.Column(db.DateTime, nullable=False)
    PHONE = db.Column(db.String(15), nullable=True)
    LOCKED_REASON = db.Column(db.String(100), nullable=True)
    wants_point_notifications = db.Column(db.Boolean, default=True, nullable=False)
    wants_order_notifications = db.Column(db.Boolean, default=True, nullable=False)
    TOTP_SECRET = db.Column(db.String(16), nullable=True)
    TOTP_ENABLED = db.Column(db.Boolean, default=False, nullable=False)
    addresses = db.relationship('Address', backref='user', lazy=True, cascade="all, delete-orphan")
    wishlist_items = db.relationship('WishlistItem', backref='user', lazy=True, cascade="all, delete-orphan")
    # sponsor = db.relationship('Sponsor', backref='user', uselist=False, cascade="all, delete-orphan")
    driver_profile = db.relationship("Driver", back_populates="user_account", uselist=False)
    sponsor_profile = db.relationship("Sponsor", back_populates="user_account", uselist=False)

    #User account
    IS_ACTIVE = db.Column(db.Integer, nullable=False)
    FAILED_ATTEMPTS = db.Column(db.Integer, default=0, nullable=False)
    LOCKOUT_TIME = db.Column(db.DateTime, nullable=True)
    RESET_TOKEN = db.Column(db.String(255), nullable=True, index=True)
    RESET_TOKEN_CREATED_AT = db.Column(db.DateTime, nullable=True)
    IS_LOCKED_OUT = db.Column(db.Integer, nullable=False)
    LOCKED_REASON = db.Column(db.String(255), nullable=True)

    def log_event(self, event_type: str, details: str = None):
        log_entry = AuditLog(EVENT_TYPE=event_type, DETAILS=details)
        db.session.add(log_entry)
        db.session.commit()

    def set_password(self, password: str) -> None:
        self.PASS = bcrypt.generate_password_hash(password).decode("utf-8")

    def admin_set_new_pass(self) -> str:
        word = random.choice(WORDS)
        num_digits = 6
        numbers = ''.join(secrets.choice(string.digits) for _ in range(num_digits))
        password = word + numbers

        self.PASS = bcrypt.generate_password_hash(password).decode('utf-8')

        return password

    def check_password(self, password : str) -> bool:
        if not self.PASS:
            return False
        return bcrypt.check_password_hash(self.PASS, password)

    def is_account_locked(self) -> bool:
        if self.LOCKOUT_TIME and datetime.utcnow() < self.LOCKOUT_TIME:
            self.IS_LOCKED_OUT = 1
            return True
        return False

    def get_totp_uri(self):
        return f'otpauth://totp/TripleTRewards:{self.USERNAME}?secret={self.TOTP_SECRET}&issuer=TripleTRewards'

    def get_totp(self):
        return pyotp.TOTP(self.TOTP_SECRET)

    def register_failed_attempt(self):
        self.FAILED_ATTEMPTS += 1
        if self.FAILED_ATTEMPTS >= LOCKOUT_ATTEMPTS:
            self.LOCKOUT_TIME = datetime.utcnow() + timedelta(minutes=15)
            self.IS_LOCKED_OUT = 1
            self.LOCKED_REASON = "failed_attempts"

    def clear_failed_attempts(self):
        self.FAILED_ATTEMPTS = 0
        self.LOCKOUT_TIME = None
        self.IS_LOCKED_OUT = 0
        self.LOCKED_REASON = None

    def generate_reset_token(self) -> str:
        token = secrets.token_urlsafe(48)
        self.RESET_TOKEN = token
        self.RESET_TOKEN_CREATED_AT = datetime.utcnow()
        return token

    def clear_reset_token(self):
        self.RESET_TOKEN = None
        self.RESET_TOKEN_CREATED_AT = None

    def get_id(self):
        return str(self.USER_CODE)

class Driver(db.Model):
    __tablename__ = "DRIVERS"

    # DRIVER_ID acts as both PK and FK → USERS.USER_CODE
    DRIVER_ID = db.Column(db.Integer, db.ForeignKey("USERS.USER_CODE"), primary_key=True)
    LICENSE_NUMBER = db.Column(db.String(50))

    user_account = db.relationship("User", back_populates="driver_profile")

    sponsor_associations = db.relationship(
        "DriverSponsorAssociation",
        back_populates="driver",
        cascade="all, delete-orphan"
    )

    applications = db.relationship(
        "DriverApplication",
        back_populates="driver",
        cascade="all, delete-orphan"
    )



class Sponsor(db.Model):
    __tablename__ = "SPONSORS"

    # SPONSOR_ID now acts as both PK and FK → USERS.USER_CODE
    SPONSOR_ID = db.Column(db.Integer, db.ForeignKey("USERS.USER_CODE"), primary_key=True)
    ORG_NAME = db.Column(db.String(100))
    STATUS = db.Column(db.String(50))

    user_account = db.relationship("User", back_populates="sponsor_profile")

    driver_associations = db.relationship(
        "DriverSponsorAssociation",
        back_populates="sponsor",
        cascade="all, delete-orphan"
    )

    applications = db.relationship(
        "DriverApplication",
        back_populates="sponsor",
        cascade="all, delete-orphan"
    )



class Admin(db.Model):
    __tablename__ = "ADMIN"
    ADMIN_ID = db.Column(db.Integer, db.ForeignKey("USERS.USER_CODE", ondelete="CASCADE"), primary_key=True)
    ROLE_TITLE = db.Column(db.String(100))

class DriverApplication(db.Model):
    __tablename__ = "DRIVER_APPLICATIONS"
    APPLICATION_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    DRIVER_ID = db.Column(db.Integer, db.ForeignKey("DRIVERS.DRIVER_ID", ondelete="CASCADE"))
    SPONSOR_ID = db.Column(db.Integer, db.ForeignKey("SPONSORS.SPONSOR_ID", ondelete="CASCADE"))
    STATUS = db.Column(db.Enum("Pending", "Accepted", "Rejected", name="DRIVER_APPLICATION_STATUS"), default="Pending")
    REASON = db.Column(db.String(255))
    APPLIED_AT = db.Column(db.DateTime, server_default=db.func.now())
    LICENSE_NUMBER = db.Column(db.String(50), nullable=True)
    driver = db.relationship("Driver", back_populates="applications")
    sponsor = db.relationship("Sponsor", back_populates="applications")

class DriverSponsorAssociation(db.Model):
    __tablename__ = "DRIVER_SPONSOR_ASSOCIATION"

    driver_id = db.Column(db.Integer, db.ForeignKey("DRIVERS.DRIVER_ID"), primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey("SPONSORS.SPONSOR_ID"), primary_key=True)
    points = db.Column(db.Integer, default=0)

    driver = db.relationship("Driver", back_populates="sponsor_associations")
    sponsor = db.relationship("Sponsor", back_populates="driver_associations")



class StoreSettings(db.Model):
    __tablename__ = 'STORE_SETTINGS'
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('SPONSORS.SPONSOR_ID'), nullable=False, unique=True)
    ebay_category_id = db.Column(db.String(50), nullable=False, default='2984')
    point_ratio = db.Column(db.Integer, nullable=False, default=10)

class CartItem(db.Model):
    __tablename__ = 'CART_ITEMS'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('USERS.USER_CODE'), nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('SPONSORS.SPONSOR_ID'), nullable=False)
    item_id = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))

class Notification(db.Model):
    __tablename__ = 'NOTIFICATIONS'
    NOTIFICATION_ID = db.Column(db.Integer, primary_key=True)
    SENDER_CODE = db.Column(db.Integer, db.ForeignKey('USERS.USER_CODE'), nullable=False)
    RECIPIENT_CODE = db.Column(db.Integer, db.ForeignKey('USERS.USER_CODE'), nullable=False)
    TIMESTAMP = db.Column(db.DateTime, nullable=False)
    MESSAGE = db.Column(db.Text, nullable=False)
    READ_STATUS = db.Column(db.Integer, nullable=False)
    sender = db.relationship('User', foreign_keys=[SENDER_CODE], backref=db.backref('notifications_sent', lazy='dynamic'))
    recipient = db.relationship('User', foreign_keys=[RECIPIENT_CODE], backref=db.backref('notifications_received', lazy='dynamic'))

    @staticmethod
    def create_notification(recipient_code, sender_code, message):
        notification = Notification(
            RECIPIENT_CODE=recipient_code,
            SENDER_CODE=sender_code,
            TIMESTAMP=datetime.utcnow(),
            MESSAGE=message,
            READ_STATUS=0
        )
        db.session.add(notification)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        return notification

class Address(db.Model):
    __tablename__ = 'ADDRESSES'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('USERS.USER_CODE'), nullable=False)
    street = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)

class WishlistItem(db.Model):
    __tablename__ = 'WISHLIST_ITEMS'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('USERS.USER_CODE'), nullable=False)
    item_id = db.Column(db.String(255), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

class Organization(db.Model):
    __tablename__ = 'ORGANIZATIONS'
    ORG_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ORG_NAME = db.Column(db.String(100), unique=True, nullable=False)
    CREATED_AT = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class ImpersonationLog(db.Model):
    __tablename__ = 'IMPERSONATION_LOG'
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('USERS.USER_CODE'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('USERS.USER_CODE'), nullable=False)
    action = db.Column(db.String(20), nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)