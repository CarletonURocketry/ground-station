# Filename: hello.py

"""Simple Hello World example with PyQt5."""

import sys


from PyQt5.QtWidgets import QLabel,QHBoxLayout, QComboBox , QMainWindow, QApplication, QWidget, QPushButton, QVBoxLayout,  QAction, QLineEdit, QMessageBox ,QPlainTextEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot , QTimer,QDateTime
from PyQt5.QtWebEngineWidgets import QWebEngineView
import io 
import folium
import packet 
import datetime
import GroundStation


# 2. Create an instance of QApplication
def init_UI():
    #make the UI window
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('MCnominal UI')
    window_width, window_height = 1600, 1200
    window.setMinimumSize(window_width, window_height)

    textbox = QPlainTextEdit(window)
    textbox.move( 1500,10)
    textbox.resize(400,400)
     

    # update the window with this method takes the dictionary and sends it to
    def update_label():
        textbox.clear()
        #somehow poll the system and get the packet 
        data = packet.test_sending_data()
        info = ''
        for key, value in data.items():
            info += key +' : ' + str(value) 
            info += "\n"
        
        textbox.insertPlainText(info)


     # button to configure radio one push to do inital setup  
    cfgRadioButton = QPushButton(window)
    cfgRadioButton.setText("configure radio")
    cfgRadioButton.clicked.connect(cfgRadioButton_clicked)
    cfgRadioButton.move(1200,100)
    
    # configure the specific parameters which have a set amount of values 
    button2 = QPushButton(window)
    button2.setText("configure specific parameters ")
    sub_window = SubWindow()
    button2.clicked.connect(sub_window.show)
    button2.move(1200,200)
    
    #configure preamble 
    configbtn = QPushButton(window)
    configbtn.setText("configure preamble")
    pre_window = preambleWindow()
    configbtn.clicked.connect(pre_window.show)
    configbtn.move(1200,300)

    #configure the power button 
    pwrconfigbtn = QPushButton(window)
    pwrconfigbtn.setText("configure power")
    pwr_window = powerWindow()
    pwrconfigbtn.clicked.connect(pwr_window.show)
    pwrconfigbtn.move(1200,400)
   
   
    
    # set the cooridnates
    coordinate = (	32.5925, -106.5811)
   
    m = folium.Map(
        tiles='Stamen Terrain',
        zoom_start=13,
        location=coordinate
    )

    # save map data to data object
    data = io.BytesIO()
    m.save(data, close_file=False)
    
    #show the map 
    webView = QWebEngineView(window)
    webView.setHtml(data.getvalue().decode())
    webView.resize(1000,1000)
    webView.show()
    
    #set the update rate of our telemetry system 
    timer = QTimer()
    timer.timeout.connect(update_label)
    timer.start(100)  # every 10,000 milliseconds
    window.show()
 

    sys.exit(app.exec_())
def cfgRadioButton_clicked():
    #can't test without radio 
  # groundradio.init_ground_station() 
    print("config complete") 


def button_config_pressed():
  print("init window ")
  sub_window = SubWindow()
  sub_window.show()
 
    
class SubWindow(QWidget):
     def __init__(self):
        super(SubWindow, self).__init__()
        self.resize(400, 300)

         
        # Label
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        self.settingstate = QComboBox()
       # turn the array of frequencies into strings
        arr = [250000, 125000, 62500.0, 31300.0, 15600.0, 7800.0, 3900.0, 200000, 100000, 50000, 25000, 12500.0, 6300.0, 3100.0, 166700.0, 83300.0, 41700.0, 20800.0, 10400.0, 5200.0, 2600.0] 
        freqarr=[]             
        for i in arr:
            freqarr.append(str(i))
        self.settingstate.addItem('radio set freq ', freqarr)
        self.settingstate.addItem('radio set freq ', ["sf7", "sf8", "sf9", "sf10", "sf11", "sf12"])
       
        # set the settings for cycling rate bandwidth and iqi values 
        self.settingstate.addItem('radio set cr ', ["4/5", "4/6", "4/7", "4/8"])
        self.settingstate.addItem('radio set bw ',[str(125), str(250), str(500)] )
        self.settingstate.addItem('radio set iqi ',["on", "off"] )
        
        
        #add the combo 
        layout.addWidget(self.settingstate)
			
        self.comboCity = QComboBox()
        layout.addWidget(self.comboCity)

        self.settingstate.currentIndexChanged.connect(self.updateSettingsCombo)
        self.updateSettingsCombo(self.settingstate.currentIndex())
        button1 = QPushButton()
        button1.setText("Button1")
        #send the settings to the radio does not work without one 
        def send():
            print(self.settingstate.currentText() + self.comboCity.currentText())
        button1.clicked.connect(send)
        layout.addWidget(button1)

         
    
     def updateSettingsCombo(self, index):
         self.comboCity.clear()
         cities = self.settingstate.itemData(index)
         if cities:
             self.comboCity.addItems(cities)
       
     
     
class preambleWindow(QWidget):
     def __init__(self):
        super(preambleWindow, self).__init__()
        self.resize(500,500)

    
        layout = QHBoxLayout()
        self.setLayout(layout)
        # box to enter preamble number 
        self.textbox = QLineEdit(self)
        self.textbox.move(20, 20)
        self.textbox.resize(280,40)
        
        layout.addWidget(self.textbox)
        button1 = QPushButton()
        button1.setText("Button1")
        layout.addWidget(button1)
        def send():
            # will set preamble length 
            print("radio set pr "+self.textbox)
        button1.clicked.connect(send)
class powerWindow(QWidget):
     def __init__(self):
        super(powerWindow, self).__init__()
        self.resize(500,500)

         # Label
        layout = QHBoxLayout()
        self.setLayout(layout)
        #text entry for power
        self.textbox = QLineEdit(self)
        self.textbox.move(20, 20)
        self.textbox.resize(280,40)
        #textbox to set the pwoer 
        layout.addWidget(self.textbox)
        button1 = QPushButton()
        button1.setText("Button1")
        layout.addWidget(button1)
        
        def send():
            print("radio set pr "+self.textbox)
        button1.clicked.connect(send)

        
def  main(): 
    init_UI()
if __name__ == "__main__":
    main()
