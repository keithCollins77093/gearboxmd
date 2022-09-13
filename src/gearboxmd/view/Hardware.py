#   Project:        GearboxMD
#   Author:         George Keith Watson
#   Date Started:   September 05, 2020
#   Copyright:      (c) Copyright 2022 George Keith Watson
#   Module:         view/Hardware.py
#   Date Started:   September 5, 2022
#   Purpose:        Display hardware information and results of hardware capability analysis and diagnostics.
#   Development:
#       2022-09-05: HardwareProbeView:
#           User will be able to select options for the hw_probe command and then run the command.
#           The raw text output will be viewable in a Text and the analysed, structured output will be
#           available in an appropriate view, such as a list for names / keys as a master for a table
#           formatted treeview of records showing log entries, events, or device descriptors, ...
#           All tables and lists will be filterable using at minimum literal strings, regular expressions,
#           and fuzzy (Levenshtein, 1965) matching.
#
#       2022-09-07:
#           Next problem is to add setModel() and getState() to all view components so that any can be reconstructed
#           in any other context.
#
#       2022-09-08:
#           Alternative table and property sheet module:
#               pip3 install tksheet
#
#       2022-09-12:
#           Test on other Mint and Linux GUI Builds, my work partition is XFCE (Light weight) and alhpa factors
#           do not work on it.
#               self.topLevelMap[frameId].attributes('-alpha', 0.5)
#

from os import walk
from os.path import isfile
from collections import OrderedDict
from copy import deepcopy
from PIL import Image, ImageTk
from enum import Enum
from functools import partial
import tarfile
from gzip import compress, decompress
from json import dumps
from math import floor
from threading import Thread


from tkinter import Tk, LabelFrame, Label, Frame, Checkbutton, Button, Listbox, Text, Toplevel, Message, OptionMenu, \
                    messagebox, filedialog, colorchooser, simpledialog,  \
                    Scrollbar, VERTICAL, HORIZONTAL, \
                    X, Y, BOTH, N, S, E, W, FLAT, SUNKEN, RAISED, GROOVE, RIDGE, NORMAL, DISABLED, \
                    TOP, BOTTOM, LEFT, RIGHT, END, \
                    StringVar, BooleanVar, IntVar

from tkinter.ttk import Treeview, Notebook

from model.Hardware import HardwareProbe, HwProbeOption, ContentID
from model.Paths import pathFromList, INSTALLATION_FOLDER, IMAGES_GEARS_FOLDER, \
                        COMMAND_OUTPUT_FOLDER, HW_PROBE_FOLDER, HW_PROBE_ZIPFILE, \
                        HW_PROBE_JSONFILE, HW_PROBE_TXZ
from model.Util import  IMAGE_DEFAULT_MOVING, ModelType
from view.Components import MasterSlaveLists, CheckBoxList, KeyName, SimplePropertyListFrame, ViewControlPopup, \
                        FrameId, TextFrame, ListFrame, ContentGridFrame, ContentFrameContainer
from view.FrameScroller import FrameScroller

PROGRAM_TITLE = "GearboxMD"
INSTALLING  = False
TESTING     = True
DEBUG       = False

GENERAL_HELP = 'Mouse over a control or selection to see help on its meaning or how it functions\n\n'

START_VIEW_SELECTION_STATE = {
            'geometry': "400x600+600+100",
            'title': " Data View Control ",
            'viewSelectors': (
                {'name': 'devices', 'infoPresent': False, 'selected': False,
                 'views': {
                     'Frame': {'present': False, 'selected': False},
                     'Notebook': {'present': False, 'selected': False},
                     'Toplevel': {'present': False, 'selected': False},
                 }},
                {'name': 'host', 'infoPresent': False, 'selected': False,
                 'views': {
                     'Frame': {'present': False, 'selected': False},
                     'Notebook': {'present': False, 'selected': False},
                     'Toplevel': {'present': False, 'selected': False},
                 }},
                {'name': 'logs', 'infoPresent': False, 'selected': False,
                 'views': {
                     'Frame': {'present': False, 'selected': False},
                     'Notebook': {'present': False, 'selected': False},
                     'Toplevel': {'present': False, 'selected': False},
                 }},
                {'name': 'acpi-dump', 'infoPresent': False, 'selected': False,
                 'views': {
                     'Frame': {'present': False, 'selected': False},
                     'Notebook': {'present': False, 'selected': False},
                     'Toplevel': {'present': False, 'selected': False},
                 }},
                {'name': 'acpi-decode', 'infoPresent': False, 'selected': False,
                 'views': {
                     'Frame': {'present': False, 'selected': False},
                     'Notebook': {'present': False, 'selected': False},
                     'Toplevel': {'present': False, 'selected': False},
                 }},
                {'name': 'cpu-perf', 'infoPresent': False, 'selected': False,
                 'views': {
                     'Frame': {'present': False, 'selected': False},
                     'Notebook': {'present': False, 'selected': False},
                     'Toplevel': {'present': False, 'selected': False},
                 }},
                {'name': 'glxgears', 'infoPresent': False, 'selected': False,
                 'views': {
                     'Frame': {'present': False, 'selected': False},
                     'Notebook': {'present': False, 'selected': False},
                     'Toplevel': {'present': False, 'selected': False},
                 }},
                {'name': 'hdd_read', 'infoPresent': False, 'selected': False,
                 'views': {
                     'Frame': {'present': False, 'selected': False},
                     'Notebook': {'present': False, 'selected': False},
                     'Toplevel': {'present': False, 'selected': False},
                 }},
                {'name': 'memtester', 'infoPresent': False, 'selected': False,
                 'views': {
                     'Frame': {'present': False, 'selected': False},
                     'Notebook': {'present': False, 'selected': False},
                     'Toplevel': {'present': False, 'selected': False},
                 }},
            )
        }
class ViewMode(Enum):
    TOPLEVEL    = 'TopLevel'
    #   FRAME       = 'Frame'
    NOTEBOOK    = 'Notebook'

    def __str__(self):
        return self.value



class Initializer:
    initializing = False
    @staticmethod
    def isInitializing():
        return Initializer.initializing
    @staticmethod
    def setInitializing(setting: bool):
        if not isinstance(setting, bool):
            raise Exception("Initializer.setInitializing - Invalid setting argument:  " + str(setting))
        Initializer.initializing = setting


