ext2 file system modification
=============================

If you want to add, remove or edit files in the file system used by the Linux system  of the camera
you have to mount the `section_4.bin` file locally:

```
$ python3 main.py unpack --input=InstaGo2FW.pkg --output=firmware_folder
$ cd firmware_folder
$ mkdir section_4.ext2
$ sudo mount -o loop section_4.bin section_4.ext2
```

Now you can change anything inside the `section_4.ext2` folder.

Once finished umount it:

```
$ sudo umount section_4.ext2
```

Pack your modified firmware:

```
$ python3 main.py pack --input=firmware_folder --output=InstaGo2FW.pkg
```

And use it to update your camera firmware.

WARNING! NEVER GROW THE EXT2 FILE SYSTEM BEYOND ITS DEFAULT SIZE!
You have only about 7MB of free space in it.
