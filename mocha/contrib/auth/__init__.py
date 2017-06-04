"""
Mocha Auth
"""

import logging
from . import signals, exceptions, oauth
import flask_login
from flask import current_app
from mocha.exceptions import AppError
import mocha.cli
from mocha import (_,
                   utc_now,
                   config,
                   abort,
                   send_mail,
                   url_for,
                   views,
                   models,
                   utils,
                   request,
                   redirect,
                   flash,
                   session,
                   init_app,
                   decorators as h_deco)
import models as auth_models
from flask_login import current_user

__version__ = "1.0.0"

__options__ = utils.dict_dot({})

# USER ROLES
ROLES_SUPERADMIN = ["SUPERADMIN"]
ROLES_ADMIN = ROLES_SUPERADMIN + ["ADMIN"]
ROLES_MANAGER = ROLES_ADMIN + ["MANAGER"]
ROLES_CONTRIBUTOR = ROLES_MANAGER + ["EDITOR", "CONTRIBUTOR"]
ROLES_MODERATOR = ROLES_CONTRIBUTOR + ["MODERATOR"]

ACTIONS = {
    "USERNAME": "USERNAME",
    "PASSWORD": "PASSWORD",
    "EMAIL": "EMAIL",
    "STATUS": "STATUS",
    "PROFILE_IMAGE": "PROFILE_IMAGE",
    "UPDATE": "UPDATE"
}

# LOGIN MANAGER: Flask Login
login_manager = flask_login.LoginManager()
login_manager.login_message_category = "error"
init_app(login_manager.init_app)


@login_manager.user_loader
def load_user(userid):
    return get_user_by_id(userid)


# def init(app):
#     @app.before_request
#     def force_password_change():
#         print("THIS IS BEFORE REQUEST")
#         _ = __options__.get("require_password_change_exclude_endpoints")
#         _ = [] if not isinstance(_, list) else _
#
#         exclude_endpoints = ["static", "ContactPage:index", "Index:index",
#                              "AuthLogin:logout"] + _
#
#         if current_user and current_user.is_authenticated:
#             if request.endpoint \
#                     and request.endpoint not in exclude_endpoints:
#                 if request.endpoint != "AuthAccount:change_password" \
#                         and session_get_require_password_change():
#                     flash("Password Change is required", "info")
#                     return redirect(views.auth.Account.account_info, edit_password=1)



# ------------------------------------------------------------------------------

def is_authenticated():
    """ A shortcut to check if a user is authenticated """
    return current_user and current_user.is_authenticated and current_user.is_active


def not_authenticated():
    """ A shortcut to check if user not authenticated."""
    return not is_authenticated()


def get_random_password(length=8):
    return utils.generate_random_string(length)


# ------------------------------------------------------------------------------
# VISIBILITY:
# The methods below return bool that are meant be pass in the
# nav_title(visible=fn) `visible` args
#

def visible_to_roles(*roles):
    """
    This is a @nav_title specific function to set the visibility of menu based on
    roles
    :param roles:
    :return: callback fn
    """
    if is_authenticated():
        return True if current_user.has_any_roles(*roles) else False
    return False


# Alias
def visible_to_superadmins():
    return visible_to_roles(*ROLES_SUPERADMIN)


def visible_to_admins():
    return visible_to_roles(*ROLES_ADMIN)


def visible_to_managers():
    return visible_to_roles(*ROLES_MANAGER)


def visible_to_contributors():
    return visible_to_roles(*ROLES_CONTRIBUTOR)


def visible_to_moderators():
    return visible_to_roles(*ROLES_MODERATOR)


def visible_to_authenticated():
    return is_authenticated()


def visible_to_non_authenticated():
    return not_authenticated()


# ------------------------------------------------------------------------------

# TOKENIZATION


def get_jwt_secret():
    """
    Get the JWT secret
    :return: str
    """
    secret_key = __options__.get("jwt_secret") or config("JWT_SECRET") or config("SECRET_KEY")
    if not secret_key:
        raise exceptions.AuthError("Missing config JWT/SECRET_KEY")
    return secret_key


