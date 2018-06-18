# -*- coding: utf-8 -*-

import sys
import os
import json
import http.client
import urllib
import time

sys.path.append('../')

from utils.NetworkingUtils import NetworkingUtils
from utils.ConstantUtils import ConstantUtils
from persistence.DBController import DBManager

'''
    Control the authentication flow of this service with the authentication micro-service
'''
class AuthController():

    def __init__(self):
        self.TAG = "AuthController"

        self.constUtils = ConstantUtils()
        self.netUtils = NetworkingUtils()
        self.dbManager = DBManager()

    '''
        Return a valid token to make requests to the service API Database
    '''
    def login(self, username, password):
        token = ""

        try:

            if not username or not password:
                print("\nFailed to login, invalid input parameters")
            else:
                # Get an instance of the service
                apiInstance = self.netUtils.getRootApiInstance()

                # Make a request to login
                connection = http.client.HTTPSConnection(apiInstance.getBaseUrl())
                headers = self.netUtils.getRequestHeaders(self.constUtils.HEADERS_TYPE_URL_ENCODED, None)
                params = urllib.parse.urlencode({
                    "username" : username,
                    "password" : password
                })
                connection.request("POST", "/login", params, headers=headers)
                
                res = connection.getresponse()
                data = res.read()
                loginResponse = json.loads(data.decode(self.constUtils.UTF8_DECODER))

                # Process the response
                if loginResponse is not None:
                    token = loginResponse["access_token"]

        except Exception as e:
            print("{0} Failed to login {1}".format(self.TAG, e))

        return token
