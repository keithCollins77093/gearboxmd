#   Project:        GearboxMD
#   Author:         George Keith Watson
#   Date Started:   September 05, 2020
#   Copyright:      (c) Copyright 2022 George Keith Watson
#   Module:         model/Hardware.py
#   Date Started:   September 5, 2022
#   Purpose:        Interface to the Linus device database, including use of hw-probe.
#   Development:
#       2022-09-09:
#           acpidump_decoded is the name of a log file produced and stored in the logs folder of hw.info.txz.
#           It will require its own specialized display design, and for now is stored and displayed
#               with the rest of the logs.
#

from os import walk, listdir, environ, mkdir
from subprocess import Popen, STDOUT, PIPE
from os.path import isfile, exists, split, isdir
from sys import stderr
from copy import deepcopy
from collections import OrderedDict
from enum import Enum
from json import loads
import re
from collections import OrderedDict
from threading import Thread
import logging
import gzip, tarfile

import pyudev

#   The current version of watchdog requires Python 3.6 or better.
#   For the external flash hardware diagnosis tool, the remastered Linus OS must have this installed.
#   Generally, the particular version of Python in the latest release of a distro is not guaranteed
#   to even be more recent than Python 2.n.

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from tkinter import Tk, messagebox

from service.Linux import LinuxUtilities
from model.Paths import COMMAND_OUTPUT_FOLDER, HW_PROBE_FOLDER, HW_PROBE_TXZ


PROGRAM_TITLE = "Hardware Inventory"
INSTALLING  = False
TESTING     = True
DEBUG       = False


class ContentID:
    DEVICES         = 'Devices'
    HOST            = 'Host'
    LOGS            = 'Logs'
    TESTS           = 'Tests'
    ACPI_DUMP       = "ACPI Dump"
    ACPI_DECODED    = "ACPI Decoded"

    def __str__(self):
        return self.value


class KeyName(Enum):
    VIEW        = 'view'
    INFO        = 'info'
    HELP        = 'help'
    NAME        = 'name'
    TEXT        = 'text'
    SLAVE_LIST  = 'slaveList'

    def __str__(self):
        return self.value


class HwProbeOption(Enum):
    ALL             = { KeyName.TEXT: '-all',
                        KeyName.HELP: "Enable all probes"}
    PROBE           = {KeyName.TEXT: '-probe',
                       KeyName.HELP: "Probe for hardware and collect only hardware related logs"}
    LOGS            = {KeyName.TEXT: '-logs',
                       KeyName.HELP: "Collect system logs"}
    LEVEL_MIN       = {KeyName.TEXT: '-minimal',
                       KeyName.HELP: "Collect minimal number of logs"}
    LEVEL_MAX       = {KeyName.TEXT: '-maximal',
                       KeyName.HELP: "Collect maximal number of logs"}
    ACPI_TABLE      = {KeyName.TEXT: '-dump-acpi',
                       KeyName.HELP: "Probe for ACPI table"}
    CHECK           = {KeyName.TEXT: '-check',
                       KeyName.HELP: "Check devices' operability"}
    LIST            = {KeyName.TEXT: '-list',
                       KeyName.HELP: "List executed probes (for debugging)"}
    DUMP_ACPI       = {KeyName.TEXT: '-dump-acpi',
                       KeyName.HELP: "Probe for ACPI table"}
    DECODE_ACPI     = {KeyName.TEXT: '-decode-acpi',
                       KeyName.HELP: "Decode ACPI table"}
    SHOW_DEVICES    = {KeyName.TEXT: '-show-devices',
                       KeyName.HELP: "Show devices list"}
    SHOW            = {KeyName.TEXT: '-show',
                       KeyName.HELP: "Show host info and devices list"}
    SHOW_HOST       = {KeyName.TEXT: '-show-host',
                       KeyName.HELP: "Show host info only"}
    VERBOSE         = {KeyName.TEXT: '-verbose',
                       KeyName.HELP: "Use with -show option to show type and status of the device"}
    SAVE_TO_DIR     = {KeyName.TEXT: '-save',
                       KeyName.HELP: "Save probe package to DIR, specified as an absolute path string"}
    MONITOR_START   = {KeyName.TEXT: '-start',
                       KeyName.HELP: "Start monitoring of the node"}
    MONITOR_STOP    = {KeyName.TEXT: '-stop',
                       KeyName.HELP: "Stop monitoring of the node"}
    MONITOR_REMIND  = {KeyName.TEXT: '-remind-inventory',
                       KeyName.HELP: "Remind node inventory ID"}

    def __str__(self):
        return str(self.value)

    @staticmethod
    def list():
        optionList = []
        for element in HwProbeOption:
            optionList.append(element.value)
        return tuple(optionList)


