# Filename: hello.py

"""Simple Hello World example with PyQt5."""

import sys


from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QAction, QLineEdit, QMessageBox ,QPlainTextEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot , QTimer,QDateTime
from PyQt5.QtWebEngineWidgets import QWebEngineView
import io 
import folium
import packet 
import datetime
# 2. Create an instance of QApplication
def init_UI():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('PyQt5 App')
    window_width, window_height = 1600, 1200
    window.setMinimumSize(window_width, window_height)

    textbox = QPlainTextEdit(window)
    textbox.move( 1500,10)
    textbox.resize(400,400)
     


    def update_label():
        textbox.clear()
        data = packet.test_sending_data()
        info = ''
        for key, value in data.items():
            info += key +' : ' + str(value) 
            info += "\n"
        
        textbox.insertPlainText(info)
    
    coordinate = (	32.5925, -106.5811)

    m = folium.Map(
        tiles='Stamen Terrain',
        zoom_start=13,
        location=coordinate
    )

    # save map data to data object
    data = io.BytesIO()
    m.save(data, close_file=False)
    

    webView = QWebEngineView(window)
    webView.setHtml(data.getvalue().decode())
    webView.resize(1000,1000)
    webView.show()
    print(m)



    timer = QTimer()
    timer.timeout.connect(update_label)
    timer.start(100)  # every 10,000 milliseconds
    # 4. Show your application's GUI
    window.show()
 

    # 4. Show your application's GUI

    # 5. Run your application's event loop (or main loop)
    sys.exit(app.exec_())


def  main(): 
    init_UI()
if __name__ == "__main__":
    main()
