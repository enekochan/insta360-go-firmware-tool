Running commands on boot
========================

The Insta360 GO 2 and GO 3 cameras firmware looks for a file named `bootup.sh` in the root of the cameras memory (that corresponds to `/tmp/SD0/bootup.sh` in the file system).
If it exists it will execute it, and you may use that to run your own scripts.

Connect the camera to your computer via USB and create a file named `bootup.sh` in the root of the USB disk drive of the camera.
For example this script will log the last time the camera was used:

```
#!/usr/bin/env sh

date > bootup.log
```

Disconnect the camera from the USB port, turn the camera off, turn it on again and then connect it to the computer's USB port.
You should see a file called `bootup.log` in the root of the disk drive with the timestamp of the last time the camera was switched on.
