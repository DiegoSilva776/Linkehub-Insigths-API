# -*- coding: utf-8 -*-

import sys
import json

sys.path.append('../')

from utils.ConstantUtils import ConstantUtils

'''
    An object of the ApiInstance class holds information about a server which is running an instance of
    the a service API
'''
class ApiInstance():

    def __init__(self):
        self.TAG = "ApiInstance"

        self.constUtils = ConstantUtils()

        self.id = 0,
        self.name = "",
        self.url = ""
        self.remainingCallsGithub = 0

    def toJSON(self):
        jsonDict = {
            'id' : self.id,
            'name' : self.name,
            'url': self.url,
            'remainingCallsGithub' : self.remainingCallsGithub
        }

        return jsonDict

    '''
        Return the full url of an instance, with this value you would be able to make a request directly on your browser
    '''
    def getUrl(self):
        url = ""

        try:
            
            if self.url is not None:
                url = self.url

        except Exception as err:
            print("{0} {1}".format(self.TAG, err))

        return url

    '''
        Return the part of the url that is used to create a connection to a server
    '''
    def getBaseUrl(self):
        baseUrl = ""

        try:
            baseUrl = self.getUrl().replace(self.constUtils.HTTPS_PREFIX, "")
            baseUrl = baseUrl.replace(self.constUtils.POSTFIX_HEROKU_APPS_URL, "")
            baseUrl = "{0}{1}".format(baseUrl, self.constUtils.POSTFIX_HEROKU_APPS_URL_NO_DASH)

        except Exception as err:
            print("Failed to getBaseUrlInstance {0}".format(err))

        return baseUrl
