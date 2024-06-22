Telnet connection
=================

The Insta360 GO 2, GO 3 and GO 3S cameras create a Wi-Fi AP (access point) that you can connect to as if it was a router.
The name of that access point should be something like `GO2 XXXXXX.OSC`,  `GO 3 XXXXXX.OSC` and `GO 3S XXXXXX.OSC` and the password is always `88888888`.

Once connected the camera will be accessible via the 192.168.42.1 IP address.

You may connect to it using a telnet client with the username `root` and no password.

```
$ telnet 192.168.42.1
Trying 192.168.42.1...
Connected to 192.168.42.1.
Escape character is '^]'

AmbaLink login: root
~#
```

In macOS you can use `nc`:

```
$ nc -v 192.168.42.1 23
Connection to 192.168.42.1 port 23 [tcp/telnet] succeeded!
��������
AmbaLink login: root
root
~#
```

Keep the camera on while connected with telnet
==============================================

One of the drawbacks of the Insta360 GO 2 and GO 3 cameras is that they will switch off themselves after a maximum of 3 minutes (configurable with the box).
This makes you push the box right button from time to time (less than 3 minutes) so you can continue tinkering with the telnet console.

The solution to this is to connect the Insta360 phone app to the camera and leave the app opened in the phone.
The app sends some kind of heart beat message that makes the camera not shut down.
