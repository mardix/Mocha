import functools
import flask_login
import signals
import inspect
from mocha import (utils,
                   abort,
                   request,
                   )
from mocha.core import apply_function_to_members
from . import (is_authenticated,
               not_authenticated,
               ROLES_ADMIN,
               ROLES_MANAGER,
               ROLES_CONTRIBUTOR,
               ROLES_MODERATOR,
               __options__,
               login_manager)


def login_required(func):
    """
    A wrapper around the flask_login.login_required.
    But it also checks the presence of the decorator: @login_not_required
    On a "@login_required" class, method containing "@login_not_required" will
    still be able to access without authentication
    :param func:
    :return:
    """
    if inspect.isclass(func):
        apply_function_to_members(func, login_required)
        return func
    else:
        @functools.wraps(func)
        def decorated_view(*args, **kwargs):
            if "login_not_required" not in utils.get_decorators_list(func) \
                    and not_authenticated():
                return login_manager.unauthorized()
            return func(*args, **kwargs)

        return decorated_view


def login_not_required(func):
    """
    Dummy decorator. @login_required will inspect the method
    to look for this decorator
    Use this decorator when you want do not require login in a "@login_required" class/method
    :param func:
    :return:
    """

    @functools.wraps(func)
    def decorated_view(*args, **kwargs):
        return func(*args, **kwargs)

    return decorated_view


def logout_user(f):
    """
    Decorator to logout user
    :param f:
    :return:
    """

    @functools.wraps(f)
    def deco(*a, **kw):
        signals.user_logout(lambda: flask_login.current_user)
        flask_login.logout_user()
        return f(*a, **kw)

    return deco


def require_verified_email(f):
    pass


def require_login_allowed(f):
    """
    Decorator to abort if login is not allowed
    :param f:
    :return:
    """

    @functools.wraps(f)
    def deco(*a, **kw):
        if not __options__.get("allow_login"):
            abort(403, "Login not allowed. Contact admin if it's a mistake")
        return f(*a, **kw)

    return deco


def require_register_allowed(f):
    """
    Decorator to abort if register is not allowed
    :param f:
    :return:
    """

    @functools.wraps(f)
    def deco(*a, **kw):
        if not __options__.get("allow_register"):
            abort(403, "Signup not allowed. Contact admin if it's a mistake")
        return f(*a, **kw)

    return deco


def require_social_login_allowed(f):
    """
    Decorator to abort if social login is not allowed
    :param f:
    :return:
    """

    @functools.wraps(f)
    def deco(*a, **kw):
        if not __options__.get("allow_social_login"):
            abort(403,
                  "Social login not allowed. Contact admin if it's a mistake")
        return f(*a, **kw)

    return deco


def accepts_roles(*roles):
    """
    A decorator to check if user has any of the roles specified

    @roles_accepted('superadmin', 'admin')
    def fn():
        pass
    """

    def wrapper(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if is_authenticated():
                if not flask_login.current_user.has_any_roles(*roles):
                    return abort(403)
            else:
                return abort(401)
            return f(*args, **kwargs)

        return wrapped

    return wrapper


def accepts_admin_roles(func):
    """
    Decorator that accepts only admin roles
    :param func:
    :return:
    """
    if inspect.isclass(func):
        apply_function_to_members(func, accepts_admin_roles)
        return func
    else:
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            return accepts_roles(*ROLES_ADMIN)(func)(*args, **kwargs)

        return decorator


def accepts_manager_roles(func):
    """
    Decorator that accepts only manager roles
    :param func:
    :return:
    """
    if inspect.isclass(func):
        apply_function_to_members(func, accepts_manager_roles)
        return func
    else:
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            return accepts_roles(*ROLES_MANAGER)(func)(*args, **kwargs)

        return decorator


def accepts_contributor_roles(func):
    """
    Decorator that accepts only contributor roles
    :param func:
    :return:
    """
    if inspect.isclass(func):
        apply_function_to_members(func, accepts_contributor_roles)
        return func
    else:
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            return accepts_roles(*ROLES_CONTRIBUTOR)(func)(*args, **kwargs)

        return decorator


def accepts_moderator_roles(func):
    """
    Decorator that accepts only moderator roles
    :param func:
    :return:
    """
    if inspect.isclass(func):
        apply_function_to_members(func, accepts_moderator_roles)
        return func
    else:
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            return accepts_roles(*ROLES_MODERATOR)(func)(*args, **kwargs)

        return decorator


def jwt_required(func):
    """
    Checks if the Authorization barer exists. Otherwise throw 401
    :param func:
    :return:
    """
    if inspect.isclass(func):
        apply_function_to_members(func, jwt_required)
        return func
    else:
        @functools.wraps(func)
        def deco(*a, **kw):
            if not "Authorization" in request.headers:
                abort(401, "Not Authorized")
            return func(*a, **kw)

        return deco
