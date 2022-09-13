#   Project:        GearboxMD
#   Author:         George Keith Watson
#   Date Started:   September 05, 2020
#   Copyright:      (c) Copyright 2022 George Keith Watson
#   Module:         model/PsUtil.py
#   Date Started:   September 7, 2022
#   Purpose:        Interface to the psutil package capabilities.
#   Development:
#       2022-09-97:
#           Appropriate polling schedules should be available for information that can change and change in which
#           is relevant to system performance evaluation or for issue diagnostics.
#

from collections import OrderedDict
from enum import Enum

from tkinter import Tk, messagebox, OptionMenu, Label, LabelFrame, Listbox, \
                    SINGLE, MULTIPLE, EXTENDED, END, \
                    FLAT, RIDGE, GROOVE, SUNKEN, RAISED, \
                    N, S, E, W, X, Y, BOTH

import psutil
from psutil import pids, pid_exists, process_iter, disk_usage, disk_partitions, disk_io_counters, \
    virtual_memory, swap_memory, cpu_stats, net_if_stats, net_if_addrs, getloadavg, wait_procs, sensors_fans, \
    sensors_battery, sensors_temperatures, boot_time, cpu_times, cpu_percent, cpu_count, cpu_freq, cpu_times_percent, \
    net_connections, net_io_counters, users, version_info
import platform
from os import environ
from datetime import datetime

"""
Not importable from psutil:
    pmem, pfullmem, win_service_get
"""
PROGRAM_TITLE = "psutil Interface"
INSTALLING  = False
TESTING     = True
DEBUG       = False

PSUTIL_SERVICES = ()

def ExitProgram():
    answer = messagebox.askyesno(parent=mainView, title='Exit program ', message="Exit the " + PROGRAM_TITLE + " program?")
    if answer:
        mainView.destroy()


if __name__ == '__main__':
    print("PsUtil.py Runnnig\n")
    print("pids:\t" + str(pids))
    print("\tpids():\t" + str(pids()))

    print("\ndisk_usage:\t" + str(disk_usage))
    print("\tdisk_usage('/'):\t" + str(disk_usage('/')))
    #   Next do ls on / and find disk usage for all directories of the root dir in a pie chart.
    #   Could let user pick one from a folder tree to show its information, adding it to a vertical bar chart.
    #   Will need to do a file system walk in a background thread since for th entire disk this can take quite
    #   a bit of time.

    print("\ndisk_partitions:\t" + str(disk_partitions))
    print("\tdisk_partitions:\t" + str(disk_partitions()))

    print("\ndisk_io_counters:\t" + str(disk_io_counters))
    print("\tdisk_io_counters():\t" + str(disk_io_counters()))

    print("\nvirtual_memory:\t" + str(virtual_memory))
    print("\tvirtual_memory():\t" + str(virtual_memory()))

    print("\nswap_memory:\t" + str(swap_memory))
    print("\tswap_memory():\t" + str(swap_memory()))

    print("\ncpu_stats:\t" + str(cpu_stats))
    print("\tcpu_stats():\t" + str(cpu_stats()))

    print("\nnet_if_stats:\t" + str(net_if_stats))
    print("\tnet_if_stats():\t" + str(net_if_stats()))

    print("\nnet_if_addrs:\t" + str(net_if_addrs))
    print("\tnet_if_addrs():\t" + str(net_if_addrs()))

    print("\ngetloadavg:\t" + str(getloadavg))
    print("\tgetloadavg():\t" + str(getloadavg()))

    #   print("\nwait_procs:\t" + str(wait_procs))
    #   print("\twait_procs(procs):\t" + str(wait_procs(pids())))

    print("\nsensors_fans:\t" + str(sensors_fans))
    print("\tsensors_fans():\t" + str(sensors_fans()))

    print("\nsensors_battery:\t" + str(sensors_battery))
    print("\tsensors_battery():\t" + str(sensors_battery()))

    print("\nsensors_temperatures:\t" + str(sensors_temperatures))
    print("\tsensors_temperatures():\t" + str(sensors_temperatures()))

    print("\nboot_time:\t" + str(boot_time))
    print("\tboot_time():\t" + str(boot_time()))

    print("\ncpu_times:\t" + str(cpu_times))
    print("\tcpu_times():\t" + str(cpu_times()))

    print("\ncpu_percent:\t" + str(cpu_percent))
    print("\tcpu_percent():\t" + str(cpu_percent()))

    print("\ncpu_count:\t" + str(cpu_count))
    print("\tcpu_count():\t" + str(cpu_count()))

    print("\ncpu_freq:\t" + str(cpu_freq))
    print("\tcpu_freq():\t" + str(cpu_freq()))

    print("\ncpu_times_percent:\t" + str(cpu_times_percent))
    print("\tcpu_times_percent():\t" + str(cpu_times_percent()))

    print("\nnet_connections:\t" + str(net_connections))
    print("\tnet_connections():\t" + str(net_connections()))

    print("\nnet_io_counters:\t" + str(net_io_counters))
    print("\tnet_io_counters():\t" + str(net_io_counters()))

    print("\nusers:\t" + str(users))
    print("\tusers():\t" + str(users()))

    print("\nversion_info:\t" + str(version_info))

    exit(0)
    mainView = Tk()
    mainView.geometry("800x600+150+50")
    mainView.title(PROGRAM_TITLE)
    mainView.protocol('WM_DELETE_WINDOW', lambda: ExitProgram())

    mainView.mainloop()

