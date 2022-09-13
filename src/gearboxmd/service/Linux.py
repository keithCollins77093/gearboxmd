#   Project:        GearboxMD
#   Author:         George Keith Watson
#   Date Started:   September 05, 2020
#   Copyright:      (c) Copyright 2022 George Keith Watson
#   Module:         service/Linux.py
#   Date Started:   September 5, 2022
#   Purpose:        Interface to the Linux services.
#   Development:
#
#   Project:        fileHero
#   Author:         George Keith Watson
#   Date Started:   September 01, 2021
#   Copyright:      (c) Copyright 2021, 2022 George Keith Watson
#   Module:         service/Linux.py
#   Date Started:   August 27, 2022
#   Purpose:        Interface to the Linux services.
#   Development:
#

from subprocess import Popen, STDOUT, PIPE
from sys import exc_info, stderr
from signal import Signals, valid_signals, SIGKILL, SIGSTOP, signal
from collections import OrderedDict
from datetime import datetime
from functools import partial
from enum import Enum

from tkinter import Tk, messagebox


PROGRAM_TITLE = "Linux Services"
INSTALLING  = False
TESTING     = True
DEBUG       = False


class DeviceCommand(Enum):
    LSBLK       = ('lsblk', '--all', '--json', '--bytes')
    LSBLK_FS    = ('lsblk', '--all', '--bytes', '--json', '-o', 'NAME,FSTYPE,FSVER,LABEL,UUID,FSAVAIL,FSUSE%,MOUNTPOINTS')
    LSUSB       = ('lsusb', '--verbose')
    BLKID       = ('blkid', '-o', 'full')

    def __str__(self):
        return str(self.value)


class LinuxTools:

    def __init__(self, toolList: tuple=None):
        if toolList is None or not isinstance(toolList, tuple):
            raise Exception('LinuxTools constructor  - invalid commandList argument:\t' + str(toolList))
        #   Key is the command tuple and value is the text output.
        #   A second run with the same commandList will overwrite and replace previous.
        self.toolOutput = OrderedDict()
        if toolList is not None:
            for commandList in toolList:
                if isinstance(commandList, DeviceCommand):
                    self.runTool(commandList)

    def runTool(self, commandList: DeviceCommand):
        if commandList is None or not isinstance(commandList, DeviceCommand):
            raise Exception('LinuxTools.runTool - invalid commandList argument:\t' + str(commandList))
        self.toolOutput[commandList]    = LinuxUtilities.runLinuxTool(commandList.value)

    def getOutput(self, commandList: DeviceCommand):
        if commandList is None or not isinstance(commandList, DeviceCommand):
            raise Exception('LinuxTools.getOutput - invalid commandList argument:\t' + str(commandList))
        return self.toolOutput[commandList]

    def list(self):
        for commandList, outputText in self.toolOutput.items():
            print("\nLinuxTool:\t" + str(commandList))
            print("Output:\n" + outputText)


class LinuxUtilities:

    def __init__(self):
        pass

    @staticmethod
    def runLinuxTool(commandList):
        if commandList is None or not isinstance(commandList, tuple):
            raise Exception('runLinuxCommand - invalid command list argument:\t' + str(commandList))
        outputText = ''
        try:
            sub     = Popen(commandList, stdout=PIPE, stderr=STDOUT )
            output, error_message = sub.communicate()
            outputText  = output.decode('utf-8')
        except Exception:
            outputText = ''
            for line in exc_info():
                outputText += str(line) + '\n'
        finally:
            return outputText


class MemoryMonitor:

    def __init__(self):
        self.index = []
        self.monitorLog = {}

    def poll(self):
        memoryStats = {}
        try:
            sub = Popen( ["free", "--mega"], stdout=PIPE, stderr=STDOUT)
            lastCommandRunTime = str(datetime.now())
            #   print("Sortable Time Stamp:\t" + lastCommandRunTime)
            output, error_message = sub.communicate()
            outputLines = output.decode('utf-8').split('\n')
            fieldNames = outputLines[0].split()
            fieldValues = outputLines[1].split()
            del (fieldValues[0])
            idx = 0
            while idx < len(fieldNames):
                memoryStats[fieldNames[idx]] = fieldValues[idx]
                idx += 1
            #   print('memoryStats (MB):\t' + str(memoryStats))
            self.index.append(lastCommandRunTime)
            self.monitorLog[lastCommandRunTime] = memoryStats
        except Exception:
            outputText = ''
            for line in exc_info():
                outputText += str(line) + '\n'
            print(outputText, file=stderr)

        return memoryStats

    def getMostRecent(self):
        pass

    def __setattr__(self, key, value):
        if key not in self.__dict__:
            self.__dict__[key] = value


class SignalMonitor:

    registry = {}

    def __init__(self, name):
        print('SignalMonitor constructor - RUNNING')
        #   print('Valid Signals:\t' + str(signal.valid_signals()))
        SignalMonitor.registry[name] = self
        self.signalLog = {}
        self.logIndex = ()
        self.signalListeners = {}

        signalList = list(valid_signals())
        idx = 0
        deleteList = []
        while idx < len(signalList):
            if type(signalList[idx]) != Signals:
                deleteList.append(idx)
            idx += 1
        #   print('deleteList:\t' + str(deleteList))
        idx = len(deleteList) - 1
        while idx >= 0:
            deleteList[idx]
            del(signalList[deleteList[idx]])
            idx -= 1
        #   print('signalList:\t' + str(signalList))

        for member in signalList:
            #   print('Type of set member:\t' + str(type(member)))
            #   print('Set member:\t' + str(member))
            if member not in (SIGKILL, Signals.SIGSTOP):
                signal( member, partial(self.signalHandler, member))
                self.signalListeners[member] = ()

    def signalHandler(self, signalName, *args):
        print('SignalMonitor.signalHandle():\t' + str(signalName))
        #   print("\t*args:\t" + str(args))
        timeStamp = str(datetime.now())
        self.signalLogger(signalName, timeStamp)
        for callback in self.signalListeners[signalName]:
            callback({"signal": signalName, 'timeStamp': str(datetime.now())})

    def signalLogger(self, signalName, timeStamo: str):
        print('SignalMonitor.signalLogger():\t' + str(signalName) + '\tat\t' + timeStamo)
        #   Make sure index is immutable:
        self.logIndex = list(self.logIndex)
        self.logIndex.append(timeStamo)
        self.logIndex = tuple(self.logIndex)
        self.signalLog[timeStamo] = signalName

    def registerListener(self, signalId, callback):
        if signalId not in valid_signals():
            raise Exception("SignalMonitor.registerListener - invalid signalId argument:    " + str(signalId))
        if not callable(callback):
            raise Exception("SignalMonitor.registerListener - invalid callback argument:    " + str(callback))
        self.signalListeners[signalId] = list(self.signalListeners[signalId])
        self.signalListeners[signalId].append(callback)
        self.signalListeners[signalId] = tuple(self.signalListeners[signalId])


def ExitProgram():
    answer = messagebox.askyesno(parent=mainView, title='Exit program ', message="Exit the " + PROGRAM_TITLE + " program?")
    if answer:
        mainView.destroy()


if __name__ == '__main__':
    mainView = Tk()
    mainView.geometry("800x500+200+100")
    mainView.title(PROGRAM_TITLE)
    mainView.protocol('WM_DELETE_WINDOW', lambda: ExitProgram())

    mainView.mainloop()

