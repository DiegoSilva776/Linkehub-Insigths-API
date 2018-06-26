# -*- coding: utf-8 -*-

import sys
import os
import re
import time
import json
import http.client
import urllib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings

sys.path.append('../')

from math import sqrt
from matplotlib import pyplot
from scipy.stats import spearmanr
from sklearn.svm import SVR
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from sklearn.cross_validation import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn import ensemble
from sklearn.cluster import KMeans
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM

from utils.Logger import Logger
from utils.NetworkingUtils import NetworkingUtils
from utils.ConstantUtils import ConstantUtils
from utils.DataframeUtils import DataframeUtils
from utils.StringUtils import StringUtils
from controllers.AuthController import AuthController
from controllers.GithubController import GithubController
from persistence.DBController import DBManager

'''
    The methods of this class create analysis of the data and return the results in JSON format.
'''
class AnalysisController():

    def __init__(self):
        self.TAG = "AnalysisController"

        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        warnings.simplefilter(action='ignore', category=FutureWarning)

        self.logger = Logger()
        self.netUtils = NetworkingUtils()
        self.strUtils = StringUtils()
        self.constUtils = ConstantUtils()
        self.dataFrameUtils = DataframeUtils()
        self.authController = AuthController()
        self.dbManager = DBManager()

    ###########################
    ## Dataset comprehension ##
    ###########################
    '''
        Create descriptive statistics for the attributes of the github_profilex_skills_location dataset.
    '''
    def describeStatsDatasetGithubProfilesSkills(self, username, password):
        response = {
            "status" : False,
            "msg" : "Failed to return descriptive statistics about the dataset github_profiles_skills_location",
            "dataset_skills" : []
        }

        try:

            if not username or not password:
                response["msg"] = "Invalid access token, please login and try again."

            else:
                token = self.authController.login(username, password)

                if token != "":
                    dataset, _ = self.getDataframeLRAGithubSuccessSkillsAllUsers(token)
                    skillsDataFrame = pd.DataFrame.from_records(dataset)
                    toDrop = self.dataFrameUtils.getColumnsToDrop(skillsDataFrame,
                        [
                            "github_userid",
                            "strong_repo"
                        ]
                    )
                    skillsDataFrame.drop(toDrop, inplace=True, axis=1)
                    skillsDataFrame.fillna(0)

                    # Extract and store information about the tech skills available in the platform
                    skills = self.getSkillsFromDBKeys(list(skillsDataFrame.columns))
                    self.dbManager.updateListTechSkillsPlatform(token, skills)

                    # Descriptive statistics of an interesting attribute accross all skills
                    interestAttrs = [
                        "num_repos_skill",
                        "lang_x_forks_max",
                        "lang_x_stargazers_max",
                        "lang_x_watchers_max",
                        "latest_created_at",
                        "latest_updated_at",
                        "latest_pushed_at",
                        "latest_size"
                    ]

                    for attr in interestAttrs:
                        skillId = 0
                        xSkills = []
                        xSkillNames = []
                        ySumAttr = []
                        yAvgAttr = []
                        yStdDevAttr = []

                        # Calculate the sum, mean and std. dev. of the datasets
                        for skill in skills.keys():
                            key = "{0}_{1}".format(attr, skill)

                            if self.dataFrameUtils.isSerieInDataframe(skillsDataFrame, key):
                                ySumAttr.append(skillsDataFrame["{0}_{1}".format(attr, skill)].sum())
                                yAvgAttr.append(skillsDataFrame["{0}_{1}".format(attr, skill)].mean())
                                yStdDevAttr.append(np.std(skillsDataFrame["{0}_{1}".format(attr, skill)]))

                                xSkills.append(skillId)
                                xSkillNames.append(skill)
                                skillId += 1

                        response["dataset_skills"] = xSkills
                        response["dataset_skill_names"] = xSkillNames

                        # Reset the plot
                        plt.clf()
                        plt.figure(figsize=(30, 15))

                        # Plot the sum
                        pathFilePlotSum = "images/gpsl_descriptive_analysis_{0}_x_{1}.png".format("skills_sum", attr)
                        yPos = np.arange(len(xSkillNames))

                        plt.bar(yPos, ySumAttr, align='center', alpha=0.5)
                        plt.xticks(yPos, xSkillNames, rotation='vertical')
                        plt.xlabel("Skills")
                        plt.ylabel("Sum of {0}".format(attr))
                        plt.savefig(pathFilePlotSum)

                        response["dataset_sum_{0}".format(attr)] = ySumAttr
                        response["plot_skills_sum_x_{0}".format(attr)] = self.dbManager.storeImage(pathFilePlotSum, token)

                        # Plot the mean
                        pathFilePlotMean = "images/gpsl_descriptive_analysis_{0}_x_{1}.png".format("skills_mean", attr)
                        yPos = np.arange(len(xSkillNames))
     
                        plt.bar(yPos, yAvgAttr, align='center', alpha=0.5)
                        plt.xticks(yPos, xSkillNames, rotation='vertical')
                        plt.xlabel("Skills")
                        plt.ylabel("Mean values of {0}".format(attr))
                        plt.savefig(pathFilePlotMean)

                        response["dataset_mean_{0}".format(attr)] = yAvgAttr
                        response["plot_skills_mean_x_{0}".format(attr)] = self.dbManager.storeImage(pathFilePlotMean, token)

                        # Plot the standard deviation
                        pathFilePlotStdDev = "images/gpsl_descriptive_analysis_{0}_x_{1}.png".format("skills_std_dev", attr)
                        yPos = np.arange(len(xSkillNames))

                        plt.bar(yPos, yStdDevAttr, align='center', alpha=0.5)
                        plt.xticks(yPos, xSkillNames, rotation='vertical')
                        plt.xlabel("Skills")
                        plt.ylabel("Std. dev. of {0}".format(attr))
                        plt.savefig(pathFilePlotStdDev)

                        response["dataset_std_dev_{0}".format(attr)] = yStdDevAttr
                        response["plot_skills_std_dev_x_{0}".format(attr)] = self.dbManager.storeImage(pathFilePlotStdDev, token)

                    response["status"] = True
                    response["msg"] = "Success! We've finished the descriptive analysis of the github_profile_skills_location dataset",

                else:
                    response["msg"] = "Invalid access token"

        except Exception as e:
            print("{0} Failed to describeStatsDatasetGithubProfilesSkills: {1}".format(self.TAG, e))

        return json.dumps(response)

    '''
        Create descriptive statistics for the attributes of the github_profilex_skills_location dataset
        after applying a groupBy location on the dataset.
    '''
    def describeStatsDatasetGithubProfilesSkillsInsights(self, username, password):
        response = {
            "status" : False,
            "msg" : "Failed to return descriptive statistics about the dataset github_profiles_skills_location",
            "dataset_skills" : []
        }

        try:

            if not username or not password:
                response["msg"] = "Invalid access token, please login and try again."

            else:
                token = self.authController.login(username, password)

                if token != "":
                    dataset, _ = self.getDataframeLRAGithubSuccessSkillsAllUsers(token)
                    skillsDataFrame = pd.DataFrame.from_records(dataset)
                    toDrop = self.dataFrameUtils.getColumnsToDrop(skillsDataFrame,
                        [
                            "github_userid",
                            "strong_repo"
                        ]
                    )
                    skillsDataFrame.drop(toDrop, inplace=True, axis=1)
                    skillsDataFrame.fillna(0)

                    # Extract and store information about the tech skills available in the platform
                    skills = self.getSkillsFromDBKeys(list(skillsDataFrame.columns))
                    self.dbManager.updateListTechSkillsPlatform(token, skills)

                    # Descriptive statistics of the dataset grouped by interesting attributes x skill
                    for skill in skills.keys():

                        interestGroups = [
                            "location"
                        ]

                        for group in interestGroups:
                            attr1 = "num_repos_skill_{0}".format(skill)
                            attr2 = "lang_x_stargazers_max_{0}".format(skill)
                            
                            dfGrouped = skillsDataFrame.filter([group, attr1, attr2], axis=1)
                            dfGrouped = dfGrouped.groupby([group]).agg(['sum']).transform(self.dataFrameUtils.makeDatasetResultGB)

                            # Plot the standard deviation
                            resultsObj = dfGrouped.to_dict()
                            insights = {}

                            print("Starting to build insights by location ...")

                            # Build an object that can be saved on the database
                            for keyColumnGroup in resultsObj.keys():
                                rows = resultsObj[keyColumnGroup]

                                for keyRowGroup in rows.keys():

                                    if keyColumnGroup[0] not in insights:
                                        insights[keyColumnGroup[0]] = []

                                    insights[keyColumnGroup[0]].append({
                                        keyRowGroup : rows[keyRowGroup]
                                    })

                            # Store the results in the database
                            for insightKey in insights.keys():
                                xValues = []
                                yValues = []
                                dbObject = {
                                    insightKey : {}
                                }

                                for locationObj in insights[insightKey]:

                                    for key in locationObj.keys():
                                        xValues.append(key)
                                        yValues.append(locationObj[key])
                                        dbObject[insightKey][key] = locationObj[key]
                                    
                                print("\nStoring insight in DB ...")
                                print(json.dumps(dbObject))

                                self.dbManager.updateStatsGroupByMetricsTechSkillsPlatform(token, dbObject)

                                pathFilePlotGroupBy = "images/gpsl_group_skills_by_{0}_x_{1}.png".format(group, insightKey)
                                yPos = np.arange(len(yValues))

                                # Prepare the chart plotter
                                plt.clf()
                                plt.figure(figsize=(30, 15))
                                plt.bar(yPos, yValues, align='center', alpha=0.5)
                                plt.xticks(yPos, xValues)
                                plt.xlabel("Skills")
                                plt.ylabel("{0} x location ".format(insightKey))
                                plt.savefig(pathFilePlotGroupBy)

                                response["group_skills_{0}_x_{1}".format(group, insightKey)] = self.dbManager.storeImage(pathFilePlotGroupBy, token)

                            response["group_skills_by_{0}".format(group)] = insights

                    response["status"] = True
                    response["msg"] = "Success! We've finished the descriptive analysis of the github_profile_skills_location dataset",

                else:
                    response["msg"] = "Invalid access token"

        except Exception as e:
            print("{0} Failed to describeStatsDatasetGithubProfilesSkills: {1}".format(self.TAG, e))

        return json.dumps(response)

    '''
        This method is used to explore the dataset github_profile_skills_location.
        It returns descriptive statistics, the correlation between the main attributes, 
        and visualizations.
    '''
    def describeCorrelationsDatasetGithubProfilesSkills(self, username, password):
        response = {
            "status" : False,
            "msg" : "Failed to describe dataset github_profile_skills_location",
            "spearmans_corr_num_repos_smnr_x_max_num_forks_smnr" : -1,
            "spearmans_corr_num_repos_smnr_x_max_num_watchers_smnr" : -1,
            "spearmans_corr_num_repos_smnr_x_max_num_stars_smnr" : -1,
            "spearmans_corr_max_num_forks_smnr_x_max_num_stars_smnr" : -1,
            "spearmans_corr_max_num_forks_smnr_x_max_num_watchers_smnr" : -1,
            "spearmans_corr_max_num_stars_smnr_x_max_num_watchers_smnr" : -1,
            "spearmans_corr_max_num_stars_smnr_x_latest_created_smnr" : -1,
            "spearmans_corr_max_num_stars_smnr_x_latest_updated_smnr" : -1,
            "spearmans_corr_max_num_stars_smnr_x_latest_pushed_smnr" : -1,
            "spearmans_corr_max_num_stars_smnr_x_latest_size_smnr" : -1,
            "plot_num_repos_smnr_x_max_num_forks_smnr" : "",
            "plot_num_repos_smnr_x_max_num_watchers_smnr" : "",
            "plot_num_repos_smnr_x_max_num_stars_smnr" : "",
            "plot_num_forks_smnr_x_max_num_stars_smnr" : "",
            "plot_num_forks_smnr_x_max_num_watchers_smnr" : "",
            "plot_num_stars_smnr_x_max_num_watchers_smnr" : "",
            "plot_num_stars_smnr_x_latest_created_smnr" : "",
            "plot_num_stars_smnr_x_latest_updated_smnr" : "",
            "plot_num_stars_smnr_x_latest_pushed_smnr" : "",
            "plot_num_stars_smnr_x_latest_size_smnr" : ""
        }

        try:

            if not username or not password:
                response["msg"] = "Invalid access token, please login and try again."

            else:
                token = self.authController.login(username, password)

                if token != "":
                    dataset, _ = self.getDataframeLRAGithubSuccessSkillsAllUsers(token)
                    dataframe = pd.DataFrame.from_records(dataset)
                    dataframe.fillna(0)

                    # Identify the correlation between: num_repos_smnr x max_num_forks_smnr
                    response["spearmans_corr_num_repos_smnr_x_max_num_forks_smnr"],\
                    response["corr_num_repos_smnr_x_max_num_forks_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "num_repos_smnr", 
                        "max_num_forks_smnr", 
                        "Number repos created with smnr (best) skill", 
                        "Max number forks repo created with smnr"
                    )

                    # Identify the correlation between: num_repos_smnr x max_num_watchers_smnr
                    response["spearmans_corr_num_repos_smnr_x_max_num_watchers_smnr"],\
                    response["corr_num_repos_smnr_x_max_num_watchers_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "num_repos_smnr", 
                        "max_num_watchers_smnr", 
                        "Number repos created with smnr (best) skill", 
                        "Max number watchers repo created with smnr"
                    )

                    # Identify the correlation between: num_repos_smnr x max_num_stars_smnr
                    response["spearmans_corr_num_repos_smnr_x_max_num_stars_smnr"],\
                    response["corr_num_repos_smnr_x_max_num_stars_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "num_repos_smnr", 
                        "max_num_stars_smnr", 
                        "Number repos created with smnr (best) skill", 
                        "Max number stars repo created with smnr"
                    )

                    # Identify the correlation between: max_num_forks_smnr x max_num_stars_smnr
                    response["spearmans_corr_max_num_forks_smnr_x_max_num_stars_smnr"],\
                    response["corr_num_forks_smnr_x_max_num_stars_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_forks_smnr", 
                        "max_num_stars_smnr", 
                        "Max number forks repo created with smnr", 
                        "Max number stars repo created with smnr"
                    )

                    # Identify the correlation between: max_num_forks_smnr x max_num_watchers_smnr
                    response["spearmans_corr_max_num_forks_smnr_x_max_num_watchers_smnr"],\
                    response["corr_num_forks_smnr_x_max_num_watchers_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_forks_smnr", 
                        "max_num_watchers_smnr", 
                        "Max number forks repo created with smnr", 
                        "Max number watchers repo created with smnr"
                    )

                    # Identify the correlation between: max_num_stars_smnr x max_num_watchers_smnr
                    response["spearmans_corr_max_num_stars_smnr_x_max_num_watchers_smnr"],\
                    response["corr_num_stars_smnr_x_max_num_watchers_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_stars_smnr", 
                        "max_num_watchers_smnr", 
                        "Max number stars repo created with smnr", 
                        "Max number watchers repo created with smnr"
                    )

                    # Identify the correlation between: max_num_stars_smnr x "latest_created_smnr
                    response["spearmans_corr_max_num_stars_smnr_x_latest_created_smnr"],\
                    response["corr_num_stars_smnr_x_latest_created_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_stars_smnr", 
                        "latest_created_smnr", 
                        "Max number stars repo created with smnr", 
                        "Latest createdAt timestamp repo created with smnr"
                    )

                    # Identify the correlation between: max_num_stars_smnr x "latest_updated_smnr
                    response["spearmans_corr_max_num_stars_smnr_x_latest_updated_smnr"],\
                    response["corr_num_stars_smnr_x_latest_updated_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_stars_smnr", 
                        "latest_updated_smnr", 
                        "Max number stars repo created with smnr", 
                        "Latest updatedAt timestamp repo created with smnr"
                    )

                    # Identify the correlation between: max_num_stars_smnr x "latest_pushed_smnr
                    response["spearmans_corr_max_num_stars_smnr_x_latest_pushed_smnr"],\
                    response["corr_num_stars_smnr_x_latest_pushed_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_stars_smnr", 
                        "latest_pushed_smnr", 
                        "Max number stars repo created with smnr", 
                        "Latest pushedAt timestamp repo created with smnr"
                    )

                    # Identify the correlation between: max_num_stars_smnr x "latest_size_smnr
                    response["spearmans_corr_max_num_stars_smnr_x_latest_size_smnr"],\
                    response["corr_num_stars_smnr_x_latest_size_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_stars_smnr", 
                        "latest_size_smnr", 
                        "Max number stars repo created with smnr", 
                        "Max size repo created with smnr"
                    )

                else:
                    response["msg"] = "Invalid access token"

            response["status"] = True
            response["msg"] = "We got some information abou the githus_profile_skills_location dataset for you!"

        except Exception as e:
            print("{0} Failed to describeCorrelationsDatasetGithubProfilesSkills: {1}".format(self.TAG, e))

        return json.dumps(response)

    ##############
    ## Analysis ##
    ##############
    def clusterUsersSkillsLocation(self, username, password):
        '''
        response = {
            "status" : False,
            "msg" : "Failed to predict trends"
        }

        interestingSkills = [
            "Java",
            "Python",
            "JavaScript",
            "TypeScript",
            "Kotlin",
            "Objective-C",
            "Swift",
            "C++",
            "Ruby",
            "C_|222|_",
            "Clojure",
            "Elixir",
            "Go",
            "Scala",
            "PHP",
            "Eagle",
            "Erlang",
            "Haskell",
            "Lua",
            "PLSQL",
            "R"
        ]

        try:

        if not username or not password:
            response["msg"] = "Invalid access token, please login and try again."

        else:
            #token = self.authController.login(username, password)
            token = "mudar depois dos testes"

            if token != "":
                dataset, _ = self.getDataframeLRAGithubSuccessSkillsAllUsers(token)
                skillsDataFrame = pd.DataFrame.from_records(dataset)

                # Extract and store information about the tech skills available in the platform
                skills = self.getSkillsFromDBKeys(list(skillsDataFrame.columns))
                #self.dbManager.updateListTechSkillsPlatform(token, skills)

                # Descriptive statistics of the dataset grouped by interesting attributes x skill
                toDropInput = []

                for skill in skills.keys():

                    if skill != "Java":
                        toDropInput.append("lang_x_forks_max_{0}".format(skill))
                        toDropInput.append("lang_x_forks_mean_{0}".format(skill))
                        toDropInput.append("lang_x_forks_sum_{0}".format(skill))
                        toDropInput.append("lang_x_stargazers_max_{0}".format(skill))
                        toDropInput.append("lang_x_stargazers_mean_{0}".format(skill))
                        toDropInput.append("lang_x_stargazers_sum_{0}".format(skill))
                        toDropInput.append("lang_x_watchers_max_{0}".format(skill))
                        toDropInput.append("lang_x_watchers_mean_{0}".format(skill))
                        toDropInput.append("lang_x_watchers_sum_{0}".format(skill))
                        toDropInput.append("latest_pushed_at_{0}".format(skill))
                        toDropInput.append("latest_updated_at_{0}".format(skill))
                        toDropInput.append("latest_created_at_{0}".format(skill))
                        toDropInput.append("latest_size_{0}".format(skill))
                        toDropInput.append("num_repos_skill_{0}".format(skill))
                        toDropInput.append("github_userid")
                        toDropInput.append("strong_repo")
                        toDropInput.append("location")
                        toDropInput.append("latest_updated_smnr")
                        toDropInput.append("max_num_forks_smnr")
                        toDropInput.append("max_num_stars_smnr")
                        toDropInput.append("max_num_watchers_smnr")
                        toDropInput.append("smnr_was_max_forks")
                        toDropInput.append("smnr_was_max_stars")
                        toDropInput.append("smnr_was_max_watchers")
                        toDropInput.append("strong_language")
                        toDropInput.append("latest_pushed_smnr")
                        toDropInput.append("latest_size_smnr")
                        toDropInput.append("num_repos_smnr")
                        toDropInput.append("was_smrn_repo_relatively_successful")

                toDrop = self.dataFrameUtils.getColumnsToDrop(skillsDataFrame, toDropInput)
                skillsDataFrame.drop(toDrop, inplace=True, axis=1)
                skillsDataFrame.dropna(inplace=True)

                print(skillsDataFrame.head())

                

                kmeans = KMeans(n_clusters=2, random_state=0)
                kmeans.fit(skillsDataFrame)
                print(kmeans.labels_)
                print(kmeans.cluster_centers_)
        '''
        

    '''
        H1 - Dada uma série com o número de repositórios criados por mês em uma linguagem, qual será o possível número de 
        repositórios criados na mesma linguagem no próximo mês?
    '''
    def predictGithubSkillTrendsWorldwide(self, username, password):
        response = {
            "status" : False,
            "msg" : "Failed to predict trends"
        }

        interestingSkills = [
            "Java",
            "Python",
            "JavaScript",
            "TypeScript",
            "Kotlin",
            "Objective-C",
            "Swift",
            "C++",
            "Ruby",
            "C_|222|_",
            "Clojure",
            "Elixir",
            "Go",
            "Scala",
            "PHP",
            "Eagle",
            "Erlang",
            "Haskell",
            "Lua",
            "PLSQL",
            "R"
        ]

        try:

            if not username or not password:
                response["msg"] = "Invalid access token, please login and try again."

            else:
                #token = self.authController.login(username, password)
                token = "mudar depois dos testes"

                if token != "":
                    dataset, _ = self.getDataframeLRAGithubSuccessSkillsAllUsers(token)
                    skillsDataFrame = pd.DataFrame.from_records(dataset)

                    # Extract and store information about the tech skills available in the platform
                    skills = self.getSkillsFromDBKeys(list(skillsDataFrame.columns))
                    #self.dbManager.updateListTechSkillsPlatform(token, skills)

                    # Descriptive statistics of the dataset grouped by interesting attributes x skill
                    toDropInput = []

                    for skill in skills.keys():
                        toDropInput.append("lang_x_forks_max_{0}".format(skill))
                        toDropInput.append("lang_x_forks_mean_{0}".format(skill))
                        toDropInput.append("lang_x_forks_sum_{0}".format(skill))
                        toDropInput.append("lang_x_stargazers_max_{0}".format(skill))
                        toDropInput.append("lang_x_stargazers_mean_{0}".format(skill))
                        toDropInput.append("lang_x_stargazers_sum_{0}".format(skill))
                        toDropInput.append("lang_x_watchers_max_{0}".format(skill))
                        toDropInput.append("lang_x_watchers_mean_{0}".format(skill))
                        toDropInput.append("lang_x_watchers_sum_{0}".format(skill))
                        toDropInput.append("latest_pushed_at_{0}".format(skill))
                        toDropInput.append("latest_updated_at_{0}".format(skill))
                        toDropInput.append("latest_size_{0}".format(skill))
                        toDropInput.append("num_repos_skill_{0}".format(skill))
                        toDropInput.append("github_userid")
                        toDropInput.append("strong_repo")
                        toDropInput.append("latest_updated_smnr")
                        toDropInput.append("location")
                        toDropInput.append("max_num_forks_smnr")
                        toDropInput.append("max_num_stars_smnr")
                        toDropInput.append("max_num_watchers_smnr")
                        toDropInput.append("smnr_was_max_forks")
                        toDropInput.append("smnr_was_max_stars")
                        toDropInput.append("smnr_was_max_watchers")
                        toDropInput.append("strong_language")
                        toDropInput.append("latest_pushed_smnr")
                        toDropInput.append("latest_size_smnr")
                        toDropInput.append("num_repos_smnr")
                        toDropInput.append("was_smrn_repo_relatively_successful")

                    toDrop = self.dataFrameUtils.getColumnsToDrop(skillsDataFrame, toDropInput)
                    skillsDataFrame.drop(toDrop, inplace=True, axis=1)

                    for skill in interestingSkills:
                        keyTSSkill = "latest_created_at_{0}".format(skill)

                        if pd.Series(keyTSSkill).isin(skillsDataFrame.columns).all():
                            skillTSDateTime = skillsDataFrame[keyTSSkill]
                            skillTSDateTime.dropna(inplace=True)

                            # Build a dataset grouped by year
                            skillTSYear = skillTSDateTime.map(lambda x: time.strftime('%Y', time.localtime(x))).sort_values(ascending=True)

                            if skillTSYear is not None:

                                if len(skillTSYear) > 1:
                                    df1 = skillTSYear.to_frame(name='year')
                                    df1.set_index('year')
                                    df1['num_created'] = 1

                                    groupNumProjectsYear = df1.groupby('year')['num_created'].count().transform(self.dataFrameUtils.makeDatasetResultGB)
                                    years = self.getGroupByLabelsAsSeries(groupNumProjectsYear)
                                    nextYear = int(years.values[-1]) + 1

                                    if len(years) > 3:

                                        # Linear Regression
                                        rmseLR, seriesWithPredictionLR, predictedValueLR = self.linearRegression(years, groupNumProjectsYear.values, nextYear)
                                        plotNameLR = self.plotSeriesWithLegend(
                                            years,
                                            groupNumProjectsYear.values,
                                            seriesWithPredictionLR,
                                            "images/gpsl_predict_lr_x_{0}.png".format(skill), 
                                            "Actual values", 
                                            "Predictions", 
                                            "Number projects created with the skill", 
                                            "Years",
                                            "Linear Regression"
                                        )

                                        response["pred_lr_{0}_rmse".format(keyTSSkill)] = rmseLR
                                        response["pred_lr_{0}_time_series".format(keyTSSkill)] = years.tolist()
                                        response["pred_lr_{0}_actual_vals".format(keyTSSkill)] = groupNumProjectsYear.tolist()
                                        response["pred_lr_{0}_predictions".format(keyTSSkill)] = seriesWithPredictionLR.tolist()
                                        response["pred_lr_{0}_next_predicted_value".format(keyTSSkill)] = predictedValueLR
                                        response["pred_lr_{0}_path_pred_plot".format(keyTSSkill)] = plotNameLR

                                        # Regression with SVR
                                        rmseSvr, seriesWithPredictionSvr, predictedValueSvr = self.svrRegression(years, groupNumProjectsYear.values, nextYear)
                                        plotNameSvr = self.plotSeriesWithLegend(
                                            years,
                                            groupNumProjectsYear.values,
                                            seriesWithPredictionSvr,
                                            "images/gpsl_predict_svr_x_{0}.png".format(skill), 
                                            "Actual values", 
                                            "Predictions", 
                                            "Number projects created with the skill", 
                                            "Years",
                                            "Support Vector Regression"
                                        )

                                        response["pred_svr_{0}_rmse".format(keyTSSkill)] = rmseSvr
                                        response["pred_svr_{0}_time_series".format(keyTSSkill)] = years.tolist()
                                        response["pred_svr_{0}_actual_vals".format(keyTSSkill)] = groupNumProjectsYear.tolist()
                                        response["pred_svr_{0}_predictions".format(keyTSSkill)] = seriesWithPredictionSvr.tolist()
                                        response["pred_svr_{0}_next_predicted_value".format(keyTSSkill)] = predictedValueSvr
                                        response["pred_svr_{0}_path_pred_plot".format(keyTSSkill)] = plotNameSvr

                                    # Build a dataset grouped by month
                                    skillTSMonth = skillTSDateTime.map(lambda x: time.strftime('%Y-%m', time.localtime(x))).sort_values(ascending=True)

                                    df2 = skillTSMonth.to_frame(name='month')
                                    df2.set_index('month')
                                    df2['num_created'] = 1

                                    groupNumProjectsMonth = df2.groupby('month')['num_created'].count().transform(self.dataFrameUtils.makeDatasetResultGB)

                                    if len(groupNumProjectsMonth.values) > 6:

                                        # Regression with Long Short-Term Memory Network - LSTM
                                        rmseLstm, actualValuesLstm, predictionsLstm = self.regressionLstm(groupNumProjectsMonth.values, keyTSSkill, 1)
                                        actualValuesLstm = actualValuesLstm[:-1]
                                        plotNameLstm = "images/gpsl_predict_lstm_x_{0}.png".format(skill)

                                        plt.clf()
                                        plt.plot(actualValuesLstm, label="Actual values")
                                        plt.plot(predictionsLstm, label="Predictions")
                                        plt.title("Long Short-Term Memory Network - LSTM")
                                        plt.legend(loc='upper left')
                                        plt.ylabel("Number projects created with the skill")
                                        plt.xlabel("Months")
                                        plt.savefig(plotNameLstm)

                                        response["pred_lstm_{0}_rmse".format(keyTSSkill)] = rmseLstm
                                        response["pred_lstm_{0}_path_pred_plot".format(keyTSSkill)] = plotNameLstm
                                        response["pred_lstm_{0}_actual_vals".format(keyTSSkill)] = actualValuesLstm
                                        response["pred_lstm_{0}_predictions".format(keyTSSkill)] = predictionsLstm

                        # N - Fetch a successful response to the user
                        response["status"] = True
                        response["msg"] = "We found your data!"

        except ValueError as ve:
            print("{0} Failed to lRAGithubSuccessSkillsAllUsers: {1}".format(self.TAG, ve))

        return json.dumps(response)

    ######################################
    ## Descriptive statistics functions ##
    ######################################
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
                    cleanedProfileSkills = self.getCleanedProfileSkills(profileSkills)

                    try:
                        skillMaxNumRepos = self.getSkillMaxNumRepos(cleanedProfileSkills)

                        if skillMaxNumRepos != "":

                            if "num_repos_skill_{0}".format(skillMaxNumRepos) in cleanedProfileSkills:
                                numReposMaxNumReposSkill = cleanedProfileSkills["num_repos_skill_{0}".format(skillMaxNumRepos)]

                            if "lang_x_forks_max_{0}".format(skillMaxNumRepos) in cleanedProfileSkills:
                                maxNumForksSkillMaxNumRepos = cleanedProfileSkills["lang_x_forks_max_{0}".format(skillMaxNumRepos)]

                            if "lang_x_stargazers_max_{0}".format(skillMaxNumRepos) in cleanedProfileSkills:
                                maxNumStargazersSkillMaxNumRepos = cleanedProfileSkills["lang_x_stargazers_max_{0}".format(skillMaxNumRepos)]

                            if "lang_x_watchers_max_{0}".format(skillMaxNumRepos) in cleanedProfileSkills:
                                maxNumWatchersSkillMaxNumRepos = cleanedProfileSkills["lang_x_watchers_max_{0}".format(skillMaxNumRepos)]

                            if "latest_created_at_{0}".format(skillMaxNumRepos) in cleanedProfileSkills:
                                latestCreatedAt = cleanedProfileSkills["latest_created_at_{0}".format(skillMaxNumRepos)]

                            if "latest_updated_at_{0}".format(skillMaxNumRepos) in cleanedProfileSkills:
                                latestUpdatedAt = cleanedProfileSkills["latest_updated_at_{0}".format(skillMaxNumRepos)]

                            if "latest_pushed_at_{0}".format(skillMaxNumRepos) in cleanedProfileSkills:
                                latestPushedAt = cleanedProfileSkills["latest_pushed_at_{0}".format(skillMaxNumRepos)]

                            if "latest_size_{0}".format(skillMaxNumRepos) in cleanedProfileSkills:
                                size = cleanedProfileSkills["latest_size_{0}".format(skillMaxNumRepos)]

                            skillMaxNumReposWasMaxForks = self.wasSkillMaxNumReposMaxX("lang_x_watchers_max_", skillMaxNumRepos, cleanedProfileSkills)                               
                            skillMaxNumReposWasMaxStars = self.wasSkillMaxNumReposMaxX("lang_x_forks_max_", skillMaxNumRepos, cleanedProfileSkills)
                            skillMaxNumReposWasMaxWatchers = self.wasSkillMaxNumReposMaxX("lang_x_stargazers_max_", skillMaxNumRepos, cleanedProfileSkills)
                            wasSmrnRepoRelativelySuccessful = self.wasSmrnRepoRelativelySuccessful(cleanedProfileSkills, skillMaxNumRepos)

                            if numReposMaxNumReposSkill and \
                               maxNumForksSkillMaxNumRepos and \
                               maxNumStargazersSkillMaxNumRepos and \
                               maxNumWatchersSkillMaxNumRepos and \
                               skillMaxNumReposWasMaxForks and \
                               skillMaxNumReposWasMaxStars and \
                               skillMaxNumReposWasMaxWatchers and \
                               latestCreatedAt and \
                               latestUpdatedAt and \
                               latestPushedAt and \
                               wasSmrnRepoRelativelySuccessful != -1 and \
                               size:

                                cleanedProfileSkills["num_repos_smnr"] = numReposMaxNumReposSkill
                                cleanedProfileSkills["max_num_forks_smnr"] = maxNumForksSkillMaxNumRepos
                                cleanedProfileSkills["max_num_stars_smnr"] = maxNumStargazersSkillMaxNumRepos
                                cleanedProfileSkills["max_num_watchers_smnr"] = maxNumWatchersSkillMaxNumRepos
                                cleanedProfileSkills["smnr_was_max_forks"] = skillMaxNumReposWasMaxForks
                                cleanedProfileSkills["smnr_was_max_stars"] = skillMaxNumReposWasMaxStars
                                cleanedProfileSkills["smnr_was_max_watchers"] = skillMaxNumReposWasMaxWatchers
                                cleanedProfileSkills["latest_created_smnr"] = latestCreatedAt
                                cleanedProfileSkills["latest_updated_smnr"] = latestUpdatedAt
                                cleanedProfileSkills["latest_pushed_smnr"] = latestPushedAt
                                cleanedProfileSkills["latest_size_smnr"] = size
                                cleanedProfileSkills["was_smrn_repo_relatively_successful"] = wasSmrnRepoRelativelySuccessful

                                moreDetailsDatasetRow = {
                                    "idx" : idx,
                                    "github_userid" : cleanedProfileSkills["github_userid"],
                                    "strong_repo" : cleanedProfileSkills["strong_repo"],
                                    "skill_max_num_repos" : skillMaxNumRepos
                                }

                                jsonDataset.append(cleanedProfileSkills)
                                moreDetailsDatasetRows.append(moreDetailsDatasetRow)

                    except Exception as e:
                        print("{0} Discarded a sample from the dataset : {1}".format(self.TAG, e))

        except Exception as e:
            print("{0} Failed to get getDataframeLRAGithubSuccessSkillsAllUsers {1}".format(self.TAG, e))

        return jsonDataset, moreDetailsDatasetRows

    '''
        Returns a profileSkills object without 'dirty/should_not_exist' db keys.
    '''
    def getCleanedProfileSkills(self, rawProfileSkills):
        cleanedProfileSkills = {}
        regexFindKey = re.compile(r": ")

        try:

            for key in rawProfileSkills.keys():

                if not regexFindKey.search(key):
                    cleanedProfileSkills[key] = rawProfileSkills[key]

        except Exception as e:
            print("{0} Failed to getCleanedProfileSkills: {1}".format(self.TAG, e))

        return cleanedProfileSkills

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

            if skillMaxNumRepos == skillMaxNumX:
                return 1

        except Exception as e:
            print("{0} Failed to verify if wasSkillMaxNumReposMaxX: {1}".format(self.TAG, e))

        return 0

    '''
        Return the Pearson's correlation between two variables and a chart that plots the 
        relationship.
    '''
    def getSpearmansCorrelationPlotTwoVariables(self, token, dataFrame, nameVar1, nameVar2, labelX, labelY):
        correlation = ""
        plotUrl = ""

        try:
            corrSmnrStarsSize, _ = spearmanr(dataFrame[nameVar1], dataFrame[nameVar2])
            correlation = corrSmnrStarsSize

            print("Spearmans correlation {0} x {1}: {2}".format(nameVar1, nameVar2, corrSmnrStarsSize))

            pathFilePlot = "images/gpsl_corr_{0}_x_{1}.png".format(nameVar1, nameVar2)

            plt.clf()
            plt.figure(figsize=(15, 15))
            plt.scatter(dataFrame[nameVar1], dataFrame[nameVar2], c='b', s=40, alpha=0.5)
            plt.xlabel(labelX)
            plt.ylabel(labelY)
            plt.savefig(pathFilePlot)
            plotUrl = self.dbManager.storeImage(pathFilePlot, token)

        except Exception as e:
            print("{0} Failed to getCorrelationPlotTwoVariables: {1}".format(self.TAG, e))

        return correlation, plotUrl

    '''
        Given a list of database keys, which contain prefixes that improve the querying 
        process, return a list only with the name of the skills contained in the dataset.
    '''
    def getSkillsFromDBKeys(self, dbKeys):
        skills = {}
        regexFindKey = re.compile(r"num_repos_skill_")

        try:

            for key in dbKeys:

                if regexFindKey.search(key):
                    skillName = key.replace("num_repos_skill_","")

                    if skillName:

                        if skillName not in skills:
                            skills[skillName] = 0

                        skills[skillName] += 1

        except Exception as e:
            print("{0} Failed to getSkillsFromDBKeys: {1}".format(self.TAG, e))

        return skills

    '''
        Returns:
            1 if a repository met certain performance metrics and, was considered successful
            0 wasn't successful
            -1 failed to determine success
    '''
    def wasSmrnRepoRelativelySuccessful(self, profileSkills, smnr):
        bestNumStars = -1
        bestNumForks = -1
        bestNumWatchers = -1

        try:

            if "lang_x_stargazers_max_{0}".format(smnr) in profileSkills:
                bestNumStars = profileSkills["lang_x_stargazers_max_{0}".format(smnr)]

            if "lang_x_forks_max_{0}".format(smnr) in profileSkills:
                bestNumForks = profileSkills["lang_x_forks_max_{0}".format(smnr)]

            if "lang_x_watchers_max_{0}".format(smnr) in profileSkills:
                bestNumWatchers = profileSkills["lang_x_watchers_max_{0}".format(smnr)]

            if bestNumStars != -1 and bestNumForks != -1 and bestNumWatchers != -1:

                if bestNumStars >= self.constUtils.NUM_STARS_SUCCESSFUL_REPO and \
                   bestNumWatchers >= self.constUtils.NUM_WATCHERS_SUCCESSFUL_REPO and \
                   bestNumForks >= self.constUtils.NUM_FORKS_SUCCESSFUL_REPO:

                    return 1
            else:
                return -1

        except Exception as e:
            print("{0} Failed to wasSmrnRepoRelativelySuccessful: {1}".format(self.TAG, e))

        return 0

    ###############################
    ## LSTM Regression Technique ##
    ###############################
    '''
        Using the sliding window method, to addapt a time series to a supervised learning algorithm.
        Reference: https://machinelearningmastery.com/time-series-forecasting-long-short-term-memory-network-python/
    '''
    def regressionLstm(self, series, skill, repeats):
        print("DNN - LSTM Regression")

        # transform data to be stationary
        raw_values = series
        diff_values = self.difference(raw_values, 1)

        # transform data to be supervised learning
        supervised = self.timeseries_to_supervised(diff_values, 1)
        supervised_values = supervised.values

        # split data into train and test-sets
        splitValue = -int(len(supervised_values) * 0.3)
        train, test = supervised_values[0:splitValue], supervised_values[splitValue:]

        # transform the scale of the data
        scaler, train_scaled, test_scaled = self.scale(train, test)

        # repeat experiment
        error_scores = list()
        predictions = list()

        for r in range(repeats):
            # fit the model
            lstm_model = self.fit_lstm(train_scaled, 1, 3000, 4)

            # forecast the entire training dataset to build up state for forecasting
            train_reshaped = train_scaled[:, 0].reshape(len(train_scaled), 1, 1)
            lstm_model.predict(train_reshaped, batch_size=1)

            # walk-forward validation on the test data
            predictions = list()

            for i in range(len(test_scaled)):
                # make one-step forecast
                X, y = test_scaled[i, 0:-1], test_scaled[i, -1]
                yhat = self.forecast_lstm(lstm_model, 1, X)

                # invert scaling
                yhat = self.invert_scale(scaler, X, yhat)

                # invert differencing
                yhat = self.inverse_difference(raw_values, yhat, len(test_scaled)+1-i)

                # store forecast
                predictions.append(yhat)
                expected = raw_values[len(train) + i + 1]
                print('Month=%d, Predicted=%f, Expected=%f' % (i+1, yhat, expected))

            # report performance
            rmse = sqrt(mean_squared_error(raw_values[splitValue:], predictions))
            print('%d) Test RMSE: %.3f' % (r+1, rmse))
            error_scores.append(rmse)

        # summarize results
        results = pd.DataFrame()
        results['rmse'] = error_scores
        mean_rmse = results['rmse'].mean()

        return mean_rmse, raw_values[splitValue:].tolist(), predictions

    # frame a sequence as a supervised learning problem
    def timeseries_to_supervised(self, data, lag=1):
        df = pd.DataFrame(data)
        columns = [df.shift(i) for i in range(1, lag+1)]
        columns.append(df)
        df = pd.concat(columns, axis=1)
        df.fillna(0, inplace=True)
        return df

    # create a differenced series
    def difference(self, dataset, interval=1):
        diff = list()
        for i in range(interval, len(dataset)):
            value = dataset[i] - dataset[i - interval]
            diff.append(value)
        return pd.Series(diff)

    # invert differenced value
    def inverse_difference(self, history, yhat, interval=1):
        return yhat + history[-interval]

    # scale train and test data to [-1, 1]
    def scale(self, train, test):
        # fit scaler
        scaler = MinMaxScaler(feature_range=(-1, 1))
        scaler = scaler.fit(train)
        # transform train
        train = train.reshape(train.shape[0], train.shape[1])
        train_scaled = scaler.transform(train)
        # transform test
        test = test.reshape(test.shape[0], test.shape[1])
        test_scaled = scaler.transform(test)
        return scaler, train_scaled, test_scaled
    
    # inverse scaling for a forecasted value
    def invert_scale(self, scaler, X, value):
        new_row = [x for x in X] + [value]
        array = np.array(new_row)
        array = array.reshape(1, len(array))
        inverted = scaler.inverse_transform(array)
        return inverted[0, -1]

    # fit an LSTM network to training data
    def fit_lstm(self, train, batch_size, nb_epoch, neurons):
        X, y = train[:, 0:-1], train[:, -1]
        X = X.reshape(X.shape[0], 1, X.shape[1])
        model = Sequential()
        model.add(LSTM(neurons, batch_input_shape=(batch_size, X.shape[1], X.shape[2]), stateful=True))
        model.add(Dense(1))
        model.compile(loss='mean_squared_error', optimizer='adam')
        for i in range(nb_epoch):
            model.fit(X, y, epochs=1, batch_size=batch_size, verbose=0, shuffle=False)
            model.reset_states()
        return model
    
    # make a one-step forecast
    def forecast_lstm(self, model, batch_size, X):
        X = X.reshape(1, 1, len(X)) # <<<< Look at what is here
        yhat = model.predict(X, batch_size=batch_size)
        return yhat[0,0]

    ##############################
    ## SVR Regression Technique ##
    ##############################
    '''
        Reference: https://machinelearningmastery.com/time-series-forecasting-supervised-learning/
                   http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html
    '''
    def svrRegression(self, X, y, nextX):
        print('SVR Regression')

        X = X.reshape(-1, 1)
        nextX = [[nextX]]
        
        # create the model
        svr_rbf = SVR(kernel='rbf', C=1e3, gamma=0.1)
        error_scores = list()

        # use kfolds to test,train the data
        kf = KFold(n_splits=4)
        kf.get_n_splits(X)

        for train_index, test_index in kf.split(X):
            X_train, X_test = X[train_index], X[test_index]
            y_train, y_test = y[train_index], y[test_index]

            # fit the model
            svr_rbf.fit(X_train, y_train)

            # forecast the test dataset
            y_forecast = svr_rbf.predict(X_test)

            # report performance
            rmse = sqrt(mean_squared_error(y_test, y_forecast))
            error_scores.append(rmse)

        # report performance
        results = pd.DataFrame()
        results['rmse'] = error_scores
        rmseRbf = results['rmse'].mean()

        print("RMSE: {0}".format(rmseRbf))

        # Predict the whole dataset only to show how the model is almost going to overfit
        y_forecast = svr_rbf.predict(X)
        y_rbf = svr_rbf.predict(nextX)
        y_forecast = np.append(y_forecast, y_rbf)

        return rmseRbf, y_forecast, y_rbf[0]

    '''
        Reference: https://medium.com/@gr33ndata/learn-regressions-analysis-23b789bf2c36
                   http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html
    '''
    def linearRegression(self, X, y, nextX):
        print('Linear Regression')

        X = X.reshape(-1, 1)
        nextX = [[nextX]]
        
        # Initialize the model then train it on the data
        lr_model = LinearRegression(normalize=True)

        error_scores = list()

        # use kfolds to test,train the data
        kf = KFold(n_splits=4)
        kf.get_n_splits(X)

        for train_index, test_index in kf.split(X):
            X_train, X_test = X[train_index], X[test_index]
            y_train, y_test = y[train_index], y[test_index]

            # fit the model
            lr_model.fit(X_train,y_train)

            # forecast the test dataset
            y_forecast = lr_model.predict(X_test)

            # report performance
            rmse = sqrt(mean_squared_error(y_test, y_forecast))
            error_scores.append(rmse)

        # report performance
        results = pd.DataFrame()
        results['rmse'] = error_scores
        rmseLR = results['rmse'].mean()

        print("RMSE: {0}".format(rmseLR))

        # Forecast the whole dataset again only to show all the plots of the model
        y_forecast = lr_model.predict(X)
        y_lr = lr_model.predict(nextX)
        y_forecast = np.append(y_forecast, y_lr)

        return rmseLR, y_forecast, y_lr[0]

    #####################
    ## Other functions ##
    #####################
    '''
        Print a chart with two Series and a legend
    '''
    def plotSeriesWithLegend(self, seriesX, seriesA, seriesB, namePlot, labelSeriesA, labelSeriesB, xLabel, yLabel, title):

        try:
            plt.clf()
            plt.scatter(range(0, len(seriesX)), seriesA, color='darkorange', label=labelSeriesA)
            plt.plot(seriesB, linestyle='solid', color='#9A30AE', label=labelSeriesB)
            plt.title(title)
            plt.legend(loc='upper left')
            plt.ylabel(xLabel)
            plt.xlabel(yLabel)
            plt.savefig(namePlot)

        except Exception as e:
            print('Failed to plotSeriesWithLegend {0}'.format(e))

        return namePlot

    '''
        Return a dataframe with the labels that were the result of a group by
    '''
    def getGroupByLabelsAsSeries(self, grouped):
        resultsObj = grouped.to_dict()
        newColumn = []

        # Build an object that can be saved on the database
        for key in resultsObj.keys():
            newColumn.append(key)

        return pd.Series(newColumn)
