echo Please enter your password so that the application has sufficient rights to create the RAM disk.
sudo mount -t tmpfs -o size=200M tmpfs $1
sudo chown $USER $1
sudo chgrp $USER $1
sudo chmod 700 $1
echo RAM disk is ready for use, press [Enter] key to continue . . .
read input