# -*- coding: utf-8 -*-
"""
core.py

This is the Mocha core. it contains the classes and functions 

"""

import re
import os
import sys
import six
import arrow
import jinja2
import inspect
import logging
import werkzeug
import functools
from . import utils
import pkg_resources
import logging.config
from .__about__ import *
from . import exceptions
from .extras.mocha_db import MochaDB
from flask_assets import Environment
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.routing import (BaseConverter, parse_rule)
from flask import (Flask,
                   g,
                   render_template,
                   flash,
                   session,
                   make_response,
                   Response,
                   request as f_request,
                   abort,
                   url_for as f_url_for,
                   redirect as f_redirect)

# ------------------------------------------------------------------------------

__all__ = [
    "Mocha",
    "Brew",
    "db",
    "models",
    "views",
    "config",
    "get_env",
    "set_env",
    "get_app_env",
    "get_env_config",
    "page_attr",
    "flash_success",
    "flash_error",
    "flash_info",
    "flash_data",
    "get_flash_data",
    "init_app",
    "register_package",
    "register_models",
    "utc_now",
    "local_datetime",

    # For convenience when importing from mocha, but can use
    # the flask one
    "flash",
    "session",
    "request",
    "abort",
    "g",

    # They have been altered with extra functionalities
    "redirect",
    "url_for"
]

# Hold the current environment
__ENV__ = None

is_method = lambda x: inspect.ismethod if six.PY2 else inspect.isfunction

# Will hold all active class views
# It can be used for redirection etc
# ie: redirect(views.ContactPage.index)
views = type('', (), {})

# Will hold models from apps, or to be shared
# ie, set new model property -> models.MyNewModel = MyModel
# ie: use property -> models.MyNewModel.all()
# For convenience, use `register_models(**kw)` to register the models
# By default mocha will load all the application/models.py models
models = type('', (), {})

# Setup the DB
# upon initialization will use the right URL for it
# also, it exposes the db object to all modules
db = MochaDB()


def register_models(**kwargs):
    """
    Alias to register model
    :param kwargs:
    :return:
    """
    [setattr(models, k, v) for k, v in kwargs.items()]


def set_env(env):
    """
    Set the envrionment manually
    :param env:
    :return:
    """
    global __ENV__
    __ENV__ = env.lower().capitalize()


def get_env():
    """
    Return the Capitalize environment name
    It can be used to retrieve class base config
    Default: Development
    :returns: str Capitalized
    """
    if not __ENV__:
        env = os.environ["env"] if "env" in os.environ else "Dev"
        set_env(env)
    return __ENV__


def get_app_env():
    """
    if the app and the envi are passed in the command line as 'app=$app:$env'
    :return: tuple app, env
    """
    app, env = None, get_env()
    if "app" in os.environ:
        app = os.environ["app"].lower()
        if ":" in app:
            app, env = os.environ["app"].split(":", 2)
            set_env(env)
    return app, env


def get_env_config(config):
    """
    Return config class based based on the config
    :param config : Object - The configuration module containing the environment object
    """
    return getattr(config, get_env())


def init_app(kls):
    """
    To bind middlewares, plugins that needs the 'app' object to init
    Bound middlewares will be assigned on cls.init()
    """
    if not hasattr(kls, "__call__"):
        raise exceptions.MochaError("init_app: '%s' is not callable" % kls)
    Mocha._init_apps.add(kls)
    return kls


def register_package(pkg, prefix=None):
    """
    Allow to register an app packages by loading and exposing: templates, static,
    and exceptions for abort()

    Structure of package
        root
            | $package_name
                | __init__.py
                |
                | /templates
                    |
                    |
                |
                | /static
                    |
                    | assets.yml

    :param pkg: str - __package__
                    or __name__
                    or The root dir
                    or the dotted resource package (package.path.path,
                    usually __name__ of templates and static
    :param prefix: str - to prefix the template path
    """

    root_pkg_dir = pkg
    if not os.path.isdir(pkg) and "." in pkg:
        root_pkg_dir = pkg_resources.resource_filename(pkg, "")

    template_path = os.path.join(root_pkg_dir, "templates")
    static_path = os.path.join(root_pkg_dir, "static")

    logging.info("Registering App: " + pkg)
    if os.path.isdir(template_path):
        loader = jinja2.FileSystemLoader(template_path)
        if prefix:
            ploader = jinja2.PrefixLoader({
                prefix: loader
            })
            loader = ploader
        Mocha._template_paths.add(loader)

    if os.path.isdir(static_path):
        Mocha._static_paths.add(static_path)
        Mocha._add_asset_bundle(static_path)


