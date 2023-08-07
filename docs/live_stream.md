Live video streaming with Insta360 GO 2 and GO 3 cameras
========================================================

Insta360 only allows video streaming with GO 2 and GO 3 using WeChat.
To sign up on WeChat you need a chinese phone number or another WeChat account to endorse you.
But what if I don't live in China? If I want to live stream to another platform?

If you tinker the camera file system enough (using telnet or mounting the ext2 file from the firmware) you'll probably find a command called `/usr/bin/AmbaRTSPServer`.
And yes, it does what it says.

With the help of [`bootup.sh`](boot_commands.md) we can run `/usr/bin/AmbaRTSPServer` when the camera is turned on:

```
#!/usr/bin/env sh

/usr/bin/AmbaRTSPServer
```

Connect you computer to the camera access point Wi-Fi network.

Now start video recording with your GO 2 or GO 3 (otherwise `AmbaRTSPServer` won't work).

Access `rtsp://192.168.42.1/liveMain` with any RTSP client, for example VLC (File > Open Network...) or `ffplay`:

```
$ ffplay rtsp://192.168.42.1/liveMain
```

You should be now seeing a live stream from your GO 2 or GO 3 camera! But with no audio for now :(

Depending on the video mode you are using while recording/streaming the format and size of the video will be different.


`AmbaRTSPServer` has this publicly mentioned parameters:

* `en_audio`: Enable audio
* `en_text`: Enable text
* `en_rtcp`: Enable RTCP

But none of them are used anymore because the RTOS decides what options to enable.

There are also 2 hidden parameters:

* `en_ap`: Enable Aggregation Packet
* `en_fg`: Enable Foreground (does not go back to console prompt when the program is started)
