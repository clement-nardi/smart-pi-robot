# install raspberry pi OS
 - Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
 - Choose recommended OS.
 - Click on the gear and fill as much as you can, especially wifi SSID/password and SSH public key

# Initial setup

Open an SSH session on the rasperry pi with `ssh pi@robot`

Then pair your phone with the raspberry pi:
``` bash
sudo bluetoothctl
default-agent
scan on # wait until you see your smartphone in the list
pair E0:CC:F8:A2:D5:7C # replace with your smartphone's MAC address, you can also find it directly in your smartphone's settings
# Then answer "yes" to all the questions
exit
```

Then enable RFCOMM:
```
sudo nano /etc/systemd/system/dbus-org.bluez.service
```

and replace this line:
```
ExecStart=/usr/lib/bluetooth/bluetoothd
```
By these two:
```
ExecStart=/usr/lib/bluetooth/bluetoothd -C
ExecStartPost=/usr/bin/sdptool add SP
```

