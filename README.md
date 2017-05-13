# Mocha

[I loving memory of Mocha. So, code up for Mocha! ]

[Documentation](https://mardix.github.io/mocha)

**Mocha** is A mid stack, batteries framework based on Flask. It adds structure 
to your Flask application, and group the endpoints by classes instead of just 
loose functions. 

Technically Mocha is my attempt of making a simple framework based on Flask Great Again!

 
## Decisions made for you + Features

- Smart routing: automatically generates routes based on the classes and methods in your views

- Class name as the base url, ie: class UserAccount will be accessed at '/user-account'

- Class methods (action) could be accessed: hello_world(self) becomes 'hello-world'

- Smart Rendering without adding any blocks in your templates

- Auto rendering by returning a dict of None

- Use Jade (Pug) template by default, but you can also use HTML. 

- Templates are mapped as the model in the class the $module/$class/$method.jade

- Markdown ready: Along with Jade and HTML, it can also properly parse Markdown

- Auto route can be edited with @route()

- Restful: GET, POST, PUT, DELETE

- REST API Ready

- bcrypt is chosen as the password hasher

- Session: Redis, AWS S3, Google Storage, SQLite, MySQL, PostgreSQL

- ORM: [Active-Alchemy](https://github.com/mardix/active-alchemy) (SQLALchemy wrapper)

- ReCaptcha: [Flask-Recaptcha](https://github.com/mardix/flask-recaptcha)

- Uses Arrow for dates 

- Active-Alchemy saves the datetime as arrow object, utc_now

- CSRF on all POST

- CloudStorage: Local, S3, Google Storage [Flask-Cloudy](https://github.com/mardix/flask-cloudy)

- Mailer (SES or SMTP)

- Caching

- Propel for deployment

- Decorators, lots of decorators

## Built-in Contrib

- Basic Layout

- Index page

- User Auth

    - login
    
    - signup
    
    - lost-password
    
    - account-settings
    
    - Can login with:
        
        - username 
        
        - email 
        
        - social login
        
    - JWT 
    
    - Ability to sign endpoint

- User Admin

- Contact Page

- Error Page (Custom error page)

- Maintenance Page

- JQuery

- Bootstrap 3.x

- Bootswatch

- Font-Awesome



## Quickstart

#### Install Mocha

To install Mocha, it is highly recommended to use a virtualenv, in this case I 
use virtualenvwrapper 

    mkvirtualenv my-mocha-site

Install Mocha

    pip install mocha
    
#### Initialize your application

Now Mocha has been installed, let's create our first application

    cd your-dir
    
    mocha init
    
`mocha init` setup the structure along with the necessary files to get started
 
 You will see a structure similar to this
 
    /your-dir
        |
        |__ .gitignore
        |
        |__ propel.yml
        |
        |__requirements.txt
        |
        |__ mocha_init.py
        |
        |__ app/
            |
            |__ __init__.py
            |
            |__ config.py
            |
            |__ /models/
                |
                |__ __init__.py
                |
                |__ models.py
            |
            |__ /views/
                |
                |__ __init__.py
                |
                |__ main.py
            |
            |__ /templates/
                | 
                |__ /layouts/
                    | 
                    |__ base.jade
                |
                |__ /main/
                    |
                    |__ /Index/
                        |
                        |__ index.jade
            |
            |__ /static/
                |
                |__ assets.yml
                |
                |__ package.json
            |
            |__ /data/
                |
                |__ babel.cfg
                |
                |__ /uploads/
                |
                |__ /babel/
                |
                |__ /mail-templates/


#### Install front end components

Your application is now initialized with all the files, now let's pull in some 
front end components via `npm`, this will JQuery, Bootstrap, Font-Awesome and more. 

If you haven't done so, you need to install `npm` in order for it to install the
components.

The code below will run `npm install`, make sure `static/package.json` contains
all the files to pull

    mocha npm-install
    
 
#### Serve your first application

If everything is all set, all you need to do now is run your site:

    mocha serve
    
It will start serving your application by default at `127.0.0.1:5000`

Go to http://127.0.0.1:5000/ 

---

I hope this wasn't too hard. Now Read The Docs at [http://mardix.github.io/mocha/](http://mardix.github.io/mocha/) 
for more 

Thanks, 

Mardix :) 

--- 

## Read The Docs

To dive into the documentation, Read the docs @ [http://mardix.github.io/mocha/](http://mardix.github.io/mocha/)

---

License MIT

Copyright: 2017 Mardix

