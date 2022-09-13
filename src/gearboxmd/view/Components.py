#   Project:        GearboxMD
#   Author:         George Keith Watson
#   Date Started:   September 05, 2020
#   Copyright:      (c) Copyright 2022 George Keith Watson
#   Module:         view/Components.py
#   Date Started:   September 6, 2022
#   Purpose:        Composite GUI components needed for display of hardware and diagnostic information.
#   Development:
#

from collections import OrderedDict
from enum import Enum
from copy import deepcopy
from functools import partial

from tkinter import Tk, Frame, LabelFrame, Listbox, messagebox, Checkbutton, Label, Button, Text, Toplevel, Message, \
                    N, S, E, W, FLAT, SUNKEN, RAISED, RIDGE, GROOVE, HORIZONTAL, VERTICAL, X, Y, BOTH, \
                    END, SINGLE, MULTIPLE, EXTENDED, DISABLED, NORMAL, \
                    StringVar, BooleanVar
from tksheet import Sheet


from model.Util import ModelType
from model.Hardware import KeyName, ContentID
from view.FrameScroller import FrameScroller

PROGRAM_TITLE = "GUI Components"
INSTALLING  = False
TESTING     = True
DEBUG       = False


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


class FrameId(Enum):
    HW_PROBE        = 'Hardware Probe'
    DEVICES         = 'Devices'
    HOST            = 'Host'
    LOGS            = 'Logs'
    TESTS           = 'Tests'
    ACPI_DUMP       = "ACPI Dump"
    ACPI_DECODED    = "ACPI Decoded"

    def __str__(self):
        return self.value


class ContentFrameContainer(LabelFrame):

    DEFAULT_CONFIG = {
        'buttons':  (
            {   'name': 'Toplevel',
                'type': 'toggle',
                'text': ' Toplevel ',
                'action': 'toggleToplevel',
                'help': 'Launch a window which displays the same content as this frame.\n'
                        'These can be viewed side-by-side for any content type in the notebook.'
            },
            {   'name': 'Filters',
                'type': 'toggle',
                'text': " Filters ",
                'action': 'toggleFilters',
                'help': 'Toggle on and off the filters for this content.\n'
                        'Filters use plain text or regular expressions to search the content and show only matching lines.'
            },
            {   'name': 'Analysis',
                'type': 'toggle',
                'text': " Analysis ",
                'action': 'toggleAnalysisFrame',
                'help': 'Toggle on and off the analysis panel.\n'
                        'Analyses can be done using any of the content currently loaded.'
             },
            {   'name': 'Export',
                'type': 'button',
                'text': "Export",
                'action': 'exportContent',
                'help': 'Export the content of this frame to file usable by other applications.\n'
                         'Format options available: json, xml, csv, ...'
             },
        ),
        'messageComponent':    {
            'type': 'label',            #   or Message
            'width': '100',
            'lines': 2
        }
    }

    def __init__(self, container, contentId: ContentID, config: dict=None, listener=None, **keyWordArguments):
        #   if not isinstance(contentId, ContentID):
        #       raise Exception("ContentFrameContainer constructor - Invalid contentId argument:  " + str(contentId))
        self.contentId = contentId
        if config is None:
            self.config = ContentFrameContainer.DEFAULT_CONFIG
        else:
            self.config = deepcopy(config)
        self.listener = None
        if listener is not None and callable(listener):
            self.listener = listener
        LabelFrame.__init__(self, container, keyWordArguments)

        if 'buttons' in self.config:
            self.frameButtonBar = Frame(self, border=3, relief=RAISED)
            self.buttonMap = OrderedDict()
            self.buttonHelpMap = OrderedDict()
            self.helpTextMap = {}
            self.toggleMap = {}
            colIdx = 0
            for buttonConfig in self.config['buttons']:
                if not 'name' in buttonConfig and 'type' in buttonConfig and 'text' in buttonConfig and 'action' in \
                        buttonConfig and 'help' in buttonConfig:
                    raise Exception("ContentFrameContainer constructor - Invalid button in config argument:  " +
                                    str(buttonConfig))
                if buttonConfig['type'] == 'toggle':
                    self.toggleMap[buttonConfig['name']] = False
                    self.buttonMap[buttonConfig['name']] = \
                        Label(self.frameButtonBar, text=buttonConfig['text'], border=2, relief=RAISED)
                    self.buttonMap[buttonConfig['name']].bind('<Button-1>',
                                                              partial(self.toggleButton, buttonConfig['name']))
                    self.buttonMap[buttonConfig['name']].bind('<Enter>', partial( self.mouseEnter, buttonConfig['name']))
                else:
                    self.buttonMap[buttonConfig['name']] = \
                        Button(self.frameButtonBar, text=buttonConfig['text'],
                               command=partial(self.buttonAction, buttonConfig['action'], buttonConfig['name']))
                    self.buttonMap[buttonConfig['name']].bind('<Enter>', partial(self.mouseEnter, buttonConfig['name']))
                self.buttonMap[buttonConfig['name']].grid(row=0, column=colIdx, padx=5, pady=5)
                self.helpTextMap[buttonConfig['name']] = buttonConfig['help']
                colIdx += 1
            self.frameButtonBar.grid(row=0, column=0, padx=15, pady=2, sticky=N+W)

        if 'messageComponent' in self.config:
            helpConfig = self.config['messageComponent']
            self.labelHelpMessages = Label(self, text="Help / Information", bd=3, relief=SUNKEN, fg='darkblue',
                                           width=helpConfig['width'], height=helpConfig['lines'])
            self.labelHelpMessages.grid(row=3, column=0, padx=15, pady=3, sticky=S+E+W)

    def mouseEnter(self, helpTopic: str, event):
        self.labelHelpMessages.config(text=self.helpTextMap[helpTopic])

    def setContent(self, contentFrame: Frame):
        if contentFrame is not None and isinstance(contentFrame, Frame):
            self.innerFrame = contentFrame
            self.innerFrame.grid(row=1, column=0, padx=15, pady=5, sticky=E + W)
        else:
            raise Exception("ContentFrameContainer.setContent - Invalid contentFrame argument:  " + str(contentFrame))

    def toggleButton(self, buttonName, event):
        if self.toggleMap[buttonName]:
            self.buttonMap[buttonName].config(relief=RAISED)
            self.toggleMap[buttonName] = False
            if buttonName == 'Toplevel':
                if self.listener is not None:
                    self.listener({'source': "ContentFrameContainer.toggleButton",
                                   'target': buttonName,
                                   'contentId': self.contentId,
                                   'newValue': self.toggleMap[buttonName]})
        else:
            self.buttonMap[buttonName].config(relief=SUNKEN)
            self.toggleMap[buttonName] = True
            if buttonName == 'Toplevel':
                if self.listener is not None:
                    self.listener({'source': "ContentFrameContainer.toggleButton",
                                   'target': buttonName,
                                   'contentId': self.contentId,
                                   'newValue': self.toggleMap[buttonName]})

    def toggleToplevel(self, event):

        #   The Toplevel for the particular contentmust be "Always on top" and the Toplevels without focus should
        #   have their -alpha set to about 0.75.

        pass

    def toggleFilters(self, event):
        pass

    def toggleAnalysisFrame(self, event):
        pass

    def buttonAction(self, action, actionName):
        if callable(action):
            action({'source': 'ContentFrameContainer.buttonAction',
                    'contentId': self.contentId,
                    'actionName': actionName})
        elif action == 'exportContent':
            pass

