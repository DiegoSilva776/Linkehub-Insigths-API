# -*- coding: utf-8 -*-

import os

from flask import Flask
from flask import request
from werkzeug.serving import WSGIRequestHandler
from controllers.DeploymentController import DeploymentController
from controllers.ScrapingController import ScrapingController
from utils.InputUtils import InputUtils

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

    except ValueError as e:
        return 'Failed to deployNCopiesRootInstance {0}'.format(e)

@app.route("/scrap_github_profiles_from_location", methods=["POST"])
def scrapGithubProfilesFromLocation():
    try:
        inputUtils = InputUtils()

        token = request.headers.get("access_token")
        location = inputUtils.getCleanString(request.form["location"])
        initialPage = request.form["initial_page"]
        numPages = request.form["num_pages"]

        scrapingController = ScrapingController()
        return scrapingController.scrapBasicProfileGithubUsers(token, location, initialPage, numPages)

    except ValueError as e:
        return 'Failed to scrapGithubProfilesFromLocation {0}'.format(e)

'''
    Initilization
'''
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)