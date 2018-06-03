# -*- coding: utf-8 -*-

import os

from flask import Flask
from flask import request

from werkzeug.serving import WSGIRequestHandler
from controllers.DeploymentController import DeploymentController

# Construction
app = Flask(__name__)

# Routing
@app.route('/')
def hello():
    return 'Linkehub API Manager'

@app.route("/deploy_n_copies_root_instance", methods=["POST"])
def deployNCopiesRootInstance():
    try:
        startIdx = request.form["start_idx"]
        endIdx = request.form["end_idx"]
        
        deploymentController = DeploymentController()
        return deploymentController.deployNCopiesRootInstance(startIdx, endIdx)

    except ValueError:
        return 'Failed to deployNCopiesRootInstance'

'''
    Initilization
'''
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)