# -*- coding: utf-8 -*-

import os

from flask import Flask
from flask import request
from werkzeug.serving import WSGIRequestHandler

from controllers.DeploymentController import DeploymentController
from controllers.ScrapingController import ScrapingController
from controllers.AnalysisController import AnalysisController
from controllers.TransformationController import TransformationController
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

# Routing: Transformations
@app.route("/transformation_append_timestamp_latest_repos_skills", methods=["POST"])
def transformAppendTimestampLatestReposSkills():
    try:
        inputUtils = InputUtils()

        username = inputUtils.getCleanString(request.form["username"])
        password = inputUtils.getCleanString(request.form["password"])

        transformationController = TransformationController()
        return transformationController.transformAppendTimestampLatestReposSkills(username, password)

    except ValueError as e:
        return 'Failed to transformAppendTimestampLatestReposSkills {0}'.format(e)

@app.route("/transformation_remove_all_keys_with_pattern_github_profile_skills", methods=["POST"])
def removeAllKeysWithPatternFrom():
    try:
        inputUtils = InputUtils()

        username = inputUtils.getCleanString(request.form["username"])
        password = inputUtils.getCleanString(request.form["password"])
        pattern = inputUtils.getCleanString(request.form["pattern"])

        transformationController = TransformationController()
        return transformationController.removeAllKeysWithPatternFrom(username, password, pattern)

    except ValueError as e:
        return 'Failed to removeAllKeysWithPatternFrom {0}'.format(e)

# Routing: Data Analysis
@app.route("/describe_correlations_dataset_github_profiles_skills_location", methods=["POST"])
def describeCorrelationsDatasetGithubProfilesSkills():
    try:
        inputUtils = InputUtils()

        username = inputUtils.getCleanString(request.form["username"])
        password = inputUtils.getCleanString(request.form["password"])

        analysisController = AnalysisController()
        return analysisController.describeCorrelationsDatasetGithubProfilesSkills(username, password)

    except ValueError as e:
        return 'Failed to describeCorrelationsDatasetGithubProfilesSkills {0}'.format(e)

@app.route("/describe_stats_dataset_github_profiles_skills", methods=["POST"])
def describeStatsDatasetGithubProfilesSkills():
    try:
        inputUtils = InputUtils()

        username = inputUtils.getCleanString(request.form["username"])
        password = inputUtils.getCleanString(request.form["password"])

        analysisController = AnalysisController()
        return analysisController.describeStatsDatasetGithubProfilesSkills(username, password)

    except ValueError as e:
        return 'Failed to describeStatsDatasetGithubProfilesSkills {0}'.format(e)

@app.route("/insights_dataset_github_profiles_skills", methods=["POST"])
def describeStatsDatasetGithubProfilesSkillsInsights():
    try:
        inputUtils = InputUtils()

        username = inputUtils.getCleanString(request.form["username"])
        password = inputUtils.getCleanString(request.form["password"])

        analysisController = AnalysisController()
        return analysisController.describeStatsDatasetGithubProfilesSkillsInsights(username, password)

    except ValueError as e:
        return 'Failed to describeStatsDatasetGithubProfilesSkillsInsights {0}'.format(e)

@app.route("/predict_github_skill_trends_worldwide", methods=["POST"])
def predictGithubSkillTrendsWorldwide():
    #try:
    inputUtils = InputUtils()

    username = inputUtils.getCleanString(request.form["username"])
    password = inputUtils.getCleanString(request.form["password"])

    analysisController = AnalysisController()
    return analysisController.predictGithubSkillTrendsWorldwide(username, password)

    #except ValueError as e:
    #    return 'Failed to predictGithubSkillTrendsWorldwide {0}'.format(e)

'''
    Initilization
'''
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)