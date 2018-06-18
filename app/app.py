# -*- coding: utf-8 -*-

import os

from flask import Flask
from flask import request
from werkzeug.serving import WSGIRequestHandler

from controllers.DeploymentController import DeploymentController
from controllers.ScrapingController import ScrapingController
from controllers.AnalysisController import AnalysisController
from utils.InputUtils import InputUtils
from utils.NetworkingUtils import NetworkingUtils

# Construction
app = Flask(__name__)

# Routing
@app.route('/')
def hello():
    return 'Linkehub API Manager'

# Routing: Deployment
@app.route("/deploy_n_copies_root_instance", methods=["POST"])
def deployNCopiesRootInstance():
    try:
        startIdx = request.form["start_idx"]
        endIdx = request.form["end_idx"]
        
        deploymentController = DeploymentController()
        return deploymentController.deployNCopiesRootInstance(startIdx, endIdx)

    except ValueError as e:
        return 'Failed to deployNCopiesRootInstance {0}'.format(e)

# Routing: Data Scraping
@app.route("/scrap_github_profiles_from_location", methods=["POST"])
def scrapGithubProfilesFromLocation():
    try:
        inputUtils = InputUtils()

        username = inputUtils.getCleanString(request.form["username"])
        password = inputUtils.getCleanString(request.form["password"])
        location = inputUtils.getCleanString(request.form["location"])
        initialPage = request.form["initial_page"]
        numPages = request.form["num_pages"]

        scrapingController = ScrapingController()
        return scrapingController.scrapBasicProfileGithubUsers(username, password, location, initialPage, numPages)

    except ValueError as e:
        return 'Failed to scrapGithubProfilesFromLocation {0}'.format(e)

@app.route("/scrap_github_users_repositories_skills", methods=["POST"])
def scrapGithubUsersRepositoriesSkills():
    try:
        inputUtils = InputUtils()

        username = inputUtils.getCleanString(request.form["username"])
        password = inputUtils.getCleanString(request.form["password"])
        location = inputUtils.getCleanString(request.form["location"])

        scrapingController = ScrapingController()
        return scrapingController.scrapGithubUsersRepositoriesSkills(username, password, location)

    except ValueError as e:
        return 'Failed to scrapGithubUsersRepositoriesSkills {0}'.format(e)

@app.route("/scrap_commits_code_samples_github_users_from_location", methods=["POST"])
def scrapCommitsCodeSamplesGithubUsersFromLocation():
    try:
        inputUtils = InputUtils()

        username = inputUtils.getCleanString(request.form["username"])
        password = inputUtils.getCleanString(request.form["password"])
        location = inputUtils.getCleanString(request.form["location"])
        skill = inputUtils.getCleanString(request.form["skill"])

        scrapingController = ScrapingController()
        return scrapingController.scrapCommitsCodeSamplesGithubUsersFromLocation(username, password, location, skill)

    except ValueError as e:
        return 'Failed to scrapCommitsCodeSamplesGithubUsersFromLocation {0}'.format(e)

# Routing: Data Analysis
@app.route("/lra_github_success_skills_all_users", methods=["POST"])
def lRAGithubSuccessSkillsAllUsersLocation():
    try:
        inputUtils = InputUtils()

        username = inputUtils.getCleanString(request.form["username"])
        password = inputUtils.getCleanString(request.form["password"])

        analysisController = AnalysisController()
        return analysisController.lRAGithubSuccessSkillsAllUsers_1(username, password)

    except ValueError as e:
        return 'Failed to lRAGithubSuccessSkillsAllUsers_1 {0}'.format(e)

'''
    Initilization
'''
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)