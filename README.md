#MythPyWii#

A Wii remote (wiimote) interface to MythTV, written in Python.

This project uses [MythFrontend's telnet interface](http://www.mythtv.org/wiki/Telnet_socket) combined with the [CWiiD](http://abstrakraft.org/cwiid/) python interface to 
allow you to control MythTV using your Wii Remote.

## Two versions?

`myth_py_wii.py` is the official version, created by Benjie.

`myth_py_wii.alister.py` is an enhanced version created by Alister Ware
which supports command line options and a configuration file. (Untested
by Benjie.)

## Want to contribute?

Get in touch. I can no longer maintain MythPyWii (due to no longer
having MythTV :-( ) so if you're looking to be a maintainer, just let me
know! If it's just a minor bugfix then send a pull request.

##Trouble shooting##

###TypeError: wmcb() takes exactly 2 arguments (3 given)###

You're using a more recent version of CWiiD. The fix is simple - change line 141:

    def wmcb(self, messages):

to:

    def wmcb(self, messages, timeIgnore):

Thanks to Mike H for pointing out this issue.

###No bluetooth interface found###

Ensure you have the dependencies installed, and then try unplugging and re-plugging the bluetooth device (if it is USB) or restarting. (Further debugging info: "hcitool scan" after pressing 1+2 on your wiimote should return an entry with "Nintendo RVL-CNT-01", if it does not then there is something wrong with your bluetooth setup and/or your Wiimote.)

###Bluetooth issues###

    error: uncaptured python exception, closing channel 
    <__main__.MythSocket connected at 0x7fd7840133b0> (<class 'socket.error'>:(111, 'Connection refused') 
    [/usr/lib/python2.5/asyncore.py|read|68] 
    [/usr/lib/python2.5/asyncore.py|handle_read_event|388] 
    [./main.py|handle_read|52] 
    [/usr/lib/python2.5/asyncore.py|recv|342])

You're probably using an old version of MythPyWii. Download the latest version, and try again. If the problem persists, please submit an ticket.

##Installation##

### (U/Ku/Edu/Myth)buntu GNU/Linux, Hardy ###
  * Enable Mythfrontend's telnet interface. (Mythfrontend Main Menu > Utilities/Setup > Setup > General > page 4 > Tick *Enable Network Remote Control interface*, Enter *6546* after *Network Remote Control Port* > Next > Next > Next > Finish. )
  * Exit mythfrontend.
  * Download the latest myth_py_wii.py and save it to your ~/Desktop
  * If you don't have the dependencies then run the following command in a terminal  
        ```$ sudo apt-get install python bluetooth python-bluez python-cwiid```  
    alternatively, install each package in synaptic.
  * Run the script: `python ~/Desktop/myth_py_wii.py`
    (you can do so using the terminal - e.g. Applications > Accessories > Terminal in Ubuntu)
  * Open MythFrontend.
  * Wait for MythFrontend to finish loading.
  * Press 1&2 simultaneously on your wiimote. After a few seconds the wiimote should vibrate and the LEDs will show [ # . . # ] where # is on and . is off.
  * Enjoy. 

##Controls##

These are liable to change, but for now, here is how they are mapped:

<table>
  <tr><th>**Combo**</th><th>**Action**</th></tr>
  <tr><td>Keypad</td><td>same as keypad on keyboard</td></tr>
  <tr><td>A</td><td>Enter (Accept, OK, next, ...)</td></tr>
  <tr><td>Minus (-)</td><td>d (Delete)</td></tr>
  <tr><td>Home</td><td>escape (Exit to previous menu/exit mythfrontend)</td></tr>
  <tr><td>Plus (+)</td><td>p (Play/pause)</td></tr>
  <tr><td>1</td><td>Info</td></tr>
  <tr><td>2</td><td>Menu</td></tr>
  <tr><td>B + left</td><td>rewind to beginning of video</td></tr>
  <tr><td>B + twist wiimote</td><td>rewind (if twisted to the left) or fastforward (otherwise) with speed dependant on twist amount.</td></tr>
  <tr><td>B + A + twist wiimote</td><td>timestretching - slower (if twisted left) or faster (if twisted right)</td></tr>
</table>

###A comment on twisting:###

Point the wii remote at the screen, and twist from the elbow so that it continues to point at the screen.

The maximum fastforward/rewind speed is 180x. The speeds are dictated by mythfrontend itself. When you rotate the wiimote, you will feel a slight vibration (0.05 seconds) to let you know you have gone up or down a speed segment. To stop fastforwarding/rewinding, simply let go of B.

###Power saving###
Turn the wiimote off (power button) when not in use, and turn it back on by holding down 1 and 2 to make it sync. (It will turn off automatically after around 35 minutes.)

# Videos

[Short version](http://www.youtube.com/watch?v=Fx8uoTlZXF0)
[Full version](http://www.youtube.com/watch?v=fqacVgG394I)

(Also: my blog's old theme! URGH!)

#LICENSE#

[New BSD License](http://benjie.mit-license.org)