def get_jwt_salt():
    """
    Get the JWT salt
    :return: str
    """
    return __options__.get("jwt_salt", "mocha:contrib:auth")


def get_jwt_ttl():
    """
    Get JWT time to live
    :return:
    """
    return __options__.get("jwt_ttl", 3600)


# ------------------------------------------------------------------------------
# SIGNUP + LOGIN


def _user(user):
    """
    Factory function to AuthUser
    :param user: AuthUser
    :return:
    """
    return UserModel(user) if user else None


def create_user(username, password, email=None, first_name="", last_name="",
                role="MEMBER", login_method=None):
    """
    Create a new user
    :param username:
    :param password:
    :param email:
    :param first_name:
    :param last_name:
    :param role: str
    :return: AuthUser
    """

    if not login_method:
        login_method = "email" if "@" in username else "username"

    def cb():
        return _user(models.AuthUser.new(username=username,
                                         password=password,
                                         email=email,
                                         first_name=first_name,
                                         last_name=last_name,
                                         login_method=login_method,
                                         role=role))

    return signals.create_user(cb)


def get_user_by_id(id):
    """
    To get a user by id
    :param id: int
    :return: AuthUser
    """
    return _user(models.AuthUser.get(id))


def get_user_by_username(username):
    """
    Return AuthUser by username
    :param username: 
    :return: AuthUser
    """
    return _user(models.AuthUser.get_by_username(username))


def get_user_by_email(email):
    """
    Return AuthUser by email
    :param email:
    :return: AuthUser
    """
    return _user(models.AuthUser.get_by_email(email))


def get_user_by_jwt(token=None):
    """
    Return the AuthUser associated to the token, otherwise it will return None.
    If token is not provided, it will pull it from the headers: Authorization

    Exception:
    Along with AuthError, it may
    :param token:
    :return: AuthUser
    """

    if not token:
        if not 'Authorization' in request.headers:
            raise exceptions.AuthError("Missing Authorization Bearer in headers")
        data = request.headers['Authorization'].encode('ascii', 'ignore')
        token = str.replace(str(data), 'Bearer ', '').strip()

    secret_key = get_jwt_secret()

    s = utils.unsign_jwt(token=token,
                         secret_key=secret_key,
                         salt=get_jwt_salt())
    if "id" not in s:
        raise exceptions.AuthError("Invalid Authorization Bearer Token")

    return get_user_by_id(int(s["id"]))


def get_user_by_action_token(action, token):
    """
    Get the user by action token
    :param action: str
    :param token: str
    :return: AuthUser
    """
    data = utils.unsign_url_safe(token,
                                 secret_key=get_jwt_secret(),
                                 salt=action)
    if data is None:
        raise exceptions.AuthError("Invalid Token")
    return get_user_by_id(int(data))


def authenticate(username, password):
    """
    To authenticate a user with user and password
    *** authenticate doesn't create a session. To create a session, 
    use login_user
    :param username: 
    :param password: 
    :return: UserModel
    """
    user = models.AuthUser.get_by_username(username)
    return _user(user) if user and user.password_matched(password) else None


def authenticate_social_login(provider, social_id):
    """
    To authenticate with social login
    :param provider:
    :param social_id:
    :return: UserModel
    """
    user = models.AuthUserSocialLogin.get_user(provider, social_id)
    return _user(user) if user else None


def login_user(user):
    """
    Login and create a session
    :param user:
    :return:
    """

    def cb():
        if user:
            if __options__.get(
                    "require_email_verification") and not user.email_verified:
                raise exceptions.VerifyEmailError()
            if flask_login.login_user(user):
                user.update(last_login_at=utc_now())
                return user
        return None

    return signals.user_login(cb)