class HardwareProbeView(LabelFrame):

    DEFAULT_VIEW_MODE   = ViewMode.NOTEBOOK

    class ToolBar(LabelFrame):

        class ToolName(Enum):
            LOAD_LATEST = 'loadLatest'
            SHOW_HIST = 'showHistory'
            RUN_PROBE = 'runProbe'
            PROBE_OPTIONS   = 'probeOptions'

            def __str__(self):
                return self.value

        DEFAULT_BUTTONS = ({    'text': 'Load Latest',
                                'name': str(ToolName.LOAD_LATEST),
                                'row': 0,
                                'col': 0
                           },
                           {    'text': 'Show History',
                                'name': str(ToolName.SHOW_HIST),
                                'row': 1,
                                'col': 0
                           },
                           {    'text': 'Run Probe',
                                'name': str(ToolName.RUN_PROBE),
                                'row': 0,
                                'col': 1
                           },
                           {    'text': 'Probe Options',
                                'name': str(ToolName.PROBE_OPTIONS),
                                'row': 1,
                                'col': 1
                           }
                        )

        def __init__(self, container, configuration: dict=None, listener=None, **keyWordArguments):
            self.listener = None
            if listener is not None and callable(listener):
                self.listener = listener
            self.configuration = OrderedDict()
            if configuration is None:
                self.configuration['buttons'] = HardwareProbeView.ToolBar.DEFAULT_BUTTONS
            elif not isinstance(configuration, OrderedDict):
                raise Exception("HardwareProbeView.ToolBar constructor - Invalid configuration argument:  " + str(configuration))
            else:
                if not 'buttons' in configuration:
                    raise Exception("HardwareProbeView.ToolBar constructor - Invalid configuration argument:  " +
                                    str(configuration))
                self.configuration = deepcopy(configuration)
            LabelFrame.__init__(self, container, keyWordArguments)
            self.buttonMap = OrderedDict()
            for buttonDef in self.configuration['buttons']:
                self.buttonMap[buttonDef['name']] = Button(self, name=buttonDef['name'], text=buttonDef['text'],
                                                           command=partial(self.buttonAction, buttonDef['name']))
                self.buttonMap[buttonDef['name']].grid(row=buttonDef['row'], column=buttonDef['col'], padx=5, pady=5)

            """
            self.labelViewMode = Label(self, text=" View Mode:", border=1, relief=RIDGE)
            self.viewOptionsVar = StringVar()
            self.viewModeOptions = tuple(map(str, ViewMode))
            self.optionsViewMode = OptionMenu(self, self.viewOptionsVar, "", *self.viewModeOptions)
            self.viewOptionsVar.trace('w', self.viewModeChange)
            Initializer.setInitializing(True)
            self.viewOptionsVar.set(str(ViewMode.NOTEBOOK))
            Initializer.setInitializing(False)
            """
            self.buttonViewDetails = Button(self, text='View Details', command=self.showViewDetails)

            #   self.labelViewMode.grid(row=0, column=2, padx=5, pady=5, ipadx=5, ipady=5)
            #   self.optionsViewMode.grid(row=0, column=3, padx=5, pady=5, ipadx=5)
            self.buttonViewDetails.grid(row=1, column=3, padx=5, pady=5, ipadx=5)

        def showViewDetails(self):
            if self.listener is not None:
                self.listener({'source': 'HardwareProbeView.showViewDetails', 'action': 'buttonClick'})

        def setModel(self, model: object):
            if isinstance(model, dict):
                if 'viewMode' in model:
                    if model['viewMode'] in ('TopLevel', 'Notebook'):
                        return
                        #   self.viewOptionsVar.set(model['viewMode'])

        def getState(self, modelType: ModelType):
            if modelType == ModelType.JSON:
                return {
                    #   'viewMode': self.viewOptionsVar.get(),
                }
            return None

        def viewModeChange(self, *args):
            if self.listener is not None:
                if not Initializer.isInitializing():
                    return
                    #   self.listener({'source': 'HardwareProbeView.viewModeChange', 'newValue': self.viewOptionsVar.get()})

        def buttonAction(self, buttonName: str):
            if self.listener is not None:
                self.listener({'source': "ToolBar.buttonAction", 'name': buttonName})

        def messageReceiver(self, message: dict):
            if not isinstance(message, dict):
                return
            if 'source' in message:
                pass

    def __init__(self, container, options: dict = None, listener=None, **keyWordArguments):
        """
        This will include various views and view types for different parts of the content of the hw-probe
        output file.
        The default command produces a host descriptor which is a list of attributes, a devices list, and
        a list of log files relevant to hardware diagnosis, each of which has a list of log entries.
        The first two require simple property sheets, and the log files require a master list of the log
        file names and a ListView for the events logged in each.
        There should be a Checkbutton list to the left to choose which to display.
        There will ultimately be a notebook with separate tabs for the various hw-probe argument sets allowed
        by this application.  Currently, there are no argument sets defined except for the default one, and
        it is also possible to let the user choose any set from the arguments that this application allows.
        Proceeding to implement in order of increasing complexity while maintaining generality is the best
        development strategy.
        :param container:
        :param options:
        :param keyWordArguments:
        """
        self.listener = None
        if listener is not None and callable(listener):
            self.listener = listener

        LabelFrame.__init__(self, container, keyWordArguments)

        self.hwProbeContentMap = None
        self.logsListExists = False
        self.hostPropSheetExists = False
        self.devicesPropSheetExists = False
        self.hardwareProbe = HardwareProbe(hwProbeArgs=None)

        self.viewMode = HardwareProbeView.DEFAULT_VIEW_MODE
        if options is not None and isinstance(options, dict):
            if 'viewMode' in options and options['viewMode'] in ViewMode:
                self.viewMode   = options['viewMode']
            self.options = deepcopy(options)
        else:
            self.options = None

        self.checkBoxList = CheckBoxList(self, None, descriptor={'orientation': VERTICAL},
                                         listener=self.messageReceiver, border=3, relief=RIDGE)
        self.toolBar = HardwareProbeView.ToolBar(self, listener=self.messageReceiver)
        if self.viewMode == ViewMode.NOTEBOOK:
            self.toolBar.setModel({'viewMode': 'Notebook'})
        elif self.viewMode == ViewMode.TOPLEVEL:
            self.toolBar.setModel({'viewMode': 'TopLevel'})
        #   elif self.viewMode == ViewMode.FRAME:
        #       self.toolBar.setModel({'viewMode': 'Frame'})

        self.messageHelp    = Message(self, width=1000, text=GENERAL_HELP, fg='darkblue',
                                       border=3, relief=SUNKEN)

        #   imageTkGears = ImageTk.PhotoImage(Image.open(IMAGE_DEFAULT_WORKING))
        imageTkGears = ImageTk.PhotoImage(Image.open(IMAGE_DEFAULT_MOVING).resize((100, 100)))

        #   self.labelWaitingForGears = Label(self, text="working", bd=4, relief=RAISED)
        self.labelWaitingForGears = Label(self, image=imageTkGears, text=" Working ", compound=TOP, bd=4, relief=RAISED)
        self.labelWaitingForGears.image = imageTkGears

        self.toolBar.grid(row=0, column=0, padx=15, pady=5, sticky=N)
        self.checkBoxList.grid(row=0, column=1, padx=15, pady=5, sticky=N+E)
        self.labelWaitingForGears.grid(row=0, column=2, padx=15, pady=5, sticky=N+E)
        self.messageHelp.grid(row=10, column=0, columnspan=3, padx=15, pady=5, ipadx=15, ipady=5, sticky=S)

        #   self.playGifAnim(IMAGE_DEFAULT_MOVING, 300, 200)

    def setModel(self, model: object):
        if isinstance(model, dict):
            if 'toolBar' in model and 'checkBoxList' in model:
                self.getToolbar().setModel(model['toolBar'])
                self.getCheckBoxList().setModel(model['checkBoxList'])

    def getState(self, modelType: ModelType):
        return {
            'toolBar': self.getToolbar().getState(),
            'checkBoxList': self.getCheckBoxList().getState()
        }

    def setViewMode(self, viewMode: ViewMode):
        if viewMode in ViewMode:
            self.viewMode = viewMode
            self.toolBar.setModel({'viewMode': str(viewMode)})

    def getToolbar(self):
        return self.toolBar

    def getCheckBoxList(self):
        return self.checkBoxList

    def messageReceiver(self, message: dict):
        if 'source' in message:
            if message['source'] == "ToolBar.buttonAction":
                if message['name'] == str(HardwareProbeView.ToolBar.ToolName.LOAD_LATEST):
                    self.hwProbeContentMap = self.hardwareProbe.loadLatest()
                    if self.listener is not None:
                        self.listener({'source': 'HardwareProbeView.loadLatest',
                                       'hwProbeContentMap': self.hwProbeContentMap,
                                       'viewMode': self.viewMode})
                    jsonString = dumps(self.hwProbeContentMap, indent=4)
                    jsonFile = open(HW_PROBE_JSONFILE, 'w')
                    jsonFile.write(jsonString)
                    jsonFile.close()

                    #   compressedJSON  = compress(jsonString.encode('utf-8'))
                    compressedJSON  = compress(jsonString.encode('utf-8'))
                    gzipFile = open(HW_PROBE_ZIPFILE, 'wb')
                    gzipFile.write(compressedJSON)
                    gzipFile.close()

                    if TESTING:
                        gzipFile = open(HW_PROBE_ZIPFILE, 'rb')
                        jsonContent = decompress(gzipFile.read()).decode('utf-8')

                elif message['name'] == str(HardwareProbeView.ToolBar.ToolName.RUN_PROBE):
                    self.hardwareProbe.launchProbe()
                elif message['name'] == str(HardwareProbeView.ToolBar.ToolName.SHOW_HIST):
                    pass
                elif message['name'] == str(HardwareProbeView.ToolBar.ToolName.PROBE_OPTIONS):
                    if self.listener is not None:
                        self.listener({'source': 'ToolBar.buttonAction', 'buttonName': message['name']})
            if message['source'] == "CheckBoxList.checkBoxClicked":
                if 'text' in message:
                    if message['text'] == "Devices":
                        if 'newValue' in message and not Initializer.isInitializing():
                            if message['newValue']:
                                if not self.devicesPropSheetExists:
                                    messagebox.showwarning("Devices: No Information", "You must run the probe\nor load probe first")
                                    if 'callBack' in message and callable(message['callBack']):
                                        message['callBack']({'source': 'HardwareProbeView.messageReceiver',
                                                             'issue': 'noInformation',
                                                             'subject': message['text']})
                                    self.devicesPropSheetExists = True
                    elif message['text'] == "Host":
                        if 'newValue' in message:
                            if message['newValue'] and not Initializer.isInitializing():
                                if not self.hostPropSheetExists:
                                    messagebox.showwarning("Host: No Information", "You must run the probe\nor load probe first")
                                    if 'callBack' in message and callable(message['callBack']):
                                        message['callBack']({'source': 'HardwareProbeView.messageReceiver',
                                                             'issue': 'noInformation',
                                                             'subject': message['text']})
                                    self.hostPropSheetExists = True
                    elif message['text'] == "Logs":
                        if 'newValue' in message:
                            if message['newValue'] and not Initializer.isInitializing():
                                if not self.logsListExists:
                                    messagebox.showwarning("Logs: No Information", "You must run the probe\nor load probe first")
                                    if 'callBack' in message and callable(message['callBack']):
                                        message['callBack']({'source': 'HardwareProbeView.messageReceiver',
                                                             'issue': 'noInformation',
                                                             'subject': message['text']})
                                    self.logsListExists = True
            elif message['source'] == 'HardwareProbeView.viewModeChange':
                if 'newValue' in message:
                    if message['newValue'] == str(ViewMode.NOTEBOOK):
                        self.viewMode = ViewMode.NOTEBOOK
                    elif message['newValue'] == str(ViewMode.TOPLEVEL):
                        self.viewMode = ViewMode.TOPLEVEL
                    #   elif message['newValue'] == str(ViewMode.FRAME):
                    #       self.viewMode = ViewMode.FRAME
                    if self.listener is not None:
                        self.listener({'source': "HardwareProbeView.viewModeChange", 'newValue': self.viewMode})
            elif message['source'] == 'HardwareProbeView.showViewDetails':
                if 'action' in message and message['action'] == 'buttonClick':
                    if self.listener is not None:
                        message['hwProbeContentMap'] = self.hwProbeContentMap
                        self.listener(message)
            elif message['source'] == 'ViewControlPopup.selectionClick':
                if 'name' in message and isinstance(message['name'], str):
                    #   Implement selection

                    if self.listener is not None:
                        self.listener(message)
            elif message['source'] == 'ViewControlPopup.frameBoxClick':
                if 'name' in message and isinstance(message['name'], str):
                    #   Implement selection

                    if self.listener is not None:
                        self.listener(message)
            elif message['source'] == 'ViewControlPopup.notebookBoxClick':
                if 'name' in message and isinstance(message['name'], str):
                    #   Implement selection

                    if self.listener is not None:
                        self.listener(message)
            elif message['source'] == 'ViewControlPopup.toplevelBoxClick':
                if 'name' in message and isinstance(message['name'], str):
                    #   Implement selection

                    if self.listener is not None:
                        self.listener(message)


    def playGifAnim(self, gifImageFile: str, width, height):
        canvas = Image.new("RGB", (width, height), "white")
        gif = Image.open(gifImageFile, 'r')
        frames = []
        try:
            while 1:
                frames.append(gif.copy())
                gif.seek(len(frames))
        except EOFError:
            pass

        for frame in frames:
            canvas.paste(frame)
            canvas.show()