class DeviceType(Enum):
    USB             = "USB"
    CD_DVD          = "CD / DVD"
    HDD             = "Internal HD"
    PARTITION       = "Partition"
    SD_MSD          = "SD / Micro SD"

    def __str__(self):
        return self.value


class SubSystem(Enum):
    BLOCK           = 'block'

    def __str__(self):
        return self.value


class DevType(Enum):
    PARTITION       = 'part'

    def __str__(self):
        return self.value


class HardwareProbe:
    """
    Uses launch of Linux process to run hw_probe and collect information, including logs, for analysis.
    """

    DEFAULT_COMMAND     = 'sudo hw-probe -all -probe -save ' + COMMAND_OUTPUT_FOLDER
    DEFAULT_COMMAND_LIST = ('sudo', 'hw-probe', '-all', '-probe', '-save', COMMAND_OUTPUT_FOLDER)
    DEFAULT_OPTIONS     = (HwProbeOption.ALL.value[KeyName.TEXT],
                           HwProbeOption.PROBE.value[KeyName.TEXT],
                           HwProbeOption.SAVE_TO_DIR.value[KeyName.TEXT],
                           COMMAND_OUTPUT_FOLDER)

    OPERABILITY_CHECK_CMD   = 'sudo hw-probe -all -probe -check -save ' + COMMAND_OUTPUT_FOLDER
    OPERABILITY_COMMAND_LIST    = ('sudo', 'hw-probe',  '-all',  '-probe',  '-check',  '-save', COMMAND_OUTPUT_FOLDER)
    OPERABILITY_CHECK_OPTIONS = (HwProbeOption.ALL.value[KeyName.TEXT],
                                 HwProbeOption.PROBE.value[KeyName.TEXT],
                                 HwProbeOption.CHECK.value[KeyName.TEXT],
                                 HwProbeOption.SAVE_TO_DIR.value[KeyName.TEXT],
                                 COMMAND_OUTPUT_FOLDER)

    ACPI_CHECK_CMD  = 'sudo hw-probe -all -probe -dump-acpi -decode-acpi -save ' + COMMAND_OUTPUT_FOLDER
    ACPI_COMMAND_LIST   = ('sudo', 'hw-probe', '-all', '-probe', '-dump-acpi', '-decode-acpi', '-save',
                              COMMAND_OUTPUT_FOLDER)
    ACPI_CHECK_OPTIONS = (HwProbeOption.ALL.value[KeyName.TEXT],
                          HwProbeOption.PROBE.value[KeyName.TEXT],
                          HwProbeOption.DUMP_ACPI.value[KeyName.TEXT],
                          HwProbeOption.DECODE_ACPI.value[KeyName.TEXT],
                          HwProbeOption.SAVE_TO_DIR.value[KeyName.TEXT],
                          COMMAND_OUTPUT_FOLDER)

    ALL_INFO_SOURCES_CMD  = 'sudo hw-probe -all -probe -dump-acpi -decode-acpi -check -save ' + COMMAND_OUTPUT_FOLDER
    ALL_INFO_SOURCES_LIST   = ('sudo', 'hw-probe', '-all', '-probe', '-dump-acpi', '-decode-acpi', '-check', '-save',
                               COMMAND_OUTPUT_FOLDER)
    ALL_INFO_SOURCES_OPTIONS = (HwProbeOption.ALL.value[KeyName.TEXT],
                                HwProbeOption.PROBE.value[KeyName.TEXT],
                                HwProbeOption.DUMP_ACPI.value[KeyName.TEXT],
                                HwProbeOption.DECODE_ACPI.value[KeyName.TEXT],
                                HwProbeOption.CHECK.value[KeyName.TEXT],
                                HwProbeOption.SAVE_TO_DIR.value[KeyName.TEXT],
                                COMMAND_OUTPUT_FOLDER)

    class FileSystemChangeHandler(FileSystemEventHandler):

        def __init__(self, outputObserver, callback):
            FileSystemEventHandler.__init__(self)
            self.callback = callback
            self.outputObserver = outputObserver

        def on_created(self, event):
            if TESTING:
                #   <FileCreatedEvent:  event_type  = created,
                #                       src_path    = '/home/keithcollins/PycharmProjects/fileHero/data/commandOutput/hw.info.2022-09-05.txz',
                #                       is_directory= False>
                for key, value in event.__dict__.items():
                    print("\t" + key + ":\t" + value)
            self.outputObserver.stop()
            if self.callback is not None and callable(self.callback):
                if '_src_path' in event.__dict__:
                    self.callback({'source': "FileSystemChangeHandler.on_created", 'type': 'created', 'path': event._src_path})
                else:
                    self.callback({'source': "FileSystemChangeHandler.on_created", 'type': 'created', 'path': "UNRECOGNIZED"})
            else:
                raise Exception("FileSystemChangeHandler.on_created - callback argument is not callable")


        def on_modified(self, event):
            self.outputObserver.stop()

        def on_moved(self, event):
            self.outputObserver.stop()

        def on_deleted(self, event):
            self.outputObserver.stop()

    def __init__(self, hwProbeArgs: tuple=None, **keyWordArguments):
        """
        Run hw-probe as subprocess with arguments specified by hwProbeArgs and pprocess results according to
        arguments in keyWordArguments.
        :param hwProbeParms:        Only certain options of the Linux hw-probe command are useful to local analysis
                                    of hardware availability, capability, and issues, so only particular ones are
                                    allowed.
        :param keyWordArguments:
        """
        self.hwProbeArgs = None
        if hwProbeArgs is None:
            #   self.hwProbeArgs = HardwareProbe.DEFAULT_OPTIONS
            #   self.hwProbeArgs = HardwareProbe.OPERABILITY_CHECK_OPTIONS
            #   self.hwProbeArgs = HardwareProbe.ACPI_CHECK_OPTIONS
            self.hwProbeArgs = HardwareProbe.ALL_INFO_SOURCES_OPTIONS
        else:
            if not isinstance(hwProbeArgs, tuple):
                raise Exception("HardwareProbe constructor - Invalid hwProbeArgs argument:  " + str(hwProbeArgs))
            self.validOptions = HardwareProbe.DEFAULT_OPTIONS
            for argument in hwProbeArgs:
                if not argument in self.validOptions:
                    raise Exception("HardwareProbe constructor - Invalid option in hwProbeArgs argument:  " + str(argument))
            self.hwProbeArgs = hwProbeArgs
        self.hardwareMap    = OrderedDict()
        self.hardwareMap['summary']     = 'Nothing Yet'

    def launchProbe(self):
        #   Set up file system monitor to listen for changes in: COMMAND_OUTPUT_FOLDER))
        #   It will call self.messageReceiver() when it detects a change.
        if not isdir(COMMAND_OUTPUT_FOLDER):
            mkdir(COMMAND_OUTPUT_FOLDER)
        self.outputObserver = Observer()
        eventHandler = HardwareProbe.FileSystemChangeHandler(self.outputObserver, self.messageReceiver)
        self.outputObserver.schedule(event_handler=eventHandler,
                                       path=COMMAND_OUTPUT_FOLDER,
                                       recursive=False)
        self.outputObserver.start()
        #   self.outputObserver.join()
        self.probeThread = Thread(target=self.runProbe, args=(self.hwProbeArgs,))
        self.probeThread.start()
        self.probeThread.join()

    def runProbe(self, hwProbeArgs):
        #   Run command in terminal to get password to run in sudo mode,
        #   then read in resulting 'hw.info.2022-09-05.txz' file to:
        #       unzip, traverse, and parse for content.
        #   Default command:    gnome-terminal -- sudo python3 -q
        commandList = tuple(['gnome-terminal', "--geometry=120x25+200+100", "--"] +
                            ['sudo', 'hw-probe'] + list(hwProbeArgs))

        process = Popen(commandList, stdout=PIPE, stderr=STDOUT)
        process.wait()
        output, errorMessge = process.communicate()
        outputLines = output.decode('utf-8').split('\n')
        if DEBUG:
            print("\nResponse to:\t" + HardwareProbe.DEFAULT_COMMAND)
            for line in outputLines:
                print('\t' + line)


    def loadLatest(self):
        hwProbeFilePath     = HW_PROBE_TXZ
        try:
            if not tarfile.is_tarfile(hwProbeFilePath):
                messagebox.showwarning("hw-probe File Not Found", "hw-probe output file\n" + hwProbeFilePath + "\n" +
                                       "Is not present.")
        except:
            messagebox.showwarning("hw-probe File Not Found", "hw-probe output file\n" + hwProbeFilePath + "\n" +
                                   "Is not present.")
            return
        if tarfile.is_tarfile(hwProbeFilePath):
            tarfileHwProbe = tarfile.open(hwProbeFilePath, 'r:xz')
            tarfileHwProbe.extractall(path=COMMAND_OUTPUT_FOLDER)
            self.hwProbeContentMap = OrderedDict()

            for dirName, subdirList, fileList in walk(HW_PROBE_FOLDER, topdown=True):
                if dirName == HW_PROBE_FOLDER:
                    #   host and devices files should be present in this folder
                    if isfile(HW_PROBE_FOLDER + '/host'):
                        self.hwProbeContentMap['hostFileLines'] = tuple(open(HW_PROBE_FOLDER + '/host', 'r').
                                                                        read().split('\n'))
                    if isfile(HW_PROBE_FOLDER + '/devices'):
                        self.hwProbeContentMap['devicesLines'] = tuple(open(HW_PROBE_FOLDER + '/devices', 'r').
                                                                       read().split('\n'))
                elif dirName == HW_PROBE_FOLDER + '/logs':
                    #   read in whatever log files are present
                    self.hwProbeContentMap['logMap'] = OrderedDict()
                    tempMap = {}
                    fNameList = []
                    for fname in fileList:
                        tempMap[fname] = tuple(open(HW_PROBE_FOLDER + '/logs/' + fname).read().split('\n'))
                        fNameList.append(fname)
                    fNameList.sort()
                    for fname in fNameList:
                        self.hwProbeContentMap['logMap'][fname] = tempMap[fname]
                        if fname == "acpidump" or fname == 'acpidump_decoded':             # ACPI Dump
                            self.hwProbeContentMap[fname] = tempMap[fname]

                elif dirName == HW_PROBE_FOLDER + '/tests':
                    #   The format of this folder is the same as that of the logs folder
                    self.hwProbeContentMap['testMap'] = OrderedDict()
                    tempMap = {}
                    fnameList = []
                    for fName in fileList:
                        tempMap[fName]  = tuple(open(HW_PROBE_FOLDER + '/tests/' + fName).read().split('\n'))
                        fnameList.append(fName)
                    fnameList.sort()
                    for fname in fnameList:
                        self.hwProbeContentMap['testMap'][fname] = tempMap[fname]

            return self.hwProbeContentMap
        else:
            messagebox.showwarning("hw-probe File Not Found", "hw-probe output file\n" + hwProbeFilePath + "\n" +
                                                              "Is not present.")

    def messageReceiver(self, message: dict):
        if 'source' in message:
            if message['source'] == "FileSystemChangeHandler.on_created":
                if 'type' in message and message['type'] == 'created':
                    if 'path' in message and isfile(message['path']):
                        pathParts = split(message['path'])
                        if pathParts[-1] == 'hw.info.2022-09-05.txz':
                            if tarfile.is_tarfile(message['path']):
                                hwProbeOutput = tarfile.open(message['path'], 'r:xz')
                                hwContent = hwProbeOutput.list()
                                print("Type of hw.info.2022-09-05.txz content:\t" + str(type(hwContent)))
                            else:
                                raise Exception("HardwareProbe.messageReceiver - hw-probe output file format not recognized:  " + \
                                                message['path'])

    def list(self):
        print("Results of HardwareProbe:")
        for name, value in self.hardwareMap.items():
            print("\t" + name + ":\t" + str(value))


