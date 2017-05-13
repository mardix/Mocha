
# About

Utils are functions or objects that are exposed to the applications. They can be shortcuts, 
or from Flask itself. Some of them may extend some functionalities. 


## get_config

---


## page_meta

---

## url_for

---

## redirect

Redirect the request to another url. It adds an extra functionality by passing 
the a class method

    from mocha import Mocha, redirect
    
    class Index(Mocha):
        
        def index(self):
            pass
            
        def hello(self):
            return redirect(self.index)
---

## request

This return the basic `flask request` object

## session

## flash_success 

## flash_error

## flash_info

## flash_data

## get_flash_data

## abort

## send_mail

## get_env 

## set_env

## get_env_app

## get_env_config

## models

## views 

## register_package

## init_app

## import_module 

## register_models

## send_mail

## upload

## storage







