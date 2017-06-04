# -*- coding: utf-8 -*-



import copy
import inspect
import arrow
import blinker
import functools
import flask_cors
from jinja2 import Markup
from dicttoxml import dicttoxml
from werkzeug.wrappers import BaseResponse
from .core import (Mocha,
                   init_app as h_init_app,
                   apply_function_to_members,
                   build_endpoint_route_name,
                   set_view_attr,
                   get_view_attr)
from flask import (Response,
                   jsonify,
                   request,
                   current_app,
                   url_for,
                   make_response,
                   g)

# ----------------------------------------------------------------------------------------------------------------------
# ----  Monkey patch jsonify, to convert other data type: ie: Arrow
import flask.json
from flask.json import dumps as flask_dumps


class _JSONEnc(flask.json.JSONEncoder):
    def default(self, o):
        if isinstance(o, arrow.Arrow):
            return o.for_json()
        else:
            return super(self.__class__, self).default(o)


def dumps(o, **kw):
    kw["cls"] = _JSONEnc
    return flask_dumps(o, **kw)
flask.json.dumps = dumps

# ----------------------------------------------------------------------------------------------------------------------


def _normalize_response_tuple(tuple_):
    """
    Helper function to normalize view return values .
    It always returns (dict, status, headers). Missing values will be None.
    For example in such cases when tuple_ is
      (dict, status), (dict, headers), (dict, status, headers),
      (dict, headers, status)

    It assumes what status is int, so this construction will not work:
    (dict, None, headers) - it doesn't make sense because you just use
    (dict, headers) if you want to skip status.
    """
    v = tuple_ + (None,) * (3 - len(tuple_))
    return v if isinstance(v[1], int) else (v[0], v[2], v[1])


__view_parsers = set()


def view_parser(f):
    """
    A simple decorator to to parse the data that will be rendered
    :param func:
    :return:
    """
    __view_parsers.add(f)
    return f


def _build_response(data, renderer=None):
    """
    Build a response using the renderer from the data
    :return:
    """
    if isinstance(data, Response) or isinstance(data, BaseResponse):
        return data
    if not renderer:
        raise AttributeError(" Renderer is required")
    if isinstance(data, dict) or data is None:
        data = {} if data is None else data
        for _ in __view_parsers:
            data = _(data)
        return renderer(data), 200
    elif isinstance(data, tuple):
        data, status, headers = _normalize_response_tuple(data)
        for _ in __view_parsers:
            data = _(data)
        return renderer(data or {}), status, headers
    return data

json_renderer = lambda i, data: _build_response(data, jsonify)
xml_renderer = lambda i, data: _build_response(data, dicttoxml)


def json(func):
    """
    Decorator to render as JSON
    :param func:
    :return:
    """
    if inspect.isclass(func):
        apply_function_to_members(func, json)
        return func
    else:
        @functools.wraps(func)
        def decorated_view(*args, **kwargs):
            data = func(*args, **kwargs)
            return _build_response(data, jsonify)
        return decorated_view


def xml(func):
    """
    Decorator to render as XML
    :param func:
    :return:
    """
    if inspect.isclass(func):
        apply_function_to_members(func, xml)
        return func
    else:
        @functools.wraps(func)
        def decorated_view(*args, **kwargs):
            data = func(*args, **kwargs)
            return _build_response(data, dicttoxml)
        return decorated_view


def jsonp(func):
    """Wraps JSONified output for JSONP requests.
    http://flask.pocoo.org/snippets/79/
    """

    @functools.wraps(func)
    def decorated_view(*args, **kwargs):
        callback = request.args.get('callback', None)
        if callback:
            data = str(func(*args, **kwargs))
            content = str(callback) + '(' + data + ')'
            mimetype = 'application/javascript'
            return current_app.response_class(content, mimetype=mimetype)
        else:
            return func(*args, **kwargs)
    return decorated_view


