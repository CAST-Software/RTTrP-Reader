import _thread
import sys
import RTTrP_Reader
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import threading
import subprocess

class MainWindow(QMainWindow):
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)

		self.centralWidget = QTabWidget()
		self.centralWidget.addTab(RTTrPMTab(self), "RTTrPM")
		self.centralWidget.addTab(RTTrPLTab(self), "RTTrPL")
		self.setCentralWidget(self.centralWidget)
		self.setFixedSize(1000, 1000)

		self.setWindowTitle("RTTrP Listener")
	
class RTTrPMTab(QWidget):
	def __init__(self, parent):
		super(RTTrPMTab, self).__init__(parent)

		IP = QLabel("IP:")
		PORT = QLabel("Port:")

		self.submitButton = QCheckBox("Start Listening")
		self.submitButton.setChecked(False)
		self.IP = QLineEdit()
		self.PORT = QLineEdit()
		
		buttonLayout1 = QVBoxLayout()
		buttonLayout1.addWidget(self.submitButton)
		buttonLayout1.addWidget(IP)
		buttonLayout1.addWidget(self.IP)
		buttonLayout1.addWidget(PORT)
		buttonLayout1.addWidget(self.PORT)

		mainLayout = QGridLayout()
		mainLayout.addLayout(buttonLayout1, 0, 1)
		
		self.setLayout(mainLayout)
	
		self.submitButton.clicked.connect(self.startListening)
		self.resizeEvent

	def startListening(self):
		IP = self.IP.text()
		PORT = self.PORT.text()

		if (self.submitButton.isChecked()):
			if (IP == "") or (PORT == ""):
				QMessageBox.information(self, "Empty Field", "Please enter a valid IP and PORT.")
				self.submitButton.setChecked(False)
				return
			else:
				self.submitButton.setText("Stop Listening")
				self.beginReading = threading.Event()
				self.beginReading.set()
				self.reader = threading.Thread(None, RTTrP_Reader.openConnection, None, (IP, PORT, self.beginReading, self.modules))
				self.reader.start()
		elif (not self.submitButton.isChecked()):
			self.submitButton.setText("Start Listening")
			self.beginReading.clear()

class RTTrPLTab(QWidget):
	def __init__(self, parent):
		super(RTTrPLTab, self).__init__(parent)

		IP = QLabel("IP:")
		PORT = QLabel("Port:")

		self.submitButton = QCheckBox("Start Listening")
		self.submitButton.setChecked(False)
		self.IP = QLineEdit()
		self.PORT = QLineEdit()
		
		buttonLayout1 = QVBoxLayout()
		buttonLayout1.addWidget(self.submitButton)
		buttonLayout1.addWidget(IP)
		buttonLayout1.addWidget(self.IP)
		buttonLayout1.addWidget(PORT)
		buttonLayout1.addWidget(self.PORT)

		mainLayout = QGridLayout()
		mainLayout.addLayout(buttonLayout1, 0, 1)
		
		self.setLayout(mainLayout)
	
		self.submitButton.clicked.connect(self.startListening)

	def startListening(self):
		IP = self.IP.text()
		PORT = self.PORT.text()

		if (self.submitButton.isChecked()):
			if (IP == "") or (PORT == ""):
				QMessageBox.information(self, "Empty Field", "Please enter a valid IP and PORT.")
				self.submitButton.setChecked(False)
				return
			else:
				self.submitButton.setText("Stop Listening")
				self.beginReading = threading.Event()
				self.beginReading.set()
				#self.reader = threading.Thread(None, RTTrP_Reader.openConnection, None, (IP, PORT, self.beginReading, self.modules))
				#self.reader.start()
		elif (not self.submitButton.isChecked()):
			self.submitButton.setText("Start Listening")
			self.beginReading.clear()

if __name__ == '__main__':

	app = QApplication(sys.argv)
	screen = MainWindow()
	screen.show()

	sys.exit(app.exec_())
