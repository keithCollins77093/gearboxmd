#   Project:        GearboxMD
#   Author:         George Keith Watson
#   Date Started:   September 05, 2020
#   Copyright:      (c) Copyright 2022 George Keith Watson
#   Module:         view/ViewManager.py
#   Date Started:   September 7, 2022
#   Purpose:        Record construction, layout and content attributes of all instantiated Frames, including
#                   floating ones like TopLevel, to coordinate show / hide behavior and movement of a Frame
#                   from one container / context to another.
#   Development:
#

from collections import OrderedDict
from enum import Enum
from copy import deepcopy

from tkinter import Tk, messagebox, OptionMenu, Label, LabelFrame, Frame, Listbox, Button, Message, \
                    SINGLE, MULTIPLE, EXTENDED, END, NORMAL, DISABLED, \
                    FLAT, RIDGE, GROOVE, SUNKEN, RAISED, \
                    N, S, E, W, X, Y, BOTH, RIGHT, LEFT, TOP, BOTTOM
from tkinter.ttk import Notebook, Treeview

from view.Hardware import HardwareProbeView

PROGRAM_TITLE = "View Manager"
INSTALLING  = False
TESTING     = True
DEBUG       = False


class LayoutMethod(Enum):
    GRID    = 'grid'
    PACK    = 'pack'
    PLACE   = 'place'

    def __str__(self):
        return self.value


class Attributes:

    def __init__(self, attributes: dict):
        """
        Key in map must be string type.
        :param attributes:
        """
        if not isinstance(attributes, dict):
            raise Exception("Attributes constructor - Invalid attributes argument:  " + str(attributes))
        for attrName in attributes:
            if not isinstance(attrName, str):
                raise Exception("Attributes constructor - Invalid attribute name:  " + str(attrName))
        self.attr = OrderedDict(attributes)

    def hasAttr(self, attrName: str):
        return attrName in self.attr

    def getValue(self, attrName: str):
        if isinstance(attrName, str) and attrName in self.attr:
            return self.attr[attrName]


class ViewAttributes(Attributes):
    """
    All of the arguments needed to construte the view other than its content, i.e. the data to be displayed.
    """
    def __init__(self, attributes: dict, **keyWordArguments):
        """
        Contains both constructor arguments and view keyWordArguments.
        :param attributes: The constructor's arguments which are not the view's key word arguments / attributes.
        """
        Attributes.__init__(self, attributes)
        self.keyWordArguments = keyWordArguments


class LayoutAttributes(Attributes):
    """
    Just the attributes needed to call grid() or pack() on the Frame placing it into a particular context.
    """
    def __init__(self, method: LayoutMethod, attributes: dict):

        # ARGUMENT CHECK, THEN:
        Attributes.__init__(self, attributes)
        self.method = method

    def getMethod(self):
        return self.method

    def getArgList(self):
        return self.attr


class ContentAttributes(Attributes):
    """
    The data to be displayed in a Frame in a form the constructor or setModel() method of the Frame understands.
    """
    pass


class ViewCatalog:

    #   This will be keyed on the reference to the Frame and contain a map to view, layout, and content
    #   attributes maps / objects
    frames = OrderedDict()

    @staticmethod
    def addView( widgetRef, containerRef, viewAttributes: ViewAttributes,
                 layoutAttributes: LayoutAttributes,
                 contentAttributes: ContentAttributes):

        # ARGUMENT CHECK, THEN:

        #   if not isinstance(widgetReference, widget):
        if not isinstance(viewAttributes, ViewAttributes):
            raise Exception("ViewCatalog.addView - Invalid viewAttributes argument:  " + str(viewAttributes))
        if not isinstance(layoutAttributes, LayoutAttributes):
            raise Exception("ViewCatalog.addView - Invalid layoutAttributes argument:  " + str(layoutAttributes))
        if not isinstance(contentAttributes, ContentAttributes):
            raise Exception("ViewCatalog.addView - Invalid contentAttributes argument:  " + str(contentAttributes))

        ViewCatalog.frames[widgetRef] = {
            'viewAttributes': viewAttributes,
            'layoutAttributes': layoutAttributes,
            'contentAttributes': contentAttributes
        }

    @staticmethod
    def checkIntegrity():
        pass

    @staticmethod
    def toNewContainer(frameRef, containerRef, layoutAttributes: LayoutAttributes):
        """
        Move the Frame referenced by frameRef if it is registered here into the Frame referenced by containerRef
        using provided LayoutAttributes.
        :param frameRef:
        :param containerRef:    must be a Frame, including LabelFrame
        :return:
        """

        # ARGUMENT CHECK, THEN:

        pass

    @staticmethod
    def toToplevel(frameRef):
        """
        Move a Frame into a new or existing Toplevel, i.e. a floating pop-up window of its own.
        :param widgetRef:
        :return:
        """

        # ARGUMENT CHECK, THEN:

        if not frameRef in ViewCatalog.frames:
            return False
        else:
            widget = ViewCatalog[frameRef]
            if widget['viewAttributes'].hasAttr('container'):
                containerRef = widget['viewAttributes']['container']
                #   Problem:    All constructor parameters, along with keyWordAerguments, must be passed in
                #               to the class constructor in the right order.
                #widgetRef.class(containerRef, )

        return False

    @staticmethod
    def hide(frameRef):
        if not frameRef in ViewCatalog.frames:
            return False
        if ViewCatalog.frames[frameRef]['layoutAttributes'].getMethod() == LayoutMethod.GRID:
            frameRef.grid_fotget()
            return True
        elif ViewCatalog.frames[frameRef]['layoutAttributes'].getMethod() == LayoutMethod.PACK:
            frameRef.pack_fotget()
            return True
        return False

    @staticmethod
    def show(frameRef):
        if not frameRef in ViewCatalog.frames:
            return False
        layoutAttr = ViewCatalog.frames[frameRef]['layoutAttributes']
        if layoutAttr.getMethod() == LayoutMethod.GRID:
            frameRef.grid(**layoutAttr.getArgList)
            return True
        elif layoutAttr.getMethod() == LayoutMethod.PACK:
            frameRef.pack(**layoutAttr.getArgList)
            return True
        return False

    @staticmethod
    def changeLayoutArgs(frameRef, newLayoutAttributes: LayoutAttributes):

        # ARGUMENT CHECK, THEN:

        if not frameRef in ViewCatalog.frames:
            return False
        return False

    @staticmethod
    def moveToContainer(frameRef, oldContainer, newContainer):

        # ARGUMENT CHECK, THEN:

        if not frameRef in ViewCatalog.frames:
            return False
        return False


