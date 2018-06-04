# -*- coding: utf-8 -*-

"""
Manage the inputs of the most external part of the API
"""

# Imports
import sys
import time
import datetime
sys.path.append("../")

from datetime import datetime
from datetime import timedelta

class InputUtils:

    def __init__(self):
        self.TAG = "StrUtils"

    def getCleanString(self, rawStr):
        cleanStr = ""

        try:
            cleanStr = " ".join(rawStr.split())

        except ValueError as e:
            return '{0}: Failed to getCleanString {1}'.format(self.TAG, e)

        return cleanStr
