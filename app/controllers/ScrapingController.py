# -*- coding: utf-8 -*-

import sys
import os
import json
import http.client
import urllib
import time

sys.path.append('../')

from utils.Logger import Logger
from utils.NetworkingUtils import NetworkingUtils
from utils.ConstantUtils import ConstantUtils
from controllers.AuthController import AuthController

'''
    The methods of this class control manage the data scraping process of the Linkehub API and distribute the
    request load among the instances of the service
'''
class ScrapingController():

    def __init__(self):
        self.TAG = "ScrapingController"

        self.logger = Logger()
        self.netUtils = NetworkingUtils()
        self.constUtils = ConstantUtils()
        self.authController = AuthController()

        self.idxNextInstance = 0
        self.locations = [
            "sao paulo",
            "rio de janeiro"
            "berlin",
            "london",
            "new york",
            "san francisco",
            "tokyo",
            "amsterdam",
            "ottawa",
            "zurich",
            "belo horizonte",
            "manaus",
            "porto alegre",
            "curitiba",
            "fortaleza",
            "recife"
        ]

    ## ------------- ##
    ## Main requests ##
    ## ------------- ##
    '''
        Scrap the basic profile info of Github users from a given city
    '''
    def scrapBasicProfileGithubUsers(self, username, password, location, initialPage, numPages):
        response = {
            "success" : False,
            "msg" : "Failed to scrap basic profile info of Github users from the given location",
            "instances" : "",
            "last_page" : "",
            "num_fails" : 0,
            "failed_pages" : [],
            "started_at" : self.logger.get_utc_iso_timestamp(),
            "finished_at" : ""
        }

        try:

            if not username or not password or not location or not initialPage or not numPages:
                response["msg"] = "{0}. {1}".format(response["msg"], "Invalid input parameters.")
            else:
                token = self.authController.login(username, password)

                if token != "":
                    print("\nRequesting basic Github profiles of users from location: {0} ...".format(location))
                    self.netUtils.updateListRemainingRequestsGithubAPI()

                    for currentPage in range(int(initialPage), int(numPages)):
                        # Hold the process until we have more requests, if needed
                        self.netUtils.waitRequestGithubApiIfNeeded()
                        apiInstance = self.netUtils.getInstanceForRequestToGithubAPI()

                        try:
                            # Make a request to the Github API and verify if the limit of requests per hour has been exceeded
                            connection = http.client.HTTPSConnection(apiInstance.getBaseUrl())
                            headers = self.netUtils.getRequestHeaders(self.constUtils.HEADERS_TYPE_AUTH_TOKEN, token)
                            endpoint = "/get_github_users_from_location/?store_in_db={0}&location={1}&page_number={2}".format(
                                True,
                                urllib.parse.quote(location),
                                currentPage
                            )
                            connection.request("GET", endpoint, headers=headers)

                            print("\nGET list of users from a location and store on DB \nurl: {0}{1}".format(apiInstance.getBaseUrl(), endpoint))

                            res = connection.getresponse()
                            data = res.read()
                            githubApiResponse = json.loads(data.decode(self.constUtils.UTF8_DECODER))
                            apiInstance.remainingCallsGithub -= 1

                            # Process the response
                            succesfulResponse = False

                            if githubApiResponse is not None:
                                
                                if "success" in githubApiResponse:

                                    if githubApiResponse["success"]:
                                        succesfulResponse = True
                                    else:
                                        print(githubApiResponse["msg"])

                            if not succesfulResponse:
                                response["num_fails"] += 1
                                response["failed_pages"].append(currentPage)

                        except Exception as e:
                            print("{0} Failed to process a Github user profile: {1}".format(self.TAG, e))

                        # Wait a little bit until the next request
                        time.sleep(0.5)

                    # Fetch a successful response
                    response["success"] = True
                    response["msg"] = "The script scrapBasicProfileGithubUsers executed correctly"
                    response["instances"] = self.netUtils.getSerializableApiInstances()
                    response["last_page"] = currentPage
                    response["finished_at"] = self.logger.get_utc_iso_timestamp()
                else:
                    response["msg"] = "{0}. {1}".format(response["msg"], "Wrong username or password.")

        except ValueError as e:
            print("{0} Failed to scrapBasicProfileGithubUsers {1}".format(self.TAG, e))

        return json.dumps(response)

    '''
        Scrap repositories and skills of Github users from a location
    '''
    def scrapGithubUsersRepositoriesSkills(self, username, password):
        response = {
            "success" : False,
            "msg" : "Failed to scrap the repositories and skills of Github users from a location",
            "instances" : "",
            "num_fails" : 0,
            "started_at" : self.logger.get_utc_iso_timestamp(),
            "finished_at" : ""
        }

        try:

            if not username or not password:
                response["msg"] = "{0}. {1}".format(response["msg"], "Invalid input parameters.")
            else:
                
                # Make a request to the Linkehub database and return all the Github user ids from a location
                for location in self.locations:
                    token = self.authController.login(username, password)

                    if token != "":
                        print("\nRequesting repositories and skills of Github users from : {0} ...".format(location))
                        self.netUtils.updateListRemainingRequestsGithubAPI()

                        try:
                            # Request a list of userIds from the service Database
                            userIds = self.getGithubUserIdsFromLocation(token, location)

                            # Request the list of repositories and skills associated to a Github user
                            for githubUserId in userIds:

                                try:
                                    # Hold the process until we have more requests, if needed
                                    self.netUtils.waitRequestGithubApiIfNeeded()
                                    apiInstance = self.netUtils.getInstanceForRequestToGithubAPI()

                                    print("Number of remaining requests to the Github API: {0}".format(self.netUtils.getNumRemaningRequestToGithub()))
                                        
                                    if apiInstance.remainingCallsGithub > 0:

                                        # This endpoint requests the repositories from the Github API, process the response and 
                                        # stores the list of repos and skills in the service Database
                                        connection = http.client.HTTPSConnection(apiInstance.getBaseUrl())
                                        headers = self.netUtils.getRequestHeaders(self.constUtils.HEADERS_TYPE_AUTH_TOKEN, token)
                                        endpoint = "/scrap_user_repositories_skils_from_github/?githubUserId={0}".format(
                                            urllib.parse.quote(githubUserId)
                                        )
                                        connection.request("GET", endpoint, headers=headers)

                                        print("\nGET repositories and skills of the Github user: {0}".format(githubUserId))
                                        print("url: {0}{1}".format(apiInstance.getBaseUrl(), endpoint))

                                        res = connection.getresponse()
                                        data = res.read()
                                        githubUserReposSkillsResponse = json.loads(data.decode(self.constUtils.UTF8_DECODER))

                                        apiInstance.remainingCallsGithub -= 1

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
                                        else:
                                            response["num_fails"] += 1

                                except Exception as e:
                                    print("{0} Failed to process the repositories and skills of the user: {1} \ncause: {2}".format(self.TAG, githubUserId, e))

                                # Wait a little bit until the next request
                                time.sleep(0.5)

                        except Exception as e:
                            print("{0} Failed to process the list of repositories and skills of Github users from: {1} \ncause:{2}".format(self.TAG, location, e))

                    else:
                        response["msg"] = "{0}. {1}".format(response["msg"], "Wrong username or password.")

                # Fetch a successful response
                response["success"] = True
                response["msg"] = "The script scrapGithubUsersRepositoriesSkills executed correctly"
                response["instances"] = self.netUtils.getSerializableApiInstances()
                response["finished_at"] = self.logger.get_utc_iso_timestamp()

        except ValueError as e:
            print("{0} Failed to scrapGithubUsersRepositoriesSkills: {1}".format(self.TAG, e))

        return json.dumps(response)

    '''
        Scrap list of commits of Github users from a location, the users are gathered from the Linkehub database 
        and them complemented with Github data
    '''
    def scrapCommitsCodeSamplesGithubUsersFromLocation(self, username, password, location, skill):
        response = {
            "success" : False,
            "msg" : "Failed to scrap the commits and code samples of the Github users from the location",
            "instances" : "",
            "num_fails" : 0,
            "started_at" : self.logger.get_utc_iso_timestamp(),
            "finished_at" : ""
        }

        try:

            if not username or not password or not location or not skill:
                response["msg"] = "{0}. {1}".format(response["msg"], "Invalid input parameters.")
            else:
                token = self.authController.login(username, password)

                if token != "":
                    print("\nRequesting commits and code samples of Github users from : {0} ...".format(location))
                    self.netUtils.updateListRemainingRequestsGithubAPI()

                    # Request a list of userIds from the service Database
                    userIds = self.getGithubUserIdsFromLocation(token, location)

                    # Request the list of repositories and skills associated to a Github user
                    for githubUserId in userIds:

                        try:
                            # Hold the process until we have more requests, if needed
                            self.netUtils.waitRequestGithubApiIfNeeded()
                            apiInstance = self.netUtils.getInstanceForRequestToGithubAPI()

                            print("Number of remaining requests to the Github API: {0}".format(self.netUtils.getNumRemaningRequestToGithub()))

                            if apiInstance.remainingCallsGithub > 0:
                                # This endpoint requests the repositories from the Github API, process the response and 
                                # stores the list of repos and skills in the service Database
                                connection = http.client.HTTPSConnection(apiInstance.getBaseUrl())
                                headers = self.netUtils.getRequestHeaders(self.constUtils.HEADERS_TYPE_AUTH_TOKEN, token)
                                endpoint = "/scrap_user_commits_language_github/?githubUserId={0}&language={1}".format(
                                    urllib.parse.quote(githubUserId),
                                    urllib.parse.quote(skill),
                                )
                                connection.request("GET", endpoint, headers=headers)

                                print("\nGET repositories and skills of the Github user: {0}".format(githubUserId))
                                print("url: {0}{1}".format(apiInstance.getBaseUrl(), endpoint))

                                res = connection.getresponse()
                                data = res.read()
                                githubUserReposSkillsResponse = json.loads(data.decode(self.constUtils.UTF8_DECODER))

                                apiInstance.remainingCallsGithub -= 1

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
                                else:
                                    response["num_fails"] += 1

                        except Exception as e:
                            print("{0} Failed to process the repositories and skills of the user: {1} \ncause: {2}".format(self.TAG, githubUserId, e))

                        # Wait a little bit until the next request
                        time.sleep(0.5)
                        
                    # Fetch a successful response
                    response["success"] = True
                    response["msg"] = "The script scrapCommitsCodeSamplesGithubUsersFromLocation executed correctly"
                    response["instances"] = self.netUtils.getSerializableApiInstances()
                    response["finished_at"] = self.logger.get_utc_iso_timestamp()
                else:
                    response["msg"] = "{0}. {1}".format(response["msg"], "Wrong username or password.")

        except ValueError as e:
            print("{0} Failed to scrapCommitsCodeSamplesGithubUsersFromLocation: {1}".format(self.TAG, e))

        return json.dumps(response)

    ## ------------------ ##
    ## Auxiliary requests ##
    ## ------------------ ##
    '''
        Return a list of all Github users in the database that are from a location
    '''
    def getGithubUserIdsFromLocation(self, token, location):
        userIds = []

        try:
            # Update the status of the instances of the service and get the best instance for the next request                            
            self.netUtils.waitRequestGithubApiIfNeeded()
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
