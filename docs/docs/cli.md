# Juice : Command Line Tool

Juice comes with a command line interface to conveniently create projects, 
build assets, push assets to S3, deploy application to production server and more.

There two types of command line tool. 
 
`mocha`: The command to let you create projects,  build assets,
push assets to S3, deploy application to production server and more 

`mocha:cli` [mocha:cli](application/cli.md) to manage your own command line interface

Below are the availale commands for `mocha`

---

## create

To create new project in your application.

    mocha create www
    
*Where `www` is the $project_name.*

**arguments**

- $project_name : The name of the project to create
    
**options**

- --skel | -s *(default: app)* - The pre-made skeleton to use for the project. 
    - `app` : Basic skeleton
    - `api` : A skeleton for RESTful API

    
---

## serve

Allows to launch a project in local dev environment.

    mocha serve

*Where `www` is the $project_name.*

**arguments**

- $project_name : The name of the project to serve
    
**options**

- -p | --port *(default: 5000)* - The port to use if you want to use one other than 5000

- --no-watch - The name of the project to create. 
No space or dashes.


This will launch the `www` project under port 5001

    mocha serve www -p 5001


To not watch the files when serving, so it doesn't reload

    mocha serve api --no-watch 1
    
---

## build-assets

Allows to build web assets static files for the project

    mocha build-assets www
    
*Where `www` is the $project_name.*

**arguments**

- $project_name : The name of the project
    
---

## assets2s3

If you want to host your assets on AWS S3, **mocha** can conveniently upload
them on S3.

    mocha asset-to-s3 www
    
*Where `www` is the $project_name.*

**arguments**

- $project_name : The name of the project
    
    
By default the `Development` config will be used. 
If you want to use the `PRODUCTION` to upload from your local machine:

    ENV='PRODUCTION' mocha assets2s3 -p www

---

## deploy

This is convenient command to push your application to production server by using GIT.

    mocha deploy web

*Where `web` is the $remote_name.*

No need to add a remote manually. By specifying the remote in your `propel.yml`
file, it will push it to that remote. This will allow to quickly change the remotes
to push to. Of course you must commit your code.

**arguments**

- $remote_name : The name of the remote in propel.yml to push
    
    
**options**

- --all : To push to all remotes

In your `/propel.yml` file, edit the section `git-remotes`:


    deploy:
      web:
        - ssh://user@host/path.git
        - ssh://user@host2/application-name.git
      workers:
        - ssh://user@host3/another.git

Now to push to `web` only:

    mocha deploy -r web

To push `workers`:

    mocha deploy -r workers
    
To push to all remotes:

    mocha deploy


## setup-models

    mocha setup-models



