# -*- coding: utf-8 -*-

import sys
import os
import json
import http.client
import urllib

sys.path.append('../')

from utils.NetworkingUtils import NetworkingUtils
from utils.ConstantUtils import ConstantUtils

'''
    The methods of this class manage requests that are related to the Github information stored in 
    the project database. The ScrapingController also has methods related to Github, however, they 
    are used only to get info from the actual Github API and store it into the dababase of this project.
'''
class GithubController():

    def __init__(self):
        self.TAG = "GithubController"

        self.netUtils = NetworkingUtils()
        self.constUtils = ConstantUtils()

    '''
        Returns a list of all Github user ids in the database that are from a location
    '''
    def getGithubUserIdsFromLocation(self, token, location):
        userIds = []

        try:
            # Update the status of the instances of the service and get the best instance for the next request                            
            apiInstance = self.netUtils.getInstanceForRequestToGithubAPI()

            connection = http.client.HTTPSConnection(apiInstance.getBaseUrl())
            headers = self.netUtils.getRequestHeaders(self.constUtils.HEADERS_TYPE_AUTH_TOKEN, token)
            endpoint = "/get_github_user_ids_from_location/?location={0}".format(
                urllib.parse.quote(location)
            )
            connection.request("GET", endpoint, headers=headers)

            res = connection.getresponse()
            data = res.read()
            githubUserIdsResponse = json.loads(data.decode(self.constUtils.UTF8_DECODER))

            apiInstance.remainingCallsGithub -= 1

            # Process the response
            if githubUserIdsResponse is not None:

                if "success" in githubUserIdsResponse:

                    if githubUserIdsResponse["success"]:

                        if "github_user_ids" in githubUserIdsResponse:

                            if isinstance(githubUserIdsResponse["github_user_ids"], list):
                                userIds = githubUserIdsResponse["github_user_ids"]

        except Exception as e:
            print("{0} Failed to getGithubUserIdsFromLocation: {1}".format(self.TAG, e))

        return userIds
