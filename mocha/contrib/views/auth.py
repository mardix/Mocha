import datetime
import uuid
import arrow
import time
import exceptions
from flask_login import fresh_login_required
import logging
import exceptions
from flask_login import (LoginManager,
                         login_user,
                         current_user,
                         fresh_login_required)
from mocha import (Mocha,
                   _,
                   g,
                   models,
                   page_attr,
                   request,
                   redirect,
                   flash_success,
                   flash_error,
                   flash_info,
                   abort,
                   recaptcha,
                   decorators as h_deco,
                   exceptions as mocha_exc,
                   exceptions,
                   utils,
                   paginate,
                   views,
                   url_for,
                   session,
                   upload_file,
                   delete_file,
                   render,
                   )

import mocha.contrib
from mocha.contrib.auth import (ACTIONS,
                                oauth,
                                is_authenticated,
                                not_authenticated,
                                get_user_by_action_token,
                                session_set_require_password_change,
                                visible_to_managers,
                                authenticate,
                                authenticate_social_login,
                                login_user,
                                UserModel,
                                create_user,
                                exceptions,
                                __options__ as auth_options,
                                login_manager,
                                decorators as deco,
                                )
from flask_oauthlib.client import OAuthException

__options__ = utils.dict_dot({})


def has_oauth_request():
    return request.args.get("oauth") == "1" or request.form.get("oauth") == "1"


def set_oauth_session(data):
    data["ttl"] = time.time() + 600
    session["oauth_session"] = data


def get_oauth_session():
    if not has_oauth_request():
        return {}
    oas = session.get("oauth_session", {})
    return oas if oas.get("ttl", 0) > time.time() else {}


def delete_oauth_session():
    del session["oauth_session"]


def main(**kwargs):
    options = kwargs.get("options", {})
    nav_title_partial = "AuthAccount/nav_title_partial.html"
    nav_kwargs = kwargs.get("nav_menu", {})
    verify_email = options.get("verify_email") or False

    # @render.nav(
    #     title=nav_kwargs.pop("title", "My Account") or "My Account",
    #     visible=is_authenticated,
    #     css_id=nav_kwargs.pop("css_id", "auth-account-menu"),
    #     css_class=nav_kwargs.pop("css_class", "auth-account-menu"),
    #     align_right=nav_kwargs.pop("align_right", True),
    #     title_partial=nav_kwargs.pop("title_partial", nav_title_partial),
    #     **nav_kwargs)


