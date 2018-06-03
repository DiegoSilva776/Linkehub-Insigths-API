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
    The methods of this class control the instances of the Linkehub microservice

    In order to work, the deployNCopiesRootInstance requires that the management and the root 
    microservices are organized like so:

        API
            instances/root_microservice              -> The microservice that is going to be copied
            management/management_service/app/app.py -> This management service
'''
class DeploymentController():

    def __init__(self):
        self.PATH_INSTANCES = "../../../instances/"

        self.ROOT_SERVICE_DIR_NAME = "linkehub_api_root"
        self.ROOT_SERVICE_NAME = "linkehub-api-root"
        self.ROOT_SERVICE_DOCKER_IMG = "linkehub-api-root:0.1"

        self.PREFIX_SERVICE_PATH_NAME = "linkehub_api_i"
        self.PREFIX_SERVICE_NAME = "linkehub-api-i"
        self.PREFIX_SERVICE_DOCKER_IMG = "linkehub-api-i{0}:0.1"

        self.logger = Logger()
        self.networkUtils = NetworkingUtils()

    '''
        Try to deploy N copies of the root microservice and if it succeeds 
        it returns a list with the urls of the running servers
    '''
    def deployNCopiesRootInstance(self, startIdx, endIdx):
        response = {
            "success" : False,
            "msg" : "Failed to deploy copies of the root microservice",
            "running_instances" : []
        }

        try:

            if not startIdx or not endIdx:
                response["msg"] = "Could not deploy instances, one or more input parameters are invalid."
            else:

                for instanceNum in range(int(startIdx), int(endIdx)):
                    # Deploy a new copy of the root service to Heroku
                    workingDir = os.getcwd()
                    rootServicePath = "{0}{1}".format(
                        self.PATH_INSTANCES,
                        self.ROOT_SERVICE_DIR_NAME
                    )
                    copyServicePath = "{0}{1}{2}".format(
                        self.PATH_INSTANCES,
                        self.PREFIX_SERVICE_PATH_NAME, 
                        instanceNum
                    )
                    copyServiceName = "{0}{1}".format(
                        self.PREFIX_SERVICE_NAME, 
                        instanceNum
                    )
                    copyServiceUrl  = "{0}{1}{2}".format(
                        self.networkUtils.HTTPS_PREFIX, 
                        copyServiceName, 
                        self.networkUtils.POSTFIX_HEROKU_APPS_URL
                    )
                    rootServiceRepoUrl = "{0}{1}{2}{3}".format(
                        self.networkUtils.HTTPS_PREFIX,
                        self.networkUtils.PREFIX_HEROKU_APPS_GIT_REPO,
                        self.ROOT_SERVICE_NAME,
                        self.networkUtils.GIT_POSTFIX
                    )
                    copyServiceRepoUrl = "{0}{1}{2}{3}".format(
                        self.networkUtils.HTTPS_PREFIX,
                        self.networkUtils.PREFIX_HEROKU_APPS_GIT_REPO,
                        copyServiceName,
                        self.networkUtils.GIT_POSTFIX
                    )
                    dockerImgNewService = self.PREFIX_SERVICE_DOCKER_IMG.format(instanceNum)

                    print("\nCreating new instance of the root service: instance name {0} ...".format(copyServiceName))
                    print("workingDir: {0}".format(workingDir))
                    print("rootServicePath: {0}".format(rootServicePath))
                    print("copyServicePath: {0}".format(copyServicePath))
                    print("copyServiceName: {0}".format(copyServiceName))
                    print("copyServiceUrl: {0}".format(copyServiceUrl))
                    print("rootServiceRepoUrl: {0}".format(rootServiceRepoUrl))

                    status = call("rm -rf {0} ".format(copyServicePath), shell=True)
                    print("\nstatus cmd delete copy folder: {0} \n".format(status))

                    status = call("cp -fr {0} {1} ".format(rootServicePath, copyServicePath), shell=True)
                    print("\nstatus cmd copy contents of root service to new service: {0} \n".format(status))

                    status = call("git remote rm heroku", cwd=copyServicePath, shell=True)
                    print("\nstatus cmd remove remote of the source service: {0} \n".format(status))

                    status = call("heroku apps:create {0} ".format(copyServiceName), cwd=copyServicePath, shell=True)
                    print("\nstatus cmd create heroku app: {0} \n".format(status))

                    status = call("git remote add heroku {0}".format(copyServiceRepoUrl), cwd=copyServicePath, shell=True)
                    print("\nstatus cmd add remote of the new service: {0} \n".format(status))

                    status = call("git remote -v ", cwd=copyServicePath, shell=True)
                    print("\nstatus cmd git remote -v: {0} \n".format(status))

                    status = call("docker image build -t {0} . ".format(dockerImgNewService), cwd=copyServicePath, shell=True)
                    print("\nstatus cmd build docker image: {0} \n".format(status))

                    status = call("heroku container:push web --app {0} ".format(copyServiceName), cwd=copyServicePath, shell=True)
                    print("\nstatus cmd push container to heroku: {0} \n".format(status))

                    status = call("heroku container:release web --app {0} ".format(copyServiceName), cwd=copyServicePath, shell=True)
                    print("\nstatus cmd release container to production: {0} \n".format(status))

                    # Append the url of the instance to the list of instances
                    response["running_instances"].append(copyServiceUrl)

                    time.sleep(60)

                # Fetch a successful response
                response["success"] = True
                response["msg"] = "The deployment script was executed"
                response["created_at"] = self.logger.get_utc_iso_timestamp()

        except Exception as err:
            print("Failed to deployNCopiesRootInstance {0}".format(err))

        return json.dumps(response)
