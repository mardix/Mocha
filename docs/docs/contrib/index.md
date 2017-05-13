# Contrib


Contribs are ready to use embeddable applications to add in your `INSTALLED_APPS` 
to get going. They solved basic and common web development problems.

They are meant to be easy to installed with less configurations possible.

They may also come decorations or helpers functions for external use.


The contribs below are built in Mocha for developers convenience:

---


## Maintenance Page

### mocha.contrib.maintenance_page

Automatically show a maintenance page on the site. No pages will be able to be 
accessed.

To disable just comment out, or remove from the `INSTALLED_APPS`

**Installation**

    MAINTENANCE_PAGE = ("mocha.contrib.views.maintenance_page", {
        "on": False,
        "excludes": []
    })
    
    INSTALLED_APPS: [
        MAINTENANCE_PAGE
    ]
    
**Options**

    - `template`: If using a different template page 
    