### Dockerizing a Python web application created with Flask  and deploying it to a container on Heroku

#### 1 - Install virtualenv to isolate the dependencies of your project:

[Info about virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/#virtualenvironments-ref)

1.1 - Make sure you have python:
```
$ python --version
```

1.2 - Make sure you have pip:
```
$ pip --version
```

1.2 - Install virtualenv:
```
$ pip install virtualenv
$ virtualenv --version
```

1.3 - Create a virtual environment for a project:
```
$ cd my_project
$ virtualenv ENV
```

1.4 - Activate the virtualenv script:
```
$ source ENV/bin/activate
```

1.5 - Install the packages required by your project, for instance:
```
$ pip install requests
$ pip install gunicorn
$ pip install Flask
$ pip install Jinja2
$ pip install Werkzeug
$ …
```

**If you cloned the repository** [ST_PythonFlaskDockerHeroku](https://github.com/DiegoSilva776/ST_PythonFlaskDockerHeroku), simply run:
```
$ pip3 install --no-cache-dir -r requirements.txt
```

#### 2 - Create a Dockerfile that encapsulates your project, like so:

```
For the following project structure:
$ root/
$ 	Dockerfile
$ 	my_project/
```

2.1 - Create this Dockerfile:

**If you cloned the repository** [ST_PythonFlaskDockerHeroku](https://github.com/DiegoSilva776/ST_PythonFlaskDockerHeroku), skip this step

```
# Grab the latest alpine image
FROM alpine:latest

# Install missing Alpine dependencies
RUN apk add --no-cache gcc musl-dev linux-headers

# Install python3 and pip
RUN apk add --no-cache --update python3 python3-dev py3-pip bash

# Install dependencies
ADD ./my_project/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Add our code
ADD ./my_project /opt/my_project/
WORKDIR /opt/my_project

# Run the image as a non-root user
RUN adduser -D myuser
USER myuser

# Expose is NOT supported by Heroku
# EXPOSE 5000

# Run the app.  CMD is required to run on Heroku
# $PORT is set by Heroku            
CMD gunicorn --bind 0.0.0.0:$PORT wsgi 
```

2.2 - On the Dockerfile replace `my_project` with the name of the directory of your web app.

#### 3 - Build a simple Flask application inside the my_project/ directory:

**If you cloned the repository** [ST_PythonFlaskDockerHeroku](https://github.com/DiegoSilva776/ST_PythonFlaskDockerHeroku), skip this step
 
wsgi.py
```
$ from app import app as application
```

tests.py
```
# -*- coding: utf-8 -*-

from app import app

import os
import unittest

class AppTestCase(unittest.TestCase):

	def test_root_text(self):
		tester = app.test_client(self)
		response = tester.get('/')
		assert ‘My project API' in response.data

	if __name__ == '__main__':
		unittest.main()
```

runtime.txt
```
$ python-3.6.2
```

requirements.txt
```
$ … results of the ‘pip freeze > requirements.txt’ command …
```

Procfile
```
$ web: gunicorn hello:app
```

app.py
```
# -*- coding: utf-8 -*-

import os

from flask import Flask
from flask import request

from werkzeug.serving import WSGIRequestHandler

# Construction
app = Flask(__name__)

# Routing
@app.route('/')
def hello():
	return ‘My Project API’

'''
	Initilization
'''
if __name__ == '__main__':
	app.run(host='0.0.0.0')
```

#### 4 - Freeze the list of packages:versions used by your project:

4.1 - Make sure the virtualenv is active:
```
$ cd my_project
$ source ENV/bin/activate
```

4.2 - Freeze the dependencies
```
$ pip freeze > requirements.txt
```

#### 5 - Test your project locally:

5.1 - Inside your project directory ‘my_project/’, export the app to start the server:
```
$ export FLASK_APP=app.py
```

5.2 - Start the server:
```
$ flask run
```

5.3 - Access the endpoints of your project and test it, or even better, create automate tests to verify if everything works the way it should

5.4 - Once the app has passed the local tests, build a Docker image and test it on a container
	
#### 6 - Encapsulate your app by building a Docker image:
	
6.1 - Navigate to the root directory of your project ‘root/’:
```
$ cd ..
```

6.2 - Build the image with the commands specified on the Dockerfile:
```
$ docker image build -t my_project_image:0.1 .
$ Obs: Do not forget the . at the end of the command!
```

6.3 - Verify the log while the image is getting built and see if everything is working flawlessly

#### 7 - If your image was built correctly locally, it means it’s probably going to work on a Heroku container, so just create a new Heroku project and associate it with your project:

7.1 - Ensure that you are in the root directory of your project, the directory with the Dockerfile:
```
$ root/
$	Dockerfile
$	my_project/
```

7.2 - Ensure you have an account on Heroku and that you have installed Heroku CLI:
[Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

7.3 - Create an empty Git repository:

**If you cloned the repository** [ST_PythonFlaskDockerHeroku](https://github.com/DiegoSilva776/ST_PythonFlaskDockerHeroku), skip this step
```
$   git init
```

7.4 - Create a new heroku project:
```
$ heroku apps:create my-project
```

7.5 - Collect the information outputted on the terminal:
```
$ Creating ⬢ my-project... done
$ https://my-project.herokuapp.com/ | https://git.heroku.com/my-project.git
```

7.6 - Add the Git repository created for the heroku project into the list of remotes of your current git repository:
```
$ git remote add heroku https://git.heroku.com/my-project.git
```

7.7 - Make sure the heroku repository was added to the list of remotes:
```
$ git remote -v
```

7.8 - **If you cloned the repository** [ST_PythonFlaskDockerHeroku](https://github.com/DiegoSilva776/ST_PythonFlaskDockerHeroku), create a new repository on GitHub, Bitbucket or somewhere else to push you code to and them:
```
$ git remote remove origin
$ git remote add origin ‘https://path_to_your_new_repo’
$ git remote -v, see if the origin is your new repository
```

#### 8 - Deploy your project to a Docker container on Heroku:

8.1 — Log in to Container Registry:
```
$ heroku container:login
```

8.2 - Build the image and push to Container Registry:
```
$ heroku container:push web
```

8.3 - Verify if your project was deployed correctly:
```
$ heroku open
```

#### 9 - Repeat the development -> testings -> deployment cycle as new features are inserted