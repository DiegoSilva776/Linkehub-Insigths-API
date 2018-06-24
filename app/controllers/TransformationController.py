# -*- coding: utf-8 -*-

import sys
import os
import json
import http.client
import urllib
import time
import pandas as pd
import numpy as np

sys.path.append('../')

from utils.Logger import Logger
from utils.NetworkingUtils import NetworkingUtils
from utils.ConstantUtils import ConstantUtils
from utils.StringUtils import StringUtils
from utils.DataframeUtils import DataframeUtils
from controllers.AuthController import AuthController
from controllers.GithubController import GithubController
from persistence.DBController import DBManager

'''
    The methods of this class create views to improve the quality of the data for analysis
'''
class TransformationController():

    def __init__(self):
        self.TAG = "TransformationController"

        self.logger = Logger()
        self.netUtils = NetworkingUtils()
        self.constUtils = ConstantUtils()
        self.strUtils = StringUtils()
        self.dataFrameUtils = DataframeUtils()
        self.authController = AuthController()
        self.gitController = GithubController()
        self.dbManager = DBManager()

        self.locations = [
            "rio de janeiro",
            "belo horizonte",
            "manaus",
            "porto alegre",
            "curitiba",
            "fortaleza",
            "recife",
            "sao paulo",
            "são paulo",
            "berlin",
            "london",
            "new york",
            "san francisco",
            "tokyo",
            "amsterdam",
            "ottawa",
            "zurich",
            "abu dhabi"
        ]

    def transformAppendTimestampLatestReposSkills(self, username, password):

        response = {
            "status" : False,
            "msg" : "Failed to append the language and date of the latest repositories into the github_profiles_skills_location dataset",
            "user_ids" : [],
            "num_profiles" : 0,
        }

        try:

            if not username or not password:
                response["msg"] = "Invalid username and password, please login and try again."

            else:

                for location in self.locations:
                    token = self.authController.login(username, password)

                    if token != "":
                        githubUserIds = self.gitController.getGithubUserIdsFromLocation(token, location)

                        if githubUserIds is not None:

                            for userId in githubUserIds:
                                response["user_ids"].append("{0} : {1}".format(location, userId))
                                response["num_profiles"] += 1

                                userRepos = self.dbManager.getListReposGithubUser(userId)

                                if userRepos is not None:

                                    if len(userRepos):
                                        reposDataFrame = pd.DataFrame(userRepos)
                                        toDrop = self.dataFrameUtils.getColumnsToDrop(reposDataFrame,
                                            [
                                                'description',
                                                'homepage',
                                                'id',
                                                'name',
                                                'url',
                                                'owner',
                                                'is_owner',
                                                'private',
                                                'watchers_count',
                                                'forks_count',
                                                'open_issues_count',
                                                'stargazers_count',
                                                'has_downloads',
                                                'has_issues',
                                                'has_pages',
                                                'has_projects',
                                                'has_wiki'
                                            ]
                                        )
                                        reposDataFrame.drop(toDrop, inplace=True, axis=1)
                                        reposDataFrame.dropna()
                                        reposDataFrame["created_at"] = pd.to_numeric(reposDataFrame["created_at"], downcast="integer")
                                        reposDataFrame["updated_at"] = pd.to_numeric(reposDataFrame["updated_at"], downcast="integer")
                                        reposDataFrame["pushed_at"] = pd.to_numeric(reposDataFrame["pushed_at"], downcast="integer")
                                        dfGrouped = reposDataFrame.groupby(['language']).agg(['max']).apply(lambda x: x.tail(len(x)))
                                    
                                        reposMax = dfGrouped.to_dict()
                                        newDbFields = {}

                                        print(userId)

                                        for keyColumnMax in reposMax.keys():
                                            rows = reposMax[keyColumnMax]

                                            for keyRowMax in rows.keys():
                                                newDbKey = self.strUtils.getCleanedJsonVal("latest_{0}_{1}".format(keyColumnMax[0], keyRowMax))

                                                print(newDbKey)

                                                newDbFields[newDbKey] = rows[keyRowMax]

                                        self.dbManager.appendTimestampsGithubProfilesSkills(token, userId, newDbFields)

                                        print()

                response["status"] = True
                response["msg"] = "We added the attributes that can be used as timestamps on github_profiles_skills"

        except ValueError as ve:
            print("{0} Failed to transformAppendTimestampLatestReposSkills: {1}".format(self.TAG, ve))

        return json.dumps(response)

    '''
        Remove all keys that contains a certain pattern from all objects in githut_profile_skills 
    '''
    def removeAllKeysWithPatternFrom(self, username, password, pattern):
        response = {
            "status" : False,
            "msg" : "Failed to remove keys from github_profile_skills",
            "user_ids" : [],
            "num_profiles_fixed" : 0,
        }

        try:

            if not username or not password:
                response["msg"] = "Invalid username and password, please login and try again."

            else:

                for location in self.locations:
                    token = self.authController.login(username, password)

                    if token != "":
                        print("{0}\n".format(location))

                        githubUserIds = self.gitController.getGithubUserIdsFromLocation(token, location)

                        if githubUserIds is not None:

                            for userId in githubUserIds:

                                if response["num_profiles_fixed"] % 100 == 0:
                                    token = self.authController.login(username, password)

                                if token != "":
                                    print(userId)

                                    self.dbManager.removeAllKeysWithPatternFrom(token, userId, pattern)
                                    response["user_ids"].append(userId)
                                    response["num_profiles_fixed"] += 1

                        print("")

                        response["status"] = True
                        response["msg"] = "Removed keys with the given pattern from github_profile_skills"

                    else:
                        response["msg"] = "Invalid access token, please login and try again."

        except Exception as err:
            print("{0} Failed to removeAllKeysWithPatternFrom {1}".format(self.TAG, err))

        return json.dumps(response)