def template(page=None, layout=None, markup="jade", **kwargs):
    """
    Decorator to change the view template and layout.

    It works on both Mocha class and view methods

    on class
        only $layout and markup are applied, everything else will be passed to the kwargs
        Using as first argument, it will be the layout.

        :first arg or $layout: The layout to use for that view
        :param layout: The layout to use for that view
        :param markup: the markup to use, by default it's html, can switch to jade.
        this will attach it to template_markup
        :param kwargs:
            get pass to the TEMPLATE_CONTEXT

    ** on method that return a dict
        page or layout are optional

        :param page: The html page
        :param layout: The layout to use for that view

        :param kwargs:
            get pass to the view as k/V

    ** on other methods that return other type, it doesn't apply

    :return:
    """
    pkey = "_template_extends__"

    def decorator(f):
        if inspect.isclass(f):
            layout_ = layout or page
            extends = kwargs.pop("extends", None)
            if extends and hasattr(extends, pkey):
                items = getattr(extends, pkey).items()
                if "layout" in items:
                    layout_ = items.pop("layout")
                for k, v in items:
                    kwargs.setdefault(k, v)
            if not layout_:
                layout_ = "layout.html"
            kwargs.setdefault("brand_name", "")
            kwargs["layout"] = layout_

            setattr(f, pkey, kwargs)
            setattr(f, "base_layout", kwargs.get("layout"))
            setattr(f, "template_markup", markup or "html")
            return f
        else:
            @functools.wraps(f)
            def wrap(*args2, **kwargs2):
                response = f(*args2, **kwargs2)
                if isinstance(response, dict) or response is None:
                    response = response or {}
                    if page:
                        response.setdefault("_template", page)
                    if layout:
                        response.setdefault("_layout", layout)
                    for k, v in kwargs.items():
                        response.setdefault(k, v)
                return response
            return wrap
    return decorator


# -----

