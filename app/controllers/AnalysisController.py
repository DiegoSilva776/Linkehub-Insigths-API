# -*- coding: utf-8 -*-

import sys
import os
import re
import json
import http.client
import urllib
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import sklearn

sys.path.append('../')

from utils.Logger import Logger
from utils.NetworkingUtils import NetworkingUtils
from utils.ConstantUtils import ConstantUtils
from controllers.AuthController import AuthController
from controllers.GithubController import GithubController
from persistence.DBController import DBManager
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

'''
    The methods of this class create analysis of the data and return the results in JSON format.
'''
class AnalysisController():

    def __init__(self):
        self.TAG = "AnalysisController"

        self.logger = Logger()
        self.netUtils = NetworkingUtils()
        self.constUtils = ConstantUtils()
        self.authController = AuthController()
        self.dbManager = DBManager()

    '''
        Analysis of the question 1: 

        "Is there a correlation between the number of repositories created by a user in a given language, 
        with the number of stars, watchers & forks the user received in projects created in that 
        same language?"

        This method implement a linear regression analysis of all Github profiles from all locations in the
        project database i.e. All users stored in the database. The focus of this analysis is to find the
        probability of a user have a successful repository in a given skill (language or technology) as 
        the number of projects in that skill gets higher.
    '''
    def lRAGithubSuccessSkillsAllUsers(self, username, password):
        response = {
            "status" : False,
            "msg" : "Failed to run the Linear Regression Analysis of the Github users in the database x the correlation of the number of repos x num success",
            "results" : "" 
        }

        try:

            if not username or not password:
                response["msg"] = "Invalid access token, please login and try again."

            else:
                token = self.authController.login(username, password)

                if token != "":
                    jsonDataset, moreDetailsDatasetRows = self.getDataframeLRAGithubSuccessSkillsAllUsers(token)

                    # 1 - Run the linear regression analysis over the dataset: num_repos_smnr x max_num_forks_smnr
                    dataframe = pd.DataFrame(jsonDataset)
                    X = dataframe.drop(['idx', 'max_num_forks_smnr'], axis=1)
                    lm0 = LinearRegression(normalize=True)
                    lm0.fit(X, dataframe["max_num_forks_smnr"])

                    print("Estimated intercept coefficient: {0}".format(lm0.intercept_))
                    print("Number of coefficients: {0}".format(lm0.coef_))

                    dataframeFeatures = pd.DataFrame(list(zip(X.columns.values, lm0.coef_)), columns=['features', 'estimated_coefficients'])
                    print(dataframeFeatures)

                    plt.scatter(dataframe["num_repos_smnr"], dataframe["max_num_forks_smnr"], c='b', s=40, alpha=0.5)
                    plt.xlabel("Number of repositories created with the smnr skill")
                    plt.ylabel("Maximun number of forks of a repository related to the smnr skill")
                    plt.savefig('images/num_repos_smnr_x_max_num_forks_smnr.1.png')

                    # 2 - Run the linear regression analysis over the dataset: num_repos_smnr x max_num_stars_smnr
                    dataframe = pd.DataFrame(jsonDataset)
                    X = dataframe.drop(['idx', 'max_num_stars_smnr'], axis=1)
                    lm1 = LinearRegression(normalize=True)
                    lm1.fit(X, dataframe["max_num_stars_smnr"])

                    print("Estimated intercept coefficient: {0}".format(lm1.intercept_))
                    print("Number of coefficients: {0}".format(lm1.coef_))

                    dataframeFeatures = pd.DataFrame(list(zip(X.columns.values, lm1.coef_)), columns=['features', 'estimated_coefficients'])
                    print(dataframeFeatures)

                    plt.scatter(dataframe["num_repos_smnr"], dataframe["max_num_forks_smnr"], c='b', s=40, alpha=0.5)
                    plt.xlabel("Number of repositories created with the smnr skill")
                    plt.ylabel("Maximun number of stars of a repository related to the smnr skill")
                    plt.savefig('images/num_repos_smnr_x_max_num_stars_smnr.png')

                    # 3 - Run the linear regression analysis over the dataset: num_repos_smnr x max_num_watchers_smnr
                    dataframe = pd.DataFrame(jsonDataset)
                    X = dataframe.drop(['idx', 'max_num_watchers_smnr'], axis=1)
                    lm2 = LinearRegression(normalize=True)
                    lm2.fit(X, dataframe["max_num_watchers_smnr"])

                    print("Estimated intercept coefficient: {0}".format(lm2.intercept_))
                    print("Number of coefficients: {0}".format(lm2.coef_))

                    dataframeFeatures = pd.DataFrame(list(zip(X.columns.values, lm2.coef_)), columns=['features', 'estimated_coefficients'])
                    print(dataframeFeatures)

                    plt.scatter(dataframe["num_repos_smnr"], dataframe["max_num_watchers_smnr"], c='b', s=40, alpha=0.5)
                    plt.xlabel("Number of repositories created with the smnr skill")
                    plt.ylabel("Maximun number of watchers of a repository related to the smnr skill")
                    plt.savefig('images/num_repos_smnr_x_max_num_watchers_smnr.png')

                    # 4 - Make predictions
                    # ----------------------------------------
                    dataframe = pd.DataFrame(jsonDataset)
                    X = dataframe.drop(['idx', 'max_num_forks_smnr'], axis=1)
                    
                    X_train, X_test, Y_train, Y_test = train_test_split( 
                        X, dataframe["max_num_forks_smnr"], test_size=0.33, random_state=5
                    )

                    lm = LinearRegression(normalize=True)
                    lm.fit(X_train, Y_train)
                    pred_train = lm.predict(X_train)
                    pred_test = lm.predict(X_test)

                    print("Fit a model X_train, calculate MSE with Y train")
                    print(np.mean((Y_train - lm.predict(X_train)) ** 2))

                    print("Fit a model X_train, calculate MSE with X_text, Y_test")
                    print(np.mean((Y_test - lm.predict(X_test)) ** 2))

                    plt.scatter(pred_train, pred_train - Y_train, c='b', s=40, alpha=0.5)
                    plt.scatter(pred_test, pred_test - Y_test, c='g', s=40, alpha=0.5)
                    plt.hlines(y = 0, xmin = 0, xmax = 5000)
                    plt.xlabel("Number of repositories created with the smnr skill")
                    plt.ylabel("Maximun number of forks of a repository related to the smnr skill")
                    plt.savefig('images/chart_4.png')

                    # N - Fetch a successful response to the user
                    response["status"] = True
                    response["msg"] = "We found your data!"
                    response["json_dataset"] = jsonDataset
                    response["more_details_dataset_rows"] = moreDetailsDatasetRows

        except ValueError as ve:
            print("{0} Failed to lRAGithubSuccessSkillsAllUsers: {1}".format(self.TAG, ve))

        return json.dumps(response)

    '''
        Return the dataset used in the analysis lRAGithubSuccessSkillsAllUsers
    '''
    def getDataframeLRAGithubSuccessSkillsAllUsers(self, token):
        jsonDataset = []
        moreDetailsDatasetRows = []

        try:

            if token:
                # 1 - Fetch data from the database to produce the desired dataset
                githubProfilesSkills = self.dbManager.getListGithubUsersSkills()

                # 2 - Build the dataset and a verctor with objects that allow the user to get 
                #     more information about a data point
                for idx, profileSkills in enumerate(githubProfilesSkills):

                    try:
                        skillMaxNumRepos = self.getSkillMaxNumRepos(profileSkills)

                        if skillMaxNumRepos != "":
                            numReposMaxNumReposSkill = profileSkills["num_repos_skill_{0}".format(skillMaxNumRepos)]
                            maxNumForksSkillMaxNumRepos = profileSkills["lang_x_forks_max_{0}".format(skillMaxNumRepos)]
                            maxNumStargazersSkillMaxNumRepos = profileSkills["lang_x_stargazers_max_{0}".format(skillMaxNumRepos)]
                            maxNumWatchersSkillMaxNumRepos = profileSkills["lang_x_watchers_max_{0}".format(skillMaxNumRepos)]
                            skillMaxNumReposWasMaxForks = self.wasSkillMaxNumReposMaxX("lang_x_watchers_max_", skillMaxNumRepos, profileSkills)                               
                            skillMaxNumReposWasMaxStars = self.wasSkillMaxNumReposMaxX("lang_x_forks_max_", skillMaxNumRepos, profileSkills)
                            skillMaxNumReposWasMaxWatchers = self.wasSkillMaxNumReposMaxX("lang_x_stargazers_max_", skillMaxNumRepos, profileSkills)
                                    
                            datasetRow = {
                                "idx" : idx,
                                "num_repos_smnr" : numReposMaxNumReposSkill,
                                "max_num_forks_smnr" : maxNumForksSkillMaxNumRepos,
                                "max_num_stars_smnr" : maxNumStargazersSkillMaxNumRepos,
                                "max_num_watchers_smnr" : maxNumWatchersSkillMaxNumRepos
                            }

                            if not skillMaxNumReposWasMaxForks:
                                datasetRow["max_num_forks_smnr"] = 0

                            if not skillMaxNumReposWasMaxStars:
                                datasetRow["max_num_stars_smnr"] = 0

                            if not skillMaxNumReposWasMaxWatchers:
                                datasetRow["max_num_watchers_smnr"] = 0

                            moreDetailsDatasetRow = {
                                "idx" : idx,
                                "github_userid" : profileSkills["github_userid"],
                                "strong_repo" : profileSkills["strong_repo"],
                                "skill_max_num_repos" : skillMaxNumRepos
                            }

                            jsonDataset.append(datasetRow)
                            moreDetailsDatasetRows.append(moreDetailsDatasetRow)

                    except Exception as e:
                        print("{0} Discarded a sample from the dataset : {1}".format(self.TAG, e))

        except Exception as e:
            print("{0} Failed to get getDataframeLRAGithubSuccessSkillsAllUsers {1}".format(self.TAG, e))

        return jsonDataset, moreDetailsDatasetRows

    '''
        Returns the name of the skill in which the user has the higher number of repositories written with.
    '''
    def getSkillMaxNumRepos(self, profileSkills):
        skillMaxNumRepos = ""
        higherNumReposSkill = -1
        regexFindKey = re.compile(r"num_repos_skill_")

        try:

            for key in profileSkills.keys():

                if regexFindKey.search(key):

                    if higherNumReposSkill == -1 or profileSkills[key] > higherNumReposSkill:
                        higherNumReposSkill = profileSkills[key]
                        skillMaxNumRepos = key.replace("num_repos_skill_","")

        except Exception as e:
            print("{0} Failed to getSkillMaxNumRepos: {1}".format(self.TAG, e))

        return skillMaxNumRepos

    '''
        Returns true if the skill with the maximum number of repos was also the skill with the 
        maximum number of a given attribute, for instance, the maximum number of stars given to a 
        repository
    '''
    def wasSkillMaxNumReposMaxX(self, attributeRegex, skillMaxNumRepos, profileSkills):
        skillMaxNumX = ""
        higherMaxNumX = -1

        try:
            regexFindKey = re.compile(r"{0}".format(attributeRegex))

            for key in profileSkills.keys():

                if regexFindKey.search(key):

                    if higherMaxNumX == -1 or profileSkills[key] > higherMaxNumX:
                        higherMaxNumX = profileSkills[key]
                        skillMaxNumX = key.replace(attributeRegex,"")

            return skillMaxNumRepos == skillMaxNumX

        except Exception as e:
            print("{0} Failed to verify if wasSkillMaxNumReposMaxX: {1}".format(self.TAG, e))

        return False

    '''
        Question 1.2:
    '''
    '''
        Analysis of the question 1: 

        "Is there a correlation between the number of repositories created by a user in a given language, 
        with the number of stars, watchers & forks the user received in projects created in that 
        same language?"

        This method implement a linear regression analysis of all Github profiles from all locations in the
        project database i.e. All users stored in the database. The focus of this analysis is to find the
        probability of a user have a successful repository in a given skill (language or technology) as 
        the number of projects in that skill gets higher.
    '''
    def lRAGithubSuccessSkillsAllUsers_1(self, username, password):
        response = {
            "status" : False,
            "msg" : "Failed to run the Linear Regression Analysis of the Github users in the database x the correlation of the number of repos x num success",
            "results" : "" 
        }

        try:

            if not username or not password:
                response["msg"] = "Invalid access token, please login and try again."

            else:
                token = self.authController.login(username, password)

                if token != "":
                    jsonDataset, moreDetailsDatasetRows = self.getDataframeLRAGithubSuccessSkillsAllUsers_1(token)

                    # 1 - Run the linear regression analysis over the dataset: num_repos_smnr x max_num_forks_smnr
                    dataframe = pd.DataFrame(jsonDataset)
                    X = dataframe.drop(['idx', 'num_repos_skill'], axis=1)
                    lm0 = LinearRegression()
                    lm0.fit(X, dataframe["num_repos_skill"])

                    print("Estimated intercept coefficient: {0}".format(lm0.intercept_))
                    print("Number of coefficients: {0}".format(lm0.coef_))

                    dataframeFeatures = pd.DataFrame(list(zip(X.columns.values, lm0.coef_)), columns=['features', 'estimated_coefficients'])
                    print(dataframeFeatures)

                    plt.scatter(dataframe["num_forks_skill"], dataframe["num_repos_skill"], c='b', s=40, alpha=0.5)
                    plt.xlabel("Sum of the number of forks of the repositories related to the skill")
                    plt.ylabel("Number of repositories created with a skill")
                    plt.savefig('images/1_num_repos_skill_x_max_num_forks_skill.1.png')

                    plt.scatter(dataframe["num_stars_skill"], dataframe["num_repos_skill"], c='g', s=40, alpha=0.5)
                    plt.xlabel("Number of repositories created with a skill")
                    plt.ylabel("Sum of the number of stars of the repositories related to the skill")
                    plt.savefig('images/1_num_repos_skill_x_max_num_stars_skill.png')

                    plt.scatter(dataframe["num_watchers_skill"], dataframe["num_repos_skill"], c='r', s=40, alpha=0.5)
                    plt.xlabel("Number of repositories created with a skill")
                    plt.ylabel("Sum of the number of watchers of the repositories related to the skill")
                    plt.savefig('images/1_num_repos_skill_x_max_num_watchers_skill.png')

                    # 2 - Make predictions
                    dataframe = pd.DataFrame(jsonDataset)
                    X = dataframe.drop(['idx', 'num_stars_skill', 'num_forks_skill', 'num_watchers_skill'], axis=1)
                    
                    X_train, X_test, Y_train, Y_test = train_test_split( 
                        X, dataframe["num_stars_skill"], test_size=0.33, random_state=5
                    )

                    lm = LinearRegression(normalize=True)
                    lm.fit(X_train, Y_train)
                    pred_train = lm.predict(X_train)
                    pred_test = lm.predict(X_test)

                    print("Fit a model X_train, calculate MSE with Y train")
                    print(np.mean((Y_train - pred_train) ** 2))

                    print("Fit a model X_train, calculate MSE with X_text, Y_test")
                    print(np.mean((Y_test - pred_test) ** 2))

                    plt.scatter(pred_train, pred_train - Y_train, c='b', s=40, alpha=0.5)
                    plt.scatter(pred_test, pred_test - Y_test, c='g', s=40, alpha=0.5)
                    plt.xlabel("Number of repositories created with the smnr skill")
                    plt.ylabel("Predicted value for the number of stars")
                    plt.savefig('images/1_prediction_num_stars_skill.png')


                    # N - Fetch a successful response to the user
                    response["status"] = True
                    response["msg"] = "We found your data!"
                    response["json_dataset"] = jsonDataset
                    response["more_details_dataset_rows"] = moreDetailsDatasetRows

        except ValueError as ve:
            print("{0} Failed to lRAGithubSuccessSkillsAllUsers: {1}".format(self.TAG, ve))

        return json.dumps(response)

    '''
        Return the dataset used in the analysis lRAGithubSuccessSkillsAllUsers
    '''
    def getDataframeLRAGithubSuccessSkillsAllUsers_1(self, token):
        jsonDataset = []
        moreDetailsDatasetRows = []

        try:

            if token:
                # 1 - Fetch data from the database to produce the desired dataset
                githubProfilesSkills = self.dbManager.getListGithubUsersSkills()

                # 2 - Build the dataset and a verctor with objects that allow the user to get 
                #     more information about a data point
                for idx, profileSkills in enumerate(githubProfilesSkills):

                    datasetRow = {
                        "idx" : idx,
                        "num_repos_skill" : idx,
                        "num_forks_skill" : idx - 1,
                        "num_stars_skill" : idx - 2,
                        "num_watchers_skill" : idx - 3
                    }

                    moreDetailsDatasetRow = {
                        "idx" : idx,
                        "github_userid" : profileSkills["github_userid"],
                        "strong_repo" : profileSkills["strong_repo"],
                        "skill_max_num_repos" : "skill"
                    }

                    jsonDataset.append(datasetRow)
                    moreDetailsDatasetRows.append(moreDetailsDatasetRow)

                    '''
                    try:
                        userSkills = self.getListSkills(profileSkills)

                        for skill in userSkills:

                            if skill != "":
                                numReposSkill = profileSkills["num_repos_skill_{0}".format(skill)]
                                numForksSkill= profileSkills["lang_x_forks_sum_{0}".format(skill)]
                                numStargazersSkill = profileSkills["lang_x_stargazers_sum_{0}".format(skill)]
                                numWatchersSkill = profileSkills["lang_x_watchers_sum_{0}".format(skill)]

                                datasetRow = {
                                    "idx" : idx,
                                    "num_repos_skill" : numReposSkill,
                                    "num_forks_skill" : numForksSkill,
                                    "num_stars_skill" : numStargazersSkill,
                                    "num_watchers_skill" : numWatchersSkill
                                }

                                moreDetailsDatasetRow = {
                                    "idx" : idx,
                                    "github_userid" : profileSkills["github_userid"],
                                    "strong_repo" : profileSkills["strong_repo"],
                                    "skill_max_num_repos" : skill
                                }

                                jsonDataset.append(datasetRow)
                                moreDetailsDatasetRows.append(moreDetailsDatasetRow)
                    
                    except Exception as e:
                        print("{0} Discarded a sample from the dataset : {1}".format(self.TAG, e))
                    '''

        except Exception as e:
            print("{0} Failed to get getDataframeLRAGithubSuccessSkillsAllUsers_1 {1}".format(self.TAG, e))

        return jsonDataset, moreDetailsDatasetRows

    def getListSkills(self, profileSkills):
        skills = []

        try:
            regexFindKey = re.compile(r"num_repos_skill_")

            for key in profileSkills.keys():

                if regexFindKey.search(key):
                    skills.append(key.replace("num_repos_skill_",""))

        except Exception as e:
            print("{0} Failed to getListSkills: {1}".format(self.TAG, e))

        return skills
