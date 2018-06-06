# -*- coding: utf-8 -*-

import sys
import os
import json
import http.client
import urllib
import time

sys.path.append("../")

from models.ApiInstance import ApiInstance
from utils.ConstantUtils import ConstantUtils

'''
    NetworkingUtils is responsible for holding the external URLs and the default parameters 
    of each URL used by the API.
'''
class NetworkingUtils():

    def __init__(self):
        self.TAG = "NetworkingUtils"
        self.PATH_SERVICES_CONFIG_FILE = "config/hosts.json"

        self.constUtils = ConstantUtils()
        self.apiInstances = []
        self.initListApiInstances()

    ## --------------------##
    ## Requests management ##
    ## --------------------##
    '''
        Return a headers object used in requests to the service API
    '''
    def getRequestHeaders(self, headersType, token):
        headers = ""

        try:

            if headersType == self.constUtils.HEADERS_TYPE_AUTH_TOKEN:
                headers = {
                    "cache-control": "no-cache",
                    "User-Agent": "Linkehub-API-Manager",
                    "access_token": "{0}".format(token)
                }

            elif headersType == self.constUtils.HEADERS_TYPE_URL_ENCODED:
                headers = {
                    "Content-type": "application/x-www-form-urlencoded",
                    "Accept": "text/plain"
                }

            elif headersType == self.constUtils.HEADERS_TYPE_NO_AUTH_TOKEN:
                headers = {
                    "cache-control": "no-cache",
                    "User-Agent": "Linkehub-API-Manager"
                }

        except Exception as e:
            print("{0} Failed to getRequestHeaders: {1}".format(self.TAG, e))
    
        return headers

    ## ---------------------##
    ## Instances management ##
    ## ---------------------##
    '''
        Initialize the list of copies running the same version of the service API
    '''
    def initListApiInstances(self):
        try:
            fileData = open(self.PATH_SERVICES_CONFIG_FILE).read()
            data = json.loads(fileData)

            for idx, hostFromList in enumerate(data["hosts"]):
                apiInstance = ApiInstance()
                apiInstance.id = idx

                if "url" in hostFromList:
                    apiInstance.url = hostFromList["url"]

                if "name" in hostFromList:
                    apiInstance.name = hostFromList["name"]

                self.apiInstances.append(apiInstance)

            print("The list of API instances has been initialized: {0}".format(json.dumps(self.getSerializableApiInstances())))

        except Exception as e:
            print("{0}: Failed to initListApiInstances: {1}".format(self.TAG, e))

    '''
        Return the serializable version of the list of ApiInstances
    '''
    def getSerializableApiInstances(self):
        sApiInstances = []

        try:

            for apiInstance in self.apiInstances:
                sApiInstances.append(apiInstance.toJSON())

        except Exception as e:
            print("{0} Failed to getSerializableApiInstances : {1}".format(self.TAG, e))

        return sApiInstances

    '''
        Return the object that represents the main instance, which contain the same content of the others,
        but it is the one used to generate the copies of the service.
    '''
    def getRootApiInstance(self):
        try:
            return self.apiInstances[0]

        except Exception as e:
            print("{0} Failed to getRootInstance: {1}".format(self.TAG, e))

    '''
        Verify how many requests an instance of the service API still has to the Github API before the 
        limit of requests per hour get exceeded.
    '''
    def updateListRemainingRequestsGithubAPI(self):
        try:
            # Identify the number of remaining requests to the Github API for each instance of the API
            print("\nVerify the number of remaining requests to the Github API for all instances: \n")

            for apiInstance in self.apiInstances:
                # Make a request to the Github API and verify if the limit of requests per hour has been exceeded
                connection = http.client.HTTPSConnection(apiInstance.getBaseUrl())
                headers = self.getRequestHeaders(self.constUtils.HEADERS_TYPE_NO_AUTH_TOKEN, None)
                endpoint = "/has_expired_requests_per_hour_github/"
                connection.request("GET", endpoint, headers=headers)

                res = connection.getresponse()
                data = res.read()
                githubApiResponse = json.loads(data.decode(self.constUtils.UTF8_DECODER))

                # Process the response
                if githubApiResponse is not None:
                                
                    if "usage" in githubApiResponse:
                        usage = githubApiResponse["usage"]

                        if "remaining" in usage:
                            apiInstance.remainingCallsGithub = usage["remaining"]

                print("{0} : {1}".format(apiInstance.getUrl(), apiInstance.remainingCallsGithub))

            print("Total number available requests : {0}".format(self.getNumRemaningRequestToGithub()))

        except Exception as e:
            print("{0} Failed to updateListRemainingRequestsGithubAPI: {1}".format(self.TAG, e))

    '''
        Returns the sum of the remaning requests to the Github API of each instance of the service
    '''
    def getNumRemaningRequestToGithub(self):
        totalRemainingRequest = 0

        try:

            for apiInstance in self.apiInstances:
                totalRemainingRequest += apiInstance.remainingCallsGithub

        except Exception as e:
            print("{0} Failed to getNumRemaningRequestToGithub: {1}".format(self.TAG, e))

        return totalRemainingRequest

    '''
        Returns the instance of the service with the largest number of remaining requests to the Github API
    '''
    def getInstanceForRequestToGithubAPI(self):
        selectedInstance = self.getRootApiInstance()
        largestNumRemainingRequests = 0

        try:

            for apiInstance in self.apiInstances:

                if apiInstance.remainingCallsGithub > largestNumRemainingRequests:
                    largestNumRemainingRequests = apiInstance.remainingCallsGithub
                    selectedInstance = apiInstance

        except Exception as e:
            print("{0} Failed to getInstanceForRequestToGithubAPI : {1}".format(self.TAG, e))

        return selectedInstance

    '''
        If the number of available requests to the Github API has exceeded, wait until the instances get refueled
    '''
    def waitRequestGithubApiIfNeeded(self):
        try:
            numRequestsGithubApi = self.getNumRemaningRequestToGithub()

            if numRequestsGithubApi == 0:
                i = 0
                print("The maximum number of requests to the Github API has been exceeded for all instances of the service, we'll resume the process soon ...")

                while i < self.constUtils.TIMEOUT_REQUEST_GITHUB_API:
                    time.sleep(1)

                    if i == 0:
                        print("We'll still have to wait {0} seconds until the next request:".format(self.constUtils.TIMEOUT_REQUEST_GITHUB_API - i))

                    elif i < self.constUtils.TIMEOUT_REQUEST_GITHUB_API:
                        print(".", end="")

                        if (self.constUtils.TIMEOUT_REQUEST_GITHUB_API / i) == 2:
                            print("\nWe are half way there, we still have to wait {0} seconds".format(i))
                            
                        elif (self.constUtils.TIMEOUT_REQUEST_GITHUB_API / i) == 3:
                            print("\nHang on a little bit more, we still have to wait {0} seconds".format(i))

                        else:
                            print(".", end="") 

                    i += 1

                self.updateListRemainingRequestsGithubAPI()
                self.waitRequestGithubApiIfNeeded()

        except Exception as e:
            print("{0} Failed to waitRequestGithubApiIfNeeded : {1}".format(self.TAG, e))
