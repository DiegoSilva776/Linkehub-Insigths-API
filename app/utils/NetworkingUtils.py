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

    ## ---------------##
    ## Initialization ##
    ## ---------------##
    def __init__(self):
        self.TAG = "NetworkingUtils"

        self.constUtils = ConstantUtils()
        self.apiInstances = []

        self.initListApiInstances()

    '''
        Initialize the list of copies running the same version of the service API
    '''
    def initListApiInstances(self):
        rootInstance = ApiInstance()
        rootInstance.id = 0,
        rootInstance.name = "root",
        rootInstance.url = "https://linkehub-api-root.herokuapp.com/"
        rootInstance.remainingCallsGithub = 0

        instanceI1 = ApiInstance()
        instanceI1.id = 1,
        instanceI1.name = "i0",
        instanceI1.url = "https://linkehub-api-i0.herokuapp.com/"
        instanceI1.remainingCallsGithub = 0

        instanceI2 = ApiInstance()
        instanceI2.id = 2,
        instanceI2.name = "i1",
        instanceI2.url = "https://linkehub-api-i1.herokuapp.com/"
        instanceI2.remainingCallsGithub = 0

        instanceI3 = ApiInstance()
        instanceI3.id = 3,
        instanceI3.name = "i2",
        instanceI3.url = "https://linkehub-api-i2.herokuapp.com/"
        instanceI3.remainingCallsGithub = 0

        instanceI4 = ApiInstance()
        instanceI4.id = 4,
        instanceI4.name = "i3",
        instanceI4.url = "https://linkehub-api-i3.herokuapp.com/"
        instanceI4.remainingCallsGithub = 0

        instanceI5 = ApiInstance()
        instanceI5.id = 5,
        instanceI5.name = "i4",
        instanceI5.url = "https://linkehub-api-i4.herokuapp.com/"
        instanceI5.remainingCallsGithub = 0

        instanceI6 = ApiInstance()
        instanceI6.id = 6,
        instanceI6.name = "i5",
        instanceI6.url = "https://linkehub-api-i5.herokuapp.com/"
        instanceI6.remainingCallsGithub = 0

        instanceI7 = ApiInstance()
        instanceI7.id = 7,
        instanceI7.name = "i6",
        instanceI7.url = "https://linkehub-api-i6.herokuapp.com/"
        instanceI7.remainingCallsGithub = 0

        instanceI8 = ApiInstance()
        instanceI8.id = 8,
        instanceI8.name = "i7",
        instanceI8.url = "https://linkehub-api-i7.herokuapp.com/"
        instanceI8.remainingCallsGithub = 0

        instanceI9 = ApiInstance()
        instanceI9.id = 9,
        instanceI9.name = "i8",
        instanceI9.url = "https://linkehub-api-i8.herokuapp.com/"
        instanceI9.remainingCallsGithub = 0

        instanceI10 = ApiInstance()
        instanceI10.id = 10,
        instanceI10.name = "i9",
        instanceI10.url = "https://linkehub-api-i9.herokuapp.com/"
        instanceI10.remainingCallsGithub = 0

        instanceI11 = ApiInstance()
        instanceI11.id = 11,
        instanceI11.name = "i10",
        instanceI11.url = "https://linkehub-api-i10.herokuapp.com/"
        instanceI11.remainingCallsGithub = 0

        instanceI12 = ApiInstance()
        instanceI12.id = 12,
        instanceI12.name = "i11",
        instanceI12.url = "https://linkehub-api-i11.herokuapp.com/"
        instanceI12.remainingCallsGithub = 0

        instanceI13 = ApiInstance()
        instanceI13.id = 13,
        instanceI13.name = "i12",
        instanceI13.url = "https://linkehub-api-i12.herokuapp.com/"
        instanceI13.remainingCallsGithub = 0

        instanceI14 = ApiInstance()
        instanceI14.id = 14,
        instanceI14.name = "i13",
        instanceI14.url = "https://linkehub-api-i13.herokuapp.com/"
        instanceI14.remainingCallsGithub = 0

        instanceI15 = ApiInstance()
        instanceI15.id = 15,
        instanceI15.name = "i14",
        instanceI15.url = "https://linkehub-api-i14.herokuapp.com/"
        instanceI15.remainingCallsGithub = 0

        self.apiInstances.append(rootInstance)
        self.apiInstances.append(instanceI1)
        self.apiInstances.append(instanceI2)
        self.apiInstances.append(instanceI3)
        self.apiInstances.append(instanceI4)
        self.apiInstances.append(instanceI5)
        self.apiInstances.append(instanceI6)
        self.apiInstances.append(instanceI7)
        self.apiInstances.append(instanceI8)
        self.apiInstances.append(instanceI9)
        self.apiInstances.append(instanceI10)
        self.apiInstances.append(instanceI11)
        self.apiInstances.append(instanceI12)
        self.apiInstances.append(instanceI13)
        self.apiInstances.append(instanceI14)
        self.apiInstances.append(instanceI15)

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

        except Exception as e:
            print("{0} Failed to getRequestHeaders: {1}".format(self.TAG, e))
    
        return headers

    ## ---------------------##
    ## Instances management ##
    ## ---------------------##
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
    def updateListRemainingRequestsGithubAPI(self, token):
        try:
            # Identify the number of remaining requests to the Github API for each instance of the API
            print("\nVerify the number of remaining requests to the Github API for all instances: \n")

            for apiInstance in self.apiInstances:
                # Make a request to the Github API and verify if the limit of requests per hour has been exceeded
                connection = http.client.HTTPSConnection(apiInstance.getBaseUrl())
                headers = self.getRequestHeaders(self.constUtils.HEADERS_TYPE_AUTH_TOKEN, token)
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
    def waitRequestGithubApiIfNeeded(self, token):
        try:
            numRequestsGithubApi = self.getNumRemaningRequestToGithub()

            if numRequestsGithubApi == 0:
                i = 0
                print("The maximum number of requests to the Github API has been exceeded for all instances of the service, we'll resume the process soon ...")

                while i < self.constUtils.TIMEOUT_REQUEST_GITHUB_API:
                    i += 1
                    time.sleep(1)
                    print("We'll still have to wait {0} ...".format(self.constUtils.TIMEOUT_REQUEST_GITHUB_API - i))

                self.updateListRemainingRequestsGithubAPI(token)

        except Exception as e:
            print("{0} Failed to waitRequestGithubApiIfNeeded : {1}".format(self.TAG, e))

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