def config(key, default=None):
    """
    Shortcut to access the application's config in your class
    :param key: The key to access
    :param default: The default value when None
    :returns mixed:
    """
    return Mocha._app.config.get(key, default) if Mocha._app else default


def page_attr(title=None, **kwargs):
    """
    Page Attr allows you to add page meta data in the request `g` context
    :params **kwargs:

    meta keys we're expecting:
        title (str)
        description (str)
        url (str) (Will pick it up by itself if not set)
        image (str)
        site_name (str) (but can pick it up from config file)
        object_type (str)
        keywords (list)
        locale (str)
        card (str)

        **Boolean By default these keys are True
        use_opengraph
        use_twitter
        use_googleplus
python
    """
    default = dict(
        title="",
        description="",
        url="",
        image="",
        site_name="",
        object_type="article",
        locale="",
        keywords=[],
        use_opengraph=True,
        use_googleplus=True,
        use_twitter=True,
        properties={}
    )
    meta = getattr(g, "__META__", default)
    if title:
        kwargs["title"] = title
    meta.update(**kwargs)
    setattr(g, "__META__", meta)


def flash_success(msg):
    """
    Alias to flash, but set a success message
    :param msg:
    :return:
    """
    return flash(msg, "success")


def flash_error(msg):
    """
    Alias to flash, but set an error message
    :param msg:
    :return:
    """
    return flash(msg, "error")


def flash_info(msg):
    """
    Alias to flash, but set an info message
    :param msg:
    :return:
    """
    return flash(msg, "info")


def flash_data(data):
    """
    Just like flash, but will save data
    :param data:
    :return:
    """
    session["_flash_data"] = data


def get_flash_data():
    """
    Retrieved
    :return: mixed
    """
    return session.pop("_flash_data", None)


def utc_now():
    """
    Return the utcnow arrow object
    :return: Arrow
    """
    return arrow.utcnow()


def local_datetime(utcdatetime, format=None, timezone=None):
    """
    Return local datetime based on the timezone
    It will automatically format the date. 
    To not format the date, set format=False
    
    :param utcdatetime: Arrow or string
    :param format: string of format or False
    :param timezone: string, ie: US/Eastern
    :return:
    """
    if utcdatetime is None:
        return None

    timezone = timezone or config("DATETIME_TIMEZONE", "US/Eastern")
    dt = utcdatetime.to(timezone) \
        if isinstance(utcdatetime, arrow.Arrow) \
        else arrow.get(utcdatetime, timezone)
    if format is False:
        return dt

    _ = config("DATETIME_FORMAT")
    format = _.get("default") or "MM/DD/YYYY" if not format else _.get(format)
    return dt.format(format)


def to_local_datetime(dt, tz=None):
    """
    DEPRECATED
    :param dt: 
    :param tz: 
    :return: 
    """
    return local_datetime(dt, tz)


def local_now():
    """
    DEPRECATED
    :return: 
    """
    return to_local_datetime(utc_now())


# ------------------------------------------------------------------------------
# Altered flask functions


def url_for(endpoint, **kw):
    """
    Mocha url_for is an alias to the flask url_for, with the ability of
    passing the function signature to build the url, without knowing the endpoint
    :param endpoint:
    :param kw:
    :return:
    """

    _endpoint = None
    if isinstance(endpoint, six.string_types):
        return f_url_for(endpoint, **kw)
    else:
        # self, will refer the caller method, by getting the method name
        if isinstance(endpoint, Mocha):
            fn = sys._getframe().f_back.f_code.co_name
            endpoint = getattr(endpoint, fn)

        if is_method(endpoint):
            _endpoint = _get_action_endpoint(endpoint)
            if not _endpoint:
                _endpoint = _build_endpoint_route_name(endpoint)
    if _endpoint:
        return f_url_for(_endpoint, **kw)
    else:
        raise exceptions.MochaError('Mocha `url_for` received an invalid endpoint')