class BlockSet:

    class BlockDev:
        def __init__(self, record: dict):
            """
            Populates fields of this descriptor object using a line of the output of the command:
                "lsblk --all --json --bytes"
            Assumes the output format of Linux Mint / Ubuntu, which also is the format for all Debian
            derivatives, and that the format is a json text.
            :param record:  A json / dict object output by the lsblk command.
            """
            if record is None or not isinstance(record, dict):
                raise Exception('BlockSet.BlockDev constructor - invalid record argument:\t' + str(record))
            self.record = deepcopy(record)
            self.name = None
            self.maj_min    = None
            self.rm     = None
            self.size   = None
            self.ro     = None
            self.type   = None
            self.mountPoints = None
            if 'name' in self.record:
                self.name = self.record['name']
            if 'maj:min' in self.record:
                self.maj_min = self.record['maj:min']
            if 'rm' in self.record:
                self.rm = self.record['rm']
            if 'size' in self.record:
                self.size = self.record['size']
            if 'ro' in self.record:
                self.ro = self.record['ro']
            if 'type' in self.record:
                self.type = self.record['type']
            if 'mountpoints' in self.record:
                self.mountPoints = tuple(self.record['mountpoints'])

        def getAttribute(self, attrName: str):
            if attrName in self.record:
                return self.record[attrName]
            return None

        def list(self):
            pass

    def __init__(self, lsblkOutput: str):
        """
        If there are ever fields other than 'blockdevices' in the json map returned by lsblk, they are not
        recorded by this class (yet).
        """

        self.toolOutput = lsblkOutput
        if DEBUG:
            print(self.toolOutput)
        self.blockJSON = loads(self.toolOutput)
        self.blockMap = OrderedDict()
        if DEBUG:
            print(self.blockJSON)
        if 'blockdevices' in self.blockJSON:
            self.blockJSON['blockdevices'] = tuple(self.blockJSON['blockdevices'])
            rowIdx = 0
            for blockDevice in self.blockJSON['blockdevices']:
                self.blockMap[rowIdx]   = BlockSet.BlockDev(blockDevice)
                rowIdx += 1

    def getBlockJSON(self):
        return self.blockJSON

    def getBlockDevices(self):
        if 'blockdevices' in self.blockJSON:
            return self.blockJSON['blockdevices']
        return None

    def getDiskJSON(self):
        diskJSON = []
        if 'blockdevices' in self.blockJSON:
            for device in self.blockJSON['blockdevices']:
                if device['type'] == 'disk':
                    diskJSON.append(device)
            return tuple(diskJSON)
        return None

    def getPartitionJSON(self):
        partitionJSON = []
        if 'blockdevices' in self.blockJSON:
            for device in self.blockJSON['blockdevices']:
                if 'type' in device and device['type'] == 'disk':
                    if 'children' in device:        #   Assumes that 'children' is either a list or a tuple
                        for subDisk in device['children']:
                            if 'type' in subDisk and subDisk['type'] == 'part':
                                partitionJSON.append(subDisk)
            return tuple(partitionJSON)
        return None

    def getBlockMap(self):
        return self.blockMap

    def getToolOutput(self):
        return self.toolOutput


