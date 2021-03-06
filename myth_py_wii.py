#!/usr/bin/env python
"""
Copyright (c) 2008, Benjie Gillam
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of MythPyWii nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
# By Benjie Gillam https://github.com/benjie/MythPyWii

import cwiid, time, StringIO, sys, asyncore, socket, os
from math import log, floor, atan, sqrt, cos, exp

# Note to self - list of good documentation:
# cwiid: http://flx.proyectoanonimo.com/proyectos/cwiid/
# myth telnet: http://www.mythtv.org/wiki/index.php/Telnet_socket

def do_scale(input, max, divisor=None):
	if divisor is None: divisor = max
	if (input > 1): input = 1
	if (input < -1): input = -1
	input = int(input * divisor)
	if input>max: input = max
	elif input < -max: input = -max
	return input


class MythSocket(asyncore.dispatcher):
	firstData = True
	data = ""
	prompt="\n# "
	owner = None
	buffer = ""
	callbacks = []
	oktosend = True
	def __init__(self, owner):
		self.owner = owner
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect(("localhost", 6546))
	def handle_close(self):
		print "Mythfrontend connection closed"
		self.owner.socket_disconnect()
		self.close()
	def handle_read(self):
		try:
			self.data = self.data + self.recv(8192)
		except:
			print """
