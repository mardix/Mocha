
import datetime
import arrow
from . import exceptions
from mocha import (db,
                   utils,
                   send_mail,
                   bcrypt,
                   _)
from mocha.exceptions import ModelError


class AuthUserRole(db.Model):

    SUPERADMIN = "SUPERADMIN"  # ALL MIGHTY, RESERVED FOR SYS ADMIN
    ADMIN = "ADMIN"  # App/Site admin
    MANAGER = "MANAGER"  # Limited access, but can approve EDITOR Data
    EDITOR = "EDITOR"  # Rights to write, manage, publish own data
    CONTRIBUTOR = "CONTRIBUTOR"  # Rights to only write and read own data
    MODERATOR = "MODERATOR"   # Moderate content
    MEMBER = "MEMBER"  # Just a member

    # BASIC ROLES
    ROLES = [(99, SUPERADMIN),
               (89, ADMIN),
               (59, MANAGER),
               (49, EDITOR),
               (39, CONTRIBUTOR),
               (29, MODERATOR),
               (10, MEMBER)]

    name = db.Column(db.String(75), index=True)
    level = db.Column(db.Integer, index=True)

    @classmethod
    def initialize__(cls):
        """
        Mocha specific
        To setup some models data after
        :return:
        """
        [cls.new(level=r[0], name=r[1]) for r in cls.ROLES]

    @classmethod
    def new(cls, name, level):
        name = cls.slug_name(name)
        if not cls.get_by_name(name) and not cls.get_by_level(level):
            return cls.create(name=name, level=level)

    @classmethod
    def get_by_name(cls, name):
        name = cls.slug_name(name)
        return cls.query().filter(cls.name == name).first()

    @classmethod
    def get_by_level(cls, level):
        return cls.query().filter(cls.level == level).first()

    @classmethod
    def slug_name(cls, name):
        return utils.slugify(name)