def redirect(endpoint, **kw):
    """
    Redirect allow to redirect dynamically using the classes methods without
    knowing the right endpoint.
    Expecting all endpoint have GET as method, it will try to pick the first
    match, based on the endpoint provided or the based on the Rule map_url

    An endpoint can also be passed along with **kw

    An http: or https: can also be passed, and will redirect to that site.

    example:
        redirect(self.hello_world)
        redirect(self.other_page, name="x", value="v")
        redirect("https://google.com")
        redirect(views.ContactPage.index)
    :param endpoint:
    :return: redirect url
    """

    _endpoint = None

    if isinstance(endpoint, six.string_types):
        _endpoint = endpoint
        # valid for https:// or /path/
        # Endpoint should not have slashes. Use : (colon) to build endpoint
        if "/" in endpoint:
            return f_redirect(endpoint)
        else:
            for r in Mocha._app.url_map.iter_rules():
                _endpoint = endpoint
                if 'GET' in r.methods and endpoint in r.endpoint:
                    _endpoint = r.endpoint
                    break
    else:
        # self, will refer the caller method, by getting the method name
        if isinstance(endpoint, Mocha):
            fn = sys._getframe().f_back.f_code.co_name
            endpoint = getattr(endpoint, fn)

        if is_method(endpoint):
            _endpoint = _get_action_endpoint(endpoint)
            if not _endpoint:
                _endpoint = _build_endpoint_route_name(endpoint)
    if _endpoint:
        return f_redirect(url_for(_endpoint, **kw))
    else:
        raise exceptions.MochaError("Invalid endpoint")


def _get_action_endpoint(action):
    """
    Return the endpoint base on the view's action
    :param action:
    :return:
    """
    _endpoint = None
    if is_method(action):
        if hasattr(action, "_rule_cache"):
            rc = action._rule_cache
            if rc:
                k = list(rc.keys())[0]
                rules = rc[k]
                len_rules = len(rules)
                if len_rules == 1:
                    rc_kw = rules[0][1]
                    _endpoint = rc_kw.get("endpoint", None)
                    if not _endpoint:
                        _endpoint = _build_endpoint_route_name(action)
                elif len_rules > 1:
                    _prefix = _build_endpoint_route_name(action)
                    for r in Mocha._app.url_map.iter_rules():
                        if ('GET' in r.methods or 'POST' in r.methods) \
                                and _prefix in r.endpoint:
                            _endpoint = r.endpoint
                            break
    return _endpoint


def _build_endpoint_route_name(endpoint):
    is_class = inspect.isclass(endpoint)
    class_name = endpoint.im_class.__name__ if not is_class else endpoint.__name__
    method_name = endpoint.__name__

    cls = endpoint.im_class() \
        if (not hasattr(endpoint, "__self__") or endpoint.__self__ is None) \
        else endpoint.__self__

    return build_endpoint_route_name(cls, method_name, class_name)


class _RequestProxy(object):
    """
    A request proxy, that attaches some special attributes to the request object
    """

    @property
    def IS_GET(self):
        return f_request.method == "GET"

    @property
    def IS_POST(cls):
        return f_request.method == "POST"

    @property
    def IS_PUT(self):
        return f_request.method == "PUT"

    @property
    def IS_DELETE(self):
        return f_request.method == "DELETE"

    @classmethod
    def _accept_method(cls, methods, f):
        kw = {
            "append_method": True,
            "methods": methods
        }
        Mocha._bind_route_rule_cache(f, rule=None, **kw)
        return f

    @classmethod
    def get(cls, f):
        """ decorator to accept GET method """
        return cls._accept_method(["GET"], f)

    @classmethod
    def post(cls, f):
        """ decorator to accept POST method """
        return cls._accept_method(["POST"], f)

    @classmethod
    def post_get(cls, f):
        """ decorator to accept POST & GET method """
        return cls._accept_method(["POST", "GET"], f)

    @classmethod
    def delete(cls, f):
        """ decorator to accept DELETE method """
        return cls._accept_method(["DELETE"], f)

    @classmethod
    def put(cls, f):
        """ decorator to accept PUT method """
        return cls._accept_method(["PUT"], f)

    @classmethod
    def all(cls, f):
        """ decorator to accept ALL methods """
        return cls._accept_method(["GET", "POST", "DELETE", "PUT", "OPTIONS", "UPDATE"], f)


    @classmethod
    def options(cls, f):
        """ decorator to accept OPTIONS methods """
        return cls._accept_method(["OPTIONS"], f)


    @classmethod
    def route(cls, rule=None, **kwargs):
        """
        This decorator defines custom route for both class and methods in the view.
        It behaves the same way as Flask's @app.route

        on class:
            It takes the following args
                - rule: the root route of the endpoint
                - decorators: a list of decorators to run on each method

        on methods:
            along with the rule, it takes kwargs
                - endpoint
                - defaults
                - ...

        :param rule:
        :param kwargs:
        :return:
        """

        _restricted_keys = ["route", "decorators"]

        def decorator(f):
            if inspect.isclass(f):
                kwargs.setdefault("route", rule)
                kwargs["decorators"] = kwargs.get("decorators", []) + f.decorators
                setattr(f, "_route_extends__", kwargs)
                setattr(f, "base_route", kwargs.get("route"))
                setattr(f, "decorators", kwargs.get("decorators", []))
            else:
                if not rule:
                    raise ValueError("'rule' is missing in @route ")

                for k in _restricted_keys:
                    if k in kwargs:
                        del kwargs[k]

                Mocha._bind_route_rule_cache(f, rule=rule, **kwargs)
            return f

        return decorator


    def __getattr__(self, item):
        # Fall back to flask_request
        return getattr(f_request, item)


