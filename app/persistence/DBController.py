# -*- coding: utf-8 -*-

import os
import json
import pyrebase

from utils.NetworkingUtils import NetworkingUtils
from utils.StringUtils import StringUtils
from utils.Logger import Logger

'''
    Manages the connection and operations of this service with its database
'''
class DBManager():

    def __init__(self):

        try:
            self.TAG = "DBManager"

            self.netUtils = NetworkingUtils()
            self.strUtils = StringUtils()
            self.logger = Logger()
            
            dirname = os.path.dirname(__file__)
            configFileName = os.path.join(dirname, '../config/linked-dev-api-firebase.json')

            with open(configFileName) as json_data:
                self.firebase = pyrebase.initialize_app(json.load(json_data))
        
        except Exception as e:
            print("Failed to __init__: {0}".format(e))

    # REALTIME DATABASE
    '''
       Returns a list of objects in which each object represents the accessment of the skills of a Github
       profile stored in the project database. The profiles are queried by their location.
    '''
    def getListGithubUsersSkills(self):
        githubProfilesSkills = []

        try:
            baseUrlGithubProfiles = {}
            profiles = []
            dirname = os.path.dirname(__file__)
            configFileName = os.path.join(dirname, '../config/linkehub-api-export-test.json')

            with open(configFileName) as json_data:
                baseUrlGithubProfiles = json.load(json_data)

                if 'github_profile_skills_location' in baseUrlGithubProfiles:
                    profiles = baseUrlGithubProfiles['github_profile_skills_location']

            for profileKey in profiles.keys():

                if profileKey in profiles:

                    if profiles[profileKey] is not None:
                        githubProfilesSkills.append(profiles[profileKey])

            '''
            db = self.firebase.database()
            githubProfilesSkillsFromDB = db.child("github_profile_skills_location").get()

            for profileSkills in githubProfilesSkillsFromDB.each():
                dbObject = profileSkills.val()

                if dbObject is not None:
                    githubProfilesSkills.append(dbObject)
            '''

        except  Exception as e:
            print("Failed to getListGithubUsersSkills: {0}".format(e))

        return githubProfilesSkills

    '''
       Returns the list of repositories of a Github user from the project's database
    '''
    def getListReposGithubUser(self, githubUserId):
        githubUserRepos = []

        try:
            db = self.firebase.database()
            userReposFromDB = db.child("github_profiles/{0}/repos".format(githubUserId)).get()

            if userReposFromDB is not None:

                if userReposFromDB.each() is not None:

                    for repo in userReposFromDB.each():
                        dbObject = repo.val()

                        if dbObject is not None:
                            githubUserRepos.append(dbObject)

                elif userReposFromDB.val() is not None:
                    githubUserRepos.append(userReposFromDB.val())

        except  Exception as e:
            print("Failed to getListReposGithubUser: {0}".format(e))

        return githubUserRepos

    '''
        Add timestamps such as (created_at, updated_at, pushed_at) x each skill, to the dataset 
        github_profile_skills_location for a given user.
    '''
    def appendTimestampsGithubProfilesSkills(self, token, userId, newDbFields):
        status = True

        try:

            if token is not None:
                db = self.firebase.database()
                db.child("github_profile_skills_location/{0}".format(userId)).update(newDbFields, token)

        except Exception as e:
            print("Failed to appendTimestampsGithubProfilesSkills: {0}".format(e))
            status = False

        return status

    '''
        Update the list of technical skills available in the plataform
    '''
    def updateListTechSkillsPlatform(self, token, skills):
        status = True

        try:

            if token is not None:
                db = self.firebase.database()
                db.child("github_profiles_tech_skills/").update(skills, token)

        except Exception as e:
            print("Failed to updateListTechSkillsPlatform: {0}".format(e))
            status = False

        return status

    '''
        Update the descriptive statistics of the github_profile_skills after grouping
        the dataset by an attribute.
    '''
    def updateStatsGroupByMetricsTechSkillsPlatform(self, token, insights):
        status = True

        try:

            if token is not None:
                db = self.firebase.database()
                db.child("github_profiles_tech_skills_insights/").update(insights, token)

        except Exception as e:
            print("Failed to updateStatsGroupByMetricsTechSkillsPlatform: {0}".format(e))
            status = False

        return status

    '''
        Remove all keys that have a certain pattern from a user from
        github_profile_skills_location.
    '''
    def removeAllKeysWithPatternFrom(self, token, userId, pattern):
        status = True

        try:

            if token is not None:
                db = self.firebase.database()
                userSkills = db.child("github_profile_skills_location/{0}".format(userId)).get()

                if userSkills is not None:
                    userProfileSkills = userSkills.val()
                    
                    if userProfileSkills is not None:

                        for key in userProfileSkills.keys():

                            if key.find(pattern) != -1:
                                db.child("github_profile_skills_location/{0}/{1}".format(userId, key)).set(None, token)

        except Exception as e:
            print("Failed to removeAllKeysWithPatternFrom: {0}".format(e))
            status = False

        return status

    # STORAGE
    '''
        Add a local image to the storage
    '''
    def storeImage(self, localImgPath, token):
        imgUrl = ""

        try:
            imageNameParts = localImgPath.split("/")
            imageNameStorage = imageNameParts[len(imageNameParts) - 1]

            storage = self.firebase.storage()
            storage.child("img_analysis/{0}".format(imageNameStorage)).put(localImgPath, token)
            imgUrl = storage.child("img_analysis/{0}".format(imageNameStorage)).get_url(token)

        except Exception as e:
            print("Failed to storeImage: {0}".format(e))

        return imgUrl