class Login(Mocha):
    registration_methods = ["username", "email", "oauth"]

    @classmethod
    def _register(cls, app, **kwargs):

        __options__.setdefault("login_view", "main.Index:index")
        __options__.setdefault("logout_view", "main.Index:index")
        __options__.setdefault("login_message", "Please log in to access this page.")
        __options__.setdefault("login_message_category", "info")
        __options__.setdefault("allow_login", True)
        __options__.setdefault("allow_registration", True)
        __options__.setdefault("registration_methods", cls.registration_methods)
        __options__.setdefault("registration_full_name", False)
        __options__.setdefault("require_email_verification", False)

        # validate registration methods
        reg_meth = []
        if not isinstance(__options__.get("registration_methods"), list):
            __options__["registration_methods"] = cls.registration_methods
        for r in __options__.get("registration_methods"):
            if r in cls.registration_methods:
                reg_meth.append(r)
        __options__["registration_methods"] = reg_meth

        if not reg_meth:
            __options__["allow_registration"] = False

        reg_methods = __options__["registration_methods"]
        __options__["registration_email"] = "email" in reg_methods
        __options__["registration_username"] = "username" in reg_methods
        __options__["registration_oauth"] = "oauth" in reg_methods

        # Nav Title
        nav = __options__.get("login.nav", {})
        nav.setdefault("title", None)
        nav.setdefault("order", 100)
        nav.setdefault("position", "right")
        nav.setdefault("title", _("Account"))
        nav["visible"] = not_authenticated

        render.nav.add(nav.pop("title"), cls, **nav)

        # Route
        kwargs["base_route"] = __options__.get("login.route", "/")

        # Set auth options
        auth_options.update(__options__)

        # Login Manager
        login_manager.login_view = "auth.Login:login"
        login_manager.login_message = __options__.get("login_message")
        login_manager.login_message_category = __options__.get("login_message_category")

        super(cls, cls)._register(app, **kwargs)

        app.config["CONTRIB_AUTH_ADMIN_DATE_FORMAT"] = "MM/DD/YYYY hh:mm a"

    @render.nav("Login", visible=not_authenticated)
    @request.post_get
    @render.template("contrib/auth/Login/login.jade")
    @deco.logout_user
    def login(self):
        if not __options__.get("allow_login"):
            abort(403, "Login is not allowed. Contact admin if it's a mistake")

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            try:
                if not username or not password:
                    raise mocha_exc.AppError("Email/Username or Password is empty")

                user = authenticate(username=username, password=password)
                if not user:
                    raise mocha_exc.AppError("Email or Password is invalid")

                login_user(user)

                # if user.require_password_change is True:
                #     flash_info("Password change is required")
                #     session_set_require_password_change(True)
                # return redirect(views.auth.Account.account_settings, edit_password=1)

                return redirect(request.form.get("next") or __options__.get("login_view"))

            except exceptions.VerifyEmailError as ve:
                return redirect(self.login, username=username, v="1")
            except (mocha_exc.AppError, exceptions.AuthError) as ae:
                flash_error(str(ae))
            except Exception as e:
                logging.exception(e)
                flash_error("Unable to login")

            return redirect(self.login, next=request.form.get("next"))

        page_attr("Login")
        return {
            "username": request.args.get("username"),
            "login_url_next": request.args.get("next", ""),
            "allow_registration": __options__.get("allow_registration"),
            "show_verification_message": True if request.args.get("v") == "1" else False
        }

    @render.nav("Register", visible=not_authenticated())
    @request.post_get
    @deco.logout_user
    @render.template("contrib/auth/Login/register.jade")
    def register(self):
        """ Registration """

        if not __options__.get("allow_registration"):
            abort(403, "Registration is not allowed. Contact admin if it's a mistake")

        page_attr("Register")

        if request.method == "POST":
            try:
                if not recaptcha.verify():
                    raise mocha_exc.AppError("Invalid Security code")

                email = request.form.get("email", "").strip()
                username = request.form.get("username", "").strip()
                password = request.form.get("password", "").strip()
                password_confirm = request.form.get("password_confirm", "").strip()
                first_name = request.form.get("first_name", "").strip()
                last_name = request.form.get("last_name", "").strip()

                with_oauth = request.form.get("with_oauth") == "1"
                oauth_provider = request.form.get("oauth_provider")
                oauth_user_id = request.form.get("oauth_user_id")

                login_method = None

                # Require username and email
                if __options__.get("registration_username"):
                    if "@" in username:
                        raise exceptions.AuthError(_("Username can't be an email"))
                    if not utils.is_email_valid(email):
                        raise exceptions.AuthError(_("Invalid email address"))
                    login_method = "username"

                # Require only email. Email will be used as username and email
                elif __options__.get("registration_email"):
                    if not utils.is_email_valid(username):
                        raise exceptions.AuthError(_("Invalid email address"))
                    email = username
                    login_method = "email"

                if not first_name:
                    raise mocha_exc.AppError(
                        _("First Name or Name is required"))
                elif not password or password != password_confirm:
                    raise mocha_exc.AppError(_("Passwords don't match"))

                if not login_method:
                    raise exceptions.AuthError(_("Registration is disabled"))

                user = create_user(username=username,
                                   password=password,
                                   email=email,
                                   first_name=first_name,
                                   last_name=last_name,
                                   login_method=login_method)

                # WITH OAUTH, we can straight up login user
                if with_oauth and oauth_provider and oauth_user_id:
                    user.add_social_login(oauth_provider, oauth_user_id)
                    login_user(user)
                    return redirect(request.form.get(
                        "next") or views.auth.Account.account_settings)

                if __options__.get("require_email_verification"):
                    user.send_welcome_email(view_class=self)
                    flash_success(_("Please check your email. We've sent you a message"))

                return redirect(
                    request.form.get("next") or __options__.get("login_view"))

            except (mocha_exc.AppError, exceptions.AuthError) as ex:
                flash_error(str(ex))
            except Exception as e:
                logging.exception(e)
                flash_error("Unable to register")
            return redirect(self.register, next=request.form.get("next"))

        return {
            "reg_email": __options__.get("registration_email"),
            "reg_username": __options__.get("registration_username"),
            "reg_social": __options__.get("registration_social"),
            "reg_full_name": __options__.get("registration_full_name"),
            "login_url_next": request.args.get("next", ""),

            "with_oauth": has_oauth_request(),
            "oauth_provider": get_oauth_session().get("provider"),
            "oauth_user_id": get_oauth_session().get("user_id"),
            "email": get_oauth_session().get("email") or "",
            "name": get_oauth_session().get("name") or "",
        }

    def _register_oauth_session_user(self, user):
        """
        Add the
        :param user:
        :return:
        """
        oauth_session = get_oauth_session()
        if oauth_session:
            if "provider" in oauth_session and "user_id" in oauth_session:
                user.add_social_login(provider=oauth_session.get("provider"),
                                      social_id=oauth_session.get("user_id"))
        delete_oauth_session()

    @render.nav("Lost Password")
    @request.post_get
    @deco.logout_user
    @render.template("contrib/auth/Login/lost_password.jade")
    def lost_password(self):

        if not __options__.get("allow_login"):
            abort(403, "Login is not allowed. Contact admin if it's a mistake")

        page_attr("Lost Password")

        if request.method == "POST":
            username = request.form.get("username")
            user = models.AuthUser.get_by_username(username)
            if user:
                user = UserModel(user)
                user.send_password_reset(view_class=self)
                flash_success("A new password has been sent to '%s'" % user.email)
                return redirect(self.login)
            else:
                flash_error("Invalid login")
                return redirect(self.lost_password)

    @render.nav("Reset Password", visible=False)
    @request.route("/reset-password/<action_token>/<signed_data>/", methods=["POST", "GET"])
    @deco.logout_user
    @render.template("contrib/auth/Login/reset_password.jade")
    def reset_password(self, action_token, signed_data):
        """Reset the user password. It was triggered by LOST-PASSWORD """
        try:
            action = "reset-password"
            user = get_user_by_action_token(action, action_token)
            if not user or not user.signed_data_match(signed_data, action):
                raise mocha_exc.AppError("Verification Invalid!")

            if request.method == "POST":
                password = request.form.get("password", "").strip()
                password_confirm = request.form.get("password_confirm",
                                                    "").strip()
                if not password or password != password_confirm:
                    raise exceptions.AuthError(
                        "Password is missing or passwords don't match")

                user.change_password(password)
                user.set_email_verified(True)
                session_set_require_password_change(False)
                flash_success("Password updated successfully!")
                return redirect(__options__.get("login_view") or self.login)

            return {"action_token": action_token, "signed_data": signed_data}

        except (mocha_exc.AppError, exceptions.AuthError) as ex:
            flash_error(str(ex))
        except Exception as e:
            logging.exception(e)
            flash_error("Unable to reset password")
        return redirect(self.login)

    @deco.login_not_required
    @request.route("/verify-email/<action_token>/<signed_data>/")
    @deco.logout_user
    @render.template("contrib/auth/Login/verify_email.jade")
    def verify_email(self, action_token, signed_data):
        """ Verify email account, in which a link was sent to """
        try:
            action = "verify-email"
            user = get_user_by_action_token(action, action_token)
            if not user or not user.signed_data_match(signed_data, action):
                raise mocha_exc.AppError("Verification Invalid!")
            else:
                user.set_email_verified(True)
                flash_success("Account verified. You can now login")
                username = user.username
                if user.login_method == "email":
                    username = user.email

                return redirect(self.login, username=username)
        except Exception as e:
            logging.exception(e)
            flash_error("Verification Failed!")
        return redirect(self.login)

    @render.nav("Confirm Email", visible=False)
    @request.post_get
    @deco.logout_user
    @render.template("contrib/auth/Login/reset_email_verification.jade")
    def request_email_verification(self):
        """"""
        if not __options__.get("verify_email"):
            return redirect(self.login)

        if request.method == "POST":
            email = request.form.get("email")
            if email and utils.is_email_valid(email):
                user = models.AuthUser.get_by_email(email)
                if user:
                    if not user.email_verified:
                        send_email_verification_email(user, view_class=self)
                        flash_success(
                            "A verification email has been sent to %s" % email)
                    else:
                        flash_success("Your account is already verified")
                    return redirect(self.login, email=email)
            flash_error("Invalid account")
            return redirect(self.request_email_verification, email=email)

        page_attr("Request Email Verification")
        return {
            "email": request.args.get("email"),
        }

    @render.nav("Logout", visible=False)
    @request.get
    @deco.logout_user
    def logout(self):
        session_set_require_password_change(False)
        return redirect(__options__.get("logout_view") or self.login)

    @render.json
    @request.route("/oauth-connect/<provider>/<action>/", methods=["GET", "POST"])
    def oauth_connect(self, provider, action):
        """
        This endpoint doesn't check if user is logged in, because it has two functions

        1. If the user is not logged in, it will try to signup the user
            - if the social info exist, it will login
            - not, it will create a new account and proceed
        2. If user is logged in, it will try to create a social login entry with
            the current user

        **** This methods doesn't save the user token, it only retrieves the ID
              to login or ID, name, email if signing up

        :param provider:
        :param action: connect|authorized|
            - connect: to connect to the endpoint
            - authorized, when coming back
        """
        valid_actions = ["connect", "authorized", "test"]

        _redirect = views.auth.Account.account_settings if is_authenticated() else self.login

        if action not in valid_actions \
                or "oauth" not in __options__.get("registration_methods") \
                or not __options__.get("allow_registration") \
                or not hasattr(oauth, provider):
            return redirect(_redirect)

        client = getattr(oauth, provider)
        params = client.__params__
        me_args = params.get("me")
        user_id = params.get("user_id")
        oauth_user_id = None
        oauth_name = None
        oauth_email = None

        if action == "test":
            session_data = {
                "provider": "ensure",
                "user_id": "1234",
                "name": "Mardix",
                "email": "mardix@email.com",
            }
            set_oauth_session(session_data)
            return redirect(url_for(self.register, oauth=1))

        if action == "connect":
            _next = request.args.get('next')
            authorized_url = url_for(self,
                                     provider=provider,
                                     action="authorized",
                                     next=_next or request.referrer or None,
                                     _external=True)
            return client.authorize(callback=authorized_url)
        elif action == "authorized":
            resp = client.authorized_response()
            if resp is None:
                pass
            elif isinstance(resp, OAuthException):
                flash_error("Access Denied")
            else:
                if not me_args:
                    oauth_user_id = resp.get(user_id)
                else:
                    me = client.get(me_args)

        if action == "authorized" and oauth_user_id:
            if is_authenticated():
                try:
                    # Add social login to current_user
                    current_user.add_social_login(provider=provider,
                                                  social_id=oauth_user_id)
                    flash_success(
                        "You can now login with your %s account" % provider.upper())
                except Exception as e:
                    logging.exception(e)
                return redirect(views.auth.Account.account_settings)

            # User not logged in
            else:
                # Existing user
                user = authenticate_social_login(provider, oauth_user_id)
                if user:
                    login_user(user)
                    return redirect(request.args.get("next") or __options__.get(
                        "login_view"))

                # New User
                else:
                    session_data = {
                        "provider": provider,
                        "user_id": oauth_user_id,
                        "name": oauth_name,
                        "email": oauth_email,
                    }
                    set_oauth_session(session_data)

        else:
            return redirect(_redirect)

        return {
            "action": action,
            "provider": provider,
            "authorized_url": ""

        }

        return redirect(_redirect)