class ContentGridFrame(LabelFrame):
    """
    This only works for Listbox content so far, but any type can potentially be placed in a frame and arranged
    in a grid using this class.
    """

    DEFAULT_DESCRIPTOR  = {        'columns': 2    }
    MAX_LIST_LINES  = 10

    def __init__(self, container, frameContents: OrderedDict, descriptor: dict=None, listener=None, **keyWordArguments):
        if not isinstance(frameContents, OrderedDict):
            raise Exception("TextFrame constructor - Invalid frameContents argument:  " + str(frameContents))
        for name, lineList in frameContents.items():
            if not isinstance(lineList, tuple):
                raise Exception("TextFrame constructor - Invalid lineList in frameContents argument:  " + str(lineList))
            for line in lineList:
                if not isinstance(line, str):
                    raise Exception("TextFrame constructor - Invalid line in lineList in frameContents argument:  " + str(line))
        self.frameContents = frameContents
        if not isinstance(descriptor, dict):
            self.descriptor = ContentGridFrame.DEFAULT_DESCRIPTOR
        else:
            self.descriptor = deepcopy(descriptor)
        self.listener = None
        if listener is not None and callable(listener):
            self.listener = listener
        LabelFrame.__init__(self, container, keyWordArguments)

        self.contentFrames = OrderedDict()
        for listName, lineList in self.frameContents.items():
            self.contentFrames[listName] = LabelFrame(self, text=listName, border=2, relief=SUNKEN)
            maxLineLen = 0
            for line in lineList:
                if len(line) > maxLineLen:
                    maxLineLen = len(line)
            listHeight = min(ContentGridFrame.MAX_LIST_LINES, len(lineList))
            listContent = Listbox(self.contentFrames[listName], border=3, relief=RIDGE,
                                                   selectmode=SINGLE, height=listHeight, width=maxLineLen+2)
            listContent.insert(END, *lineList)
            if len(lineList) > 0:
                listContent.selection_set(0, 0)
            listContent.bind('<<ListboxSelect>>', partial(self.listSelection, listName))
            listContent.pack(expand=True, fill=BOTH)

        if 'columns' in self.descriptor and isinstance(self.descriptor['columns'], int):
            self.colCount = self.descriptor['columns']
        else:
            self.colCount = 2
        rowIdx = 0
        colIdx = 0
        for listName, frame in self.contentFrames.items():
            frame.grid(row=rowIdx, column=colIdx, padx=15, pady=5)
            colIdx += 1
            if colIdx % self.colCount == 0:
                rowIdx += 1
                colIdx = 0

    def listSelection(self, event, listName: str):
        pass

    def messageReceiver(self, message: dict):
        if not isinstance(message, dict):
            return
        if 'source' in message:
            pass

    def setModel(self, model: tuple):
        pass

    def getState(self):
        pass