#
class UserModel(flask_login.UserMixin):
    def __init__(self, user):
        self.user = user.user if isinstance(user, self.__class__) else user
        self.user_salt = "USER:%s" % self.user.id

    def __getattr__(self, item):
        return getattr(self.user, item)

    # ------ FLASK-LOGIN REQUIRED METHODS ----------------------------------
    @property
    def is_active(self):
        return self.active

    # ---------- END FLASK-LOGIN REQUIREMENTS ------------------------------

    def change_username(self, username):
        """
        Change user's login email
        :param user: AuthUser
        :param email:
        :return:
        """

        def cb():

            if self.login_method == "username" and "@" in username:
                raise exceptions.AuthError(_("Username can't be an email"))
            elif self.login_method == "email" and "@" not in username:
                raise exceptions.AuthError(_("Invalid email login"))
            if "@" in username:
                if not utils.is_email_valid(username):
                    raise exceptions.AuthError("Email address invalid")
            elif not utils.is_username_valid(username):
                raise exceptions.AuthError("Username invalid")

            # Change both email and
            if self.login_method == "email":
                if not models.AuthUser.get_by_username(username) \
                        and not models.AuthUser.get_by_email(username):
                    self.user.change_username(username)
                    self.user.change_email(username)
            else:
                self.user.change_username(username)
            return username

        return signals.user_update(self, ACTIONS["USERNAME"], cb)

    def change_email(self, email):
        """
        Change user's login email
        :param user: AuthUser
        :param email:
        :return:
        """

        def cb():
            if not utils.is_email_valid(email):
                raise exceptions.AuthError("Email address invalid")
            self.user.change_email(email)
            return email

        return signals.user_update(self, ACTIONS["EMAIL"], cb,
                                   {"email": self.email})

    def update_info(self, _action=None, **kwargs):
        """
        UPdate info
        :param user:
        :param email:
        :return:
        """

        def cb():
            kwargs.pop("email", None)
            kwargs.pop("username", None)
            kwargs.pop("password_hash", None)
            kwargs.pop("require_password_change", None)
            self.user.update(**kwargs)
            return kwargs

        _action = ACTIONS["UPDATE"] if _action is None else _action
        return signals.user_update(self, _action, cb, data=self.to_dict())

    def change_password(self, password):
        """
        Change a user's password
        :param user:
        :param password:
        :param password_confirm:
        :return:
        """

        def cb():
            if not utils.is_password_valid(password):
                raise exceptions.AuthError("Invalid Password")
            self.user.change_password(password)
            return True

        return signals.user_update(self, ACTIONS["PASSWORD"], cb)

    def reset_password(self):
        """
        Return the new random password that has been reset
        :param user_login: AuthUserLogin
        :return: string - the new password
        """

        def cb():
            password = get_random_password()
            self.change_password(password)
            return password

        return signals.user_update(self, ACTIONS["PASSWORD"], cb)

    def change_status(self, status):
        """
        Change the user's status
        :param user:
        :param email:
        :return:
        """

        def cb():
            self.user.update(status=status)
            return status

        return signals.user_update(self, ACTIONS["STATUS"], cb,
                                   data={"status": self.status})

    def create_jwt(self, expires_in=None):
        """
        Create a secure timed JWT token that can be passed. It save the user id,
        which later will be used to retrieve the data

        :param user: AuthUser, the user's object
        :param expires_in: - time in second for the token to expire
        :return: string
        """
        s = utils.sign_jwt(data={"id": self.user.id},
                           secret_key=get_jwt_secret(),
                           salt=get_jwt_salt(),
                           expires_in=expires_in or get_jwt_ttl())
        return s

    def create_action_token(self, action, expires_in):
        """
        Create a url safe action token attached to the user
        :param action:
        :param expires_in:
        :return:
        """
        return utils.sign_url_safe(self.user.id,
                                   secret_key=get_jwt_secret(),
                                   salt=action,
                                   expires_in=expires_in)

    def sign_data(self, data, expires_in=None, url_safe=True):
        """
        To safely sign a user data. It will be signed with the user key
        :param data: mixed
        :param expires_in: The time for it to expire
        :param url_safe: bool. If true it will allow it to be passed in URL
        :return: str -  the token/signed data
        """
        if url_safe:
            return utils.sign_url_safe(data,
                                       secret_key=self.secret_key,
                                       salt=self.user_salt,
                                       expires_in=expires_in)
        else:
            return utils.sign_data(data,
                                   secret_key=self.secret_key,
                                   salt=self.user_salt,
                                   expires_in=expires_in)

    def unsign_data(self, data, url_safe=True):
        """
        Retrieve the signed data. If it is expired, it will throw an exception
        :param data: token/signed data
        :param url_safe: bool. If true it will allow it to be passed in URL
        :return: mixed, the data in its original form
        """
        if url_safe:
            return utils.unsign_url_safe(data,
                                         secret_key=self.secret_key,
                                         salt=self.user_salt)
        else:
            return utils.unsign_data(data,
                                     secret_key=self.secret_key,
                                     salt=self.user_salt)

    def signed_data_match(self, data, matched_data, url_safe=True):
        """
        See if a data matched a signed one
        :param data:
        :param matched_data:
        :param url_safe:
        :return:
        """
        try:
            u_data = self.unsign_data(data, url_safe=url_safe)
            return u_data == matched_data
        except Exception as e:
            return False

    def send_email(self, template, **kwargs):
        """
        To send email to user
        :param template:
        :param kwargs:
        :return:
        """
        user_data = {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email
        }
        kwargs.pop("user", None)
        send_mail(to=self.email, template=template, user=user_data, **kwargs)

    def send_password_reset(self, base_url=None, view_class=None, **kw):
        """
        Reset a password and send email
        :param user: AuthUser
        :param email: str - The auth user login email
        :param base_url: str - By default it will use the current url, base_url will allow custom url
        :param template: str - The email template
        :param method: str - token or email - The method to reset the password
        :param view_class: obj - The view instance of the login
        :param kwargs: Any data to pass
        :return:
        """

        view = view_class or views.auth.Login
        endpoint_reset = getattr(view, "reset_password")
        endpoint_login = getattr(view, "login")
        action = "reset-password"

        method = __options__.get("reset_password_method", "TOKEN")
        template = __options__.get("email_templates.reset_password",
                                   "auth/reset-password.txt")
        new_password = None

        if method.upper() == "TOKEN":
            expires_in = __options__.get("reset_password_token_ttl", 1)
            action_token = self.create_action_token(action, expires_in)
            signed_data = self.sign_data(action, expires_in=expires_in)
            url = _url_for_email(endpoint_reset,
                                 base_url=base_url,
                                 action_token=action_token,
                                 signed_data=signed_data)
        else:
            new_password = self.reset_password()
            url = _url_for_email(endpoint_login, base_url=base_url)

        self.send_email(template=template,
                        action={
                            "reset_method": method.upper(),
                            "url": url,
                            "new_password": new_password
                        },
                        data=kw)

    def send_verification_email(self, base_url=None, view_class=None, **kw):

        template = __options__.get("email_templates.verify_email",
                                   "auth/verify-email.txt")

        url = self._create_verify_email_token_url(base_url=base_url,
                                                  view_class=view_class)

        self.send_email(template=template,
                        action={
                            "url": url,
                        },
                        data=kw)

    def send_welcome_email(self, base_url=None, view_class=None, **kw):

        verify_email = __options__.get("require_email_verification") or False
        template = __options__.get("email_templates.welcome",
                                   "auth/welcome.txt")

        url = self._create_verify_email_token_url(base_url=base_url,
                                                  view_class=view_class)

        self.send_email(template=template,
                        action={
                            "url": url,
                            "require_email_verification": verify_email,
                        },
                        data=kw)

    def _create_verify_email_token_url(self, base_url=None, view_class=None):
        """
        To create a verify email token url
        :param user: (object) AuthUser
        :param base_url: a base_url to use instead of the native one
        :param view_class: (obj) the view class, to allow build the url
        :return: string
        """
        view = view_class or views.auth.Login
        endpoint = getattr(view, "verify_email")
        action = "verify-email"
        expires_in = __options__.get("verify_email_token_ttl") or (60 * 24)
        action_token = self.create_action_token(action, expires_in)
        signed_data = self.sign_data(action, expires_in=expires_in)
        url = _url_for_email(endpoint,
                             base_url=base_url,
                             action_token=action_token,
                             signed_data=signed_data)

        return url

    def add_social_login(self, provider, social_id):
        """
        Add social login to the current user
        :param provider:
        :param social_id:
        :return:
        """
        models.AuthUserSocialLogin.new(user=self,
                                       provider=provider,
                                       social_id=social_id)


