# gearboxmd

GearboxMD


GearboxMD is a GUI application that uses the Linux hw-probe command as its primary source of hardware information and uses the operational tests it includes for diagnosis of hardware problems.


Dependencies:

This software is meant currently to be run only on debian Linux operating system installations.  It currently requires, for instance the gnome-terminal program which is the terminal emulation program installed on many debian versions of Linux, including Ubuntu and Linux Mint.  You know you have debian Linux if you can install software applications and packages ising the apt and apt-get package manager programs.  To see if you need to install gnome-terminal, try displaying its manual page in the terminal on your computer.  At the prompt, enter "man gnome-terminal".  If the manual page appears, then you have it.  If not, then to run this application you need to run "sudo apt-get install gnome-terminal" while connected to the Internet nto install it.

Another requirement is that the hw-probe command line program be installed on your booted Linux OS. GearboxMD uses this as its primary source of hardware information and uses the operational tests it includes for diagnosis of hardware problems.  This is not the only Linux command line program that GearboxMD will use and not the only one that it can use, but currently it is the only one that it does use.  It can incorporate almost any linux command line program output into its knowledge base, and many additions to GearboxMD are currently planned.  Many of these Linux tools just provide information on what hardware you have installed in your computer, many can perform diagnostic tests, and many can monitor you computer's insides in real time and provide a dashboard of information to work with in evaluating your computer for performance, failures, and for early warning signs.  Their output goes either to the command console / terminal or a file, so the addition of a graphical user interface for random access to any of the information they provide, and an API to use to analyse that information, is a significant work saver.

The GUI itself requires the standard Python GUI building package known as tkinter.  This can be installed using the command: sudo apt-get install python-tk while connected to the Internet.

Summary of Linux Installations Possibly Required:
	sudo apt-get install gnome-terminal
	sudo apt-get install hw-probe
	sudo apt-get install python-tk

You might be wondering how to install the latest version of Python also, and I highly recommend that you do to benefit from the platform's most advanced features.  A good to-do list is provided at:
	https://dev.to/ivayloiv/install-latest-python-version-on-any-linux-distro-5gc3


Goals:

One of my primary goals in developing this project is to provide analysis of the information gathered using models of correct or standard system behavior to find issues needing attention.  For both performance and diagnostic issues, prioritization depends on the user's requirements, so the GUI I designed provides a random-access collection of output components which you can arrange according to your own needs and work-flow in your area of interest.  


Installation:

This application is not ready for general distribution.  I have uploaded it to the Test PyPI website for those who might be curious about its features or how it is implemented.  

The mose useful and easiest installation method for this purpose is to unzip the source archive, gearboxmd-0.0.1.tar.gz, from your home directory.  The folders / paths the application uses are structured to store and locate its files and folders only within its own working folder, meaning it can, as packaged, only work with your home folder as a root or point of reference for decompression of the source archive.

Once you have decompressed the source archive, start yout terminal / console program and switch from your home folder to:

	/HOME/gearboxmd-0.0.1/src/gearboxmd

This README.MD file is located in the gearboxmd-0.0.1 folder.  In the gearboxmd-0.0.1/src/gearboxmd folder you will find the main python file.  Running your interpreter on this file will launch the application.  At the terminal prompt enter the command:
	
	$ python gearboxmd.py
		or
	$ python3 gearboxmd.py

depending on how your system invokes the python version 3 interpreter.  GearboxMD requires Python 3.6 or better since certain features rely on the more recent versions of its libraries, so it's best to update your interpreter first.


Features and Use:

The main GUI window is a notebook titled "GearboxMD" with a single page on it at the start titled "Hardware Probe".  To gather the information needed from your computer, you must first run the hw-probe program.  This is done by pressing the [Run Probe] button in the toolbar at the top.  The program needs to run as the "super user", or as root, so a terminal will then appear requesting your password.  Enter your password and the probe starts.  The default options currently configured for the hw-probe program include reading in hardware information, reading logs relevant to hardware activity and diagnostics, reading in the acpi table, and running some initial tests.  The acpi table is also decoded so that you can view it in human readable form.  The hw-probe program will display a message stating which scan or test it is currently doing.  These will include:

	Probe for hardware,
	Reading logs,
	Check graphics,
	Check memory,
	Check HDDs, and
	Check CPU. 

When it is checking the graphics, a separate wnidow will pop up with three colored spinning gears in it.  You will need to exit thie window for the hw-probe program to continue.  Once the probe is complete, GearboxMD is ready to display the information gathered.  The output of hw-probe is stored in the data/commandOutput folder under the installation source code folder, so you can view the latest probe any time after running the probe.

The view the results, click on the [Load Latest] button in the same toolbar.  After a few seconds, a set of notebook tabs will appear to the right of the "Hardware Probe" tab, each with a separate category of information on its page.  The categories in the default configuration of hw-probe launched when you pressed the [Run Probe] button include:

	Logged Events,
	Host Hardware,
	Devices,
	Tests Run,
	ACPI Dump, and
	ACPI Decoded.

Each of these pages has a toolbar at the top and a help message box across the bottom.  As you mouse over the tools, their help message will appear in the message box at the bottom.  Only one of the buttons in the toolbar is implemented currently, "Toplevel".  This is a toggle for a "Toplevel" window which displays the same information frame as is displayed in the notebook page.  You can have as many of the pages displayed simultaneously in pop-up windows as you like.

Not Implemented / Planned:

In the "Hardware Probe" page, there is a vertical list of checkboxes, one for each of the information categories displayed in the notebook pages.  When finished, these will toggle the pages and their corresponding pop-up windows.

The "View Details" button on the toolbar has a similar purpose.  Pressing it causes a window to appear which has a layout of check boxes which will control which pages and windows appear at any given time.  Each information category has a check box to select it, and under each category are selectors for "Notebook" and "Toplevel".

The "Probe Options" button in the toolbar will allow you to select the options or arguments you want to run the hw-probe command with.  These will control what information is included in the probe output.  Mousing over any of these displays a short help message for the option at the bottom of the window, copied from the help provided by the program itself.


Tricks:

Features planned include the ability to store a history of probe results.  Since the results are always written to a gzip'd archive at:
	HOME/gearboxmd-0.0.1/scr/gearboxmd/data/commandOutput/hw.info.txz, you can copy that file to your own archive of probe results.  Copying one back to that path and file name will make it available for loading by GearboxMD.


Develpopment:

I have many and long term plans for development of this application, and you are welcome to do your own work on it.  I will be updating it at Test PyPI and at my repos at GitHub and BitBucket periodically.  I use Pycharm for this project, and the directory structure of the src/gearboxmd folder in the source dist archive is identical to my Pycharm project folder for this project.