class TextFrame(LabelFrame):

    def __init__(self, container, content: tuple, descriptor: dict=None, listener=None, **keyWordArguments):
        if not isinstance(content, tuple):
            raise Exception("TextFrame constructor - Invalid content argument:  " + str(content))
        for line in content:
            if not isinstance(line, str):
                raise Exception("TextFrame constructor - Invalid line in content argument:  " + str(line))
        self.content = content
        if not isinstance(descriptor, dict):
            raise Exception("TextFrame constructor - Invalid descriptor argument:  " + str(descriptor))
        self.listener = None
        if listener is not None and callable(listener):
            self.listener = listener
        self.descriptor = deepcopy(descriptor)
        LabelFrame.__init__(self, container, keyWordArguments)
        if 'name' in self.descriptor:
            self.config(text=self.descriptor['name'])
        self.textContent = Text(self)
        for line in self.content:
            self.textContent.insert('1.0', line+'\n')
        self.textContent.config(state=DISABLED)
        self.textContent.pack(expand=True, fill=BOTH)

    def setModel(self, model: dict):
        pass

    def getState(self):
        return None

    def messageReceiver(self, message: dict):
        if not isinstance(message, dict):
            return
        if 'source' in message:
            pass

    def list(self):
        pass


class ListFrame(LabelFrame):
    """
    2022-09-12:
    This list container can contain lists of any length, and an ACPI dump can have tens of thousands of lines.
    It therefore should have the option of a regular expression based filter available and activated
    using the descriptor argument.
    """

    def __init__(self, container, content: tuple, descriptor: dict=None,listener=None, **keyWordArguments):
        if not isinstance(content, tuple):
            raise Exception("TextFrame constructor - Invalid content argument:  " + str(content))
        for line in content:
            if not isinstance(line, str):
                raise Exception("TextFrame constructor - Invalid line in content argument:  " + str(line))
        self.content = content
        if not isinstance(descriptor, dict):
            raise Exception("TextFrame constructor - Invalid descriptor argument:  " + str(descriptor))
        self.listener = None
        if listener is not None and callable(listener):
            self.listener = listener
        self.descriptor = deepcopy(descriptor)
        LabelFrame.__init__(self, container, keyWordArguments)
        if 'name' in self.descriptor:
            self.config(text=self.descriptor['name'])
        self.listBoxContent = Listbox(self, border=3, relief=RIDGE, selectmode=SINGLE, height=30, width=100)
        self.listBoxContent.insert(END, *self.content)
        if len(self.content) > 0:
            self.listBoxContent.selection_set(0, 0)
        self.listBoxContent.bind('<<ListboxSelect>>', self.listSelection)
        self.listBoxContent.pack(expand=True, fill=BOTH)

    def listSelection(self, event):
        pass

    def setModel(self, model: dict):
        pass

    def getState(self):
        return None

    def messageReceiver(self, message: dict):
        if not isinstance(message, dict):
            return
        if 'source' in message:
            pass

    def list(self):
        pass


