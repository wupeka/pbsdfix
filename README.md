Switch the serial number of Pocketbook internal SD card. Tested with PB626
Usage:
 1. Dump the contents of the card:
   dd if=/dev/mmcblk0 of=pb.img
 2. Read the serial numbers of old and new card using e.g. cat /sys/block/mmcblk0/device/serial, e.g. 01234567 for old card, abcdef00
 3. Back the original image up:
   cp pb.img pb.img.bak
 4. Launch the script, as root (unfortunately...)
   sudo ./fix.py pb.img 01234567 abcdef00
 5. Write the image to the new card:
   dd if=pb.img of=/dev/mmcblk0