class AuthUser(db.Model):

    STATUS_ACTIVE = "active"
    STATUS_SUSPENDED = "suspended"
    STATUS_DELETED = "deleted"

    """
    User
    """
    role_id = db.Column(db.Integer, db.ForeignKey(AuthUserRole.id))
    login_method = db.Column(db.String(75), index=True)
    username = db.Column(db.String(255), index=True, unique=True)
    email = db.Column(db.EmailType, index=True)
    email_verified = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(255))
    require_password_change = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    profile_image = db.Column(db.StorageObjectType)
    options = db.Column(db.JSONType)
    status = db.Column(db.String(255), default=STATUS_ACTIVE, index=True)
    last_login_at = db.Column(db.DateTime)
    locale = db.Column(db.String(10), default="en")
    timezone = db.Column(db.String(255))
    # A secret key to sign data per user. If a key is compromised,
    # we can reset this one only and not affect anyone else
    secret_key = db.Column(db.String(255))
    # Relationship to role
    role = db.relationship(AuthUserRole)

    @classmethod
    def encrypt_password(cls, password):
        return bcrypt.hash(password)

    @classmethod
    def new(cls,
            username,
            password,
            email=None,
            first_name="",
            last_name="",
            login_method=None,
            role="MEMBER"
            ):
        """
        Create a new user
        :param username: str
        :param password: str
        :param email: str
        :param first_name: str
        :param last_name: str
        :param login_method: str
        :param role: str
        :return: AuthUser
        """
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email
        }

        username = username.strip().lower()
        if "@" in username and not email:
            if not utils.is_email_valid(username):
                exceptions.AuthError(_("Invalid username"))
            data["email"] = username
        elif email:
            if not utils.is_email_valid(email):
                exceptions.AuthError(_("Invalid username"))

        if not utils.is_username_valid(username):
            exceptions.AuthError(_("Invalid username"))
        if not utils.is_password_valid(password):
            raise exceptions.AuthError(_("Password is invalid"))

        if cls.get_by_username(username):
            raise exceptions.AuthError(_("Username exists already"))
        _email = data.get("email")
        if _email:
            if cls.get_by_email(_email):
                raise exceptions.AuthError(_("Email address exists already"))

        role = AuthUserRole.get_by_name(role or "MEMBER")
        if not role:
            raise exceptions.AuthError(_("Invalid user role"))

        data.update({
            "username": username,
            "password_hash": cls.encrypt_password(password),
            "email_verified": False,
            "login_method": login_method,
            "role": role,
            "status": cls.STATUS_ACTIVE
        })
        user = cls.create(**data)
        user.reset_secret_key()
        return user

    @classmethod
    def get_by_username(cls, username):
        """
        Return a User by email address
        """
        return cls.query().filter(cls.username == username).first()

    @classmethod
    def get_by_email(cls, email):
        """
        Return a User by email address
        """
        return cls.query().filter(cls.email == email).first()

    @classmethod
    def search_by_name(cls, query, name):
        """
        Make a search
        :param query:
        :param name:
        :return:
        """
        query = query.filter(db.or_(cls.first_name.contains(name),
                                    cls.last_name.contains(name)))
        return query

    @property
    def active(self):
        return self.status == self.STATUS_ACTIVE

    @property
    def suspended(self):
        return self.status == self.STATUS_SUSPENDED

    @property
    def deleted(self):
        return self.is_deleted or self.status == self.STATUS_DELETED

    @property
    def name(self):
        return self.first_name

    @property
    def full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def change_username(self, username):
        """
        Change username
        :param username: email or str
        :return:
        """
        username = username.lower()
        if self.username != username:
            if self.get_by_username(username):
                raise exceptions.AuthError("Username exists already")
            self.update(username=username)

    def change_email(self, email, as_username=False):
        """
        Change account email
        :param email:
        :param as_username
        :return: the email provided
        """
        email = email.lower()
        data = {"email": email}
        if self.email != email:
            if self.get_by_email(email):
                raise exceptions.AuthError("Email exists already")
            if as_username:
                if self.username != email:
                    if self.get_by_username(email):
                        raise exceptions.AuthError("Username exists already")
                data["username"] = email

            self.update(**data)

    def change_password(self, password):
        """
        Change the password.
        :param password:
        :return:
        """
        self.update(password_hash=self.encrypt_password(password),
                    require_password_change=False)

        # Whenever the password is changed, reset the secret key to invalidate
        # any tokens in the wild
        self.reset_secret_key()

    def set_email_verified(self, verified=False):
        self.update(email_verified=verified)
        self.reset_secret_key()

    def password_matched(self, password):
        """
        Check if the password matched the hash
        :returns bool:
        """
        return bcrypt.verify(password, self.password_hash)

    def reset_secret_key(self):
        """
        Run this whenever there is a security change in the account.
        ie: password change.
        BTW, AuthUserLogin.change_password, already performs this method
        """
        self.update(secret_key=utils.guid())

    def set_options(self, **kwargs):
        """
        Set the options. Existing value will persist
        :param kwargs:
        :return:
        """
        options = self.options
        options.update(kwargs)
        self.update(options=options)

    def set_role(self, role):
        role_ = AuthUserRole.get_by_name(role.upper())
        if not role_:
            raise ModelError("Invalid user role: '%s'" % role)
        self.update(role=role_)

    def has_any_roles(self, *roles):
        """
        Check if user has any of the roles requested
        :param roles: tuple of roles string
        :return: bool
        """
        roles = map(utils.slugify, list(roles))

        return True \
            if AuthUserRole.query() \
            .join(AuthUser) \
            .filter(AuthUserRole.name.in_(roles)) \
            .filter(AuthUser.id == self.id) \
            .count() \
            else False


class AuthUserSocialLogin(db.Model):
    """
    Only store the provider name and social_id, to match user
    """
    user_id = db.Column(db.Integer, db.ForeignKey(AuthUser.id))
    provider = db.Column(db.String(50), index=True)
    social_id = db.Column(db.String(255), index=True)
    user = db.relationship(AuthUser, backref='social_logins')
    active = db.Column(db.Boolean, default=True)

    @classmethod
    def get_user(cls, provider, social_id):
        login = cls.query() \
            .filter(cls.provider == provider) \
            .filter(cls.social_id == social_id) \
            .first()
        return login.user if login else None

    @classmethod
    def new(cls, user, provider, social_id):
        """
        Create a new login
        :param user: AuthUser
        :param provider: str - ie: facebook, twitter, ...
        :param social_id: str - an id associated to provider
        :return:
        """
        if cls.get_user(provider, social_id):
            raise exceptions.AuthError("Social Login exists already")

        return cls.create(user_id=user.id,
                          provider=provider,
                          social_id=social_id)