class CheckBoxList(LabelFrame):

    DEFAULT_CONTENT  = (
        {   KeyName.TEXT: str(FrameId.DEVICES)},
        {   KeyName.TEXT: str(FrameId.HOST)},
        {   KeyName.TEXT: str(FrameId.LOGS)},
        {   KeyName.TEXT: str(FrameId.TESTS)},
        {   KeyName.TEXT: str(FrameId.ACPI_DUMP)},
        {   KeyName.TEXT: str(FrameId.ACPI_DECODED)},
    )
    DEFAULT_HEIGHT  = 10
    DEFAULT_DESCRIPTOR = {
        'orientation': VERTICAL
    }

    def __init__(self, container, content: tuple, descriptor: dict=None, listener=None, **keyWordArguments):
        if content is None:
            self.content = CheckBoxList.DEFAULT_CONTENT
        else:
            if not isinstance(content, tuple):
                raise Exception("CheckBoxList constructor - Invalid configuration argument:  " + str(content))
            self.content = deepcopy(content)
        self.listener = None
        if listener is not None and callable(listener):
            self.listener = listener
        if descriptor is None:
            self.descriptor = CheckBoxList.DEFAULT_DESCRIPTOR
        elif isinstance(descriptor, dict):
            self.descriptor = deepcopy(descriptor)
        else:
            raise Exception("CheckBoxList constructor - Invalid descriptor argument:  " + str(descriptor))

        LabelFrame.__init__(self, container, keyWordArguments)
        self.vertical = True        #   Default
        if 'orientation' in self.descriptor:
            self.vertical = self.descriptor['orientation'] == VERTICAL
        if self.vertical:
            self.padx = 15
        else:
            self.padx = 0
        if 'labelLength' in self.descriptor:
            self.labelLength = self.descriptor['labelLength']
        else:
            self.labelLength = 8
        if 'helpText' in self.descriptor:
            self.helpKey = self.descriptor['helpText']
        else:
            self.helpKey = None

        self.checkVars = OrderedDict()
        self.checkBoxes = OrderedDict()
        self.helpMap    = OrderedDict()
        self.outsideChange = False
        groupIdx = 0
        rowIdx = 0
        colIdx = 0
        for checkItem in self.content:
            self.checkVars[checkItem[KeyName.TEXT]] = BooleanVar()
            self.checkBoxes[checkItem[KeyName.TEXT]] = Checkbutton(self, text=str(checkItem[KeyName.TEXT]),
                                                                    variable=self.checkVars[checkItem[KeyName.TEXT]],
                                                                   width=self.labelLength, anchor=W)
            self.checkVars[checkItem[KeyName.TEXT]].trace('w', partial(self.checkBoxClicked,
                                                                        text=str(checkItem[KeyName.TEXT])))

            self.checkBoxes[checkItem[KeyName.TEXT]].bind('<Enter>', self.mouseEnter)
            self.checkBoxes[checkItem[KeyName.TEXT]].bind('<Leave>', self.mouseLeave)

            self.checkBoxes[checkItem[KeyName.TEXT]].grid(row=groupIdx+rowIdx, column=colIdx, padx=self.padx, pady=1,
                                                          ipadx=15, sticky=N+W)
            if self.helpKey is not None:
                self.helpMap[checkItem[KeyName.TEXT]] = checkItem[self.helpKey]
                if TESTING:
                    print(self.helpMap[checkItem[KeyName.TEXT]])
            if self.vertical:
                rowIdx += 1
            else:
                colIdx += 1

        # Optional (Future) local help message box for checkbox lists that are short enough to not require scrolling:
        #   self.messageHelp  = Message(self, text="informative messages \nregarding selections",
        #                             width=self.labelLength*10, fg='darkblue', border=3, relief=SUNKEN)
        #   self.messageHelp.grid(row=rowIdx, column=0, padx=15, pady=5, sticky=E + W)

    def mouseEnter(self, event):
        if TESTING:
            print("mouseEnter:\t" + event.widget.cget('text'))
        optionText = event.widget.cget('text')
        if optionText in self.helpMap:
            if self.listener is not None:
                self.listener({'source': 'CheckBoxList.mouseEnter',
                               'optionText': event.widget.cget('text') })
                #   self.messageHelp.config(text=self.helpMap[optionText])

    def mouseLeave(self, event):
        pass

    def setModel(self, model: object):
        if isinstance(model, dict):
            for name, value in model.items():
                self.checkVars[name].set(value)

    def getState(self, modelType: ModelType):
        if modelType == ModelType.JSON:
            state = {}
            for checkItem in self.content:
                state[checkItem[KeyName.TEXT]] = self.checkVars[checkItem[KeyName.TEXT]].get()
            return state
        return None

    def checkBoxClicked(self, *args, text: str=None):
        if TESTING:
            print("checkBoxClicked:\t" + text)
        if self.outsideChange:
            return
        if self.listener is not None:
            self.listener({'source': "CheckBoxList.checkBoxClicked",
                           'text': text,
                           'newValue': self.checkVars[text].get(),
                           'callBack': self.messageReceiver})

    def messageReceiver(self, message: dict):
        if not isinstance(message, dict):
            raise Exception("CheckBoxList.messageReceiver  Invalid message argument:  " + str(message))
        if 'source' in message:
            if message['source'] == 'HardwareProbeView.messageReceiver':
                if 'issue' in message:
                    if message['issue'] == 'noInformation':
                        if 'subject' in message:
                            self.outsideChange = True
                            self.checkVars[message['subject']].set(False)
                            self.checkBoxes[message['subject']].update()
                            self.outsideChange = False

    def setCheck(self, id: str, on: bool):
        if id in self.checkVars:
            self.checkVars[id].set(on)