class BlkIdSet:

    class BlockIdAttr(Enum):
        BLOCK_SIZE  = 'BLOCK_SIZE'
        LABEL       = 'LABEL'
        UUID        = 'UUID'
        TYPE        = 'TYPE'
        PARTUUID    = 'PARTUUID'

        def __str__(self):
            return self.value

    class BlockId:
        def __init__(self, textRecord: str):
            """
            Populates fields of this descriptor object using a line of the output of the command:
                "blkid -o full"
            Assumes the output format of Linux Mint / Ubuntu, which also is the format for all Debian
            derivatives.
            :param textRecord:  A line of output from the blkid command.
            """
            if not isinstance(textRecord, str):
                raise Exception('BlockId constructor - invalid textRecord argument:\t' + str(textRecord))
            self.label      = None
            self.devPath    = None
            self.blockSize  = None
            self.uuid       = None
            self.type       = None
            self.partUUID   = None
            self.devPath, attributetext  = textRecord.split(':')
            #   Since value can have spaces in them a simple solit() will not work.
            #   However, all values are in double quotes, so scanning for these will work.
            attributes = attributetext.split('" ')
            for attribute in attributes:
                name, value = attribute.split('=')
                if str(BlkIdSet.BlockIdAttr.BLOCK_SIZE) in name:
                    self.blockSize = int(value.strip('"'))
                elif str(BlkIdSet.BlockIdAttr.TYPE) in name:
                    self.type = value.strip('"')
                elif str(BlkIdSet.BlockIdAttr.UUID) in name:
                    self.uuid = value.strip('"')
                elif str(BlkIdSet.BlockIdAttr.LABEL) in name:
                    self.label  = value.strip('"')
                elif str(BlkIdSet.BlockIdAttr.PARTUUID) in name:
                    self.partUUID  = value.strip('"')

        def list(self):
            print("\nBlockId:")
            print('\tlabel:\t' + str(self.label))
            print('\tdevPath:\t' + str(self.devPath))
            print('\tblockSize:\t' + str(self.blockSize))
            print('\tuuid:\t' + str(self.uuid))
            print('\ttype:\t' + str(self.type))
            print('\tpartUUID:\t' + str(self.partUUID))

    def __init__(self, blkIdTextOutput: str):
        if not isinstance(blkIdTextOutput, str):
            raise Exception('BlkIdSet constructor - invalid blkIdTextOutput argument:\t' + str(blkIdTextOutput))
        self.lines  = blkIdTextOutput.split('\n')
        self.blockIdList = []
        for line in self.lines:
            if line.strip() != '':
                self.blockIdList.append(BlkIdSet.BlockId(line))
        self.blockIdList = tuple(self.blockIdList)