request = _RequestProxy()

# ------------------------------------------------------------------------------


class Mocha(object):
    decorators = []
    base_route = None
    route_prefix = None
    trailing_slash = True
    base_layout = "layouts/base.jade"
    template_markup = "jade"
    assets = None
    logger = None
    _ext = set()
    __special_methods = ["get", "put", "patch", "post", "delete", "index"]
    _installed_apps = []
    _app = None
    _init_apps = set()
    _template_paths = set()
    _static_paths = set()
    _asset_bundles = set()

    @classmethod
    def __call__(cls,
                 flask_or_import_name,
                 projects=None,
                 project_name=None,
                 app_directory=None
                 ):
        """

        :param flask_or_import_name: Flask instance or import name -> __name__
        :param projects: dict of app and views to load. ie:
            {
                "main": [
                    "main",
                    "api"
                ]
            }
        :param project_name: name of the project. If empty, it will try to get
                             it from the app_env(). By default it is "main"
                             The app main is set as environment variable
                             ie: app=PROJECT_NAME:CONFIG -> app=main:production
        :param app_directory: the directory name relative to the current execution path
        :return:
        """
        if not app_directory:
            app_directory = "application"
        if not project_name:
            project_name = get_app_env()[0] or "main"

        app_env = get_env()

        app = flask_or_import_name \
            if isinstance(flask_or_import_name, Flask) \
            else Flask(flask_or_import_name)

        app.url_map.converters['regex'] = RegexConverter
        app.template_folder = "%s/templates" % app_directory
        app.static_folder = "%s/static" % app_directory

        # Load configs
        c = "%s.config.%s" % (app_directory, app_env)
        app.config.from_object(c)

        # Proxyfix
        # By default it will use PROXY FIX
        # To by pass it, or to use your own, set config
        # USE_PROXY_FIX = False
        if app.config.get("USE_PROXY_FIX", True):
            app.wsgi_app = werkzeug.contrib.fixers.ProxyFix(app.wsgi_app)

        cls._app = app
        cls.assets = Environment(cls._app)
        cls._load_extensions()
        cls._setup_logger()
        cls._setup_db()

        cls.setup_installed_apps()
        cls._expose_models()

        try:

            # import models
            m = "%s.models" % app_directory
            werkzeug.import_string(m)
            cls._expose_models()

            # import projects views
            if not projects:
                projects = {"main": "main"}

            if project_name not in projects:
                raise ValueError("Missing project: %s" % project_name)

            _projects = projects.get(project_name)
            if isinstance(_projects, six.string_types):
                _projects = [_projects]
            for _ in _projects:
                werkzeug.import_string("%s.views.%s" % (app_directory, _))

        except ImportError as ie1:
            pass
        cls._expose_models()

        # Setup init_app
        # init_app instanciate functions that may need the flask.app object
        # Usually for flask extension to be setup
        _ = [_app(cls._app) for _app in cls._init_apps]

        # Add bundles
        cls._add_asset_bundle(cls._app.static_folder)

        # Register templates
        if cls._template_paths:
            loader = [cls._app.jinja_loader] + list(cls._template_paths)
            cls._app.jinja_loader = jinja2.ChoiceLoader(loader)

        # Static
        if cls._static_paths:
            cls.assets.load_path = [cls._app.static_folder] + list(cls._static_paths)
            [cls.assets.from_yaml(a) for a in cls._asset_bundles]

        # Register views
        for subcls in cls.__subclasses__():
            base_route = subcls.base_route
            if not base_route:
                base_route = utils.dasherize(utils.underscore(subcls.__name__))
                if subcls.__name__.lower() == "index":
                    base_route = "/"
            subcls._register(cls._app, base_route=base_route)

        return cls._app

    @classmethod
    def setup_installed_apps(cls):
        """
        To import 3rd party applications along with associated properties

        It is a list of dict or string.

        When a dict, it contains the `app` key and the configuration,
        if it's a string, it is just the app name

        If you require dependencies from other packages, dependencies
        must be placed before the calling package.

        It is required that __init__ in the package app has an entry point method
        -> 'main(**kw)' which will be used to setup the default app.

        As a dict
        INSTALLED_APPS = [
            "it.can.be.a.string.to.the.module",
            ("in.a.tuple.with.props.dict", {options}),
            [
                ("multi.app.list.in.a.list.of.tuple", {options}),
                ("multi.app.list.in.a.list.of.tuple2", {options})
            ]
        ]

        :return:
        """

        cls._installed_apps = cls._app.config.get("INSTALLED_APPS", [])
        if cls._installed_apps:
            def import_app(module, props={}):
                _ = werkzeug.import_string(module)
                setattr(_, "__options__", utils.dict_dot(props))

            for k in cls._installed_apps:
                if isinstance(k, six.string_types):  # One string
                    import_app(k, {})
                elif isinstance(k, tuple):
                    import_app(k[0], k[1])
                elif isinstance(k, list):  # list of tuple[(module props), ...]
                    for t in k:
                        import_app(t[0], t[1])

    @classmethod
    def render(cls, data={}, _template=None, _layout=None, **kwargs):
        """
        Render the view template based on the class and the method being invoked
        :param data: The context data to pass to the template
        :param _template: The file template to use. By default it will map the module/classname/action.html
        :param _layout: The body layout, must contain {% include __template__ %}
        """

        # Invoke the page meta so it can always be set
        page_attr()

        # Add some global Mocha data in g, along with APPLICATION DATA
        vars = dict(
            __NAME__=__title__,
            __VERSION__=__version__,
            __YEAR__=utc_now().year
        )
        for k, v in vars.items():
            setattr(g, k, v)

        # Build the template using the method name being called
        if not _template:
            stack = inspect.stack()[1]
            action_name = stack[3]
            _template = build_endpoint_route_name(cls, action_name)
            _template = utils.list_replace([".", ":"], "/", _template)
            _template = "%s.%s" % (_template, cls.template_markup)

        data = data or {}
        data.update(kwargs)
        data["__template__"] = _template

        return render_template(_layout or cls.base_layout, **data)

    @classmethod
    def _add_asset_bundle(cls, path):
        """
        Add a webassets bundle yml file
        """
        f = "%s/assets.yml" % path
        if os.path.isfile(f):
            cls._asset_bundles.add(f)

    @classmethod
    def _setup_logger(cls):
        logging_config = cls._app.config.get("LOGGING")
        if not logging_config:
            logging_config = {
                "version": 1,
                "handlers": {
                    "default": {
                        "class": cls._app.config.get("LOGGING_CLASS", "logging.StreamHandler")
                    }
                },
                'loggers': {
                    '': {
                        'handlers': ['default'],
                        'level': 'WARN',
                    }
                }
            }

        logging.config.dictConfig(logging_config)
        cls.logger = logging.getLogger("root")
        cls._app._logger = cls.logger
        cls._app._loger_name = cls.logger.name

    @classmethod
    def _setup_db(cls):
        """
        Setup the DB connection if DB_URL is set 
        """
        uri = cls._app.config.get("DB_URL")
        if uri:
            db.connect__(uri, cls._app)

    @classmethod
    def _expose_models(cls):
        """
        Register the models and assign them to `models`
        :return: 
        """
        if db._IS_OK_:
            register_models(**{m.__name__: m
                               for m in db.Model.__subclasses__()
                               if not hasattr(models, m.__name__)})

    @classmethod
    def _register(cls,
                  app,
                  base_route=None,
                  subdomain=None,
                  route_prefix=None,
                  trailing_slash=True):
        """Registers a Mocha class for use with a specific instance of a
        Flask app. Any methods not prefixes with an underscore are candidates
        to be routed and will have routes registered when this method is
        called.

        :param app: an instance of a Flask application

        :param base_route: The base path to use for all routes registered for
                           this class. Overrides the base_route attribute if
                           it has been set.

        :param subdomain:  A subdomain that this registration should use when
                           configuring routes.

        :param route_prefix: A prefix to be applied to all routes registered
                             for this class. Precedes base_route. Overrides
                             the class' route_prefix if it has been set.
        """

        if cls is Mocha:
            raise TypeError("cls must be a subclass of Mocha, not Mocha itself")

        # Create a unique namespaced key to access view.
        # $module.$class_name.$Method
        module = cls.__module__.split(".")[-1]

        if not hasattr(views, module):
            setattr(views, module, type('', (), {}))
        mod = getattr(views, module)
        setattr(mod, cls.__name__, cls)

        if base_route:
            cls.orig_base_route = cls.base_route
            cls.base_route = base_route

        if route_prefix:
            cls.orig_route_prefix = cls.route_prefix
            cls.route_prefix = route_prefix

        if not subdomain:
            if hasattr(app, "subdomain") and app.subdomain is not None:
                subdomain = app.subdomain
            elif hasattr(cls, "subdomain"):
                subdomain = cls.subdomain

        if trailing_slash is not None:
            cls.orig_trailing_slash = cls.trailing_slash
            cls.trailing_slash = trailing_slash

        for name, value in get_interesting_members(Mocha, cls):
            proxy = cls.make_proxy_method(name)
            route_name = build_endpoint_route_name(cls, name)
            try:
                if hasattr(value, "_rule_cache") and name in value._rule_cache:
                    for idx, cached_rule in enumerate(value._rule_cache[name]):
                        rule, options = cached_rule
                        rule = cls.build_rule(rule)
                        sub, ep, options = cls.parse_options(options)

                        if not subdomain and sub:
                            subdomain = sub

                        if ep:
                            endpoint = ep
                        elif len(value._rule_cache[name]) == 1:
                            endpoint = route_name
                        else:
                            endpoint = "%s_%d" % (route_name, idx,)

                        app.add_url_rule(rule, endpoint, proxy,
                                         subdomain=subdomain,
                                         **options)
                elif name in cls.__special_methods:
                    if name in ["get", "index"]:
                        methods = ["GET"]
                        if name == "index":
                            if hasattr(value, "_methods_cache"):
                                methods = value._methods_cache
                    else:
                        methods = [name.upper()]

                    rule = cls.build_rule("/", value)
                    if not cls.trailing_slash:
                        rule = rule.rstrip("/")
                    app.add_url_rule(rule, route_name, proxy,
                                     methods=methods,
                                     subdomain=subdomain)

                else:
                    methods = value._methods_cache \
                        if hasattr(value, "_methods_cache") \
                        else ["GET"]

                    name = utils.dasherize(name)
                    route_str = '/%s/' % name
                    if not cls.trailing_slash:
                        route_str = route_str.rstrip('/')
                    rule = cls.build_rule(route_str, value)
                    app.add_url_rule(rule, route_name, proxy,
                                     subdomain=subdomain,
                                     methods=methods)
            except DecoratorCompatibilityError:
                raise DecoratorCompatibilityError(
                    "Incompatible decorator detected on %s in class %s" % (name, cls.__name__))

        if hasattr(cls, "orig_base_route"):
            cls.base_route = cls.orig_base_route
            del cls.orig_base_route

        if hasattr(cls, "orig_route_prefix"):
            cls.route_prefix = cls.orig_route_prefix
            del cls.orig_route_prefix

        if hasattr(cls, "orig_trailing_slash"):
            cls.trailing_slash = cls.orig_trailing_slash
            del cls.orig_trailing_slash

    @classmethod
    def parse_options(cls, options):
        """Extracts subdomain and endpoint values from the options dict and returns
           them along with a new dict without those values.
        """
        options = options.copy()
        subdomain = options.pop('subdomain', None)
        endpoint = options.pop('endpoint', None)
        return subdomain, endpoint, options,

    @classmethod
    def make_proxy_method(cls, name):
        """Creates a proxy function that can be used by Flasks routing. The
        proxy instantiates the Mocha subclass and calls the appropriate
        method.
        :param name: the name of the method to create a proxy for
        """

        i = cls()
        view = getattr(i, name)

        for decorator in cls.decorators:
            view = decorator(view)

        @functools.wraps(view)
        def proxy(**forgettable_view_args):
            # Always use the global request object's view_args, because they
            # can be modified by intervening function before an endpoint or
            # wrapper gets called. This matches Flask's behavior.
            del forgettable_view_args

            if hasattr(i, "before_request"):
                response = i.before_request(name, **request.view_args)
                if response is not None:
                    return response

            before_view_name = "before_" + name
            if hasattr(i, before_view_name):
                before_view = getattr(i, before_view_name)
                response = before_view(**request.view_args)
                if response is not None:
                    return response

            response = view(**request.view_args)

            # You can also return a dict or None, it will pass it to render
            if isinstance(response, dict) or response is None:
                response = response or {}
                if hasattr(i, "_renderer"):
                    response = i._renderer(response)
                else:
                    _template = build_endpoint_route_name(cls, view.__name__)
                    _template = utils.list_replace([".", ":"], "/", _template)
                    _template = "%s.%s" % (_template, cls.template_markup)

                    # Set the title from the nav title, if not set
                    _meta_title = getattr(g, "__META__", {}).get("title")
                    if (not _meta_title or _meta_title == "") and get_view_attr(view, "title"):
                        page_attr(title=get_view_attr(view, "title"))

                    response.setdefault("_template", _template)
                    response = i.render(**response)

            if not isinstance(response, Response):
                response = make_response(response)

            for ext in cls._ext:
                response = ext(response)

            after_view_name = "after_" + name
            if hasattr(i, after_view_name):
                after_view = getattr(i, after_view_name)
                response = after_view(response)

            if hasattr(i, "after_request"):
                response = i.after_request(name, response)

            return response

        return proxy

    @classmethod
    def build_rule(cls, rule, method=None):
        """Creates a routing rule based on either the class name (minus the
        'View' suffix) or the defined `base_route` attribute of the class

        :param rule: the path portion that should be appended to the
                     route base

        :param method: if a method's arguments should be considered when
                       constructing the rule, provide a reference to the
                       method here. arguments named "self" will be ignored
        """

        rule_parts = []

        if cls.route_prefix:
            rule_parts.append(cls.route_prefix)

        base_route = cls.get_base_route()
        if base_route:
            rule_parts.append(base_route)

        rule_parts.append(rule)
        ignored_rule_args = ['self']
        if hasattr(cls, 'base_args'):
            ignored_rule_args += cls.base_args

        if method:
            args = get_true_argspec(method)[0]
            for arg in args:
                if arg not in ignored_rule_args:
                    rule_parts.append("<%s>" % arg)

        result = "/%s" % "/".join(rule_parts)
        return re.sub(r'(/)\1+', r'\1', result)

    @classmethod
    def get_base_route(cls):
        """Returns the route base to use for the current class."""
        base_route = cls.__name__.lower()
        if cls.base_route is not None:
            base_route = cls.base_route
            base_rule = parse_rule(base_route)
            cls.base_args = [r[2] for r in base_rule]
        return base_route.strip("/")

    @staticmethod
    def _bind_route_rule_cache(f, rule, append_method=False, **kwargs):
        # Put the rule cache on the method itself instead of globally
        if rule is None:
            rule = utils.dasherize(f.__name__) + "/"
        if not hasattr(f, '_rule_cache') or f._rule_cache is None:
            f._rule_cache = {f.__name__: [(rule, kwargs)]}
        elif not f.__name__ in f._rule_cache:
            f._rule_cache[f.__name__] = [(rule, kwargs)]
        else:
            # when and endpoint accepts multiple METHODS, ie: post(), get()
            if append_method:
                for r in f._rule_cache[f.__name__]:
                    if r[0] == rule and "methods" in r[1] and "methods" in kwargs:
                        r[1]["methods"] = list(set(r[1]["methods"] + kwargs["methods"]))
            else:
                f._rule_cache[f.__name__].append((rule, kwargs))
        return f

    @classmethod
    def _load_extensions(cls):
        extensions = [
            'pyjade.ext.jinja.PyJadeExtension',
            'mocha.extras.jade.JadeTagExtension',
            'mocha.extras.md.MarkdownExtension',
            'mocha.extras.md.MarkdownTagExtension',
        ]
        if cls._app.config.get("COMPRESS_HTML"):
            extensions.append('mocha.extras.htmlcompress.HTMLCompress')
        for ext in extensions:
            cls._app.jinja_env.add_extension(ext)