# ------------------------------------------------------------------------------
# EMAIL SENDING


def _url_for_email(endpoint, base_url=None, **kw):
    """
    Create an external url_for by using a custom base_url different from the domain we
    are on
    :param endpoint:
    :param base_url:
    :param kw:
    :return:
    """
    base_url = base_url or config("MAIL_EXTERNAL_BASE_URL")
    _external = True if not base_url else False
    url = url_for(endpoint, _external=_external, **kw)
    if base_url and not _external:
        url = "%s/%s" % (base_url.strip("/"), url.lstrip("/"))
    return url


def session_set_require_password_change(change=True):
    session["auth:require_password_change"] = change


def session_get_require_password_change():
    return session.get("auth:require_password_change")


# ------------------------------------------------------------------------------
# CLI


class CLI(mocha.cli.Manager):

    def __init__(self, command, click):
        @command("auth:create-super-admin")
        @click.argument("email")
        def create_super_admin(email):
            """
            To create a super admin by providing the email address
            """
            print("-" * 80)
            print("Mocha Auth: Create Super Admin")
            print("Email: %s" % email)
            try:
                password = get_random_password()
                user = create_user(username=email,
                                   password=password,
                                   first_name="SuperAdmin",
                                   role="Superadmin")
                user.update(require_password_change=True)

                print("Password: %s" % password)
            except Exception as e:
                print("ERROR: %s" % e)

            print("Done!")

        @command("auth:reset-password")
        @click.argument("email")
        def reset_password(email):
            """
            To reset password by email
            """
            print("-" * 80)
            print("Mocha Auth: Reset Password")
            try:
                ul = models.AuthUserLogin.get_by_email(email)

                if not ul:
                    raise Exception("Email '%s' doesn't exist" % email)
                password = get_random_password()
                ul.change_password(password)
                ul.update(require_password_change=True)
                print("Email: %s" % email)
                print("New Password: %s" % password)
            except Exception as e:
                print("ERROR: %s" % e)

            print("Done!")

        @command("auth:user-info")
        @click.option("--email")
        @click.option("--id")
        def reset_password(email=None, id=None):
            """
            Get the user info by email or ID
            """
            print("-" * 80)
            print("Mocha Auth: User Info")
            print("")
            try:
                if email:
                    ul = models.AuthUserLogin.get_by_email(email)
                    if not ul:
                        raise Exception("Invalid Email address")
                    user_info = ul.user
                elif id:
                    user_info = models.AuthUser.get(id)
                    if not user_info:
                        raise Exception("Invalid User ID")

                k = [
                    ("ID", "id"), ("Name", "name"),
                    ("First Name", "first_name"),
                    ("Last Name", "last_name"), ("Signup", "created_at"),
                    ("Last Login", "last_login"),
                    ("Signup Method", "register_method"),
                    ("Status", "status")
                ]
                print("Email: %s" % user_info.get_email_login().email)
                for _ in k:
                    print("%s : %s" % (_[0], getattr(user_info, _[1])))

            except Exception as e:
                print("ERROR: %s" % e)

            print("")
            print("Done!")


# ---

from .decorators import *