class ViewControlPopup(Toplevel):
    """
    Needs next:
        If the user deselects a category, its view options become DISABLED.
        If a new hw-probe is run changing the categories of information available and this Toplevel is shown,
            it should update accordingly via a message passed to its listener.
    """

    DEFAULT_DESCRIPTOR = {
        'geometry': "400x600+600+100",
        'title': " Data View Control ",
        'viewSelectors': (
            {'name': 'devices', 'infoPresent': False, 'selected': True,
             'views': {
                 'Frame':   {'present': True, 'selected': True},
                 'Notebook': {'present': True, 'selected': True},
                 'Toplevel': {'present': True, 'selected': True},
             }},
            {'name': 'host', 'infoPresent': True, 'selected': True,
             'views': {
                 'Frame':   {'present': True, 'selected': True},
                 'Notebook': {'present': True, 'selected': True},
                 'Toplevel': {'present': True, 'selected': True},
             }},
            {'name': 'logs', 'infoPresent': True, 'selected': True,
             'views': {
                 'Frame':   {'present': True, 'selected': True},
                 'Notebook': {'present': True, 'selected': True},
                 'Toplevel': {'present': True, 'selected': True},
             }},
            {'name': 'acpi-dump', 'infoPresent': True, 'selected': True,
             'views': {
                 'Frame':   {'present': True, 'selected': True},
                 'Notebook': {'present': True, 'selected': True},
                 'Toplevel': {'present': True, 'selected': True},
             }},
            {'name': 'acpi-decode', 'infoPresent': True, 'selected': True,
             'views': {
                 'Frame':   {'present': True, 'selected': True},
                 'Notebook': {'present': True, 'selected': True},
                 'Toplevel': {'present': True, 'selected': True},
             }},
            {'name': 'cpu-perf', 'infoPresent': True, 'selected': True,
             'views': {
                 'Frame':   {'present': True, 'selected': True},
                 'Notebook': {'present': True, 'selected': True},
                 'Toplevel': {'present': True, 'selected': True},
             }},
            {'name': 'glxgears', 'infoPresent': True, 'selected': True,
             'views': {
                 'Frame':   {'present': True, 'selected': True},
                 'Notebook': {'present': True, 'selected': True},
                 'Toplevel': {'present': True, 'selected': True},
             }},
            {'name': 'hdd_read', 'infoPresent': True, 'selected': True,
             'views': {
                 'Frame':   {'present': True, 'selected': True},
                 'Notebook': {'present': True, 'selected': True},
                 'Toplevel': {'present': True, 'selected': True},
             }},
            {'name': 'memtester', 'infoPresent': True, 'selected': False,
             'views': {
                 'Frame':   {'present': True, 'selected': True},
                 'Notebook': {'present': True, 'selected': True},
                 'Toplevel': {'present': True, 'selected': False},
             }},
        )
    }

    def __init__(self, container, descriptor: dict = None, listener=None, **keyWordArguments):
        if descriptor is None:
            self.descriptor = ViewControlPopup.DEFAULT_DESCRIPTOR
        elif not isinstance(descriptor, dict):
            raise Exception("ViewControlPopup constructor - Invalid descriptor argument:  " + str(descriptor))
        else:
            self.descriptor = deepcopy(descriptor)
        self.listener = None
        if listener is not None and callable(listener):
            self.listener = listener
        Toplevel.__init__(self, container, keyWordArguments)
        if 'geometry' in self.descriptor and isinstance(self.descriptor['geometry'], str):
            self.geometry(self.descriptor['geometry'])
        if 'title' in self.descriptor and isinstance(self.descriptor['title'], str):
            self.title(self.descriptor['title'])
        self.selectorVarMap = OrderedDict()
        self.selectorCheckboxMap =  OrderedDict()
        if 'viewSelectors' in self.descriptor:
            rowIdx = 0
            colIdx = 0
            for selector in self.descriptor['viewSelectors']:
                if not ('name' in selector and 'infoPresent' in selector and 'selected' in selector):
                    continue
                self.selectorCheckboxMap[selector['name']] = OrderedDict()
                self.selectorVarMap[selector['name']] = OrderedDict()
                self.selectorVarMap[selector['name']]['checkBox'] = BooleanVar()
                self.selectorCheckboxMap[selector['name']]['checkBox'] = \
                    Checkbutton(self, text=selector['name'], variable=self.selectorVarMap[selector['name']]['checkBox'],
                                      bd=1, relief=RIDGE, anchor=W, width=15, font=('arial', 11, 'bold'))

                self.selectorCheckboxMap[selector['name']]['viewSelectors'] = OrderedDict()
                self.selectorVarMap[selector['name']]['viewSelectors'] = OrderedDict()

                #   self.selectorVarMap[selector['name']]['viewSelectors']['Frame'] = BooleanVar()
                #   self.selectorCheckboxMap[selector['name']]['viewSelectors']['Frame'] = \
                #       Checkbutton(self, text='Frame', bd=1, relief=RIDGE, anchor=W, width=10,
                #                   variable=self.selectorVarMap[selector['name']]['viewSelectors']['Frame'])

                self.selectorVarMap[selector['name']]['viewSelectors']['Notebook'] = BooleanVar()
                self.selectorCheckboxMap[selector['name']]['viewSelectors']['Notebook'] = \
                    Checkbutton(self, text='Notebook', bd=1, relief=RIDGE, anchor=W, width=10,
                                variable=self.selectorVarMap[selector['name']]['viewSelectors']['Notebook'])

                self.selectorVarMap[selector['name']]['viewSelectors']['Toplevel'] = BooleanVar()
                self.selectorCheckboxMap[selector['name']]['viewSelectors']['Toplevel'] = \
                    Checkbutton(self, text='Toplevel', bd=1, relief=RIDGE, anchor=W, width=10,
                                variable=self.selectorVarMap[selector['name']]['viewSelectors']['Toplevel'])

                self.selectorCheckboxMap[selector['name']]['checkBox'].grid(row=rowIdx, column=colIdx, columnspan=3,
                                                                            padx=15, pady=5)
                #   self.selectorCheckboxMap[selector['name']]['viewSelectors']['Frame'].\
                #       grid(row=rowIdx+1, column=colIdx+1, columnspan=2, padx=15, pady=0)
                self.selectorCheckboxMap[selector['name']]['viewSelectors']['Notebook'].\
                    grid(row=rowIdx+2, column=colIdx+1, columnspan=2, padx=15, pady=0)
                self.selectorCheckboxMap[selector['name']]['viewSelectors']['Toplevel'].\
                    grid(row=rowIdx+3, column=colIdx+1, columnspan=2, padx=15, pady=0)

                self.selectorVarMap[selector['name']]['checkBox'].\
                    trace('w', partial(self.selectionClick, selector['name']))
                #   self.selectorVarMap[selector['name']]['viewSelectors']['Frame'].\
                #       trace('w', partial(self.frameBoxClick, selector['name']))
                self.selectorVarMap[selector['name']]['viewSelectors']['Notebook'].\
                    trace('w', partial(self.notebookBoxClick, selector['name']))
                self.selectorVarMap[selector['name']]['viewSelectors']['Toplevel'].\
                    trace('w', partial(self.toplevelBoxClick, selector['name']))

                rowIdx += 4
                if rowIdx % 20 == 0:
                    rowIdx = 0
                    colIdx += 3
            self.setModel(self.descriptor)



    def getState(self):
        return None

    def setModel(self, model: dict):
        """
        Set the current state of the selection controls using the model argument.
        This method uses only what is present in the model and does not check for completeness.
        It uses only those elements which are structurally consistent with this class' DEFAULT_DESCRIPTOR,
        ignoring anything else that might be present, so that adapters are not required, provided the internal
        storage structures of this application are consistent when organizing the same content.
        :param model: A JSON structure of the same form as this class' DEFAULT_DESCRIPTOR.
        :return:
        """
        if 'viewSelectors' in model and isinstance(model['viewSelectors'], tuple):
            Initializer.setInitializing(True)
            for category in model['viewSelectors']:
                self.selectorVarMap[category['name']]['checkBox'].set(category['selected'])
                #   If the information category is not present in the hw-probe output selected, then
                #       the view cannot be selected.
                #   If the information is present but the view is not, the view can be created, so a message
                #       to the main view controller's listener should be sent when the view is selected here.
                if not category['infoPresent']:
                    self.selectorCheckboxMap[category['name']]['checkBox'].config(state=DISABLED)
                    self.selectorCheckboxMap[category['name']]['viewSelectors']['Frame'].config(state=DISABLED)
                    self.selectorCheckboxMap[category['name']]['viewSelectors']['Notebook'].config(state=DISABLED)
                    self.selectorCheckboxMap[category['name']]['viewSelectors']['Toplevel'].config(state=DISABLED)
                else:
                    self.selectorVarMap[category['name']]['checkBox'].set(category['selected'])
                    self.selectorVarMap[category['name']]['viewSelectors'] \
                        ['Frame'].set(category['views']['Frame']['selected'])
                    self.selectorVarMap[category['name']]['viewSelectors'] \
                        ['Notebook'].set(category['views']['Notebook']['selected'])
                    self.selectorVarMap[category['name']]['viewSelectors'] \
                        ['Toplevel'].set(category['views']['Toplevel']['selected'])
                    if not category['selected']:
                        self.selectorCheckboxMap[category['name']]['viewSelectors']['Frame'].config(state=DISABLED)
                        self.selectorCheckboxMap[category['name']]['viewSelectors']['Notebook'].config(state=DISABLED)
                        self.selectorCheckboxMap[category['name']]['viewSelectors']['Toplevel'].config(state=DISABLED)

            Initializer.setInitializing(False)

    def selectionClick(self, name: str=None, *args):
        if TESTING:
            print("selectionClick:\t" + str(name))
        if not Initializer.isInitializing():
            if self.selectorVarMap[name]['checkBox'].get():
                self.selectorCheckboxMap[name]['viewSelectors']['Frame'].config(state=NORMAL)
                self.selectorCheckboxMap[name]['viewSelectors']['Notebook'].config(state=NORMAL)
                self.selectorCheckboxMap[name]['viewSelectors']['Toplevel'].config(state=NORMAL)
            else:
                self.selectorCheckboxMap[name]['viewSelectors']['Frame'].config(state=DISABLED)
                self.selectorCheckboxMap[name]['viewSelectors']['Notebook'].config(state=DISABLED)
                self.selectorCheckboxMap[name]['viewSelectors']['Toplevel'].config(state=DISABLED)

            if self.listener is not None:
                self.listener({'source': 'ViewControlPopup.selectionClick',
                               'name': name, 'newValue': self.selectorVarMap['name']['checkBox'].get()})

    def frameBoxClick(self, name: str=None, *args):
        if TESTING:
            print("frameBoxClick:\t" + str(name))
        if not Initializer.isInitializing() and self.listener is not None:
            self.listener({'source': 'ViewControlPopup.frameBoxClick',
                           'name': name, 'newValue': self.selectorVarMap['name']['viewSelectors']['Frame'].get()})
    def notebookBoxClick(self, name: str=None, *args):
        if TESTING:
            print("notebookBoxClick:\t" + str(name))
        if not Initializer.isInitializing() and self.listener is not None:
            self.listener({'source': 'ViewControlPopup.notebookBoxClick',
                           'name': name, 'newValue': self.selectorVarMap['name']['viewSelectors']['Notebook'].get()})

    def toplevelBoxClick(self, name: str=None, *args):
        if TESTING:
            print("toplevelBoxClick:\t" + str(name))
        if not Initializer.isInitializing() and self.listener is not None:
            self.listener({'source': 'ViewControlPopup.toplevelBoxClick',
                           'name': name, 'newValue': self.selectorVarMap['name']['viewSelectors']['Toplevel'].get()})

    def messageReceiver(self, message: dict):
        if not isinstance(message, dict):
            raise Exception("ViewControlPopup.messageReceiver - Invalid message argument:  " + str(message))