# Brew, initialize Mocha as a single instance that will be served
Brew = Mocha()

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------


def build_endpoint_route_name(cls, method_name, class_name=None):
    """
    Build the route endpoint
    It is recommended to place your views in /views directory, so it can build
    the endpoint from it. If not, it will make the endpoint from the module name
    The main reason for having the views directory, it is explicitly easy
    to see the path of the view

    :param cls: The view class
    :param method_name: The name of the method
    :param class_name: To pass the class name.
    :return: string
    """

    module = cls.__module__.split("views.")[1] if ".views." in cls.__module__ \
        else cls.__module__.split(".")[-1]
    return "%s.%s:%s" % (module, class_name or cls.__name__, method_name)


def get_interesting_members(base_class, cls):
    """Returns a generator of methods that can be routed to"""

    base_members = dir(base_class)
    predicate = inspect.ismethod if six.PY2 else inspect.isfunction
    all_members = inspect.getmembers(cls, predicate=predicate)
    return (member for member in all_members
            if not member[0] in base_members
            and (
                (hasattr(member[1], "__self__") and not member[1].__self__ in inspect.getmro(cls)) if six.PY2 else True)
            and not member[0].startswith("_")
            and not member[0].startswith("before_")
            and not member[0].startswith("after_"))


def apply_function_to_members(cls, fn):
    """
    Apply a function to all the members of a class.
    Used for decorators that is applied in a class and want all the members
    to use it
    :param cls: class
    :param fn: function
    :return: 
    """
    for name, method in get_interesting_members(Mocha, cls):
        setattr(cls, name, fn(method))


