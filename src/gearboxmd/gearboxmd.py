"""
Purpose:        GUI for Linux's hw-probe.
Author:         George Keith Watson, (c) 2022.
DBA:            modelSoftTech
Date Initiated: September 6, 2022
Spawn Source:   fileHero Python Project by same author.

"""
#   Project:        GearboxMD
#   Author:         George Keith Watson
#   Date Started:   September 05, 2020
#   Copyright:      (c) Copyright 2022 George Keith Watson
#   Module:         gearboxmd.py
#   Date Started:   September 6, 2022
#   Purpose:
#   Development:
#

from tkinter import Tk, messagebox, N, S, E, W

from view.Hardware import HardwareProbeViewController, ViewMode

PROGRAM_TITLE   = 'GearboxMD'
TESTING = True
DEBUG = False
INSTALLING = False

def messageReceiver(message: dict):
    if TESTING:
        print("main.messageReceiver:\t" + str(message))

def ExitProgram():
    answer = messagebox.askyesno(parent=mainView, title='Exit program ', message="Exit the " + PROGRAM_TITLE + " program?")
    if answer:
        mainView.destroy()


if __name__ == '__main__':
    mainView = Tk()
    mainView.geometry("1000x600+50+50")
    mainView.title(PROGRAM_TITLE)
    mainView.protocol('WM_DELETE_WINDOW', lambda: ExitProgram())

    hardwareProbeController = HardwareProbeViewController(mainView, options={'viewMode': ViewMode.NOTEBOOK})
    hardwareProbeController.grid(row=0, column=0, sticky=N+S+E+W)

    #   hardwareProbeView.pack(expand=True, fill=BOTH)
    mainView.mainloop()
