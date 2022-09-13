#   Project:        LinuxLogForensics
#   Author:         George Keith Watson
#   Date Started:   July 12, 2021
#   Copyright:      (c) Copyright 2021 George Keith Watson
#   Module:         model/Util.py
#   Purpose:        Base utilities which even Logging and Configuration are dependent on.
#                   Solves circular dependencies between these.
#   Development:
#

import sqlite3, os, sys, subprocess, json, signal
import platform
from datetime import datetime
from functools import partial
from signal import Signals
from copy import deepcopy
from datetime import date
from enum import Enum

if 'HOME' in os.environ:
    USER_HOME =  os.environ['HOME']
else:
    USER_HOME = '~'
INSTALLATION_FOLDER             = USER_HOME + '/PycharmProjects/GearboxMD'
IMAGES_FOLDER                       = INSTALLATION_FOLDER + "/graphics"
IMAGES_GEARS_FOLDER                 = IMAGES_FOLDER + "/gears"
IMAGE_DEFAULT_MOVING                = IMAGES_GEARS_FOLDER + "/27578gears-3032961665.gif"
IMAGE_DEFAULT_WORKING               = IMAGES_GEARS_FOLDER + "/still/th-1607793070.png"

class ModelType(Enum):
    JSON        = 'json'
    OBJECT      = 'object'


def pathTuple2String(pathTuple: tuple):
    pathSpec    = ""
    for folderName in pathTuple:
        pathSpec += '/' + folderName
    return pathSpec


class TimeSpan:

    def __init__(self, name: str, startTime: date, endTime: date):
        if not isinstance(name, str):
            raise Exception("TimeSpan constructor - Invalid name argument:  " + str(name))
        if not isinstance(startTime, date):
            raise Exception("TimeSpan constructor - Invalid startTime argument:  " + str(startTime))
        if not isinstance(endTime, date):
            raise Exception("TimeSpan constructor - Invalid endTime argument:  " + str(endTime))
        self.name = name
        self.startTime = startTime
        self.endTime = endTime

    def getName(self):
        return self.name

    def getStartTime(self):
        return self.startTime

    def getEndTime(self):
        return self.endTime

    def getDuration(self):
        return self.endTime - self.startTime

    def list(self, timeFormat):
        print("\nTimeSpan:\t" + self.name)
        #   datetime.now().strftime(self.menuBar.getTimeFormat())
        print("\tStart Time:\t" + self.startTime.strftime(timeFormat))
        print("\tEnd Time:\t" + self.endTime.strftime(timeFormat))
        print("\tDuration:\t" + str(self.endTime - self.startTime))


class TimeStamp:

    def __init__(self, **keyWordArguments):
        """
        No argument filtering required.
        It is appropriate that the application crash if invalid data is passed to the TimeStamp constructor.
        Including argument filtering code will expose the internal structure of the object.
        :param keyWordArguments:
        """
        if 'datetime' in keyWordArguments:
            timeStamp = keyWordArguments['datetime']
            self.year       = timeStamp.year
            self.month      = timeStamp.month
            self.day        = timeStamp.day
            self.hour       = timeStamp.hour
            self.minute     = timeStamp.minute
            self.second     = timeStamp.second
            self.micro      = timeStamp.microsecond
        else:
            for key, value in keyWordArguments.items():
                self.__dict__[key] = value

    def __setattr__(self, key, value):
        if not key in self.__dict__:
            self.__dict__[key] = value
        else:
            raise Exception('TimeStamp:    Attempt to set immutable attribute')

    def parse(self):
        """
        Parses the timeStamp string format constructed by this class' __str__() method into its separate fields.
        example: "2021/07/22 16:22:06.303286"
        :return: a map with the different time fields in it.
        """
        (date, time) = self.__str__().split(' ')
        (year, month, day)  = date.split('/')
        (hour, minute, second)   = time.split(':')
        (second, micro)     = second.split('.')
        return TimeStamp(year=int(year), month=int(month), day=int(day), hour=int(hour), minute=int(minute),
                         second=int(second), micro=int(micro))

    def __str__(self):
        return "{year:4d}/{month:2d}/{day:2d}".format(year=self.year, month=self.month, day=self.day).replace(' ', '0')\
               + ' ' + "{hour:2d}:{minute:2d}:{second:2d}.{micro:6d}".format(hour=self.hour, minute=self.minute,
                second=self.second, micro=self.micro).replace(' ', '0')

    @staticmethod
    def formatDateTime(dateTime: datetime, formatType: str=None):
        dateTimeStr = "{year:4d}/{month:2d}/{day:2d}".format(year=dateTime.year, month=dateTime.month, day=dateTime.day).replace(' ', '0')\
               + ' ' + "{hour:2d}:{minute:2d}:{second:2d}.{micro:6d}".format(hour=dateTime.hour, minute=dateTime.minute,
                second=dateTime.second, micro=dateTime.microsecond).replace(' ', '0')
        if formatType == "filename":
            dateTimeStr = dateTimeStr.replace('/', '-').replace(' ', '_')
        return dateTimeStr


class ListFileRow:

    def __init__(self, fileName: str):
        """
        Make a tuple of the values in an ls -l listing for a particular file and assign immutable attributes
        recording the same.
        :param fileName:     Full path from root to file as a string.
        """
        if fileName is None or not isinstance(fileName, str):
            raise Exception("ListFileRow constructor - invalid fileName argument:    " + str(fileName))
        if os.path.isfile(fileName):
            print('ListFileRow:\t' + fileName)
            self.fileName   = fileName
            argv = ('ls', '-l', fileName)
            sub = subprocess.Popen(argv,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output, error_message = sub.communicate()
            print(output.decode('utf-8'))
            self.attributeList  = tuple(output.decode('utf-8').split())
            print('self.attributeList:\t' + str(self.attributeList))
            self.permissions    = self.attributeList[0]
            self.dirOrLinkCount = self.attributeList[1]
            self.owner          = self.attributeList[2]
            self.group          = self.attributeList[3]
            self.size           = self.attributeList[4]
            self.month          = self.attributeList[5]
            self.day            = self.attributeList[6]
            self.timeYear       = self.attributeList[7]
            self.name           = self.attributeList[8]

    def __str__(self):
        text = '\nAttribute of:\t' + self.fileName
        for key, value in self.__dict__.items():
            text    += "\n\t" + key + ":\t" + str(value)
        return text

    def __setattr__(self, key, value):
        if not key in self.__dict__:
            self.__dict__[key] = value


def listFromPathString(pathName: str):
    """
    Assumes Linux formatted path name, i.e. no 'file::' or other protocol prepended and with '/' for separation.
    This will be modified as needed to handle MS Windows format and URI/URL strings.
    :param pathName:
    :return:
    """
    list = pathName.split('/')
    if len( list[0] ) == 0:
        del(list[0])
    return tuple(list)


def alarmSignalHandler(message: dict, *args):
    print('alarmSignalHandler - message:\t' + str(message))


def listMap(name: str, map: dict):
    print("\nMap:\t" + str(name))
    for name, value in map.items():
        print("\t" + str(name) + ":\t\t" + str(value))


if __name__ == '__main__':
    print('Util.py RUNNING')