[ERROR] The connection to Mythfrontend failed - is it running?
If so, do you have the socket interface enabled?
Please follow the instructions at http://www.benjiegillam.com/mythpywii-installation/
"""
			self.handle_close()
			return
		while len(self.data)>0:
			a = self.data.find(self.prompt)
			if a>-1:
				self.oktosend = True
				result = self.data[:a]
				self.data = self.data[a+len(self.prompt):]
				if not self.firstData:
					print ">>>", result
					cb = self.callbacks.pop(0)
					if cb:
						cb(result)
				else:
					print "Logged in to MythFrontend"
					self.firstData = False
			else:
				break;
	def writable(self):
		return (self.oktosend) and (len(self.buffer) > 0) and (self.buffer.find("\n") > 0)
	def handle_write(self):
		a = self.buffer.find("\n")
		sent = self.send(self.buffer[:a+1])
		print "<<<", self.buffer[:sent-1]
		self.buffer = self.buffer[sent:]
		self.oktosend = False
	def cmd(self, data, cb = None):
		self.buffer += data + "\n"
		self.callbacks.append(cb)
		self.owner.lastaction = time.time()
	def raw(self, data):
		cmds = data.split("\n")
		for cmd in cmds:
			if len(cmd.strip())>0:
				self.cmd(cmd)
	def ok(self):
		return len(self.callbacks) == len(self.buffer) == 0


class WiiMyth:
	wii_calibration = False
	wm = None
	ms = None
	wii_calibration = None
	#Initialize variables
	reportvals = {"accel":cwiid.RPT_ACC, "button":cwiid.RPT_BTN, "ext":cwiid.RPT_EXT,  "status":cwiid.RPT_STATUS}
	report={"accel":True, "button":True}
	state = {"acc":[0, 0, 1]}
	lasttime = 0.0
	laststate = {}
	lastaction = 0.0
	responsiveness = 0.15
	firstPress = True
	firstPressDelay = 0.5
	maxButtons = 0
	#wii_rel = lambda v, axis: float(v - self.wii_calibration[0][axis]) / (
	#	self.wii_calibration[1][axis] - self.wii_calibration[0][axis])
	def wii_rel(self, v, axis):
		return float(v - self.wii_calibration[0][axis]) / (
		self.wii_calibration[1][axis] - self.wii_calibration[0][axis])
	def socket_disconnect(self):
		if self.wm is not None:
			#self.wm.led = cwiid.LED2_ON | cwiid.LED3_ON
			print "About to close connection to the Wiimote"
			self.wm.close()
			self.wm = None
		return
	def rumble(self,delay=0.2): # rumble unit - default = 0.2 seconds
		self.wm.rumble=1
		time.sleep(delay)
		self.wm.rumble=0
	def wmconnect(self):
		print "Please open Mythfrontend and then press 1&2 on the wiimote..."
		try:
			self.wm = cwiid.Wiimote()
		except:
			self.wm = None
			if self.ms is not None:
				self.ms.close()
				self.ms = None
			return None
		if self.ms is None:
			self.ms = MythSocket(self)
		print "Connected to a wiimote :)"
		self.lastaction = time.time()
		self.rumble()
		# Wiimote calibration data (cache this)
		self.wii_calibration = self.wm.get_acc_cal(cwiid.EXT_NONE)
		return self.wm
	def wmcb(self, messages, extra=None):
		state = self.state
		for message in messages:
			if message[0] == cwiid.MESG_BTN:
				state["buttons"] = message[1]
			#elif message[0] == cwiid.MESG_STATUS:
			#	print "\nStatus: ", message[1]
			elif message[0] == cwiid.MESG_ERROR:
				if message[1] == cwiid.ERROR_DISCONNECT:
					self.wm = None
					if self.ms is not None:
						self.ms.close()
						self.ms = None
					continue
				else:
					print "ERROR: ", message[1]
			elif message[0] == cwiid.MESG_ACC:
				state["acc"] = message[1]
			else:
				print "Unknown message!", message
			laststate = self.laststate
			if ('buttons' in laststate) and (laststate['buttons'] <> state['buttons']):
				if state['buttons'] == 0:
					self.maxButtons = 0
				elif state['buttons'] < self.maxButtons:
					continue
				else:
					self.maxButtons = state['buttons']
				self.lasttime = 0
				self.firstPress = True
				if laststate['buttons'] == cwiid.BTN_B and not state['buttons'] == cwiid.BTN_B:
					del state['BTN_B']
					if not (state['buttons'] & cwiid.BTN_B):
						self.ms.cmd('play speed normal')
				if (laststate['buttons'] & cwiid.BTN_A and laststate['buttons'] & cwiid.BTN_B) and not (state['buttons'] & cwiid.BTN_A and state['buttons'] & cwiid.BTN_B):
					del state['BTN_AB']
					#self.ms.cmd('play speed normal')
			if self.ms.ok() and (self.wm is not None) and (state["buttons"] > 0) and (time.time() > self.lasttime+self.responsiveness):
				self.lasttime = time.time()
				wasFirstPress = False
				if self.firstPress:
					wasFirstPress = True
					self.lasttime = self.lasttime + self.firstPressDelay
					self.firstPress = False
				# Stuff that doesn't need roll/etc calculations
				if state["buttons"] == cwiid.BTN_HOME:
					self.ms.cmd('key escape')
				if state["buttons"] == cwiid.BTN_A:
					self.ms.cmd('key enter')
				if state["buttons"] == cwiid.BTN_MINUS:
					self.ms.cmd('key d')
				if state["buttons"] == cwiid.BTN_UP:
					self.ms.cmd('key up')
				if state["buttons"] == cwiid.BTN_DOWN:
					self.ms.cmd('key down')
				if state["buttons"] == cwiid.BTN_LEFT:
					self.ms.cmd('key left')
				if state["buttons"] == cwiid.BTN_RIGHT:
					self.ms.cmd('key right')
				if state["buttons"] == cwiid.BTN_PLUS:
					self.ms.cmd('key p')
				if state["buttons"] == cwiid.BTN_1:
					self.ms.cmd('key i')
				if state["buttons"] == cwiid.BTN_2:
					self.ms.cmd('key m')
				# Do we need to calculate roll, etc?
				# Currently only BTN_B needs this.
				calcAcc = state["buttons"] & cwiid.BTN_B
				if calcAcc:
					# Calculate the roll/etc.
					X = self.wii_rel(state["acc"][cwiid.X], cwiid.X)
					Y = self.wii_rel(state["acc"][cwiid.Y], cwiid.Y)
					Z = self.wii_rel(state["acc"][cwiid.Z], cwiid.Z)
					if (Z==0): Z=0.00000001 # Hackishly prevents divide by zeros
					roll = atan(X/Z)
					if (Z <= 0.0):
						if (X>0): roll += 3.14159
						else: roll -= 3.14159
					pitch = atan(Y/Z*cos(roll))
					#print "X: %f, Y: %f, Z: %f; R: %f, P: %f; B: %d    \r" % (X, Y, Z, roll, pitch, state["buttons"]),
					sys.stdout.flush()
				if state["buttons"] & cwiid.BTN_B and state["buttons"] & cwiid.BTN_LEFT:
					self.ms.cmd('play seek beginning')
				if state["buttons"] & cwiid.BTN_B and state["buttons"] & cwiid.BTN_A:
					speed=do_scale(roll/3.14159, 20, 25)
					if (speed<-10): speed = -10
					state['BTN_AB'] = speed
					cmd = ""
					# on first press,  press a,
					# after then use the diff to press left/right
					if not 'BTN_AB' in laststate:
						# # query location
						# Playback Recorded 00:04:20 of 00:25:31 1x 30210 2008-09-10T09:18:00 6523 /video/30210_20080910091800.mpg 25
						cmd += "play speed normal\nkey a\n"#"play speed normal\n"
					else:
						speed = speed - laststate['BTN_AB']
					if speed > 0:
						cmd += (speed / 5) * "key up\n" # Floor is automatic
						cmd += (speed % 5) * "key right\n"
					elif speed < 0:
						cmd += (-speed / 5) * "key down\n" # Floor is automatic
						cmd += (-speed % 5) * "key left\n"
					if speed <> 0:
						self.rumble(.05)
					if cmd is not None and cmd:
						self.ms.raw(cmd)
				if state["buttons"] == cwiid.BTN_B:
					speed=do_scale(roll/3.14159, 8, 13)
					state['BTN_B'] = speed
					if not 'BTN_B' in laststate:
						# # query location
						# Playback Recorded 00:04:20 of 00:25:31 1x 30210 2008-09-10T09:18:00 6523 /video/30210_20080910091800.mpg 25
						cmd = ""#"play speed normal\n"
						if speed > 0:
							cmd += "key .\n"
						elif speed < 0:
							cmd += "key ,\n"
						if speed <> 0:
							cmd += "key "+str(abs(speed)-1)+"\n"
						#print cmd
					elif laststate['BTN_B']<>speed:
						self.rumble(.05)
						if speed == 0:
							cmd = "play speed normal"
						elif ((laststate['BTN_B'] > 0) and (speed > 0)) or ((laststate['BTN_B'] < 0) and (speed < 0)):
							cmd = "key "+str(abs(speed)-1)+"\n"
						elif speed>0:
							cmd = "key .\nkey "+str(abs(speed)-1)+"\n"
						else:
							cmd = "key ,\nkey "+str(abs(speed)-1)+"\n"
					else:
						cmd = None
					if cmd is not None:
						self.ms.raw(cmd)
			self.laststate = state.copy() #NOTE TO SELF: REMEMBER .copy() !!!
	def mythLocation(self, data):
		#Playback Recorded 00:00:49 of 00:25:31 1x 30210 2008-09-10T09:18:00 1243 /video/30210_20080910091800.mpg 25
		#PlaybackBox
		temp = data.split(" ")
		output = {}
		output['mode'] = temp[0]
		if output['mode'] == "Playback":
			output['position'] = temp[2]
			output['max'] = temp[4]
		return output
	def main(self):
		while True:
			if self.wm is None:
				#Connect wiimote
				self.wmconnect()
				if self.wm:
					#Tell Wiimote to display rock sign
					self.wm.led = cwiid.LED1_ON | cwiid.LED4_ON
					self.wm.rpt_mode = sum(self.reportvals[a] for a in self.report if self.report[a])
					self.wm.enable(cwiid.FLAG_MESG_IFC | cwiid.FLAG_REPEAT_BTN)
					self.wm.mesg_callback = self.wmcb
					self.lastaction = time.time()
					os.system("xset dpms force on")
					print("Forcing on the display")
				else:
					print "Retrying... "
					print
			asyncore.loop(timeout=0, count=1)
			if self.lastaction < time.time() - 2100:
				#2100 seconds is 35 minutes
				#1200 seconds is 20 minutes
				self.socket_disconnect()
				print "35 minutes has passed since last action, disconnecting Wiimote"
			time.sleep(0.05)
		print "Exited Safely"

# Instantiate our class, and start.
inst = WiiMyth()
inst.main()