class MasterSlaveLists(LabelFrame):

    DEFAULT_MASTER_WIDTH        = 30
    DEFAULT_SLAVE_WIDTH         = 40

    def __init__(self, container, descriptor: dict, listener, **keyWordArguments):
        if not isinstance(descriptor, OrderedDict):
            raise Exception("MasterSlaveLists constructor - Invalid configuration argument:  " + str(descriptor))
        if not KeyName.VIEW in descriptor or not KeyName.INFO in descriptor:
            raise Exception("MasterSlaveLists constructor - Key missing in configuration argument:  " + str(descriptor))
        for item in descriptor[KeyName.INFO]:
            if not KeyName.NAME in item or not KeyName.TEXT in item or not KeyName.SLAVE_LIST in item:
                raise Exception(
                    "MasterSlaveLists constructor - Key missing in info list in configuration argument:  " + str(descriptor))
            for slaveItem in item[KeyName.SLAVE_LIST]:
                if not KeyName.TEXT in slaveItem:
                    raise Exception(
                        "MasterSlaveLists constructor - Text missing in slave info list in configuration argument:  " + str(descriptor))

        LabelFrame.__init__(self, container, keyWordArguments)
        self.listener = None
        if listener is not None and callable(listener):
            self.listener = listener
        self.descriptor = descriptor
        if 'masterWidth' in self.descriptor[KeyName.VIEW]:
            self.masterWidth = self.descriptor[KeyName.VIEW]['masterWidth']
        else:
            self.masterWidth = MasterSlaveLists.DEFAULT_MASTER_WIDTH
        if 'slaveWidth' in self.descriptor[KeyName.VIEW]:
            self.slaveWidth = self.descriptor[KeyName.VIEW]['slaveWidth']
        else:
            self.slaveWidth = MasterSlaveLists.DEFAULT_SLAVE_WIDTH

        Initializer.setInitializing(True)
        self.masterList = []
        self.slaveMap   = OrderedDict()
        for item in self.descriptor[KeyName.INFO]:
            self.masterList.append(item[KeyName.TEXT])
            self.slaveMap[item[KeyName.TEXT]] = []
            for slaveItem in item[KeyName.SLAVE_LIST]:
                self.slaveMap[item[KeyName.TEXT]].append(slaveItem[KeyName.TEXT])
            self.slaveMap[item[KeyName.TEXT]] = tuple(self.slaveMap[item[KeyName.TEXT]])
        self.masterList = tuple(self.masterList)

        self.listBoxMaster = Listbox(self, border=3, relief=RIDGE, selectmode=SINGLE, height=20, width=self.masterWidth)
        self.listBoxMaster.insert(END, *self.masterList)
        if len(self.masterList) == 0:
            self.listBoxMaster.insert(END, *('empty',))
        self.listBoxMaster.selection_set(0, 0)
        self.listBoxMaster.bind('<<ListboxSelect>>', self.masterListSelection)

        self.listBoxSlave = Listbox(self, border=3, relief=RIDGE, selectmode=SINGLE, height=20, width=self.slaveWidth)
        self.slaveList = self.slaveMap[self.masterList[0]]
        self.listBoxSlave.insert(END, *self.slaveList)
        self.listBoxSlave.bind('<<ListboxSelect>>', self.slaveListSelection)

        self.listBoxMaster.grid(row=0, column=0, padx=5, pady=5, sticky=N+W)
        self.listBoxSlave.grid(row=0, column=1, padx=5, pady=5, sticky=N+W)
        Initializer.setInitializing(False)

    def messageReceiver(self, message: dict):
        if TESTING:
            print("MasterSlaveLists.messageReceiver:\t" + str(message))
        if not isinstance(message, dict):
            raise Exception("MasterSlaveLists.messageReceiver  Invalid message argument:  " + str(message))
        if 'source' in message:
            pass

    def setModel(self, model: object):
        if isinstance(model, dict):
            pass

    def getState(self, modelType: ModelType):
        if modelType == ModelType.JSON:
            state = {}
            return state
        return None

    def masterListSelection(self, event):
        if event.x == 0 and event.y == 0 and event.x_root == 0 and event.y_root == 0:
            return
        if not Initializer.isInitializing():
            selection = self.listBoxMaster.selection_get()
            if TESTING:
                print("MasterSlaveLists.masterListSelection:\t" + selection)
            self.slaveList = self.slaveMap[self.masterList[self.masterList.index(selection)]]
            self.listBoxSlave.delete(0, END)
            self.listBoxSlave.insert(END, *self.slaveList)

    def slaveListSelection(self, event):
        if not Initializer.isInitializing():
            if TESTING:
                print("MasterSlaveLists.slaveListSelection:\t" + str(event))


