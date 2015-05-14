import socket
import binascii
import struct
import thirdParty_lighting
import traceback

# Main class for the packet header, to keep things simply we just leave this as a generic class
# we won't derive sub-classes from here.
class RTTrP:

	def __init__(self, data):
			# Unpack the signature fields from the packet, followed by the packet version, these are ALWAYS
			# in network (Big Endian) order.
			(self.intHeader, self.fltHeader) = struct.unpack("!H H", data[0:4])
			(self.version) = struct.unpack("!H", data[4:6])[0] 
			
			# Determine Endianness. In general all x86-64 machines are Little Endian, this gets confusing because
			# Tracking Adapter can send in Big/Little Endian format. This means if values are sent as Big Endian from
			# Tracking Adapter, they are still represented in Little Endian by the OS, so we need to instruct
			# "unpack" to treat the values as Big Endian. For Little Endian, we just read values straight from the
			# packet without worrying about byte order.
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
		""" 	Header:	RTTrP header, with data attached 
				
				Description:

				This function initializes the RTTrPM packet, with the header values from
				the RTTrP module passed in. All other values are extracted byte by byte.
		"""
				
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
	"""
		IP:			The IP to listen on for RTTrPM packets
		Port:		The Port to listen on for RTTrPM packets from the given IP
		isReading:	A signal for the thread running this function, when triggered, the connection will close
		OutModules:	TBD, will be used to update fields in the GUI

		Description:
					
					This function is where the packets are read in and split into their
					various modules. It will determine the type of packet and begin
					disecting it into its various modules (depending on what is present).
	"""

	UDP_IP = str(IP)
	UDP_PORT = int(PORT)

	# Create the socketm then bind it to the (IP, PORT) pair
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT))

	count = 1
	data = 1 
	addr = 1

	# So long as the signal is set, then we will continue to listen on the given (IP, PORT) socket
	while isReading.isSet():
		# Set the size of the buffer to the maximum UDP packet size, and retrieve the data sent
		data, addr = sock.recvfrom(65535)

		if(data != None and addr != None):
			
			# Create the RTTrP header
			pkt = RTTrP(data)

			try:
				# If we have an RTTrPM packet, begin to extract the components
				if (hex(pkt.fltHeader) == "0x4334" or hex(pkt.fltHeader) == "0x3443"):
					pkt = RTTrPM(pkt)

					# After determining the number of trackables (listed in the RTTrP header) we begin to extract
					# each trackable from the packet and return it to the GUI
					for i in range(pkt.rttrp_head.numMods):
						module = thirdParty_lighting.Trackable(pkt.data, pkt.rttrp_head.intHeader, pkt.rttrp_head.fltHeader)

						pkt.trackable = module
	
						# For each trackable, we need to extract each module. Keep in mind when dealing with LED modules, each
						# individual LED is considered it's own separate module, so we don't need to worry about
						# modules within modules, except in the case of a Trackable.
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
				elif (hex(pkt.fltHeader) == "0x4434" or hex(pkt.fltHeader) == "0x3444"): # TODO: Create the RTTrPL code that reads an RTTrPL packet
					pkt = RTTrPL(pkt)
					sock.close()
					exit()
			except Exception as e:
				print(traceback.print_exc(None))
				continue

			pkt.printPacket()
			print("===========================================")

	sock.close()