class HardwareProbeViewController(LabelFrame):

    VIEW_MODE_DEFAULT   = ViewMode.NOTEBOOK

    def __init__(self, container, options: dict=None, **keyWordArguments):
        self.container = container
        LabelFrame.__init__(self, self.container, keyWordArguments)
        Initializer.setInitializing(True)
        self.viewMode = HardwareProbeViewController.VIEW_MODE_DEFAULT
        self.notebookMain = None
        self.hardwareProbeView = None
        self.masterSlaveListsLogs   = None
        self.propertySheetHost      = None
        self.propertySheetDevices   = None
        self.masterSlaveListsTests = None
        self.optionsToplevel = None
        self.tabIds = OrderedDict()
        self.hwProbeContentMap = None
        self.hwProbeOptionList = HwProbeOption.list()
        self.messageOptionHelp = None
        self.viewDetailsPopup = None
        self.optionHelpMap = OrderedDict()
        self.topLevelMap = OrderedDict()
        self.topLevelThreadMap = OrderedDict()

        for option in self.hwProbeOptionList:
            self.optionHelpMap[option[KeyName.TEXT]] = option[KeyName.HELP]
        if isinstance(options, dict):
            if 'viewMode' in options and isinstance(options['viewMode'], ViewMode):
                self.viewMode = options['viewMode']
            self.options = deepcopy(options)
        else:
            self.options = {}
        if self.viewMode == ViewMode.NOTEBOOK:
            Initializer.setInitializing(True)
            self.notebookMain = Notebook(self)
            self.hardwareProbeView = HardwareProbeView(self.notebookMain, options={'viewMode': self.viewMode},
                                                       listener=self.messageReceiver)
            self.hardwareProbeView.config(text=None)
            self.notebookMain.add(self.hardwareProbeView, state=NORMAL, sticky=N + S + E + W,
                                                    padding=(10, 10, 10, 10), text=" Hardware Probe ")
            self.tabIds[FrameId.HW_PROBE] = 0
            self.notebookMain.grid(row=0, column=0, sticky=N + S + E + W)
            self.hardwareProbeView.setViewMode(ViewMode.NOTEBOOK)
            Initializer.setInitializing(False)
        elif self.viewMode == ViewMode.TOPLEVEL:
            pass

        #   elif self.viewMode == ViewMode.FRAME:
        #       Initializer.setInitializing(True)
        #       self.hardwareProbeView = HardwareProbeView(self, options={'viewMode': self.viewMode},
        #                                                  listener=self.messageReceiver)
        #       self.hardwareProbeView.grid(row=0, column=0, sticky=N+S+E+W)
        #       Initializer.setInitializing(False)

        Initializer.setInitializing(False)

    def constructorViewDescriptor(self, hwProbeContentMap: dict):
        descriptor = deepcopy(START_VIEW_SELECTION_STATE)
        nameMap = {}
        for selector in descriptor['viewSelectors']:
            nameMap[selector['name']] = selector
        if self.hwProbeContentMap is not None:
            if 'hostFileLines' in self.hwProbeContentMap:
                nameMap['host']['infoPresent'] = True
            if 'devicesLines' in self.hwProbeContentMap:
                nameMap['devices']['infoPresent'] = True
            if 'testMap' in self.hwProbeContentMap:
                if 'cpu_perf' in self.hwProbeContentMap['testMap']:
                    nameMap['cpu-perf']['infoPresent'] = True
                if 'glxgears' in self.hwProbeContentMap['testMap']:
                    nameMap['glxgears']['infoPresent'] = True
                if 'hdd_read' in self.hwProbeContentMap['testMap']:
                    nameMap['hdd_read']['infoPresent'] = True
                if 'memtester' in self.hwProbeContentMap['testMap']:
                    nameMap['memtester']['infoPresent'] = True
            if 'logMap' in self.hwProbeContentMap:
                nameMap['logs']['infoPresent'] = True
                if 'acpidump' in self.hwProbeContentMap['logMap']:
                    nameMap['acpi-dump']['infoPresent'] = True
                if 'acpidump_decoded' in self.hwProbeContentMap['logMap']:
                    nameMap['acpi-decode']['infoPresent'] = True

        return descriptor

    def topLevelLaunch(self, frameId: FrameId, listener, position: dict):
        """
        Result of this implementation:
            "RuntimeError: Calling Tcl from different apartment"
        The memory allocated to the self.xxx references in this object is shared among multiple threads,
        which in the case of a Tk mainloop() is a dangerous configuration, as tkinter is not designed
        to do proper locking of resources shared between its mainloop() threads.
        For this to work, separate instances of the view controller, consequently with their own memory
        spaces, would be needed for each mainloop() invoking instance of Toplevel.
        A copy-constructor could be used or a specialized class which is an allocation subset of the main
        view controller could be designed.
        For Now:
            User will be able to launch a Toplevel copy of any Notebook page using a toolbar at the top.
        :param frameId:
        :param listener:
        :param position:
        :return:
        """
        position = deepcopy(position)
        self.topLevelMap[frameId] = Toplevel(self)
        if frameId == str(FrameId.LOGS):
            self.masterSlaveListsLogs = \
                self.scrollableContent(ContentID.LOGS, container=self.topLevelMap[frameId])
            self.masterSlaveListsLogs.pack(fill=BOTH, expand=True)
        elif frameId == str(FrameId.HOST):
            self.propertySheetHost = \
                self.scrollableContent(ContentID.HOST, container=self.topLevelMap[frameId])
            self.propertySheetHost.pack(fill=BOTH, expand=True)
        elif frameId == str(FrameId.DEVICES):
            self.propertySheetDevices = \
                self.scrollableContent(ContentID.DEVICES, container=self.topLevelMap[frameId])
            self.propertySheetDevices.pack(fill=BOTH, expand=True)
        elif frameId == str(FrameId.TESTS):
            self.masterSlaveListsTests = \
                self.scrollableContent(ContentID.TESTS, container=self.topLevelMap[frameId])
            self.masterSlaveListsTests.pack(fill=BOTH, expand=True)
        elif frameId == str(FrameId.ACPI_DUMP):
            self.textFrameACPI_Dump = \
                self.scrollableContent(ContentID.ACPI_DUMP, container=self.topLevelMap[frameId])
            self.textFrameACPI_Dump.pack(fill=BOTH, expand=True)
        elif frameId == str(FrameId.ACPI_DECODED):
            self.listFrameACPI_Decoded = \
                self.scrollableContent(ContentID.ACPI_DECODED, container=self.topLevelMap[frameId])
            self.listFrameACPI_Decoded.pack(fill=BOTH, expand=True)
        self.topLevelMap[frameId].protocol('WM_DELETE_WINDOW', partial(self.exitTopLevel, frameId))
        geometryStr = '600x500+' + str(position['left']) + '+' + str(position['top'])
        self.topLevelMap[frameId].title(str(frameId))
        #   -alpha is not supported on Linux Mint XFCE
        #   self.topLevelMap[frameId].attributes('-alpha', 0.5)
        self.topLevelMap[frameId].attributes('-topmost', True)
        self.topLevelMap[frameId].mainloop()

    def messageReceiver(self, message):
        if not isinstance(message, dict):
            return
        if 'source' in message:
            if message['source'] == "HardwareProbeView.viewModeChange":
                if 'newValue' in message and isinstance(message['newValue'], ViewMode):
                    #   FRAME is too crowded to be useful for the number of information categories and the
                    #   size of some.  TOPLEVEL and NOTEBOOK will be the only two view modes initially.
                    if message['newValue'] == ViewMode.NOTEBOOK:
                        if self.viewMode == ViewMode.TOPLEVEL:
                            pass
                    elif message['newValue'] == ViewMode.TOPLEVEL:
                        if self.viewMode == ViewMode.NOTEBOOK:
                            pass
                    self.viewMode = message['newValue']

                    """ INITIAL PROTOTYPE CODE ONLY:
                    if message['newValue'] == ViewMode.NOTEBOOK:
                        if self.viewMode == ViewMode.FRAME:
                            Initializer.setInitializing(True)
                            if self.notebookMain is None:
                                self.notebookMain = Notebook(self)
                            checkListState = self.hardwareProbeView.getCheckBoxList().getState(ModelType.JSON)
                            toolBarState = self.hardwareProbeView.getToolbar().getState(ModelType.JSON)
                            self.hardwareProbeView.grid_forget()
                            self.hardwareProbeView = HardwareProbeView(self.notebookMain,
                                                                       options={'viewMode':ViewMode.NOTEBOOK},
                                                                       listener=self.messageReceiver)
                            self.hardwareProbeView.config(text=None)
                            if self.tabIds[FrameId.HW_PROBE] == None:
                                self.tabIds[FrameId.HW_PROBE] = 0
                                self.notebookMain.add(self.hardwareProbeView, state=NORMAL, sticky=N + S + E + W,
                                                      padding=(10, 10, 10, 10), text=" Hardware Probe ")
                            self.notebookMain.grid(row=0, column=0, sticky=N+S+E+W)
                            self.viewMode = ViewMode.NOTEBOOK
                            self.hardwareProbeView.setViewMode(ViewMode.NOTEBOOK)
                            self.hardwareProbeView.getCheckBoxList().setModel(checkListState)
                            toolBarState['viewMode'] = 'Notebook'
                            self.hardwareProbeView.getToolbar().setModel(toolBarState)
                            Initializer.setInitializing(False)

                    if message['newValue'] == ViewMode.FRAME:
                        if self.viewMode == ViewMode.NOTEBOOK:
                            Initializer.setInitializing(True)
                            checkListState = self.hardwareProbeView.getCheckBoxList().getState(ModelType.JSON)
                            toolBarState = self.hardwareProbeView.getToolbar().getState(ModelType.JSON)
                            self.notebookMain.grid_forget()
                            self.hardwareProbeView = HardwareProbeView(self, options={'viewMode': ViewMode.FRAME},
                                                                       listener=self.messageReceiver,
                                                                       text=" Hardware Probe ")
                            self.hardwareProbeView.getCheckBoxList().setModel(checkListState)
                            self.hardwareProbeView.getToolbar().setModel(toolBarState)
                            self.hardwareProbeView.grid(row=0, column=0, sticky=N + S + E + W)
                            self.viewMode = ViewMode.FRAME
                            self.hardwareProbeView.setViewMode(ViewMode.FRAME)
                            Initializer.setInitializing(False)
                    """
            elif message['source'] == 'HardwareProbeView.loadLatest':
                if 'hwProbeContentMap' in message and isinstance(message['hwProbeContentMap'], dict):
                    self.hwProbeContentMap = message['hwProbeContentMap']
                else:
                    raise Exception("HardwareProbeViewController.messageReceiver - Invalid hwProbeContentMap:  " +
                                    str(self.hwProbeContentMap))
                if self.viewMode == ViewMode.NOTEBOOK:
                    if self.notebookMain is not None:
                        if 'logMap' in self.hwProbeContentMap:
                            if FrameId.LOGS not in self.tabIds:
                                self.contentFrameContainer = \
                                    ContentFrameContainer(self.notebookMain, ContentID.LOGS, config=None,
                                                          listener=self.messageReceiver, border=4, relief=GROOVE)
                                self.masterSlaveListsLogs = self.scrollableContent(ContentID.LOGS,
                                                                                   container=self.contentFrameContainer)
                                self.contentFrameContainer.setContent(self.masterSlaveListsLogs)
                                self.notebookMain.add(self.contentFrameContainer, state=NORMAL, sticky=N + S + E + W,
                                                      padding=(10, 10, 10, 10), text=" Logged Events ")
                                self.tabIds[FrameId.LOGS] = self.tabIds[list(self.tabIds.keys())[-1]] + 1

                        if 'hostFileLines' in self.hwProbeContentMap:
                            if FrameId.HOST not in self.tabIds:
                                self.contentFrameContainer = \
                                    ContentFrameContainer(self.notebookMain, ContentID.HOST, config=None,
                                                          listener=self.messageReceiver, border=4, relief=GROOVE)
                                self.propertySheetHost = self.scrollableContent(ContentID.HOST,
                                                                                container=self.contentFrameContainer)
                                self.contentFrameContainer.setContent(self.propertySheetHost)
                                self.notebookMain.add(self.contentFrameContainer, state=NORMAL, sticky=N + S + E + W,
                                                      padding=(10, 10, 10, 10), text=" Host Hardware ")
                                self.tabIds[FrameId.HOST] = self.tabIds[list(self.tabIds.keys())[-1]] + 1

                        if 'devicesLines' in self.hwProbeContentMap:
                            if FrameId.DEVICES not in self.tabIds:
                                self.contentFrameContainer = \
                                    ContentFrameContainer(self.notebookMain, ContentID.DEVICES, config=None,
                                                          listener=self.messageReceiver, border=4, relief=GROOVE)
                                self.propertySheetDevices = self.scrollableContent(ContentID.DEVICES,
                                                                                   container=self.contentFrameContainer)
                                self.contentFrameContainer.setContent(self.propertySheetDevices)
                                self.notebookMain.add(self.contentFrameContainer, state=NORMAL, sticky=N + S + E + W,
                                                      padding=(10, 10, 10, 10), text=" Devices ")
                                self.tabIds[FrameId.DEVICES] = self.tabIds[list(self.tabIds.keys())[-1]] + 1

                        if 'testMap' in self.hwProbeContentMap:
                            if FrameId.TESTS not in self.tabIds:
                                self.contentFrameContainer = \
                                    ContentFrameContainer(self.notebookMain, ContentID.TESTS, config=None,
                                                          listener=self.messageReceiver, border=4, relief=GROOVE)
                                self.masterSlaveListsTests = self.scrollableContent(ContentID.TESTS,
                                                                                   container=self.contentFrameContainer)
                                self.contentFrameContainer.setContent(self.masterSlaveListsTests)
                                self.notebookMain.add(self.contentFrameContainer, state=NORMAL, sticky=N + S + E + W,
                                                      padding=(10, 10, 10, 10), text=" Tests Run ")
                                self.tabIds[FrameId.TESTS] = self.tabIds[list(self.tabIds.keys())[-1]] + 1

                        if 'acpidump' in self.hwProbeContentMap:
                            if FrameId.ACPI_DUMP not in self.tabIds:
                                self.contentFrameContainer = \
                                    ContentFrameContainer(self.notebookMain, ContentID.ACPI_DUMP, config=None,
                                                          listener=self.messageReceiver, border=4, relief=GROOVE)
                                self.textFrameACPI_Dump     = self.scrollableContent(ContentID.ACPI_DUMP,
                                                                                   container=self.contentFrameContainer)
                                self.contentFrameContainer.setContent(self.textFrameACPI_Dump)
                                self.notebookMain.add(self.contentFrameContainer, state=NORMAL, sticky=N + S + E + W,
                                                      padding=(10, 10, 10, 10), text=" ACPI Dump ")
                                self.tabIds[FrameId.ACPI_DUMP] = self.tabIds[list(self.tabIds.keys())[-1]] + 1

                        if 'acpidump_decoded' in self.hwProbeContentMap:
                            if FrameId.ACPI_DECODED not in self.tabIds:
                                self.contentFrameContainer = \
                                    ContentFrameContainer(self.notebookMain, ContentID.ACPI_DECODED, config=None,
                                                          listener=self.messageReceiver, border=4, relief=GROOVE)
                                self.listFrameACPI_Decoded     = self.scrollableContent(ContentID.ACPI_DECODED,
                                                                                   container=self.contentFrameContainer)
                                self.contentFrameContainer.setContent(self.listFrameACPI_Decoded)
                                self.notebookMain.add(self.contentFrameContainer, state=NORMAL, sticky=N + S + E + W,
                                                      padding=(10, 10, 10, 10), text=" ACPI Decoded ")
                                self.tabIds[FrameId.ACPI_DECODED] = self.tabIds[list(self.tabIds.keys())[-1]] + 1

                elif self.viewMode == ViewMode.TOPLEVEL:
                    position = {'left':100, 'top':100}
                    if 'logMap' in self.hwProbeContentMap:
                        if FrameId.LOGS not in self.topLevelMap:
                            self.topLevelThreadMap[FrameId.LOGS] = \
                                Thread(target=self.topLevelLaunch, args=(FrameId.LOGS, self.messageReceiver, position))
                            self.topLevelThreadMap[FrameId.LOGS].start()
                            position['left'] += 50
                            position['top'] += 50
                    if 'hostFileLines' in self.hwProbeContentMap:
                        if FrameId.HOST not in self.topLevelMap:
                            self.topLevelThreadMap[FrameId.HOST] = \
                                Thread(target=self.topLevelLaunch, args=(FrameId.HOST, self.messageReceiver, position))
                            self.topLevelThreadMap[FrameId.HOST].start()
                            position['left'] += 50
                            position['top'] += 50

                    if 'devicesLines' in self.hwProbeContentMap:
                        if FrameId.DEVICES not in self.topLevelMap:
                            self.topLevelThreadMap[FrameId.DEVICES] = \
                                Thread(target=self.topLevelLaunch, args=(FrameId.DEVICES, self.messageReceiver, position))
                            self.topLevelThreadMap[FrameId.DEVICES].start()
                            position['left'] += 50
                            position['top'] += 50

                    if 'testMap' in self.hwProbeContentMap:
                        if FrameId.TESTS not in self.topLevelMap:
                            self.topLevelThreadMap[FrameId.TESTS] = \
                                Thread(target=self.topLevelLaunch, args=(FrameId.TESTS, self.messageReceiver, position))
                            self.topLevelThreadMap[FrameId.TESTS].start()
                            position['left'] += 50
                            position['top'] += 50

                    if 'acpidump' in self.hwProbeContentMap:
                        if FrameId.ACPI_DUMP not in self.topLevelMap:
                            self.topLevelThreadMap[FrameId.ACPI_DUMP] = \
                                Thread(target=self.topLevelLaunch, args=(FrameId.ACPI_DUMP, self.messageReceiver, position))
                            self.topLevelThreadMap[FrameId.ACPI_DUMP].start()
                            position['left'] += 50
                            position['top'] += 50

                    if 'acpidump_decoded' in self.hwProbeContentMap:
                        if FrameId.ACPI_DECODED not in self.topLevelMap:
                            self.topLevelThreadMap[FrameId.ACPI_DECODED] = \
                                Thread(target=self.topLevelLaunch, args=(FrameId.ACPI_DECODED, self.messageReceiver, position))
                            self.topLevelThreadMap[FrameId.ACPI_DECODED].start()
                            position['left'] += 50
                            position['top'] += 50

                """
                elif self.viewMode == ViewMode.FRAME:
                    if self.masterSlaveListsLogs is None:
                        self.masterSlaveListsLogs = self.scrollableContent(ContentID.LOGS)
                    if self.propertySheetHost is None:
                        self.propertySheetHost = self.scrollableContent(ContentID.HOST)
                    if self.propertySheetDevices is None:
                        self.propertySheetDevices = self.scrollableContent(ContentID.DEVICES)
                    self.masterSlaveListsLogs.grid(row=3, column=0, padx=15, pady=5)
                    self.propertySheetHost.grid(row=3, column=1, padx=15, pady=5)
                    self.propertySheetDevices.grid(row=3, column=2, padx=15, pady=5)
                """
                #   Set the toggle check boxes for each of these to on since they are all displayed.
                Initializer.setInitializing(True)
                if 'devicesLines' in self.hwProbeContentMap:
                    self.hardwareProbeView.checkBoxList.setCheck('Devices', True)
                if 'hostFileLines' in self.hwProbeContentMap:
                    self.hardwareProbeView.checkBoxList.setCheck('Host', True)
                if 'logMap' in self.hwProbeContentMap:
                    self.hardwareProbeView.checkBoxList.setCheck('Logs', True)
                if 'testMap' in self.hwProbeContentMap:
                    self.hardwareProbeView.checkBoxList.setCheck('Tests', True)
                if 'acpidump' in self.hwProbeContentMap:
                    self.hardwareProbeView.checkBoxList.setCheck('ACPI Dump', True)
                if 'acpidump_decoded' in self.hwProbeContentMap:
                    self.hardwareProbeView.checkBoxList.setCheck('ACPI Decoded', True)


                Initializer.setInitializing(False)

            elif message['source'] == 'ToolBar.buttonAction':
                if 'buttonName' in message and message['buttonName'] == str(HardwareProbeView.ToolBar.ToolName.PROBE_OPTIONS):
                    #   Plan:   Pop-Up Options Dialog (initially as Toplevel), which is a scrollable view.CheckBoxList
                    #           with help messages.
                    if self.optionsToplevel is None:
                        self.optionsToplevel = Toplevel(self)
                        self.optionsToplevel.title(" hw-probe Options ")
                        windowWidth = 350
                        self.optionsToplevel.geometry(str(windowWidth) + "x500+50+100")
                        self.optionsToplevel.protocol('WM_DELETE_WINDOW', lambda: self.exitOptionsToplevel())

                        #   self.scrollerText = Text(self.optionsToplevel)
                        self.scrollableOptions = FrameScroller(self.optionsToplevel, name='scrollableOptions')
                        self.checkBoxListOptions = CheckBoxList(self.scrollableOptions.getScrollerFrame(),
                                                                self.hwProbeOptionList,
                                                                descriptor={'orientation': VERTICAL,
                                                                            'labelLength': 25,
                                                                            'helpText': KeyName.HELP},
                                                               listener=self.messageReceiver,
                                                                width=windowWidth, border=3, relief=RIDGE)
                        self.messageOptionHelp = Message(self.optionsToplevel, text="informative messages \nregarding selections",
                                                         width=windowWidth, fg='darkblue', border=1, relief=SUNKEN)

                        self.checkBoxListOptions.pack(expand=True, fill=BOTH)
                        self.messageOptionHelp.pack(pady=5, side='bottom', fill=Y, expand=True)
                        self.scrollableOptions.pack(expand=True, fill=BOTH)
                        self.optionsToplevel.mainloop()

            #   {'source': 'CheckBoxList.mouseEnter', 'optionText': event.widget.cget('text') }
            elif message['source'] == 'CheckBoxList.mouseEnter':
                if 'optionText' in message:
                    self.messageOptionHelp.config(text=self.optionHelpMap[message['optionText']])

            #   {'source': 'HardwareProbeView.showViewDetails', 'action' 'buttonClick'}
            elif message['source'] == 'HardwareProbeView.showViewDetails':
                if 'action' in message and message['action'] == 'buttonClick':
                    if "hwProbeContentMap" in message:
                        if isinstance(message['hwProbeContentMap'], dict):
                            if self.viewDetailsPopup is None:
                                descriptor = self.constructorViewDescriptor(message['hwProbeContentMap'])
                                self.viewDetailsPopup = ViewControlPopup(self, descriptor)
                                self.viewDetailsPopup.protocol('WM_DELETE_WINDOW', self.exitViewDetailsPopup)
                        else:
                            #   User likely has not run probe and loaded the results yet.
                            messagebox.showwarning("Views: No Information",
                                                   "You must run the probe or,\n"
                                                   "if there is a dataset from a\n"
                                                   "previous probe already,\n"
                                                   " load the probe first")

            elif message['source'] == 'ViewControlPopup.selectionClick':
                if 'name' in message and isinstance(message['name'], str):
                    if 'newValue' in message and isinstance(message['newValue'], bool):
                        #   Record new view state

                        pass

            elif message['source'] == 'ViewControlPopup.frameBoxClick':
                if 'name' in message and isinstance(message['name'], str):
                    if 'newValue' in message and isinstance(message['newValue'], bool):
                        #   Record new view state

                        pass

            elif message['source'] == 'ViewControlPopup.notebookBoxClick':
                if 'name' in message and isinstance(message['name'], str):
                    if 'newValue' in message and isinstance(message['newValue'], bool):
                        #   Record new view state

                        pass

            elif message['source'] == 'ViewControlPopup.toplevelBoxClick':
                if 'name' in message and isinstance(message['name'], str):
                    if 'newValue' in message and isinstance(message['newValue'], bool):
                        #   Record new view state

                        pass
            #   {'source': "ContentFrameContainer.toggleButton",
            #                                    'target': buttonName,
            #                                    'contentId': self.contentId,
            #                                    'newValue': self.toggleMap[buttonName]}
            elif message['source'] == 'ContentFrameContainer.toggleButton':
                if 'target' in message and message['target'] == "Toplevel":
                    if 'newValue' in message and isinstance(message['newValue'], bool):
                        if message['newValue']:
                            if 'contentId' in message:
                                if not message['contentId'] in self.topLevelMap or \
                                        self.topLevelMap[message['contentId']] is None:
                                    self.topLevelLaunch(message['contentId'], self.messageReceiver,
                                                        {'left': 400, 'top': 100})
                        else:
                            if 'contentId' in message:
                                if message['contentId'] in self.topLevelMap and \
                                        self.topLevelMap[message['contentId']] is not None:
                                    self.exitTopLevel(message['contentId'])

    def exitTopLevel(self, frameId: FrameId):
        if frameId in self.topLevelMap and self.topLevelMap[frameId] is not None:
            self.topLevelMap[frameId].destroy()
            self.topLevelMap[frameId] = None
        elif str(frameId) in self.topLevelMap and self.topLevelMap[str(frameId)] is not None:
            self.topLevelMap[str(frameId)].destroy()
            self.topLevelMap[str(frameId)] = None
        #   self.topLevelThreadMap[frameId].join()

    def exitViewDetailsPopup(self):
        self.viewDetailsPopup.destroy()
        self.viewDetailsPopup = None

    def exitOptionsToplevel(self):
        self.optionsToplevel.destroy()
        self.optionsToplevel = None

    def propertySheetAdapter(self, properties):
        fields = OrderedDict()
        for propertyLine in properties:
            lineParts = propertyLine.split(':')
            if len(lineParts) >= 2:
                fields[lineParts[0].strip()] = lineParts[1].strip()
            elif len(lineParts) == 1:
                fields[lineParts[0].strip()] = None

        return fields

    def masterSlaveAdapter(self, contentMap: dict):
        descriptor = OrderedDict({  KeyName.VIEW: {
                                        'masterWidth': 15,
                                        'slaveWidth': '100'
                                    },
                                    KeyName.INFO: []
                                 })
        for name, content in contentMap.items():
            descriptor[KeyName.INFO].append({
                KeyName.NAME: name,
                KeyName.TEXT: name,
                KeyName.SLAVE_LIST: []
            })
            for logLine in content:
                descriptor[KeyName.INFO][-1][KeyName.SLAVE_LIST].append( {
                    KeyName.TEXT: logLine
                })
            descriptor[KeyName.INFO][-1][KeyName.SLAVE_LIST] = tuple(descriptor[KeyName.INFO][-1][KeyName.SLAVE_LIST])
        return descriptor

    def scrollableContent(self, contentId: ContentID, container=None):
        if container is None:
            container = self
        contentView = None
        scrollFrame = Frame(container, border=3, relief=RIDGE)
        if contentId == ContentID.HOST:
            textWidth = 70
            title = " Host "
        elif contentId == ContentID.DEVICES:
            textWidth = 140
            title = " Devices "
        elif contentId == ContentID.LOGS:
            textWidth = 100
            title = " Logs "
        elif contentId == ContentID.ACPI_DUMP:
            textWidth = 100
            title = " ACPI Dump "
        elif contentId == ContentID.ACPI_DECODED:
            textWidth = 80
            title = " ACPI Decoded "
        else:
            textWidth = 20
            title = " Unknown Source "
        scrollerText = Text(scrollFrame, width=textWidth)
        if contentId == ContentID.HOST:
            contentView = SimplePropertyListFrame(scrollerText, self.propertySheetAdapter(self.hwProbeContentMap['hostFileLines']),
                                                  valueWidth=40, listener=self.messageReceiver, text=title,
                                                  border=3, relief=GROOVE)
        elif contentId == ContentID.DEVICES:
            maxLineLen = 0
            for line in self.hwProbeContentMap['devicesLines']:
                if len(line) > maxLineLen:
                    maxLineLen = len(line)
            #   Font width correction:
            maxLineLen =  floor(maxLineLen * 0.8)
            contentView = SimplePropertyListFrame(scrollerText, self.propertySheetAdapter(self.hwProbeContentMap['devicesLines']),
                                                  valueWidth=maxLineLen, listener=self.messageReceiver, text=title,
                                                  border=3, relief=GROOVE)
            self.container.geometry("1200x600+50+50")
        elif contentId == ContentID.LOGS:
            contentView = MasterSlaveLists(scrollFrame, self.masterSlaveAdapter(self.hwProbeContentMap['logMap']),
                                            listener=self.messageReceiver, text=title, border=3, relief=GROOVE)
            contentView.pack(fill=BOTH, expand=True)
            return scrollFrame

        elif contentId == ContentID.TESTS:
            testContents = OrderedDict({
                'CPU Performance': self.hwProbeContentMap['testMap']['cpu_perf'],
                'Graphics': self.hwProbeContentMap['testMap']['glxgears'],
                'Hard Disk': self.hwProbeContentMap['testMap']['hdd_read'],
                'Memory': self.hwProbeContentMap['testMap']['memtester'],
            })
            contentView = ContentGridFrame(scrollFrame, self.hwProbeContentMap['testMap'], descriptor = {},
                                            listener=self.messageReceiver, text=title, border=3, relief=GROOVE)
            contentView.pack(fill=BOTH, expand=True)
            return scrollFrame

        elif contentId == ContentID.ACPI_DUMP:
            contentView = TextFrame(scrollFrame, self.hwProbeContentMap['acpidump'], descriptor={'name': "ACPI Dump"},
                                            listener=self.messageReceiver, text=title, border=3, relief=GROOVE)
            contentView.pack(fill=BOTH, expand=True)

        elif contentId == ContentID.ACPI_DECODED:
            contentView = ListFrame(scrollFrame, self.hwProbeContentMap['acpidump_decoded'], descriptor={},
                                            listener=self.messageReceiver, text=title, border=3, relief=GROOVE)
            contentView.pack(fill=BOTH, expand=True)

        if contentView is not None:
            scrollerText.window_create('1.0', window=contentView)
            vertScrollBar   = Scrollbar(scrollFrame, orient=VERTICAL, command=scrollerText.yview)
            horzScrollBar   = Scrollbar(scrollFrame, orient=HORIZONTAL, command=scrollerText.xview)
            scrollerText.config(yscrollcommand=vertScrollBar.set, xscrollcommand=horzScrollBar.set, state=DISABLED)

            scrollerText.grid(row=0, column=0, sticky=N+S+E+W)
            vertScrollBar.grid(row=0, column=1, sticky=N+S)
            horzScrollBar.grid(row=1, column=0, sticky=E+W)
        return scrollFrame


def ExitProgram():
    answer = messagebox.askyesno(parent=mainView, title='Exit program ', message="Exit the " + PROGRAM_TITLE + " program?")
    if answer:
        mainView.destroy()


if __name__ == '__main__':
    #simpledialog.

    mainView = Tk()
    mainView.geometry("1000x600+50+50")
    mainView.title(PROGRAM_TITLE)
    mainView.protocol('WM_DELETE_WINDOW', lambda: ExitProgram())

    hardwareProbeController = HardwareProbeViewController(mainView, options={'viewMode': ViewMode.NOTEBOOK})
    hardwareProbeController.grid(row=0, column=0, sticky=N+S+E+W)

    mainView.mainloop()