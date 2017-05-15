
import inspect
from mocha import (register_package,
                     get_config,
                     decorators as h_deco,
                     abort)


# `contrib` prefix is set so all templates in this package
# get accessed via `contrib/`
register_package(__package__, "contrib")


# ------------------------------------------------------------------------------

# ADMIN

ADMIN_LAYOUT = "contrib/admin/layout.jade"

ADMIN_TAG = "ADMIN"

def disable_admin(*a, **kw):
    abort(404)

# @admin
def admin(f):
    """
    @admin
    A decorator that turns a class into ADMIN
    """
    import auth.decorators as a_deco

    if not inspect.isclass(f):
        raise TypeError("@ADMIN expects a Mocha class")

    if get_config("ADMIN_ENABLED", True):

        # Index route
        index_route = get_config("ADMIN_INDEX_ROUTE", "/")

        # ROLES
        min_role = get_config("ADMIN_MIN_ACL", "ADMIN")
        role_name = "accepts_%s_roles" % min_role.lower()

        if not hasattr(a_deco, role_name):
            raise ValueError("Invalid ADMIN_MIN_ACL: %s" % min_role)

        getattr(a_deco, role_name)(f)
        a_deco.login_required(f)

        f._nav_tags = [ADMIN_TAG]
        layout = get_config("ADMIN_LAYOUT") or ADMIN_LAYOUT
        return h_deco.template(layout=layout)(f)

    else:
        f._nav_visible = False
        f.before_request = disable_admin
        return f

