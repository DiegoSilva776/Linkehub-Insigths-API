# -*- coding: utf-8 -*-

'''
    NetworkingUtils is responsible for holding the external URLs and the default parameters 
    of each URL used by the API.
'''
class NetworkingUtils():

    def __init__(self):
        self.HTTPS_PREFIX = "https://"
        self.GIT_POSTFIX = ".git"
        self.JSON_PARSER = "json.parser"
        self.HTML_PARSER = "html.parser"
        self.UTF8_DECODER = "utf-8"
        self.ISO8859_15_DECODER = "iso8859-15"

        self.POSTFIX_HEROKU_APPS_URL = ".herokuapp.com/"
        self.PREFIX_HEROKU_APPS_GIT_REPO = "git.heroku.com/"