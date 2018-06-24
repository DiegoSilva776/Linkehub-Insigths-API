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
from utils.DataframeUtils import DataframeUtils
from utils.StringUtils import StringUtils
from controllers.AuthController import AuthController
from controllers.GithubController import GithubController
from persistence.DBController import DBManager
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from scipy.stats import spearmanr

'''
    The methods of this class create analysis of the data and return the results in JSON format.
'''
class AnalysisController():

    def __init__(self):
        self.TAG = "AnalysisController"

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

                        # Plot the sum
                        pathFilePlotSum = "images/descriptive_analysis_gpsl_{0}_x_{1}.png".format("skills_sum", attr)
                        yPos = np.arange(len(xSkillNames))

                        plt.figure(figsize=(30, 15))
                        plt.bar(yPos, ySumAttr, align='center', alpha=0.5)
                        plt.xticks(yPos, xSkillNames, rotation='vertical')
                        plt.xlabel("Skills")
                        plt.ylabel("Sum of {0}".format(attr))
                        plt.savefig(pathFilePlotSum)

                        response["dataset_sum_{0}".format(attr)] = ySumAttr
                        response["plot_skills_sum_x_{0}".format(attr)] = self.dbManager.storeImage(pathFilePlotSum, token)

                        # Plot the mean
                        pathFilePlotMean = "images/descriptive_analysis_gpsl_{0}_x_{1}.png".format("skills_mean", attr)
                        yPos = np.arange(len(xSkillNames))

                        plt.figure(figsize=(30, 15))
                        plt.bar(yPos, yAvgAttr, align='center', alpha=0.5)
                        plt.xticks(yPos, xSkillNames, rotation='vertical')
                        plt.xlabel("Skills")
                        plt.ylabel("Mean values of {0}".format(attr))
                        plt.savefig(pathFilePlotMean)

                        response["dataset_mean_{0}".format(attr)] = yAvgAttr
                        response["plot_skills_mean_x_{0}".format(attr)] = self.dbManager.storeImage(pathFilePlotMean, token)

                        # Plot the standard deviation
                        pathFilePlotStdDev = "images/descriptive_analysis_gpsl_{0}_x_{1}.png".format("skills_std_dev", attr)
                        yPos = np.arange(len(xSkillNames))

                        plt.figure(figsize=(30, 15))
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
                            
                            #dfGrouped = pd.DataFrame(zip(skillsDataFrame[attr1], skillsDataFrame[attr2], skillsDataFrame[attr3], skillsDataFrame[attr4]))
                            f = lambda x: x.tail(len(x))

                            dfGrouped = skillsDataFrame.filter([group, attr1, attr2], axis=1)
                            dfGrouped = dfGrouped.groupby([group]).agg(['sum']).transform(f)

                            # Plot the standard deviation
                            resultsObj = dfGrouped.to_dict()
                            insights = {}

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
                                
                                pathFilePlotGroupBy = "images/group_skills_by_{0}_x_{1}.png".format(group, insightKey)
                                yPos = np.arange(len(yValues))
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
                    response["plot_num_repos_smnr_x_max_num_forks_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "num_repos_smnr", 
                        "max_num_forks_smnr", 
                        "Number repos created with smnr (best) skill", 
                        "Max number forks repo created with smnr"
                    )

                    # Identify the correlation between: num_repos_smnr x max_num_watchers_smnr
                    response["spearmans_corr_num_repos_smnr_x_max_num_watchers_smnr"],\
                    response["plot_num_repos_smnr_x_max_num_watchers_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "num_repos_smnr", 
                        "max_num_watchers_smnr", 
                        "Number repos created with smnr (best) skill", 
                        "Max number watchers repo created with smnr"
                    )

                    # Identify the correlation between: num_repos_smnr x max_num_stars_smnr
                    response["spearmans_corr_num_repos_smnr_x_max_num_stars_smnr"],\
                    response["plot_num_repos_smnr_x_max_num_stars_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "num_repos_smnr", 
                        "max_num_stars_smnr", 
                        "Number repos created with smnr (best) skill", 
                        "Max number stars repo created with smnr"
                    )

                    # Identify the correlation between: max_num_forks_smnr x max_num_stars_smnr
                    response["spearmans_corr_max_num_forks_smnr_x_max_num_stars_smnr"],\
                    response["plot_num_forks_smnr_x_max_num_stars_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_forks_smnr", 
                        "max_num_stars_smnr", 
                        "Max number forks repo created with smnr", 
                        "Max number stars repo created with smnr"
                    )

                    # Identify the correlation between: max_num_forks_smnr x max_num_watchers_smnr
                    response["spearmans_corr_max_num_forks_smnr_x_max_num_watchers_smnr"],\
                    response["plot_num_forks_smnr_x_max_num_watchers_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_forks_smnr", 
                        "max_num_watchers_smnr", 
                        "Max number forks repo created with smnr", 
                        "Max number watchers repo created with smnr"
                    )

                    # Identify the correlation between: max_num_stars_smnr x max_num_watchers_smnr
                    response["spearmans_corr_max_num_stars_smnr_x_max_num_watchers_smnr"],\
                    response["plot_num_stars_smnr_x_max_num_watchers_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_stars_smnr", 
                        "max_num_watchers_smnr", 
                        "Max number stars repo created with smnr", 
                        "Max number watchers repo created with smnr"
                    )

                    # Identify the correlation between: max_num_stars_smnr x "latest_created_smnr
                    response["spearmans_corr_max_num_stars_smnr_x_latest_created_smnr"],\
                    response["plot_num_stars_smnr_x_latest_created_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_stars_smnr", 
                        "latest_created_smnr", 
                        "Max number stars repo created with smnr", 
                        "Latest createdAt timestamp repo created with smnr"
                    )

                    # Identify the correlation between: max_num_stars_smnr x "latest_updated_smnr
                    response["spearmans_corr_max_num_stars_smnr_x_latest_updated_smnr"],\
                    response["plot_num_stars_smnr_x_latest_updated_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_stars_smnr", 
                        "latest_updated_smnr", 
                        "Max number stars repo created with smnr", 
                        "Latest updatedAt timestamp repo created with smnr"
                    )

                    # Identify the correlation between: max_num_stars_smnr x "latest_pushed_smnr
                    response["spearmans_corr_max_num_stars_smnr_x_latest_pushed_smnr"],\
                    response["plot_num_stars_smnr_x_latest_pushed_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
                        token, 
                        dataframe, 
                        "max_num_stars_smnr", 
                        "latest_pushed_smnr", 
                        "Max number stars repo created with smnr", 
                        "Latest pushedAt timestamp repo created with smnr"
                    )

                    # Identify the correlation between: max_num_stars_smnr x "latest_size_smnr
                    response["spearmans_corr_max_num_stars_smnr_x_latest_size_smnr"],\
                    response["plot_num_stars_smnr_x_latest_size_smnr"] = self.getSpearmansCorrelationPlotTwoVariables(
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
    '''
        H0 - Quanto maior for o número de projetos feitos por um usuário em uma dada tecnologia predominante, 
        maiores são as chances de os repositórios mais bem sucedidos deste usuário, considerando o números de forks, 
        estrelas e downloads como indicadores de sucesso, terem sido feitos naquela tecnologia predominante. 
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
                    dataset, moreDetailsDatasetRows = self.getDataframeLRAGithubSuccessSkillsAllUsers(token)
                    dataframe = pd.DataFrame.from_records(dataset)

                    print(dataframe.head())

                    '''
                    # 1 - Run the linear regression analysis over the dataset: num_repos_smnr x max_num_forks_smnr
                    
                    X = dataframe.drop(['idx', 'max_num_forks_smnr'], axis=1)
                    lm0 = LinearRegression(normalize=True)
                    lm0.fit(X, dataframe["max_num_forks_smnr"])

                    print("Estimated intercept coefficient: {0}".format(lm0.intercept_))
                    print("Number of coefficients: {0}".format(lm0.coef_))

                    dataframeFeatures = pd.DataFrame(list(zip(X.columns.values, lm0.coef_)), columns=['features', 'estimated_coefficients'])
                    print(dataframeFeatures)

                    plt.scatter(dataframe["num_repos_smnr"], dataframe["max_num_forks_smnr"], c='b', s=40, alpha=0.5)
                    plt.xlabel("Number repos created with smnr (best) skill")
                    plt.ylabel("Max number forks created with smnr")
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

                    plt.scatter(dataframe["num_repos_smnr"], dataframe["max_num_stars_smnr"], c='b', s=40, alpha=0.5)
                    plt.xlabel("Number repos created with smnr (best) skill")
                    plt.ylabel("Max number stars repo created with smnr")
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
                    plt.xlabel("Number repos created with smnr (best) skill")
                    plt.ylabel("Max number watchers repo created with smnr")
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
                    print(np.mean((Y_train - pred_train) ** 2))

                    print("Fit a model X_train, calculate MSE with Y_test")
                    print(np.mean((Y_test - pred_test) ** 2))

                    plt.scatter(pred_train, pred_train - Y_train, c='b', s=40, alpha=0.5)
                    plt.scatter(pred_test, pred_test - Y_test, c='g', s=40, alpha=0.5)
                    plt.hlines(y = 0, xmin = 0, xmax = 5000)
                    plt.xlabel("Predicted train/test value")
                    plt.ylabel("Predicted value - Actual value")
                    plt.savefig('images/linear_regression_results_train_x_test_errors.png')
                    '''

                    # N - Fetch a successful response to the user
                    response["status"] = True
                    response["msg"] = "We found your data!"
                    response["json_dataset"] = dataset
                    response["more_details_dataset_rows"] = moreDetailsDatasetRows

        except ValueError as ve:
            print("{0} Failed to lRAGithubSuccessSkillsAllUsers: {1}".format(self.TAG, ve))

        return json.dumps(response)


    ###################
    ## Aux functions ##
    ###################
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

                            if "num_repos_skill_{0}".format(skillMaxNumRepos) in profileSkills:
                                numReposMaxNumReposSkill = profileSkills["num_repos_skill_{0}".format(skillMaxNumRepos)]

                            if "lang_x_forks_max_{0}".format(skillMaxNumRepos) in profileSkills:
                                maxNumForksSkillMaxNumRepos = profileSkills["lang_x_forks_max_{0}".format(skillMaxNumRepos)]

                            if "lang_x_stargazers_max_{0}".format(skillMaxNumRepos) in profileSkills:
                                maxNumStargazersSkillMaxNumRepos = profileSkills["lang_x_stargazers_max_{0}".format(skillMaxNumRepos)]

                            if "lang_x_watchers_max_{0}".format(skillMaxNumRepos) in profileSkills:
                                maxNumWatchersSkillMaxNumRepos = profileSkills["lang_x_watchers_max_{0}".format(skillMaxNumRepos)]

                            if "latest_created_at_{0}".format(skillMaxNumRepos) in profileSkills:
                                latestCreatedAt = profileSkills["latest_created_at_{0}".format(skillMaxNumRepos)]

                            if "latest_updated_at_{0}".format(skillMaxNumRepos) in profileSkills:
                                latestUpdatedAt = profileSkills["latest_updated_at_{0}".format(skillMaxNumRepos)]

                            if "latest_pushed_at_{0}".format(skillMaxNumRepos) in profileSkills:
                                latestPushedAt = profileSkills["latest_pushed_at_{0}".format(skillMaxNumRepos)]

                            if "latest_size_{0}".format(skillMaxNumRepos) in profileSkills:
                                size = profileSkills["latest_size_{0}".format(skillMaxNumRepos)]

                            skillMaxNumReposWasMaxForks = self.wasSkillMaxNumReposMaxX("lang_x_watchers_max_", skillMaxNumRepos, profileSkills)                               
                            skillMaxNumReposWasMaxStars = self.wasSkillMaxNumReposMaxX("lang_x_forks_max_", skillMaxNumRepos, profileSkills)
                            skillMaxNumReposWasMaxWatchers = self.wasSkillMaxNumReposMaxX("lang_x_stargazers_max_", skillMaxNumRepos, profileSkills)
                            wasSmrnRepoRelativelySuccessful = self.wasSmrnRepoRelativelySuccessful(profileSkills, skillMaxNumRepos)

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

                                profileSkills["num_repos_smnr"] = numReposMaxNumReposSkill
                                profileSkills["max_num_forks_smnr"] = maxNumForksSkillMaxNumRepos
                                profileSkills["max_num_stars_smnr"] = maxNumStargazersSkillMaxNumRepos
                                profileSkills["max_num_watchers_smnr"] = maxNumWatchersSkillMaxNumRepos
                                profileSkills["smnr_was_max_forks"] = skillMaxNumReposWasMaxForks
                                profileSkills["smnr_was_max_stars"] = skillMaxNumReposWasMaxStars
                                profileSkills["smnr_was_max_watchers"] = skillMaxNumReposWasMaxWatchers
                                profileSkills["latest_created_smnr"] = latestCreatedAt
                                profileSkills["latest_updated_smnr"] = latestUpdatedAt
                                profileSkills["latest_pushed_smnr"] = latestPushedAt
                                profileSkills["latest_size_smnr"] = size
                                profileSkills["was_smrn_repo_relatively_successful"] = wasSmrnRepoRelativelySuccessful

                                moreDetailsDatasetRow = {
                                    "idx" : idx,
                                    "github_userid" : profileSkills["github_userid"],
                                    "strong_repo" : profileSkills["strong_repo"],
                                    "skill_max_num_repos" : skillMaxNumRepos
                                }

                                jsonDataset.append(profileSkills)
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

            pathFilePlot = "images/{0}_x_{1}.png".format(nameVar1, nameVar2)
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
