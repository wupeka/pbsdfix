#!/usr/bin/env python3
"""
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
"""
import sys
import subprocess
import json
import tempfile
import struct
import os
def mount(imgname):
    v = subprocess.run(["/usr/sbin/sfdisk", "-J",imgname], capture_output=True)
    if v.returncode != 0:
        sys.exit("Unable to dump partition table from image")
    partitions = json.loads(v.stdout)["partitiontable"]["partitions"]
    for part in partitions:
        if part["node"] == imgname+"9":
            break
    dir = tempfile.mkdtemp()
    v = subprocess.run(["mount", "-o", "loop,offset=%d,user" % (int(part["start"]) * 512), imgname, dir])
    if v.returncode != 0:
        sys.exit("Unable to mount the image")
    return dir
    
def umount(dir):
    v = subprocess.run(["sudo","umount", dir])
    if v.returncode != 0:
        sys.exit("Unable to unmount the image")

def calculate(serial, sd_id):
    uv4 = 0
    p1 = 0x5e4c99ac
    for c in serial:
        uv4 = ((uv4*0x3d) + ord(c)) & 0xffffffff
    iv10 = (uv4 ^ 0x6eca1735) * 0x2d10a39b + uv4*0x36dcc025 + p1
    iv10 = (iv10 + (sd_id ^ 0x3ac19b9e) * 0x51670edf + sd_id) & 0xffffffff
    return iv10
    
def main():
    if os.geteuid() != 0:
        sys.exit("Must be run as root, unfortunately...")
    if len(sys.argv) != 4:
        sys.exit("Usage %s <image_name> <old_card_cid_hex> <new_card_cid_hex>")
    old_cid = int(sys.argv[2], 16)
    new_cid = int(sys.argv[3], 16)
    mountdir = mount(sys.argv[1])

    with open(os.path.join(mountdir, ".freezestatus"), "rb") as fsfile:
        old_fs = fsfile.read(4)
    old_fs = struct.unpack("<I", old_fs)[0]
    print("Old freezestatus: %.8x" % old_fs)
    
    with open(os.path.join(mountdir, "device.cfg"), "r") as devcfg:
        for l in devcfg.readlines():
            if l.startswith("serial="):
                serial = l[7:].strip()
                break
    print("Device serial: %s" % serial)
    ek = calculate(serial, old_cid)
    ek -= old_fs
    print("Enc key: %.8x" % ek)
    new_ek = calculate(serial, new_cid)
    new_fs = new_ek - ek
    print("New freezestatus: %.8x" % new_fs)
    new_fs = struct.pack("<I", new_fs)
    with open(os.path.join(mountdir, ".freezestatus"), "wb") as fsfile:
        fsfile.write(new_fs)
    umount(mountdir)

if __name__ == "__main__":
    main()
