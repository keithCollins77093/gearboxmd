#   Project:        LinuxLogForensics
#   Author:         George Keith Watson
#   Date Started:   September 10, 2022
#   Copyright:      (c) Copyright 2021 George Keith Watson
#   Module:         model/Paths.py
#   Purpose:        Paths for both developer and user installations of source code for running and development.
#                   Includes path building and breakdown utilities.
#   Development:
#

import os
import platform

#   Installation location of USER_HOME
if 'HOME' in os.environ:
    USER_HOME =  os.environ['HOME']
else:
    raise Exception("Paths.py - 'HOME' not in os.environ.  You must set your HOME environment variable to your user home folder.")

BASE_LOG_FOLDER                 = '/var/log'

INSTALLATION_FOLDER                 = USER_HOME + '/gearboxmd-0.0.1/src/gearboxmd'
#   INSTALLATION_FOLDER                 = USER_HOME + '/gearboxmd/src/gearboxmd'
TEMP_DATA_FOLDER                    = INSTALLATION_FOLDER + '/data/temp'
COMMAND_OUTPUT_FOLDER               = INSTALLATION_FOLDER + '/data/commandOutput'

HW_PROBE_FOLDER                     = COMMAND_OUTPUT_FOLDER + '/hw.info'
HW_PROBE_TXZ                        = COMMAND_OUTPUT_FOLDER + '/hw.info.txz'
HW_PROBE_JSONFILE                   = COMMAND_OUTPUT_FOLDER + '/hw.info.json'
HW_PROBE_ZIPFILE                    = COMMAND_OUTPUT_FOLDER + '/hw.info.gzip'

DOCUMENTATION_FOLDER                = INSTALLATION_FOLDER + '/documentation'
IMAGES_FOLDER                       = INSTALLATION_FOLDER + "/graphics"
IMAGES_GEARS_FOLDER                 = IMAGES_FOLDER + "/gears/still"
LOGS_FOLDER                         = INSTALLATION_FOLDER + "/logs"
SCRIPTS_FOLDER                      = INSTALLATION_FOLDER + "/scripts"


def pathTuple2String(pathTuple: tuple):
    pathSpec    = ""
    for folderName in pathTuple:
        pathSpec += '/' + folderName
    return pathSpec


def pathFromList(fileNameList: tuple):
    if fileNameList is None or not isinstance(fileNameList, tuple) or len(fileNameList) < 1:
        raise Exception('Util.pathFromList - invalid fileNameList argument:    ' + str(fileNameList))
    fileNameList = list(fileNameList)
    pathName = fileNameList[0]
    if platform.system() == 'Windows':
        pathParts = []
        for pathPart in fileNameList:
            pathParts += list(listFromPathString(pathPart))
        pathName = pathParts[0]
        pathParts.pop(0)
        return os.path.join(pathName, *pathParts)
    idx = 1
    while idx < len(fileNameList):
        pathName += '/' + fileNameList[idx]
        idx += 1
    return pathName


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


if __name__ == '__main__':
    print('Paths.py RUNNING')
