Description
===========
Unofficial Insta360 GO2 camera firmware tool.

The GO2 camera uses an Ambarella H22 SoC and the firmware has a very similar structure to other cameras that also use
Ambarella chips (A2, A7, A9, A12, H2 and others) like the GoPro Hero 3, SJCAM SJ7 and SJ8, Xiaomi Yi and Mi, DJI drones and many more.
See a more detailed list [here](https://en.wikipedia.org/wiki/List_of_Ambarella_products).

Disclaimer
==========
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND.

THIS MAY HARM YOUR CAMERA. USE AT YOUR OWN RISK.

THE AUTHOR TAKES NO RESPONSIBILITY FOR ANYTHING THAT MAY HAPPEN AS A RESULT OF USING THIS SOFTWARE.

Usage
=====

To validate a firmware file:

```
$ python main.py validate --input=InstaGo2FW.pkg
```

To unpack a firmware file:

```
$ python main.py unpack --input=InstaGo2FW.pkg --output=firmware_folder
```

This will unpack the firmware file to the output folder. Some firmware sections will be processed accordingly too:

* The ROMFS sections will be unpacked.
* The DTB will be converted to DTS if possible.

To pack a firmware folder into a file:

```
$ python main.py pack --input=firmware_folder --output=InstaGo2FW.pkg
```

This will use the unpacked firmware data from the input folder to create a valid firmware file.

The output filename can be anything you want (as long as that file does not currently exist) but when uploading it to the camera it always must be named `InstaGo2FW.pkg`.

See the [docs](docs/README.md) for more info.

Insta360 GO2 camera firmware update
===================================

* Once you have your modified firmware file make sure you rename it to `InstaGo2FW.pkg`.
* Connect the box to your computer with a USB-C cable.
* Put the camera inside the box and leave the box open.
* Press the right button in the box to connect it with the camera. The box screen should show "USB Mode".
* In your computer the camera should be shown as a normal USB disk drive named `Insta360GO2`.
* Copy your `InstaGo2FW.pkg` file to the root of that disk drive.
* Unmount that disk drive safely. 
* Disconnect the USB-C cable from the box to exit the USB Mode.
* Press the right button in the box to connect it to the camera again.
* Once connected the screen should show "Camera Firmware Checking" for some time and then both the camera and the box will reset.
* When both finish resetting connect again the box to the camera pressing the right button.
* Go to Settings > About > Fw version to see the firmware version.
