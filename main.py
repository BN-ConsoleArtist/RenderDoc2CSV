import sys, pathlib, csv
from collections import Counter
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (QPlainTextEdit, QLineEdit, QLabel, QApplication, QMainWindow, QPushButton,
                               QFileDialog, QVBoxLayout, QHBoxLayout, QBoxLayout, QWidget, QStyle)



def parse_drawcall(l):
        """ Returns draw calls in format: "Actor Name" ("Material Name")"""
        parsed_line = l.split('|')[1].split('-')[1].strip().split()
        return f'{parsed_line[1]} ({parsed_line[0]})'


def export_csv(f_import, f_export, log_callback=None):

        file_path = pathlib.Path(f_import)
        export_path = pathlib.Path(f_export)

        drawcall_list_Opaque = []
        drawcall_list_Translucency = []
        drawcall_count_opaque = 0
        drawcall_count_translucency = 0
        mobile_base_pass = False
        translucency_pass = False

        log_callback("Opening File...")

     # Open RenderDoc file, parse and store draw call lines into separate Opaque and Translucent lists
        if file_path.is_file():
                with open(file_path, newline='') as file:
                        for line in file:
                                if 'MobileBasePass' in line:
                                        mobile_base_pass = True
                                        continue
                                elif 'Translucency' in line:
                                        translucency_pass = True
                                        continue
                                elif 'DynamicEd' in line:
                                        mobile_base_pass = False
                                        continue
                                elif 'ResolveSubresource' in line:
                                        translucency_pass = False
                                        continue

                                if mobile_base_pass == True and 'DrawIndexed' not in line:
                                        drawcall_list_Opaque.append(parse_drawcall(line))
                                        drawcall_count_opaque += 1
                                if translucency_pass == True and 'DrawIndexed' not in line:
                                        drawcall_count_translucency += 1
                                        drawcall_list_Translucency.append(parse_drawcall(line))

        #Sort lists by frequency of draw calls, store in dictionary (key=actor, value=count)
        log_callback("Sorting Drawcalls by number of occurrences...")
        base_pass_count = Counter(drawcall_list_Opaque).most_common()
        translucency_pass_count = Counter(drawcall_list_Translucency).most_common()

        #Print lists to console
        log_callback(f'\n---------Draw Calls Mobile Base Pass (Total={drawcall_count_opaque}):----------')
        for k,v in base_pass_count:
                print(k,v)

        log_callback(f'\n----------Draw Calls Translucency Pass(Total={drawcall_count_translucency})----------')
        for k,v in translucency_pass_count:
                print(k,v)


        #Export to CSV file
        log_callback("Exporting CSV file...")
        with open(export_path, mode='w', newline='') as f:
                writer = csv.writer(f)

                # Write Opaque Section
                writer.writerow(['Opaque Pass (Total = ' + str(drawcall_count_opaque) + ')', 'Count  '])
                writer.writerows(base_pass_count)

                # Add a spacer row
                writer.writerow([])

                # Write Translucency Section
                writer.writerow(['Translucency Pass (Total = ' + str(drawcall_count_translucency) + ')', 'Count  '])
                writer.writerows(translucency_pass_count)



class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.path_import = "Choose File..."
        self.path_export = "No File Selected"

       # Set the window title and initial size
        self.setWindowTitle("RenderDoc to CSV Exporter")
        self.resize(800, 100)
        self.setStyleSheet("background-color: lightgrey;")

        # Create layout and attributes
        VLayout_main = QVBoxLayout()
        VLayout_main.setDirection(QBoxLayout.Direction.TopToBottom)
        VLayout_main.setSpacing(10)

        HLayout1 = QHBoxLayout()
        HLayout1.setDirection(QBoxLayout.Direction.LeftToRight)
        HLayout2 = QHBoxLayout()
        HLayout2.setDirection(QBoxLayout.Direction.LeftToRight)
        HLayout3 = QHBoxLayout()
        HLayout4 = QHBoxLayout()

        # Create button widgets
        self.folder_button = QPushButton()
        self.folder_button.setFixedSize(32, 32)
        self.folder_button.setStyleSheet("background-color: transparent; border: none;")
        folder_button_style = self.folder_button.style()
        folder_icon = folder_button_style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        self.folder_button.setIcon(folder_icon)
        self.folder_button.setIconSize(QSize(32, 32))
        self.folder_button.clicked.connect(self.get_file)

        self.button2 = QPushButton("Set Export Path")

        self.button3 = QPushButton("Export CSV")
        self.button3.setEnabled(False) #Keep disabled until initial file selected
        self.button3.clicked.connect(lambda: export_csv(self.path_import, self.path_export, self.terminal.appendPlainText))
        self.button3.setFixedSize(200,50)

        # Create file path text widgets
        self.display_path_import = QLineEdit(self.path_import)
        self.display_path_import.setReadOnly(True)
        self.display_path_import.setStyleSheet("background-color: white; border: none;")
        self.display_path_export = QLineEdit(self.path_export)
        self.display_path_export.setReadOnly(True)
        self.display_path_export.setStyleSheet("border-width: 1px; border-style: solid; border-color: rgb(150,150,150);")

        # Create Label Widgets
        self.label1 = QLabel("RenderDoc File: ", self)
        self.label2 = QLabel("CSV File Path : ", self)

        # Create Terminal Widget
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setMaximumBlockCount(100)
        self.terminal.setPlaceholderText('Log Updates...')
        self.terminal.setMinimumHeight(250)
        self.terminal.setStyleSheet("background-color: white;")

        # Assemble the layouts, add widgets, nest HLayouts under VLayout_main
        HLayout1.addWidget(self.label1)
        HLayout1.addWidget(self.display_path_import)
        HLayout1.addWidget(self.folder_button)
        HLayout2.addWidget(self.label2)
        HLayout2.addWidget(self.display_path_export)
        HLayout3.addWidget(self.button3)
        HLayout4.addWidget(self.terminal)

        VLayout_main.addLayout(HLayout1)
        VLayout_main.addLayout(HLayout2)
        VLayout_main.addLayout(HLayout3)
        VLayout_main.addLayout(HLayout4)

        # Create a central widget, set the layout, and apply it to the QMainWindow
        central_widget = QWidget()
        central_widget.setLayout(VLayout_main)
        self.setCentralWidget(central_widget)

    def get_file(self):
        # Browse system folders, set import and export paths, enable the export button
         self.path_import = QFileDialog.getOpenFileName(filter="*.txt")[0] #string type
         self.display_path_import.setText(self.path_import)

         export_path = self.path_import.rsplit('/', 1)[0]
         export_csv = self.path_import.rsplit('/', 1)[1].split('.')[0] + '.csv'
         self.path_export = export_path + '/' + export_csv
         self.display_path_export.setText(self.path_export)

         self.terminal.appendPlainText(self.path_import + " selected...")

         self.button3.setEnabled(True)



if __name__ == "__main__":

    # Create the application instance
    app = QApplication(sys.argv)

    # Create and show the window
    window = Window()
    window.show()

    # Start the event loop
    sys.exit(app.exec())