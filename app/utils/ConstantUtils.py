# -*- coding: utf-8 -*-

import sys

sys.path.append("../")

class ConstantUtils:

    def __init__(self):
        # General purpose
        self.HTTPS_PREFIX = "https://"
        self.GIT_POSTFIX = ".git"
        self.JSON_PARSER = "json.parser"
        self.HTML_PARSER = "html.parser"
        self.UTF8_DECODER = "utf-8"
        self.ISO8859_15_DECODER = "iso8859-15"
        
        # Heroku related
        self.POSTFIX_HEROKU_APPS_URL = ".herokuapp.com/"
        self.POSTFIX_HEROKU_APPS_URL_NO_DASH = ".herokuapp.com"
        self.PREFIX_HEROKU_APPS_GIT_REPO = "git.heroku.com/"

        # Github related
        self.TIMEOUT_REQUEST_GITHUB_API = 3000

        # Service API related
        self.LINKEHUB_API_INSTANCE_PREFIX_BASE_URL = "linkehub-api-"
        self.HEADERS_TYPE_AUTH_TOKEN = 1
        self.HEADERS_TYPE_URL_ENCODED = 2
        self.HEADERS_TYPE_NO_AUTH_TOKEN = 3

        # Metrics
        self.NUM_STARS_SUCCESSFUL_REPO = 1
        self.NUM_FORKS_SUCCESSFUL_REPO = 1
        self.NUM_WATCHERS_SUCCESSFUL_REPO = 1