class USBset:

    class USBRecord:
        def __init__(self, textLines: tuple):
            if not isinstance(textLines, tuple):
                raise Exception('USBset.USBRecord constructor - invalid textLines argument:\t' + str(textLines))
            self.lineAnalysis = []
            for line in textLines:
                if not isinstance(line, str):
                    raise Exception('USBset.USBRecord constructor - invalid line in textLines argument:\t' + str(line))
                if len(line.strip()) == 0:
                    continue
                count   = 0
                idx     = 0
                while line[idx] == ' ':
                    count += 1
                    idx += 1
                self.lineAnalysis.append({
                    'leadingSpaces': count,
                    'text': line
                })

                #   Still need to detect when block headings happen.
                #   They are on separate lines, are indented two spaces less than their content lines,
                #       appear to have standard phrases for names and all end in a colon.
                if count % 2 == 0:
                    self.lineAnalysis[-1]['name-value'] = True
                    lineParts   = re.split(r'\s{2,}', line.strip())
                    if len(lineParts) > 1:
                        self.lineAnalysis[-1]['attrName'] = lineParts[0]
                        self.lineAnalysis[-1]['attrValue']  = lineParts[1]
                    if len(lineParts) > 2:
                        self.lineAnalysis[-1]['description']  = lineParts[2]
                else:
                    self.lineAnalysis[-1]['name-value'] = False

            if DEBUG:
                print("")
                for line in textLines:
                    print(line)

            self.bLength            = None
            self.bDescriptorType    = None
            self.bcdUSB             = None
            self.bDeviceClass       = None
            self.bDeviceSubClass    = None
            self.bDeviceProtocol    = None
            self.bMaxPacketSize0    = None
            self.idVendor           = None
            self.idProduct          = None
            self.bcdDevice          = None
            self.iManufacturer      = None
            self.iProduct           = None
            self.iSerial            = None
            self.bNumConfigurations = None

            self.fieldDescription = OrderedDict({
                'bLength' : None,
                'bDescriptorType' : None,
                'bcdUSB' : None,
                'bDeviceClass' : None,
                'bDeviceSubClass ' : None,
                'bDeviceProtocol' : None,
                'bMaxPacketSize0' : None,
                'idVendor' : None,
                'idProduct' : None,
                'bcdDevice' : None,
                'iManufacturer' : None,
                'iProduct' : None,
                'iSerial ' : None,
                'bNumConfigurations' : None
            })
            """
              bLength                18
              bDescriptorType         1
              bcdUSB               2.00
              bDeviceClass          239 Miscellaneous Device
              bDeviceSubClass         2 
              bDeviceProtocol         1 Interface Association
              bMaxPacketSize0        64
              idVendor           0x0c45 Microdia
              idProduct          0x6321 HP Integrated Webcam
              bcdDevice           11.11
              iManufacturer           2 DC01901LO0W30H
              iProduct                1 HP Webcam-101
              iSerial                 0 
              bNumConfigurations      1
            """


            #   count spaces at the start to determine nesting level in the attribute lists.from

    def __init__(self, lsUSBoutput: str):
        """
        Parse the output of the lsusb --verbose command and build the equivalent internal objects from it.
        This may be missing some information due to not using su, sudo or being root when run.
        If the user does run the application as root or using sudo, then additional information should be
        captured.
        :param lsUSBoutput:
        """
        if lsUSBoutput is None or not isinstance(lsUSBoutput, str):
            raise Exception('USBset constructor - invalid lsUSBoutput argument:\t' + str(lsUSBoutput))
        if DEBUG:
            print("\nlsusb Output:")
            print("\n" + lsUSBoutput.strip('\t'))       #   this shows that only space characters are used for tree
                                                        #   format of output.  This parse will fail otherwise.
        #   Divide into individual device record text
        self.outputLines = lsUSBoutput.split('\n')
        lineIdx = 0
        inBlock = False
        blockLines = []
        self.usbRecords = []
        while lineIdx < len(self.outputLines)-1:
            if self.outputLines[lineIdx].upper().startswith("BUS") and \
                    self.outputLines[lineIdx+1].upper().startswith("DEVICE DESCRIPTOR:"):
                inBlock = True
                lineIdx += 2
                while inBlock and lineIdx < len(self.outputLines):
                    if self.outputLines[lineIdx].upper().startswith("BUS") and \
                            self.outputLines[lineIdx + 1].upper().startswith("DEVICE DESCRIPTOR:"):
                        inBlock = False
                        self.usbRecords.append(USBset.USBRecord(tuple(blockLines)))
                    else:
                        blockLines.append(self.outputLines[lineIdx])
                        lineIdx += 1
            lineIdx += 1


