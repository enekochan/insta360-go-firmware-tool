Connect with telnet to Insta360 GO2 camera
==========================================

When turning on the GO2 camera it creates a Wi-Fi AP (access point) you can connect to as if was any other router or similar.
The name of that access point should be something like `GO2 XXXXXX.OSC` and the password to connect is always `88888888`.

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

One of the drawbacks of the Insta360 GO2 camera is that it will switch off itself after a maximum of 3 minutes (configurable with the box).
This makes you push the box right button from time to time (less than 3 minutes) so you can continue tinkering with the telnet console.

The solution to this is to connect the Insta360 phone app to the camera and leave the app opened in the phone.
The app sends some kind of heart beat message that makes the camera not shut down.