class SimplePropertyListFrame(LabelFrame):

    def __init__(self, container, fields: OrderedDict, valueWidth: int, listener=None, **keyWordArguments):
        """
        This is a frame with two columns of labels, one for the names of the fields and one for their values.
        It can be made scrollable by placing it in a Text with it's create_window() method and attaching
        scrollbars to the Text.
        :param container:
        :param info:        Must be a list of name-value pairs, so a simple OrderedDict will work.
        :param listener:
        :param keyWordArguments:
        """
        if not isinstance(fields, OrderedDict):
            raise Exception("SimplePropertyListFrame constructor - Invalid info argument:  " + str(fields))
        self.listener = None
        if listener is not None and callable(listener):
            self.listener = listener
        LabelFrame.__init__(self, container, keyWordArguments)
        self.valueWidth = valueWidth

        self.labelNameHeading = Label(self, text=' Name ', font=('arial', 12, 'bold'))
        self.labelValueHeading = Label(self, text=' Value ', width=self.valueWidth-20, font=('arial', 12, 'bold'))
        self.labelNameHeading.grid(row=0, column=0, padx=15, pady=10)
        self.labelValueHeading.grid(row=0, column=1, padx=15, pady=10)

        self.setModel(fields)

    def messageReceiver(self, message: dict):
        if TESTING:
            print("SimplePropertyListFrame.messageReceiver:\t" + str(message))
        if not isinstance(message, dict):
            raise Exception("SimplePropertyListFrame.messageReceiver  Invalid message argument:  " + str(message))
        if 'source' in message:
            pass

    def setModel(self, fields: OrderedDict):
        if isinstance(fields, OrderedDict):
            self.nameLabels = OrderedDict()
            self.valueLabels = OrderedDict()
            rowIdx = 1
            for name, value in fields.items():
                self.nameLabels[name] = Label(self, text=name, width=15, anchor=W, border=1, relief=GROOVE, padx=5)
                self.nameLabels[name].grid(row=rowIdx, column=0, padx=15, pady=0, ipadx=5)
                self.valueLabels[name] = Label(self, text=value, anchor=W, width=self.valueWidth,
                                               border=1, relief=SUNKEN, padx=5, bg='white')
                self.valueLabels[name].grid(row=rowIdx, column=1, padx=15, pady=5, ipadx=5)
                rowIdx += 1
            self.fields = deepcopy(fields)
            return True
        return False

    def getState(self, modelType: ModelType):
        if modelType == ModelType.JSON:
            return self.fields
        return "Not Implemented Yet"


