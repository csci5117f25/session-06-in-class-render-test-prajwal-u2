# Render-test
A basic website -- just enough to test out hooking things up to render, and not much more.

We will go over steps in lecture. You should fill out the following:

## What steps do I need to do when I download this repo to get it running?

update the pipfile to python 3.13.2 and delete the pipfile lock
`pipenv install` - install the dependencies

test the server by running it locally without entering the pipenv using the command `pipenv run flask --app server.py run`


## What commands starts the server?

`pip install pipenv && pipenv install` - install command on render

`pipenv run gunicorn server:app` - run command for the app to start

## Before render

Before render you will need to set up a more production-grade backend server process. We will do this together in lecture, once that's done you should update the command above for starting the server to be the **production grade** server.