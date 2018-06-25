# -*- coding: utf-8 -*-

import pandas as pd

'''
    Provide methods to help handling Panda's Dataframe
'''
class DataframeUtils():

    def __init__(self):
        self.TAG = "DataframeUtils"
        self.makeDatasetResultGB = lambda x: x.tail(len(x))

    '''
        Ensure that a valid list of columns are going to be passed to the drop function on Pandas
    '''
    def getColumnsToDrop(self, df, listColumnNames):
        toDrop = []

        try:

            if df is not None and listColumnNames is not None:

                for column in listColumnNames:
                    
                    if pd.Series(column).isin(df.columns).all():
                        toDrop.append(column)

        except Exception as err:
            print("{0} Failed to getColumnsToDrop {1}".format(self.TAG, err))

        return toDrop

    '''
        Return true if a given serie is present in the dataframe
    '''
    def isSerieInDataframe(self, df, columnName):
        try:

            if df is not None and columnName is not None:

                if pd.Series(columnName).isin(df.columns).all():
                    return True

        except Exception as err:
            print("{0} Failed to isSerieInDataframe {1}".format(self.TAG, err))

        return False