@deco.login_required
class Account(Mocha):
    @classmethod
    def _register(cls, app, **kwargs):

        # Nav
        nav = __options__.get("account.nav", {})
        nav.setdefault("title", None)
        nav.setdefault("order", 100)
        nav["visible"] = is_authenticated
        nav["position"] = "right"
        nav["tags"] = ["default", "ADMIN"]
        title = nav.pop("title") or _("My Account")

        # Custom Nav Title
        # Since Title can also be a callback function
        # We can do some customization to display a more fun account menu
        # Specially in the top nav
        custom_nav_title = __options__.get("account.custom_nav_title")
        if __options__.get("account.set_custom_nav_title") and custom_nav_title:
            def custom_nav():
                if is_authenticated():
                    return custom_nav_title.format(USER_NAME=current_user.name,
                                                   USER_EMAIL=current_user.login_email,
                                                   USER_PROFILE_IMAGE_URL=current_user.profile_image_url)

            title = custom_nav

        # Set the nav title
        render.nav.add(title, cls, **nav)

        # Route
        kwargs["base_route"] = __options__.get("account.route", "/account/")

        super(cls, cls)._register(app, **kwargs)

    def _assert_current_password(self):
        """Assert the password to make sure it matches the current user """
        password = request.form.get("current_password")
        if not current_user.password_matched(password):
            raise exceptions.AuthError("Invalid password")

    @render.nav("Logout", endpoint="auth.Login:logout", order=100)
    def _(self):
        pass

    @render.nav("Account Settings", order=1)
    @render.template("contrib/auth/Account/account_settings.jade")
    def account_settings(self):
        page_attr("Account Info")
        return {}

    @request.post
    def change_username(self):
        """Update the login email"""
        try:
            self._assert_current_password()
            username = request.form.get("username")
            current_user.change_username(username)
            flash_success(_("Login changed successfully!"))
        except exceptions.AuthError as ex:
            flash_error(str(ex))
        except Exception as e:
            logging.exception(e)
            flash_error(_("Unable to change username"))

        redirect_url = request.form.get("redirect") or self.account_settings
        return redirect(redirect_url)

    @request.post
    def change_email(self):
        """Update the login email"""
        try:
            self._assert_current_password()
            email = request.form.get("email")
            current_user.change_email(email)
            flash_success(_("Email changed successfully!"))
        except exceptions.AuthError as ex:
            flash_error(str(ex))
        except Exception as e:
            logging.exception(e)
            flash_error(_("Unable to change email"))

        redirect_url = request.form.get("redirect") or self.account_settings
        return redirect(redirect_url)

    @request.post
    def change_password(self):
        """Change password """
        try:
            self._assert_current_password()
            password = request.form.get("password", "").strip()
            password_confirm = request.form.get("password_confirm", "").strip()
            if password != password_confirm:
                raise exceptions.AuthError("Passwords don't match")
            current_user.change_password(password)
            flash_success(_("Your password updated successfully!"))
        except exceptions.AuthError as ex:
            flash_error(str(ex))
        except Exception as e:
            logging.exception(e)
            flash_error(_("Unable to update password"))

        redirect_url = request.form.get("redirect") or self.account_settings
        return redirect(redirect_url)

    @request.post
    def update_info(self):
        """Update basic account info"""
        try:
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            delete_photo = request.form.get("delete_photo", "").strip()
            file = request.files.get("file")
            kwargs = {
                "first_name": first_name,
                "last_name": last_name
            }

            if file:
                prefix = __options__.get("profile_image_dir",
                                         "profile.imgs").replace("/", "")
                prefix += "/"

                profile_image = upload_file(None, file,
                                            name=utils.guid(),
                                            prefix=prefix,
                                            public=True,
                                            extensions=[
                                                "jpg", "jpeg",
                                                "png", "gif"])
                kwargs["profile_image"] = profile_image

            if delete_photo == "1":
                if current_user.profile_image is not None:
                    delete_file(current_user.profile_image)
                    kwargs["profile_image"] = None

            if kwargs:
                current_user.update_info(**kwargs)
            flash_success(_("Info updated successfully!"))
        except exceptions.AuthError as ex:
            flash_error(str(ex))
        except Exception as e:
            logging.exception(e)
            flash_error(_("Unable to update info"))

        redirect_url = request.form.get("redirect") or self.account_settings
        return redirect(redirect_url)

    @render.nav("Setup Login", visible=False)
    @request.post_get
    @render.template("contrib/auth/Account/setup_login.jade")
    def setup_login(self):
        return
        user_login = current_user.user_login("email")
        if user_login:
            return redirect(self.account_settings)

        if request.IS_POST:
            try:
                email = request.form.get("email")
                password = request.form.get("password")
                password2 = request.form.get("password2")

                if not password.strip() or password.strip() != password2.strip():
                    raise exceptions.AuthError("Passwords don't match")
                else:
                    new_login = models.AuthUserLogin.new(login_type="email",
                                                         user_id=current_user.id,
                                                         email=email,
                                                         password=password.strip())
                    if verify_email:
                        send_registration_welcome_email(new_login.user)
                        flash_success(
                            "A welcome email containing a confirmation link has been sent to your email")
                        return redirect(self.account_settings)
            except exceptions.AuthError as ex:
                flash_error(ex.message)
                return redirect(self.setup_login)
            except Exception as e:
                logging.exception(e)
                flash_error("Unable to setup login")
                return redirect(self)


