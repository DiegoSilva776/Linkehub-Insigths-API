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
            configFileName = os.path.join(dirname, '../config/linkehub-api-firebase.json')

            with open(configFileName) as json_data:
                self.firebase = pyrebase.initialize_app(json.load(json_data))
        
        except Exception as e:
            print("Failed to __init__: {0}".format(e))

    '''
       Returns a list of objects in which each object represents the accessment of the skills of a Github
       profile stored in the project database. The profiles are queried by their location.
    '''
    def getListGithubUsersSkills(self):
        githubProfilesSkills = []

        try:
            db = self.firebase.database()
            baseUrlGithubProfiles = db.child("github_profile_skills_location")
            profiles = baseUrlGithubProfiles.get()

            for profileSkills in profiles.each():
                dbObject = profileSkills.val()

                if dbObject is not None:
                    githubProfilesSkills.append(dbObject)

        except  Exception as e:
            print("Failed to getListGithubUsersSkills: {0}".format(e))

        return githubProfilesSkills
