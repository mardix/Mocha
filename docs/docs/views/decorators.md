
# Decorators

Mocha exposes decorators to simplify your app development

For convenience, we are going to use the same decora

### Import

    from mocha import decorators as deco

This will allow you to explicitely call the decorators in a similar as:

    @deco.route

---

## Route

Allows you to apply a route on a view class or a single method

### Class based route

When applied to a view class, all methods will be prefixed with the toute

The following code will use the `/account/` route, and `/account/hello`


    @deco.route("/account/")
    class Index(Mocha):

        def index(self):
            pass

        def hello(self):
            pass


### Method based route

Method based route only applies the route to the method.

The code below will expose `/hello-world`. By default `Index` and `index` will
reference to the root, unless a route is applied

    class Index(Mocha):

        def index(self):
            pass

        @deco.route("hello-world")
        def hello(self):
            pass

### Combined Class and Method Based

You can combine both class and method based.

The code below will now be accessed at: `/account/`, `/account/hello-world`

    @deco.route("/account/")
    class Index(Mocha):

        def index(self):
            pass

        @deco.route("/hello-world")
        def hello(self):
            pass

---

## Methods

The method decorators help specify what methods the views will accept.
Multiple methods can be applied.

Since Mocha allows you to write API endpoints
(thanks mainly to Flask), the methods below can make your endpoints RESTful.

### accept_get

Accepts GET method. By default, all endpoints are GET.

    class Index(Mocha):
        
        @deco.accept_get
        def hello(self):
            pass
            
### accept_post

Accepts POST method.

    class Index(Mocha):

        @deco.accept_post
        def save_data(self):
            pass


### accept_post_get

Accepts POST & GET method.

    class Index(Mocha):

        @deco.accept_post_get
        def my_thing(self):
            if request.method == "POST":
                # do some post stuff in here
                # return a redirect or something else
                pass

            # below will proceed for GET, since the POST return something
            name = "Mocha"
            return {"name": name}


### accept_delete

Accepts DELETE method.

### accept_put

Accepts PUT method.

### accept_options

Accepts OPTIONS method.


### Combining methods

You can combine multiple methods

    class Index(Mocha):

        @deco.accept_post
        @deco.accept_put
        @deco.accept_delete
        def save_data(self):
            pass

---

## Render Format

By default, the responses will render normal HTML. But if you want to return
JSON, or XML data, the methods below will conveniently help you do that.

N.B.: The methods must return DICT for them to benefit from multiple response format

### render_json

It return a dict into JSON. Good for API endpoint.

    class Index(Mocha):

        @deco.render_json
        def my_data(self):
            return {
                "name": "Mocha",
                "version": "xxx"
            }

### render_jsonp

It return a dict into JSON for JSONP.

    class Index(Mocha):

        @deco.render_jsonp
        def my_data(self):
            return {
                "name": "Mocha",
                "version": "xxx"
            }


### render_xml

It return a dict into XML.

    class Index(Mocha):

        @deco.render_xml
        def my_data(self):
            return {
                "name": "Mocha",
                "version": "xxx"
            }


### html

There is no decorator for HTML, as it will fall back to it if a view is not decorated
with `render_json` or `render_xml`

---

## Template

This decorator allows you to change the view template or layout

It can be applied on both class based or method based

Params:

**template(page, markup="jade")**

- page: the path of the new layout or template
- markup: the markup to use for all pages: `jade` or `html`


### Class based

This will change the default layout to another one.

    @deco.template('/layouts/my-new-layouts.jade')
    class Index(Mocha):

        def index(self):
            return

        def hello(self):
            return


### Method based

By default the template for method is based on its name, to use a different
template, specify the full path

    class Index(Mocha):


        def index(self):
            return

        @deco.template('/my-path/new-world.html', markup='html')
        def hello(self):
            return

---

## Cache

Flask-Caching is used for caching

### cache

    from mocha.ext import cache
    class Index(Mocha):

        @cache.cached(500)
        def my_cache_view(self):
            return

### memoize

---

## CSRF

All POST methods are required to receive `_csrf_token` from the application.

It it fails, the user will not be able to use it.


### exempt_csrf

In some cases you will want to bypass a POST method CSRF check, to do, we
have to exempt that method

    from mocha.ext import csrf
    import mocha.decorators as deco

    class Index(Mocha):

        @csrf.exempt
        @deco.accept_post
        def my_exempted_csrf_post(self):
            return

---

## nav_menu

**@nav_menu** creates a **navigation menu** for UI

    from mocha import nav_menu
    


## view_parser

**@view_parser**

    from mocha import view_parser