@deco.accepts_manager_roles
@mocha.contrib.admin
class Admin(Mocha):
    @classmethod
    def _register(cls, app, **kwargs):

        # Nav
        nav = __options__.get("admin.nav", {})
        nav.setdefault("title", None)
        nav.setdefault("order", 100)
        nav["visible"] = visible_to_managers
        title = nav.pop("title") or _("User Admin")
        render.nav.add(title, cls, **nav)

        # Route
        kwargs["base_route"] = __options__.get("admin.route", "/admin/users/")

        super(cls, cls)._register(app, **kwargs)

    def _confirm_password(self):
        user_login = current_user.user_login("email")
        password = request.form.get("confirm-password")
        if not user_login.password_matched(password):
            raise exceptions.AuthError("Invalid password")
        return True

    @classmethod
    def _user_roles_options(cls):
        _r = models.AuthUserRole.query() \
            .filter(models.AuthUserRole.level <= current_user.role.level) \
            .order_by(models.AuthUserRole.level.desc())
        return [(r.id, r.name.upper()) for r in _r]

    @render.nav("All Users")
    @render.template("contrib/auth/Admin/index.jade")
    def index(self):

        page_attr("All Users")

        include_deleted = True if request.args.get("include-deleted") == "y" else False
        username = request.args.get("username")
        name = request.args.get("name")
        email = request.args.get("email")
        role = request.args.get("role")
        sorting = request.args.get("sorting", "first_name__asc")
        users = models.AuthUser.query(include_deleted=include_deleted)
        users = users.join(models.AuthUserRole).filter(models.AuthUserRole.level <= current_user.role.level)

        if username:
            users = users.filter(models.AuthUser.username.contains(username))
        if email:
            users = users.filter(models.AuthUser.email.contains(email))
        if name:
            users = models.AuthUser.search_by_name(users, name)
        if role:
            users = users.filter(models.AuthUser.role_id == int(role))
        if sorting and "__" in sorting:
            col, dir = sorting.split("__", 2)
            if dir == "asc":
                users = users.order_by(getattr(models.AuthUser, col).asc())
            else:
                users = users.order_by(getattr(models.AuthUser, col).desc())

        users = paginate(users)

        sorting = [("username__asc", "Username ASC"),
                   ("username__desc", "Username DESC"),
                   ("email__asc", "Email ASC"),
                   ("email__desc", "Email DESC"),
                   ("first_name__asc", "First Name ASC"),
                   ("first_name__desc", "First Name DESC"),
                   ("last_name__asc", "Last Name ASC"),
                   ("last_name__desc", "Last Name DESC"),
                   ("created_at__asc", "Signup ASC"),
                   ("created_at__desc", "Signup DESC"),
                   ("last_login__asc", "Login ASC"),
                   ("last_login__desc", "Login DESC")
                   ]

        return dict(user_roles_options=self._user_roles_options(),
                    sorting_options=sorting,
                    users=users,
                    search_query={
                        "include-deleted": request.args.get("include-deleted", "n"),
                        "role": int(request.args.get("role")) if request.args.get("role") else "",
                        "status": request.args.get("status"),
                        "name": request.args.get("name", ""),
                        "username": request.args.get("username", ""),
                        "email": request.args.get("email", ""),
                        "sorting": request.args.get("sorting")
                        }
                    )

    @render.nav("User Info", visible=False)
    @render.template("contrib/auth/Admin/info.jade")
    def info(self, id):
        page_attr("User Info")
        user = models.AuthUser.get(id, include_deleted=True)
        if not user:
            abort(404, "User doesn't exist")

        if current_user.role.level < user.role.level:
            abort(403, "Not enough rights to access this user info")

        return {
            "user": user,
            "user_roles_options": self._user_roles_options()
        }

    @request.post
    def action(self):
        id = request.form.get("id")
        action = request.form.get("action")

        try:
            user = models.AuthUser.get(id, include_deleted=True)

            if not user:
                abort(404, "User doesn't exist or has been deleted!")
            if current_user.role.level < user.role.level:
                abort(403, "Not enough power level to update this user info")

            user = UserModel(user)

            if current_user.id != user.id:
                if action == "activate":
                    user.change_status("active")
                    flash_success("User has been ACTIVATED")
                elif action == "deactivate":
                    user.change_status("suspended")
                    flash_success("User is now SUSPENDED")
                elif action == "delete":
                    user.change_status("deleted")
                    user.delete()
                    flash_success("User has been DELETED")
                elif action == "undelete":
                    user.change_status("suspended")
                    user.delete(False)
                    flash_success("User is now RESTORED / Use is now SUSPENDED")

            if action == "info":
                first_name = request.form.get("first_name")
                last_name = request.form.get("last_name")

                data = {}
                if first_name:
                    data["first_name"] = first_name
                if last_name:
                    data["last_name"] = last_name

                if current_user.id != user.id:
                    user_role = request.form.get("user_role")
                    _role = models.AuthUserRole.get(user_role)
                    if not _role:
                        raise exceptions.AuthError("Invalid ROLE selected")
                    data["role"] = _role
                if data:
                    user.update_info(ACTIONS["UPDATE"], **data)
                    flash_success("User info updated successfully!")

            elif action == "change-username":
                username = request.form.get("username")
                user.change_username(username)
                flash_success("Username changed successfully!")

            elif action == "change-email":
                email = request.form.get("email")
                user.change_email(email)
                flash_success("Email changed successfully!")

            elif action == "change-password":
                password = request.form.get("password", "").strip()
                password_confirm = request.form.get("password_confirm", "").strip()
                if password != password_confirm:
                    raise exceptions.AuthError("Invalid passwords")
                user.change_password(password)
                flash_success("Password changed successfully!")

            elif action == "email-reset-password":
                user.send_password_reset()
                flash_success("Password reset was sent to email")

            elif action == "email-account-verification":
                user.send_verification_email()
                flash_success("Email verification was sent")

            elif action == "reset-secret-key":
                user.reset_secret_key()
                flash_success("The account's secret key has been changed")

            elif action == "delete-profile-image":
                if user.profile_image is not None:
                    delete_file(user.profile_image)
                    user.update_info(profile_image=None,
                                     _action=ACTIONS["PROFILE_IMAGE"])
                    flash_success("Profile Image deleted successfully!")

        except exceptions.AuthError as ae:
            flash_error(ae.message)
        return redirect(self.info, id=id)

    @request.post
    def create(self):
        try:

            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "").strip()
            password_confirm = request.form.get("password_confirm", "").strip()

            user_role = request.form.get("user_role")
            role = models.AuthUserRole.get(user_role)
            if not role:
                raise exceptions.AuthError("Invalid ROLE selected")
            if not first_name:
                raise mocha_exc.AppError("First Name is required")
            elif not password or password != password_confirm:
                raise mocha_exc.AppError("Passwords don't match")

            user = create_user(username=email,
                               password=password,
                               first_name=first_name,
                               last_name=last_name,
                               login_method="email",
                               role=role.name)

            if user:
                flash_success("New account created successfully!")
                return redirect(self.info, id=user.id)
            else:
                raise exceptions.AuthError("Account couldn't be created")
        except exceptions.AuthError as ae:
            flash_error(ae.message)

        return redirect(self.index)

    @render.nav("User Roles", order=2)
    @request.post_get
    @render.template("contrib/auth/Admin/roles.jade")
    def roles(self):
        """
        Only admin and super admin can add/remove roles
        RESTRICTED ROLES CAN'T BE CHANGED
        """
        roles_max_range = 11
        if request.IS_POST:
            try:
                id = request.form.get("id")
                name = request.form.get("name")
                level = request.form.get("level")
                action = request.form.get("action")
                if name and level:
                    level = int(level)
                    name = name.upper()
                    _levels = [r[0] for r in models.AuthUserRole.ROLES]
                    _names = [r[1] for r in models.AuthUserRole.ROLES]
                    if level in _levels or name in _names:
                        raise exceptions.AuthError(
                            "Can't modify PRIMARY Roles - name: %s, level: %s " % (
                                name, level))
                    else:
                        if id:
                            role = models.AuthUserRole.get(id)
                            if role:
                                if action == "delete":
                                    role.update(level=0)  # Free the role
                                    role.delete()
                                    flash_success(
                                        "Role '%s' deleted successfully!" % role.name)
                                elif action == "update":
                                    if role.level != level and models.AuthUserRole.get_by_level(
                                            level):
                                        raise exceptions.AuthError(
                                            "Role Level '%s' exists already" % level)
                                    elif role.name != models.AuthUserRole.slug_name(
                                            name) and models.AuthUserRole.get_by_name(
                                        name):
                                        raise exceptions.AuthError(
                                            "Role Name '%s'  exists already" % name)
                                    else:
                                        role.update(name=name, level=level)
                                        flash_success(
                                            "Role '%s (%s)' updated successfully" % (
                                                name, level))
                            else:
                                raise exceptions.AuthError("Role doesn't exist")
                        else:
                            if models.AuthUserRole.get_by_level(level):
                                raise exceptions.AuthError(
                                    "New Role Level '%s' exists already" % level)
                            elif models.AuthUserRole.get_by_name(name):
                                raise exceptions.AuthError(
                                    "New Role Name '%s'  exists already" % name)
                            else:
                                models.AuthUserRole.new(name=name, level=level)
                                flash_success(
                                    "New Role '%s (%s)' addedd successfully" % (
                                        name, level))
            except exceptions.AuthError as ex:
                flash_error("%s" % ex.message)
            return redirect(self.roles)

        page_attr("User Roles")
        roles = models.AuthUserRole.query().order_by(
            models.AuthUserRole.level.desc())

        allocated_levels = [r.level for r in roles]
        # levels_options = [(l, l) for l in range(1, roles_max_range) if l not in allocated_levels]
        levels_options = [(l, l) for l in range(1, roles_max_range)]

        return {
            "roles": roles,
            "levels_options": levels_options
        }