class NotebookFrame(LabelFrame):
    """
    TEST CASE FOR ViewManager CLASS FEATURES:
        1.  Move a frame in a notebook or other container to a different container, i.e. another page in the
                Notebook.
        2.  Move and entore Notebook pare to a toplevel or from a Toplevel to an inserted Notebook page.
        3.  Move any control or frame in any container, whether it is a Notebook pare or a frame to a
                Toplevel or back.
        Focus can be used to specify the element to be moved or a short description of each can be stored so that
        they can be listed for each window / page / frame to or from which an element can be moved.
        Process:
            a.  User selects page or frame by displaying it amd clicks the checkbox for the layout change bar.
            b.  A layout change bar specialized for that window, page or frame type displays in Toplevel.
            c.  User selects from a drop-down list the particular element they want moved.
                    This needs to be a list in which a mouse enter event and mouse leave event can be
                    bound so that the color or other feature of the subject element can be changed to indicate it
                    will be the subject of the move.
            d.  User then selects the destination window, page, or frame from another list of short descriptions.
                    if the container is present in the view it should be highlighted when the user passes the mouse
                    over its description.
            e.  User then selects the placement of the frame within the container.
                    If the layout manager for the container is grid, only selections available in a
                    a grid layout will be offered.  Likewise for pack.
            f.  Optional feature:   User can make the new placement a synchronezed copy of the original.
                Default behavior is to then move the frame or other element to the new location.
    """

    DEFAULT_DESCRIPTOR   = {
        'pages':    (
            {   'title': "First Page",
                'identifier': None,
                'style': None,
                'components':   (
                    {   'info': {
                            'type': 'list',
                            'data': ('one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten')
                        }
                    },
                    {   'frame': {
                            'type': 'fill',
                            'config':   {
                                'border': 3,
                                'relief': SUNKEN
                            }
                        }
                    }
                )
            },
            {   'title': "Second Page",
                'identifier': None,
                'style': None,
                'components':   (
                    {   'control': {
                            'type': 'buttonBar',
                            'items': (
                                {'text': 'Tool One',
                                 'command': None,
                                 },
                                {'text': 'Tool Two',
                                 'command': None,
                                 },
                                {'text': 'Tool Three',
                                 'command': None,
                                 }
                            )
                            }
                    },
               )
            },
            {   'title': "Third Page",
                'identifier': None,
                'style': None,
                'components':   (
                    {   'info': {
                            'type': 'tree',
                            'data': None
                        }
                    },
                )
            },
            {   'title': "Fourth Page",
                'identifier': None,
                'style': None,
                'components':   (
                    {   'info': {
                            'type': 'message',
                            'config': {
                                'width': 600,
                                'border': 3,
                                'relief': SUNKEN,
                                'text': "Four score and seven years ago our forefathers brought forth onto this continent "
                                        "a new nation, conceived in liberty and dedicated to the proposition that all men "
                                        "are created equal. ... that these dead shall not have dies in vain==that this nation, "
                                        "under God, shall have a new birth of freedom--and that government of the people, by "
                                        "the people, for the people, shall not perish from the earth."
                            }
                        }
                    },
                )
            }
        )
    }

    def __init__(self, container, descriptor: dict, **keyWordArguments):
        self.descriptor = None
        if descriptor is None:
            self.descriptor = NotebookFrame.DEFAULT_DESCRIPTOR
        else:
            if isinstance(descriptor, dict):
                self.descriptor = deepcopy(descriptor)
            else:
                raise Exception("NotebookFrame constructor - Invalid descriptor argument:  " + str(descriptor))
        LabelFrame.__init__(self, container, keyWordArguments)
        self.notebook = Notebook(self)
        if 'pages' in self.descriptor and isinstance(self.descriptor['pages'], tuple):
            for page in self.descriptor['pages']:
                if isinstance(page, dict) and 'title' in page:
                    innerFrame = Frame(self.notebook)
                    if 'components' in page and isinstance(page['components'], tuple):
                        colIdx = 0
                        for component in page['components']:
                            if 'info' in component and isinstance(component['info'], dict):
                                if 'type' in component['info']:
                                    if component['info']['type'] == 'list' and isinstance(component['info']['data'], tuple):
                                        listBox = Listbox(innerFrame)
                                        #   listBox = Listbox(innerFrame, height=20)
                                        listBox.insert(END, *component['info']['data'])
                                        listBox.grid(row=0, column=colIdx, padx=15, pady=5)
                                        colIdx += 1
                                    elif component['info']['type'] == 'tree':
                                        treeView = Treeview(innerFrame, padding=(2, 2), selectmode=EXTENDED)
                                        rowIds = {}
                                        rowIds['1.0'] = treeView.insert('', 0, text='Item 01')
                                        rowIds['2.0'] = treeView.insert('', 'end', text='Item 02')
                                        rowIds['3.0'] = treeView.insert('', 'end', text='Item 03')
                                        rowIds['3.1'] = treeView.insert(rowIds['3.0'], 0, text='Sub-Item 3.1')
                                        rowIds['3.2'] = treeView.insert(rowIds['3.0'], 1, text='Item 3.2')

                                        #   treeView.bind('<<TreeviewSelect>>', self.itemSelected)
                                        treeView.grid(row=0, column=colIdx, sticky='nsew', padx=5, pady=5)
                                        colIdx += 1
                                    elif component['info']['type'] == 'message':
                                        message = Message(innerFrame, **component['info']['config'])
                                        message.grid(row=0, column=colIdx, sticky='nsew', padx=5, pady=5)
                                        colIdx += 1
                            if 'control' in component and isinstance(component['control'], dict):
                                if 'type' in component['control']:
                                    if component['control']['type'] == 'buttonBar':
                                        if 'items' in component['control'] and isinstance(component['control']['items'], tuple):
                                            buttonBarFrame = Frame(innerFrame, border=3, relief=RAISED)
                                            for item in component['control']['items']:
                                                button = Button(buttonBarFrame, text=item['text'], border=1, relief=RAISED)
                                                if 'command' in item and item['command'] is not None and callable(item['command']):
                                                    button.config(command=item['command'])
                                                button.pack(side=LEFT)
                                            buttonBarFrame.grid(row=0, column=colIdx, padx=15, pady=5)
                                            colIdx += 1
                            if 'frame' in component and isinstance(component['frame'], dict):
                                frame = Frame(innerFrame)
                                if 'config' in component['frame'] and isinstance(component['frame']['config'], dict):
                                    frame.config(**component['frame']['config'])
                                fillType = False
                                if 'type' in component['frame']:
                                    if component['frame']['type'] == 'fill':
                                        fillType = True
                                if fillType:
                                    fillLabel = Label(frame, width=40, height=20)
                                    frame.grid(row=0, column=colIdx, padx=15, pady=5, sticky=N+S+E+W)
                                    fillLabel.pack()
                                else:
                                    frame.grid(row=0, column=colIdx, padx=15, pady=5, sticky=N+S+E+W)
                                frame.grid_propagate(False)
                                colIdx += 1

                    self.notebook.add(innerFrame, state=NORMAL, sticky=N+S+E+W, padding=(10, 10, 10, 10), text=page['title'] )

        self.notebook.pack(expand=True, fill=BOTH)


def ExitProgram():
    answer = messagebox.askyesno(parent=mainView, title='Exit program ', message="Exit the " + PROGRAM_TITLE + " program?")
    if answer:
        mainView.destroy()


if __name__ == '__main__':

    mainView = Tk()
    mainView.geometry("800x600+150+50")
    mainView.title(PROGRAM_TITLE)
    mainView.protocol('WM_DELETE_WINDOW', lambda: ExitProgram())

    """
    HWP_ClassRef = HardwareProbeView
    methodArgs = (mainView, )
    hardwareProbeView = HWP_ClassRef(*methodArgs)
    layoutAttrs = {
        'row': 0,
        'column': 0,
        'sticky': N + S + E + W
    }
    hardwareProbeView.grid(**layoutAttrs)
    ViewCatalog.addView(hardwareProbeView, mainView, ViewAttributes({'container': mainView}),
                        LayoutAttributes({'type': 'grid', 'row': 0, 'column': 0, 'sticky': N + S + E + W}),
                        ContentAttributes({}))
    """

    notebookFrame = NotebookFrame( mainView, None, border=4, relief=RAISED)
    notebookFrame.pack(expand=True, fill=BOTH)

    mainView.mainloop()