def get_true_argspec(method):
    """Drills through layers of decorators attempting to locate the actual argspec for the method."""

    argspec = inspect.getargspec(method)
    args = argspec[0]
    if args and args[0] == 'self':
        return argspec
    if hasattr(method, '__func__'):
        method = method.__func__
    if not hasattr(method, '__closure__') or method.__closure__ is None:
        raise DecoratorCompatibilityError

    closure = method.__closure__
    for cell in closure:
        inner_method = cell.cell_contents
        if inner_method is method:
            continue
        if not inspect.isfunction(inner_method) \
                and not inspect.ismethod(inner_method):
            continue
        true_argspec = get_true_argspec(inner_method)
        if true_argspec:
            return true_argspec


class DecoratorCompatibilityError(Exception):
    pass


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

# ------------------------------------------------------------------------------

"""
Views attributes store data that was set for the views
It prevents overrite from custom class attribute with other attributes
Meant to be used internally, for holding global view-based data
"""

_views_attr = {}


def set_view_attr(view, key, value, cls_name=None):
    """
    Set the view attributes
    :param view: object (class or instance method)
    :param key: string - the key
    :param value: mixed - the value
    :param cls_name: str - To pass the class name associated to the view
            in the case of decorators that may not give the real class name
    :return: 
    """
    ns = view_namespace(view, cls_name)
    if ns:
        if ns not in _views_attr:
            _views_attr[ns] = {}
        _views_attr[ns][key] = value


def get_view_attr(view, key, default=None, cls_name=None):
    """
    Get the attributes that was saved for the view
    :param view: object (class or instance method)
    :param key: string - the key
    :param default: mixed - the default value
    :param cls_name: str - To pass the class name associated to the view
            in the case of decorators that may not give the real class name
    :return: mixed
    """
    ns = view_namespace(view, cls_name)
    if ns:
        if ns not in _views_attr:
            return default
        return _views_attr[ns].get(key, default)
    return default


def view_namespace(view, cls_name=None):
    """
    Create the namespace from the view
    :param view: object (class or instance method)
    :param cls_name: str - To pass the class name associated to the view
            in the case of decorators that may not give the real class name
    :return: string or None
    """
    ns = view.__module__
    if inspect.isclass(view):
        ns += ".%s" % view.__name__
    else:
        if hasattr(view, "im_class") or hasattr(view, "im_self"):
            if view.im_class is not None:
                cls_name = view.im_class.__name__
            elif view.im_self is not None:
                cls_name = view.im_self.__name__
        if cls_name is None:
            return None
        ns += ".%s.%s" % (cls_name, view.__name__)
    return ns

# ------------------------------------------------------------------------------