class SiteNavigation(object):
    """
    SiteNavigation is class decorator to build page menu while building the enpoints

    Decorator to build navigation menu directly on the methods
    By default it will build the menu of the module, class an method
    If the class is also decorated, it will use the menu _name as the top level _name

    :param title: str or function : The menu title
                 if string, it will just display the text
                 if function, it will run it each time
    :param kwargs: extra options to pass into the menu or to move the menu somewhere else

        order int: The order of the menu in the set

        visible (list of bool or callback): To hide and show menu. Accepts bool or
                    list of callback function the callback function must return
                    a bool to check if all everything is True to show or will be False
                    ** When this menu is inside of a menu set, or has parent, if you want
                    that page to be activated, but don't want to create a menu link,
                    for example: a blog read page, set show to False. It will know
                    the menu set is active

        endpoint string: By default the endpoint is built based on the method and class.
                    When set it will be used instead

        endpoint_kwargs dict: dict of k/v data for endpoint

        tags: list or str - tags menu together. Which can be used to build custom one

        attach_to: list of full module.Class path to attach the menu to.
                        by default it will detach the class it is attached to
                        To reattach it, add the string `self` in the list
                ie: 
                    @nav("Hi", attach_to=["full.module.name.ClassName"])
                    Will attach the menu to the `full.module.name.ClassName`, 
                     so 'Hello' menu, will be shown under the attached module. 
                    (it will no longer be shown under itself)

                    To attach it to itself also, add `self` in the list
                    @nav("Hi", attach_to=["full.module.name.ClassName", "self"]


        position: string - of right or left. By default it's left
                      it will position the the menu to the specified place

        The args below will allow you to change where the menu is placed.
        By default they are set automatically

        module_: the module _name. Usually if using another module
        class_: the class _name class _name in the module
        method_: The method _name, to build endpoint. Changing this will change the url

        some other kwargs:
            url
            target
            fa_icon
            align_right
            show_profile_avatar
            show_profile_name
            css_class
            css_id

    :return:
    """

    _title_map = {}

    def __call__(self, title, **kwargs):
        def wrap(f):
            _class = inspect.stack()[1][3]
            _is_class = inspect.isclass(f)
            kwargs.setdefault("key", _class)
            self._push(title=title,
                       view=f,
                       class_name=_class,
                       is_class=_is_class,
                       **kwargs)
            return f

        return wrap

    def __init__(self):
        self.MENU = {}

    def add(self, title, obj, **kwargs):
        """
        Add a title
        :param title: str: The title of the menu
        :param obj: class or method
        :param kwargs:
        :return:
        """
        is_class = inspect.isclass(obj)
        self._push(title=title,
                   view=obj,
                   class_name=obj.im_class.__name__ if not is_class else obj.__name__,
                   is_class=is_class,
                   **kwargs)

    def clear(self):
        self.MENU = {}

    def _push(self, title, view, class_name, is_class, **kwargs):
        """ Push nav data stack """

        # Set the page title
        set_view_attr(view, "title", title, cls_name=class_name)

        module_name = view.__module__
        method_name = view.__name__

        _endpoint = build_endpoint_route_name(view, "index" if is_class else method_name, class_name)
        endpoint = kwargs.pop("endpoint", _endpoint)
        kwargs.setdefault("endpoint_kwargs", {})
        order = kwargs.pop("order", 0)

        # Tags
        _nav_tags = get_view_attr(view, "nav_tags", ["default"], cls_name=class_name)
        tags = kwargs.pop("tags", _nav_tags)
        if not isinstance(tags, list):
            _ = tags
            tags = [_]
        kwargs["tags"] = tags

        # visible: accepts a bool or list of callback to execute
        visible = kwargs.pop("visible", [True])
        if not isinstance(visible, list):
            visible = [visible]

        if get_view_attr(view, "nav_visible", cls_name=class_name) is False:
            visible = False

        kwargs["view"] = view
        kwargs["visible"] = visible
        kwargs["active"] = False
        kwargs["key"] = class_name

        if is_class:  # class menu
            kwargs["endpoint"] = endpoint
            kwargs["has_subnav"] = True
        else:
            kwargs["has_subnav"] = False
            kwargs.update({
                "order": order,
                "has_subnav": False,
                "title": title,
                "endpoint": endpoint,
            })

        self._title_map[endpoint] = title

        path = "%s.%s" % (module_name, method_name if is_class else class_name)
        attach_to = kwargs.pop("attach_to", [])
        if not attach_to:
            attach_to.append(path)

        for path in attach_to:
            if path not in self.MENU:
                self.MENU[path] = {
                    "title": None,
                    "endpoint": None,
                    "endpoint_kwargs": {},
                    "order": None,
                    "subnav": [],
                    "kwargs": {}
                }

            if is_class:  # class menu
                self.MENU[path]["title"] = title
                self.MENU[path]["order"] = order
                self.MENU[path]["kwargs"] = kwargs

            else:  # sub menu
                self.MENU[path]["subnav"].append(kwargs)

    def _get_title(self, title):
        """Title can also be a function"""
        return title() if hasattr(title, '__call__') else title

    def _test_visibility(self, shows):
        if isinstance(shows, bool):
            return shows
        elif not isinstance(shows, list):
            shows = [shows]
        return all([x() if hasattr(x, "__call__") else x for x in shows])

    def get(self, cls):
        key = self.get_key(cls)
        return self.MENU[key]

    def get_key(self, cls):
        """
        Return the string key of the class
        :param cls: class
        :return: str
        """
        return "%s.%s" % (cls.__module__, cls.__name__)

    def render(self):
        """ Render the menu into a sorted by order multi dict """
        menu_list = []
        menu_index = 0
        for _, menu in copy.deepcopy(self.MENU).items():
            subnav = []

            menu["kwargs"]["_id"] = str(menu_index)
            menu["kwargs"]["active"] = False
            if "visible" in menu["kwargs"]:
                menu["kwargs"]["visible"] = self._test_visibility(menu["kwargs"]["visible"])

            for s in menu["subnav"]:
                if s["title"]:
                    s["title"] = self._get_title(s["title"])

                if s["endpoint"] == request.endpoint:
                    s["active"] = True
                    menu["kwargs"]["active"] = True
                s["visible"] = self._test_visibility(s["visible"])
                menu_index += 1
                s["_id"] = str(menu_index)
                subnav.append(s)

            _kwargs = menu["kwargs"]

            if menu["title"]:
                _kwargs.update({
                    "subnav": self._sort(subnav),
                    "order": menu["order"],
                    "title": self._get_title(menu["title"])
                })
                menu_list.append(_kwargs)
            else:
                menu_list += subnav
            menu_index += 1

        return self._sort(menu_list)

    def _sort(self, items):
        """ Reorder the nav by key order """
        return sorted(items, key=lambda s: s["order"])

    def init_app(self, app):

        def link_for(endpoint, props={}, **kwargs):
            url = url_for(endpoint, **kwargs)
            title = self._title_map.get(endpoint, "")
            props = " ".join(["%s='%s'" % (k, v) for k, v in props.items()])
            a = "<a href='{url}' {props}>{title}</a>".format(title=title,
                                                             url=url,
                                                             props=props)
            return Markup(a)

        @app.context_processor
        def _():
            return dict(link_for=link_for)

        @app.before_request
        def p(*args, **kwargs):
            """ Will always run the menu """
            if request.endpoint not in ["static", None]:
                setattr(g, "__SITENAV__", nav.render())


nav = SiteNavigation()
h_init_app(nav.init_app)




