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
        self.locations = [
            "recife",
            "manaus",
            "curitiba",
            "sao paulo",
            "belo horizonte",
            "rio de janeiro",
            "porto alegre",
            "fortaleza"
            "berlin",
            "london",
            "new york",
            "san francisco",
            "tokyo",
            "amsterdam",
            "ottawa"
        ]
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
            "num_requests_missing_to_fully_complete_goal" : "",
            "last_page" : "",
            "num_fails" : 0,
            "failed_pages" : [],
            "created_at" : ""
        }

        try:

            if not token or not location or not initialPage or not numPages:
                response["msg"] = "{0}. {1}".format(response["msg"], "Invalid location.")
            else:
                print("\nRequesting profiles for location: {0} ...".format(location))
                currentPage = int(initialPage)
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

                for apiInstance in range(0, numPages):
                    apiInstance = self.getInstanceForRequestToGithubAPI()

                    if apiInstance["remaining_calls_github"] > 0:
                        url = self.getBaseUrlInstance(apiInstance["name"])

                        if url is not None:

                            # Create a connection to the Github API
                            try:
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

                                print("GET list of users from a location and store on DB \nurl: {0}{1}".format(url, endpoint))

                                # Process the response
                                if githubApiResponse is not None:
                                    currentPage += 1

                                    if "success" in githubApiResponse:

                                        if not githubApiResponse["success"]:
                                            response["num_fails"] += 1
                                            response["failed_pages"].append(currentPage)

                                            print(githubApiResponse["msg"])

                                    else:
                                        response["num_fails"] += 1
                                        response["failed_pages"].append(currentPage)
                                else:
                                    response["num_fails"] += 1
                                    response["failed_pages"].append(currentPage)

                                apiInstance["remaining_calls_github"] -= 1

                            except Exception as e:
                                print("Failed to process a Github user profile: {0}".format(e))

                    # Hold the process until we have more requests, if needed
                    self.waitRequestGithubApiIfNeeded()

                    # Wait a little bit until the next request
                    time.sleep(1)

                # Ensure the limit of requests is going to reset until the next location
                time.sleep(3)

                # Fetch a successful response
                response["success"] = True
                response["msg"] = "The script scrapBasicProfileGithubUsers executed correctly"
                response["last_page"] = currentPage
                response["created_at"] = self.logger.get_utc_iso_timestamp()

        except ValueError as err:
            print("Failed to scrapBasicProfileGithubUsers {0}".format(err))

        return json.dumps(response)

    '''
        Scrap repositories and skills of Github users from a location
    '''
    def scrapGithubUsersRepositoriesSkills(self, token, location):
        response = {
            "success" : False,
            "msg" : "Failed to scrap the repositories and skills of Github users from a location",
            "instances" : "",
            "num_requests_missing_to_fully_complete_goal" : 0,
            "num_fails" : 0,
            "failed_locations" : [],
            "failed_user_ids" : [],
            "created_at" : ""
        }

        try:

            if not token or not location:
                response["msg"] = "{0}. {1}".format(response["msg"], "Invalid input parameters.")
            else:
                # Todo: >>>> remove this after batch scraping
                for listLocation in self.locations:
                    location = listLocation

                    print("\nRequesting repositories and skills of Github users from a location: {0} ...".format(location))

                    # Todo: remove this after the script
                    headers = {
                        "Content-type": "application/x-www-form-urlencoded",
                        "Accept": "text/plain"
                    }
                    params = urllib.parse.urlencode({
                        "username" : "adm.linkehub@gmail.com",
                        "password" : "<<FprojLinkehub01<<"
                    })
                    connection = http.client.HTTPSConnection("linkehub-api-root.herokuapp.com")
                    connection.request("POST", "/login", params, headers=headers)

                    res = connection.getresponse()
                    data = res.read()
                    loginResponse = json.loads(data.decode(self.netUtils.UTF8_DECODER))

                    if loginResponse is not None:
                        token = loginResponse["access_token"]

                    print("location: {0}".format(location))
                    print("token: {0}".format(token))
                    # ./Todo

                    # Identify the number of remaining requests to the Github API for each instance of the service
                    self.apiInstancesUrls = self.updateListRemainingRequestsGithubAPI(token, self.apiInstancesUrls)
                    response["instances"] = self.apiInstancesUrls

                    # Request the list of Github user ids from a location
                    apiInstance = self.getInstanceForRequestToGithubAPI()
                    url = self.getBaseUrlInstance(apiInstance["name"])

                    if url is not None:

                        try:
                            # Make a request to the Linkehub database and return all the Github user ids from a location
                            connection = http.client.HTTPSConnection(url)
                            headers = {
                                "cache-control": "no-cache",
                                "User-Agent": "Linkehub-API-Manager",
                                "access_token": token
                            }
                            endpoint = "/get_github_user_ids_from_location/?location={0}".format(
                                urllib.parse.quote(location)
                            )
                            connection.request("GET", endpoint, headers=headers)

                            res = connection.getresponse()
                            data = res.read()
                            githubUserIdsResponse = json.loads(data.decode(self.netUtils.UTF8_DECODER))
                            apiInstance["remaining_calls_github"] -= 1

                            # Process the response
                            if githubUserIdsResponse is not None:

                                if "success" in githubUserIdsResponse:

                                    if githubUserIdsResponse["success"]:

                                        if "github_user_ids" in githubUserIdsResponse:
                                            userIds = githubUserIdsResponse["github_user_ids"]

                                            if isinstance(userIds, list):
                                                # Get the number of remaining requests to the Github API for each instance of the Linkehub API
                                                numRequestsGithubApi = self.getNumRemaningRequestToGithub(self.apiInstancesUrls)

                                                if len(userIds) > numRequestsGithubApi:
                                                    response["num_requests_missing_to_fully_complete_goal"] = len(userIds) - numRequestsGithubApi

                                                # Hold the process until we have more requests, if needed
                                                self.waitRequestGithubApiIfNeeded()

                                                for githubUserId in userIds:

                                                    # Request the list of repositories and skills associated to a Github user id
                                                    try:
                                                        apiInstance = self.getInstanceForRequestToGithubAPI()
                                                        url = self.getBaseUrlInstance(apiInstance["name"])

                                                        if apiInstance["remaining_calls_github"] > 0 and url is not None:
                                                            # This endpoint requests the repositories from the Github API, process the response and 
                                                            # stores the list of repos and skills in the Linkehub Database
                                                            connection = http.client.HTTPSConnection(url)
                                                            headers = {
                                                                "cache-control": "no-cache",
                                                                "User-Agent": "Linkehub-API-Manager",
                                                                "access_token": token
                                                            }
                                                            endpoint = "/scrap_user_repositories_skils_from_github/?githubUserId={0}".format(
                                                                urllib.parse.quote(githubUserId)
                                                            )
                                                            connection.request("GET", endpoint, headers=headers)

                                                            print("\nGET repositories and skills of the Github user: {0}".format(githubUserId))
                                                            print("url: {0}{1}".format(url, endpoint))

                                                            res = connection.getresponse()
                                                            data = res.read()
                                                            githubUserReposSkillsResponse = json.loads(data.decode(self.netUtils.UTF8_DECODER))
                                                            apiInstance["remaining_calls_github"] -= 1

                                                            # Process the response
                                                            if githubUserReposSkillsResponse is not None:

                                                                if "success" in githubUserReposSkillsResponse:

                                                                    if not githubUserReposSkillsResponse["success"]:
                                                                        response["num_fails"] += 1

                                                                        if "msg" in githubUserReposSkillsResponse:
                                                                            print(githubUserReposSkillsResponse["msg"])

                                                                    else:
                                                                        response["num_fails"] += 1
                                                                else:
                                                                    response["num_fails"] += 1
                                                            else:
                                                                response["num_fails"] += 1

                                                    except Exception as e:
                                                        print("Failed to process the repositories and skills of the user: {0} \ncause: {1}".format(githubUserId, e))

                                                    # Wait a little bit until the next request
                                                    time.sleep(1)

                                            else:
                                                response["failed_locations"].append(location)
                                        else:
                                            response["failed_locations"].append(location)
                                    else:
                                        response["failed_locations"].append(location)
                                else:
                                    response["failed_locations"].append(location)
                            else:
                                response["failed_locations"].append(location)

                        except Exception as e:
                            print("Failed to process the list of repositories and skills of Github users from: {0} \n cause:{1}".format(location, e))

                    # Wait a little bit until the next request
                    time.sleep(3)

                # Fetch a successful response
                response["success"] = True
                response["msg"] = "The script scrapGithubUsersRepositoriesSkills executed correctly"
                response["created_at"] = self.logger.get_utc_iso_timestamp()

        except ValueError as err:
            print("Failed to scrapGithubUsersRepositoriesSkills {0}".format(err))

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
        If the number of available requests to the Github API has exceeded, wait until the instances get refueled
    '''
    def waitRequestGithubApiIfNeeded(self):
        try:
            numRequestsGithubApi = self.getNumRemaningRequestToGithub(self.apiInstancesUrls)
            print("Number of available requests to the Github API: {0} \n".format(numRequestsGithubApi))

            if numRequestsGithubApi == 0:
                i = 0
                print("The maximum number of requests to the Github API has been exceeded for all instances of the service, we'll resume the process in an hour ...")

                while i < self.netUtils.TIMEOUT_REQUEST_GITHUB_API:
                    i += 1
                    time.sleep(1)
                    print("We'll still have to wait {0} ...".format(self.netUtils.TIMEOUT_REQUEST_GITHUB_API - i))

        except Exception as err:
            print("Failed to waitRequestGithubApiIfNeeded {0}".format(err))

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