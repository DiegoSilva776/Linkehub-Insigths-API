# -*- coding: utf-8 -*-

import os
import json
import http.client
import urllib
import time

from subprocess import call, run, PIPE, Popen
from utils.Logger import Logger
from utils.NetworkingUtils import NetworkingUtils

'''
    The methods of this class control manage the data scraping process of the Linkehub API and distribute the
    request load among the instances of the service
'''
class ScrapingController():

    def __init__(self):
        self.logger = Logger()
        self.netUtils = NetworkingUtils()
        self.idxNextInstance = 0
        self.apiInstancesUrls = [
            {
                "id" : 0,
                "name" : "root",
                "url" : "https://linkehub-api-root.herokuapp.com/",
                "remaining_calls_github" : 0
            },
            {
                "id" : 1,
                "name" : "i0",
                "url" : "https://linkehub-api-i0.herokuapp.com/",
                "remaining_calls_github" : 0
            },
            {
                "id" : 2,
                "name" : "i1",
                "url" : "https://linkehub-api-i1.herokuapp.com/",
                "remaining_calls_github" : 0
            },
            {
                "id" : 3,
                "name" : "i2",
                "url" : "https://linkehub-api-i2.herokuapp.com/",
                "remaining_calls_github" : 0
            },
            {
                "id" : 4,
                "name" : "i3",
                "url" : "https://linkehub-api-i3.herokuapp.com/",
                "remaining_calls_github" : 0
            },
            {
                "id" : 5,
                "name" : "i4",
                "url" : "https://linkehub-api-i4.herokuapp.com/",
                "remaining_calls_github" : 0
            },
            {
                "id" : 6,
                "name" : "i5",
                "url" : "https://linkehub-api-i5.herokuapp.com/",
                "remaining_calls_github" : 0
            },
            {
                "id" : 7,
                "name" : "i6",
                "url" : "https://linkehub-api-i6.herokuapp.com/",
                "remaining_calls_github" : 0
            },
            {
                "id" : 8,
                "name" : "i7",
                "url" : "https://linkehub-api-i7.herokuapp.com/",
                "remaining_calls_github" : 0
            },
            {
                "id" : 9,
                "name" : "i8",
                "url" : "https://linkehub-api-i8.herokuapp.com/",
                "remaining_calls_github" : 0
            },
            {
                "id" : 10,
                "name" : "i9",
                "url" : "https://linkehub-api-i9.herokuapp.com/",
                "remaining_calls_github" : 0
            }
        ]

    '''
        Scrap the basic profile info of Github users from a given city
    '''
    def scrapBasicProfileGithubUsers(self, token, location, initialPage, numPages):
        response = {
            "success" : False,
            "msg" : "Failed to scrap basic profile info of Github users from the given location",
            "instances" : "",
            "last_page" : "",
            "num_fails" : "",
            "failed_pages" : [],
            "created_at" : ""
        }

        try:

            if not token or not location or not initialPage or not numPages:
                response["msg"] = "{0}. {1}".format(response["msg"], "Invalid location.")
            else:
                initialPage = int(initialPage)
                numPages = int(numPages)

                # Identify the number of remaining requests to the Github API for each instance of the service
                self.apiInstancesUrls = self.updateListRemainingRequestsGithubAPI(token, self.apiInstancesUrls)
                response["instances"] = self.apiInstancesUrls

                # Identify the number of remaining requests to the Github API for each instance of the API
                numRequestsGithubApi = self.getNumRemaningRequestToGithub(self.apiInstancesUrls)
                response["num_requests_missing_to_fully_complete_goal"] = 0

                if numPages > numRequestsGithubApi:
                    response["num_requests_missing_to_fully_complete_goal"] = numPages - numRequestsGithubApi

                # Distribute the load of requests to the Github API between the servers
                print("\nScrap the basic profile of Github users in {0}: \n".format(location))

                currentPage = int(initialPage)
                numFails = 0

                for apiInstance in range(0, numPages):
                    apiInstance = self.getInstanceForRequestToGithubAPI()

                    if apiInstance["remaining_calls_github"] > 0:

                        # Create a connection to the Github API
                        url = self.getBaseUrlInstance(apiInstance["name"])

                        if url is not None:
                            connection = http.client.HTTPSConnection(url)

                            # Make a request to the Github API and verify if the limit of requests per hour has been exceeded
                            headers = {
                                "cache-control": "no-cache",
                                "User-Agent": "Linkehub-API-Manager",
                                "access_token": token
                            }
                            endpoint = "/get_github_users_from_location/?store_in_db={0}&location={1}&page_number={2}".format(
                                True,
                                urllib.parse.quote(location),
                                currentPage
                            )

                            connection.request("GET", endpoint, headers=headers)

                            res = connection.getresponse()
                            data = res.read()
                            githubApiResponse = json.loads(data.decode(self.netUtils.UTF8_DECODER))

                            print("Request endpoint: {0}".format(endpoint))

                            # Process the response
                            if githubApiResponse is not None:
                                currentPage += 1

                                if "success" in githubApiResponse:

                                    if not githubApiResponse["success"]:
                                        numFails += 1
                                        response["failed_pages"].append(currentPage)
                                        print(githubApiResponse["msg"])

                                else:
                                    numFails += 1
                                    response["failed_pages"].append(currentPage)
                            else:
                                numFails += 1
                                response["failed_pages"].append(currentPage)

                            apiInstance["remaining_calls_github"] -= 1

                    numRequestsGithubApi = self.getNumRemaningRequestToGithub(self.apiInstancesUrls)
                    print("Number of available requests to the Github API: {0} \n".format(numRequestsGithubApi))

                    # Wait a little bit until the next request
                    time.sleep(1)

                # Fetch a successful response
                response["success"] = True
                response["msg"] = "The deployment script was executed"
                response["last_page"] = currentPage
                response["num_fails"] = numFails
                response["created_at"] = self.logger.get_utc_iso_timestamp()

        except Exception as err:
            print("Failed to scrapBasicProfileGithubUsers {0}".format(err))

        return json.dumps(response)

    '''
        Verify how many requests an instance of the Linkehub API still has to the Github API before the 
        limit of requests per hour get exceeded.
    '''
    def updateListRemainingRequestsGithubAPI(self, token, apiInstancesUrls):
        try:

            # Identify the number of remaining requests to the Github API for each instance of the API
            print("\nVerify the number of remaining requests to the Github API for the instance: \n")

            for apiInstance in apiInstancesUrls:

                # Create a connection with the Github API
                url = self.getBaseUrlInstance(apiInstance["name"])

                if url is not None:
                    connection = http.client.HTTPSConnection(url)

                    # Make a request to the Github API and verify if the limit of requests per hour has been exceeded
                    print(url)

                    headers = {
                        "cache-control": "no-cache",
                        "User-Agent": "Linkehub-API-Manager",
                        "access_token": token
                    }
                    endpoint = "/has_expired_requests_per_hour_github/"

                    connection.request("GET", endpoint, headers=headers)

                    res = connection.getresponse()
                    data = res.read()
                    githubApiResponse = json.loads(data.decode(self.netUtils.UTF8_DECODER))

                    if githubApiResponse is not None:
                                
                        if "usage" in githubApiResponse:
                            usage = githubApiResponse["usage"]

                            if "remaining" in usage:
                                apiInstance["remaining_calls_github"] = usage["remaining"]

        except Exception as err:
            print("Failed to scrapBasicProfileGithubUsers {0}".format(err))

        return apiInstancesUrls

    '''
        Build the base url of an instance of the API
    '''
    def getBaseUrlInstance(self, name):
        baseUrl = None

        try:        
            baseUrl = "{0}{1}{2}".format(
                self.netUtils.LINKEHUB_API_INSTANCE_PREFIX_BASE_URL, 
                name, 
                self.netUtils.POSTFIX_HEROKU_APPS_URL_NO_DASH
            )

        except Exception as err:
            print("Failed to getBaseUrlInstance {0}".format(err))

        return baseUrl

    '''
        Returns the sum of the remaning requests to the Github API for each instance of the service
    '''
    def getNumRemaningRequestToGithub(self, apiInstancesUrls):
        totalRemainingRequestToGithubAPI = 0

        try:

            for apiInstance in apiInstancesUrls:
                
                if "remaining_calls_github" in apiInstance:
                    totalRemainingRequestToGithubAPI += apiInstance["remaining_calls_github"]

        except Exception as err:
            print("Failed to getBaseUrlInstance {0}".format(err))

        return totalRemainingRequestToGithubAPI

    '''
        Return the instance of the service with the largest number of remaining requests to the Github API
    '''
    def getInstanceForRequestToGithubAPI(self):
        nextInstance = self.apiInstancesUrls[0]
        largestNumRemainingRequests = 0

        try:

            for apiInstance in self.apiInstancesUrls:

                if "remaining_calls_github" in apiInstance:

                    if apiInstance["remaining_calls_github"] > largestNumRemainingRequests:
                        largestNumRemainingRequests = apiInstance["remaining_calls_github"]
                        nextInstance = apiInstance

        except Exception as err:
            print("Failed to getInstanceForRequestToGithubAPI {0}".format(err))

        return nextInstance