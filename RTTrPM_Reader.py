import socket
import binascii
import struct
import thirdParty_lighting
import traceback

class RTTrP:

	def __init__(self, data):
			(self.intHeader, self.fltHeader) = struct.unpack("!H H", data[0:4])
			(self.version) = struct.unpack("!H", data[4:6])[0] 
			
			if (hex(self.intHeader) == "0x4154"):
				(self.pID, self.pForm, self.pktSize, self.context, self.numMods) = struct.unpack("!IBHIB", data[6:18])
			elif (hex(self.intHeader) == "0x5441"):
				(self.pID, self.pForm) = struct.unpack("IB", data[6:11])
				(self.pktSize) = struct.unpack("H", data[11:13])[0]
				(self.context, self.numMods) = struct.unpack("IB", data[13:18])

			self.data = data[18:]

	def printHeader(self):
		print("===============RTTrP Header================")
		print("Integer Signature	:	", hex(self.intHeader))
		print("Float Signature		:	", hex(self.fltHeader))
		print("Version			:	", self.version)
		print("Packet ID		:	", self.pID)
		print("Packet Format		:	", self.pForm)
		print("Packet Size		:	", self.pktSize)
		print("Context			:	", hex(self.context))
		print("Number of Modules	:	", self.numMods)

class RTTrPM():

	def __init__(self, header):
		self.rttrp_head = header
		self.data = header.data
		self.trackable = None #0x01
		self.centroidMod = None #0x02
		self.quatMod = None #0x03
		self.eulerMod = None #0x04
		self.ledMod = [] #0x06
		self.centroidAccVelMod = None #0x20
		self.LEDAccVelMod = [] #0x21

	def printPacket(self):
		self.rttrp_head.printHeader()
		self.trackable.printModule()

		if self.centroidMod:
			self.centroidMod.printModule()

		if self.ledMod:
			for LED in self.ledMod:
				LED.printModule()

		if self.quatMod:
			self.quatMod.printModule()

		if self.eulerMod:
			self.eulerMod.printModule()

		if self.centroidAccVelMod:
			self.centroidAccVelMod.printModule()

		if self.LEDAccVelMod:
			for LED in self.LEDAccVelMod:
				LED.printModule()

class RTTrPL():
	def __init__(self, header):
		self.rttrp_head = header
		self.data = header.data

def openConnection(IP, PORT, isReading, outModules):
	UDP_IP = str(IP)
	UDP_PORT = int(PORT)

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT))

	count = 1
	data = 1 
	addr = 1

	while isReading.isSet():
		data, addr = sock.recvfrom(65535)

		if(data != None and addr != None):
			
			pkt = RTTrP(data)

			try:
				if (hex(pkt.fltHeader) == "0x4334" or hex(pkt.fltHeader) == "0x3443"):
					pkt = RTTrPM(pkt)

					for i in range(pkt.rttrp_head.numMods):
						module = thirdParty_lighting.Trackable(pkt.data, pkt.rttrp_head.intHeader, pkt.rttrp_head.fltHeader)

						pkt.trackable = module
	
						for i in range(module.numMods):
							if (module.data[0] == 2):
								pkt.centroidMod = thirdParty_lighting.CentroidMod(module.data, module.intSig, module.fltSig)
								module.data = pkt.centroidMod.data
							elif (module.data[0] == 3):
								pkt.quatMod = thirdParty_lighting.QuatModule(module.data, module.intSig, module.fltSig)
								module.data = pkt.quatMod.data
							elif (module.data[0] == 4):
								pkt.eulerMod = thirdParty_lighting.EulerModule(module.data, module.intSig, module.fltSig)
								module.data = pkt.eulerMod.data
							elif (module.data[0] == 6):
								pkt.ledMod.append(thirdParty_lighting.LEDModule(module.data, module.intSig, module.fltSig))
								module.data = pkt.ledMod[len(pkt.ledMod)-1].data
							elif (module.data[0] == 32):
								pkt.centroidAccVelMod = thirdParty_lighting.CentroidAccVelMod(module.data, module.intSig, module.fltSig)
								module.data = pkt.centroidAccVelMod.data
							elif (module.data[0] == 33):
								pkt.LEDAccVelMod.append(thirdParty_lighting.LEDAccVelMod(module.data, module.intSig, module.fltSig))
								module.data = pkt.LEDAccVelMod[len(pkt.LEDAccVelMod)-1].data
							else:
								# unknwon packet type, da fuq is this
								exit()
				elif (hex(pkt.fltHeader) == "0x4434" or hex(pkt.fltHeader) == "0x3444"):
					pkt = RTTrPL(pkt)
					sock.close()
					exit()
			except Exception as e:
				print(traceback.print_exc(None))
				continue

			pkt.printPacket()
			print("===========================================")

	sock.close()