class TableSheet(Sheet):

    def __init__(self, container, data: tuple, config: dict):
        Sheet.__init__(self, container, data=data)
        self.enable_bindings()


class BackGroundProcessWindow(Toplevel):
    """
    Show a turning gears graphic  (possibly assigned by the user for this process) in a Toplevel window with
    a title identifying the feature selected by the user and in the window have a table or other arrangement
    of real-time information on the progress of the process.
    """
    pass

def messageReceiverTest(message: dict):
    if TESTING:
        print("messageReceiverTest:\t" + str(message))


def ExitProgram():
    answer = messagebox.askyesno(parent=mainView, title='Exit program ', message="Exit the " + PROGRAM_TITLE + " program?")
    if answer:
        mainView.destroy()


if __name__ == '__main__':

    mainView = Tk()
    mainView.geometry("1100x500+50+50")
    mainView.title(PROGRAM_TITLE)
    mainView.protocol('WM_DELETE_WINDOW', lambda: ExitProgram())

    descriptor = OrderedDict({
        KeyName.VIEW: { 'masterWidth': 20,
                        'slaveWidth': 30},
        KeyName.INFO:
            (
                {   KeyName.NAME: 'item 01',
                    KeyName.TEXT: 'First master list item',
                    KeyName.SLAVE_LIST:    ({KeyName.TEXT: 'Bill'}, {KeyName.TEXT: 'Jim'}, {KeyName.TEXT: 'Steve'})
                },
                {   KeyName.NAME: 'item 02',
                    KeyName.TEXT: 'Second master list item',
                    KeyName.SLAVE_LIST:    ({KeyName.TEXT: 'Kate'}, {KeyName.TEXT: 'Patricia'}, {KeyName.TEXT: 'Cindy'})
                },
                {   KeyName.NAME: 'item 03',
                    KeyName.TEXT: 'Third master list item',
                    KeyName.SLAVE_LIST:     ({KeyName.TEXT: 'Carlos'}, {KeyName.TEXT: 'Jose'}, {KeyName.TEXT: 'Jorge'})
                 },
                {   KeyName.NAME: 'item 04',
                     KeyName.TEXT: 'Fourth master list item',
                     KeyName.SLAVE_LIST: tuple([{KeyName.TEXT: " "+str(n)+" "} for n in range(420,460)])
                 },
                {   KeyName.NAME: 'item 05',
                     KeyName.TEXT: 'Fifth master list item',
                     KeyName.SLAVE_LIST: tuple([{KeyName.TEXT: " "+str(n)+" "} for n in range(536,558)])
                 },
                {   KeyName.NAME: 'item 06',
                     KeyName.TEXT: 'Sixth master list item',
                     KeyName.SLAVE_LIST: tuple([{KeyName.TEXT: " "+str(n)+" "} for n in range(680,725)])
                 },
            )
    })
    masterSlaveLists = MasterSlaveLists(mainView, descriptor, listener=messageReceiverTest,
                                        text="Master Slave List Demo", border=4, relief=RAISED)
    masterSlaveLists.grid(row=0, column=0, sticky=N+S+E+W)

    tableFrame = LabelFrame(mainView, text="TkSheet Demo", width=600, border=3, relief=GROOVE)
    tableFrame.grid_propagate(False)
    tableFrame.grid_columnconfigure(0, weight=1)
    tableFrame.grid_rowconfigure(0, weight=1)

    data = tuple([tuple([f"Row {r}, Column {c}\nnewline1\nnewline2" for c in range(50)]) for r in range(500)])
    config = {
    }
    tableSheet = TableSheet(tableFrame, data=data, config=config)
    tableSheet.grid(row=0, column=0, sticky=N+S+E+W)
    tableFrame.grid(row=0, column=1, sticky=N+S+E+W)

    #   hardwareProbeView.pack(expand=True, fill=BOTH)
    viewControlPopup = ViewControlPopup(mainView)
    viewControlPopup.mainloop()

    mainView.mainloop()