class DeviceList:

    def __init__(self):
        self.context = pyudev.Context()
        self.devices = self.context.list_devices()

    def getDevices(self):
        return self.devices

    def list(self):
        print("\nDeviceList:")
        for device in self.devices:
            print("\t" + str(device))


class BlockPartitions:

    def __init__(self):
        self.context = pyudev.Context()
        self.devices = self.context.list_devices(subsystem='block', DEVTYPE='partition')

    def getByName(self, name: str):
        """
        Retrieve a Device object for the named block device.
        :param name: e.g. sda, sdb, sdc
        :return:
        """
        return pyudev.Devices.from_name(self.context, 'block', name)

    def list(self):
        print("\nBlock Partition List:")
        for device in self.devices:
            print("\t" + str(device))


class BlockFileSystems:

    def __init__(self):
        self.inventoryJSON = loads(LinuxUtilities.runLinuxTool(LinuxUtilities.DeviceCommand.LSBLK_FS.value))


def ExitProgram():
    answer = messagebox.askyesno(parent=mainView, title='Exit program ', message="Exit the " + PROGRAM_TITLE + " program?")
    if answer:
        mainView.destroy()


if __name__ == '__main__':

    for name, value in environ.items():
        print(name + ':\t' + value)
    exit(0)

    #   deviceList = DeviceList()
    #   deviceList.list()

    blockPartitions = BlockPartitions()
    sda = blockPartitions.getByName('sda')
    blockPartitions.list()

    blockFileSystems    = BlockFileSystems()

    exit(0)

    mainView = Tk()
    mainView.geometry("800x500+200+100")
    mainView.title(PROGRAM_TITLE)
    mainView.protocol('WM_DELETE_WINDOW', lambda: ExitProgram())

    mainView.mainloop()

