import sys
import os
import re
from datetime import datetime
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSpacerItem, QMainWindow, QFrame, QLineEdit, QSizePolicy, QMessageBox
from PySide6.QtGui import QFont, QGuiApplication, QPalette, QColor, QPixmap, QCursor
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtCore import Qt, QUrl, QTimer, QPoint
from frontend.browser import MicroBrowser
from frontend.styling import get_chop_palette, Colors, regular_font, bold_font, title_font, subtitle_font
from frontend.funcs import set_labels_properties, get_screen_geometry

from backend.main import User, Event, get_column_names, export_table_to_csv
from backend.hash import get_salt_hash
from itertools import islice
from frontend.settings import SettingsGUI


AUTOLOGOUT_TIME = 600000   # milliseconds
INACTIVITY_CHECK_INTERVAL = 1000   #milliseconds

 

# NOTE: Mini GUI and Big GUI are instantiated from the same module (to avoid circular import)
''' --- Mini GUI ---'''
class ContentMiniGui(QFrame):
    def __init__(self):
        super().__init__()
        # self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet("background-color: rgba(138,210,240, 100); border-radius: 5px;")
        self.setStyleSheet("border-radius: 5px;")
        # self.setStyleSheet("border-radius: 5px;")
        self.frame_layout = QHBoxLayout()
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame_layout.setSpacing(0)
        self.setLayout(self.frame_layout)
        # one label (will show User info)
        self.label = QLabel("text will be set in MiniGui")
        self.label.setContentsMargins(5,5,5,5)
        self.label.setStyleSheet("background-color: rgba(200, 200, 200, 255);")
        self.frame_layout.addWidget(self.label) 
        # buttons_layout: holds Logout and Collapse buttons
        self.buttons_layout = QVBoxLayout()     
        self.frame_layout.addLayout(self.buttons_layout)
        # buttons: Logout and Collapse
        self.logout_btn = QPushButton("Logout")         # NOTE: <== is connected in the MiniGui()
        self.hide_btn = QPushButton("Hide")       # NOTE: <== is connected in the MiniGui()
        
        # Creating the Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.settings_btn.setStyleSheet("background-color: rgba(200, 200, 200, 255);")
        self.buttons_layout.addWidget(self.settings_btn)

        # set Logout and Collapse buttons appearance and add them to the layout
        for _ in [self.logout_btn, self.hide_btn, self.settings_btn]: 
            _.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)            
            _.setStyleSheet("background-color: rgba(200, 200, 200, 255);")  # if not used, buttons will be transparent
            self.buttons_layout.addWidget(_)
        self.show()  # <== necessary to calculate correctly the width of the buttons
        button_width = 10  # <= minimum button width
        # calculate the width of the widest button
        for _ in [self.logout_btn, self.hide_btn, self.settings_btn]:
            button_width = max(button_width, _.width()) + 10 # 5 pixels on each side
        # make both buttons of fixed, equal width
        for _ in [self.logout_btn, self.hide_btn, self.settings_btn]:    
            _.setFixedWidth(button_width)

        


class MiniGui(QFrame):
    def __init__(self, curr_user, login_event, config_dict):
        # NOTE: MiniGui needs config_dict for restarting the BigGui
        super().__init__()
        self.autologout_time = AUTOLOGOUT_TIME
        self.inactivity_check_interval = INACTIVITY_CHECK_INTERVAL
        self.ready_to_close = False
        self.login_event = login_event
        self.config_dict = config_dict
        self.curr_user = curr_user
        # self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint)
        # DELTE Qt.tool
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)  # <== QtTool crashes the mini_gui
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.move(0, 500)
        self.width_px = 300                  # mini_gui WIDTH
        self.setFixedWidth(self.width_px)
        self.height_px = 75                  # mini_gui HEIGHT
        self.setFixedHeight = self.height_px
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.is_minimized = False  # flag used to toggle between collapsed and expanded states
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)


        self.content_frame = ContentMiniGui()
        self.content_frame.label.setText(f"<strong>{self.curr_user.name}<br></strong>Email: {self.curr_user.email}<br>phone: {self.curr_user.phone}<br>login: {self.login_event.login_time}")
        self.content_frame.label.setStyleSheet("background-color: rgba(177,225,245, 200);")
        main_layout.addWidget(self.content_frame)
        
        toggle_size_btn = QPushButton('')
        self.toggle_btn_size = 10
        toggle_size_btn.setFixedWidth(self.toggle_btn_size)
        toggle_size_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        toggle_size_btn.setStyleSheet( "background-color: rgba(255, 25, 0, 150); border-radius: 4px;")
        toggle_size_btn.clicked.connect(self.toggle_size)
        main_layout.addWidget(toggle_size_btn)
        self.content_frame.hide_btn.clicked.connect(self.toggle_size)

        self.content_frame.logout_btn.clicked.connect(self.logout_and_start_big_gui)
        # self.content_frame.hide_btn.clicked.connect(self.onMinimize)
        # Connect the Settings button to open the Settings GUI
        self.content_frame.settings_btn.clicked.connect(self.openSettingsGUI)


        # turn on timers when mini_gui starts
        self.turn_on_mini_gui_timers()

    def onMinimize(self):
        self.showMinimized()

    def turn_on_mini_gui_timers(self):
        # Mouse Idle Detection setup
        self.last_mouse_position = QPoint()
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.check_mouse_idle)
        self.idle_timer.start(self.inactivity_check_interval)       # in milliseconds 
        self.total_idle_time_timer = QTimer(self)                   # QTimer to track the TOTAL idle time
        self.total_idle_time_timer.start(self.autologout_time)

    def turn_off_mini_gui_timers(self):
        self.idle_timer.stop()
        self.total_idle_time_timer.stop()
        self.idle_timer.deleteLater()
        self.total_idle_time_timer.deleteLater()

    def toggle_size(self):
        if self.is_minimized:
            self.setFixedWidth(self.width_px)
            self.content_frame.show()
            self.is_minimized = False
        else:     
            self.content_frame.hide()  
            self.setFixedWidth(self.toggle_btn_size) 
            self.is_minimized = True            

    def logout_by_user(self):
        self.login_event.logout_type = 'by_user'
        self.logout_and_start_big_gui()

    def logout_by_inactivity(self):
        self.login_event.logout_type = 'by_inactivity'
        self.logout_and_start_big_gui()

    def logout_and_start_big_gui(self):
        self.logout()
        self.big_gui = BigGui(self.config_dict)
        # fill out the email address of the user who logged out (in case of accidental logout)
        self.big_gui.email_pass_button_frame.email_line_edit.setText(self.curr_user.email)
        self.big_gui.email_pass_button_frame.pass_line_edit.setText("")
        self.big_gui.show()
        self.turn_off_mini_gui_timers()
        self.close()  # Close mini_gui

    # check if the mouse is idle every interval = INACTIVITY_CHECK_MILLISECONDS
    def check_mouse_idle(self):
        current_mouse_position = self.mapFromGlobal(QCursor.pos())
        if current_mouse_position == self.last_mouse_position:
            # If the mouse is idle, increment the idle time 
            self.idle_time += self.idle_timer.interval()
            # Restart the idle time timer to count the idle time
            self.total_idle_time_timer.start(self.idle_timer.interval())
            print('...idle_time: ', int(self.idle_time)/1000, ' seconds', ' ' * 30, end="\r")
            if int(self.idle_time) >= self.autologout_time:
                self.logout_by_inactivity()

        else:                           # if the mouse moved
            self.idle_time = 0          # reset the idle time to 0
            self.total_idle_time_timer.stop() #stop the idle time timer
            
            print(f"...mouse cursor moved to: {current_mouse_position.x()}, {current_mouse_position.y()}",  ' ' * 50, end='\r')

        # Update the last known mouse position
        self.last_mouse_position = current_mouse_position

    def logout(self):
        if self.login_event:
            # Record logout event before closing the MiniGUI
            self.login_event.logout_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.login_event.record_logout()
            
            logout_event_id = self.login_event.lastrowid
            if logout_event_id:
                print(f"Logout successful. Logout event recorded with ID {logout_event_id}")
            else:
                print("Error recording logout event.")
            self.ready_to_close = True

    def closeEvent(self, event):
        if self.ready_to_close:  
            event.accept()  # Allow the window to close
        else:
            event.ignore()  # Keep ignoring
    
    def openSettingsGUI(self):
        self.settingsGUI = SettingsGUI(self.curr_user)
        self.settingsGUI.show()


''' --- Big GUI ---'''
class QFrameWithBoxLayout(QFrame):
    """Used for device_login_panel, login_panel, extra_panel""" 
    def __init__(self, orientation=None, frame_color=None):
        super().__init__()
        self.setContentsMargins(0,0,0,0)
        # set background color
        if frame_color != None:
            self.setStyleSheet(f"background-color: {frame_color}")  

        # add a layout (default orientation = "vertical")
        if orientation == "vertical" or orientation == None:
            self.layout = QVBoxLayout(self) 
        elif orientation == "horizontal":
            self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)


class DevicePanel(QFrame):
    ''' Create a white QFrame with CHOP logo, device_name, _device_type and message'''
    def __init__(self, label_title, label_subtitle):
        super().__init__()   
        spacer_size = 5 # used with setContentsMargins, form top/bottom spacing
        # logo_device_frame = QFrame()
        self.setStyleSheet("background-color: White;")
        
        logo_device_layout = QVBoxLayout(self)  # add layout to self=QFrame
        logo_device_layout.setContentsMargins(0,0,0,30)
        logo_device_layout.addStretch()
        # Create a QLabel to display the CHOP logo
        chop_logo_label = QLabel()
        logo_device_layout.addWidget(chop_logo_label)

        # Get the path of the current Python script
        script_path = os.path.abspath(__file__)
        logo_image_path = os.path.join(os.path.dirname(script_path), "./assets/chop_logo.jpg")
        chop_logo_pixmap = QPixmap(logo_image_path)             # Load the image 
        chop_logo_label.setPixmap(chop_logo_pixmap.scaled(300, 129)) 
        # chop_logo_label.setPixmap(chop_logo_pixmap.scaled(300, 300), Qt.AspectRatioMode.KeepAspectRatio)
        

        chop_logo_label.setAlignment(Qt.AlignCenter)
        chop_logo_label.setContentsMargins(0, spacer_size, 0, spacer_size)

        # Title Label (shows  device_name)
        self.title_label = QLabel(label_title)
        logo_device_layout.addWidget(self.title_label)
        blue_0 = Colors.blue_0.name()
        blue_1 = Colors.blue_1.name()
        self.title_label.setStyleSheet(f"color: {blue_0};")  # CHOP dark blue
        self.title_label.setFont(title_font())

        # Subtitle QLabel (shows  device_type)
        self.subtitle_label = QLabel(label_subtitle)
        logo_device_layout.addWidget(self.subtitle_label)
        self.subtitle_label.setFont(subtitle_font())
        self.subtitle_label.setStyleSheet(f"color: {blue_1};")  # CHOP light blue 
        self.subtitle_label.setContentsMargins(0, spacer_size, 0, spacer_size)
        
        logo_device_layout.addSpacing(100)   

        # message_label
        self.message_label = QLabel("No special anouncements to display.") 
        self.message_label.setStyleSheet("color: gray;") 
        self.message_label.setFont(regular_font())
        spacer_label = QLabel("* * * * *") 
        spacer_label.setStyleSheet("color: gold;")
        # # Set common appearance features for title and subtitle
        for label in [self.title_label, self.subtitle_label, spacer_label, self.message_label]:
            label.setAlignment(Qt.AlignCenter)
            logo_device_layout.addWidget(label)


class EmailPassButtonPanel(QFrame):
    ''' Create a panel with QLabels and QLineEdits and Button
        for entering a email and password
    '''
    def __init__(self, big_gui_ref, config_dict):
        super().__init__()
        self.big_gui_ref = big_gui_ref
        self.config_dict = config_dict
        
        self.setContentsMargins(50,30,50,30)

        # vertical layout that holds the email, password and login button elements
        email_pass_button_status_layout =QVBoxLayout(self)
        email_pass_button_status_layout.addSpacing(50)   
        email_pass_button_layout = QHBoxLayout()
        email_pass_button_status_layout.addLayout(email_pass_button_layout)                                                                         
        # Vertical layout that holds the email and password elements                                        
        email_pass_layout = QVBoxLayout()
        email_pass_button_layout.addLayout(email_pass_layout)

        # email elements (QLabel, QLineEdit)
        email_label = QLabel("Email:")
        self.email_line_edit = QLineEdit()
        self.email_line_edit.setPlaceholderText("type your email address ")

        
        # Horizontal layout that holds the email elements (QLabel and QLineEdit)        
        email_layout = QHBoxLayout()
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_line_edit)

        # Password elements (QLabel, QLineEdit)
        pass_label = QLabel("Password:")
        self.pass_line_edit = QLineEdit()
        self.pass_line_edit.setEchoMode(QLineEdit.Password)  # hide characters 
        self.pass_line_edit.setPlaceholderText(" type your password ")


        # Horiz. layout holds the password elements (QLabel and QLineEdit) 
        pass_layout = QHBoxLayout()       
        pass_layout.addWidget(pass_label)
        pass_layout.addWidget(self.pass_line_edit) 

        #  set color for line edits
        for _ in [self.email_line_edit, self.pass_line_edit]:
            _.setStyleSheet("background-color: rgba(216,240,250,1); \
                              color: rgba(0,105,155,1);\
                              border: 2px solid rgba(216,240,250,1); \
                              border-radius: 5px;")                                     # qss
        
        # Add email_layout, pass_layout to email_pass_layout
        for _ in [email_layout, pass_layout]: email_pass_layout.addLayout(_)
        
        # login button
        login_button = QPushButton("Login")
        button_font = login_button.font()   # get the current font
        button_font.setBold(True)           # make bold
        login_button.setFont(button_font)   # set bold font on login_buttonc


        # Add login button to email_pass_button_layout
        email_pass_button_layout.addWidget(login_button)
        login_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum) 

        # Login status QLabel
        login_status_label = QLabel("")
        login_status_label.setAlignment(Qt.AlignCenter)

        email_pass_button_status_layout.addWidget(login_status_label)
        email_pass_button_status_layout.addSpacing(100)    
        # set width of labels equal (email and password) and set alignment
        set_labels_properties(email_label, pass_label)  

        # Login with iLab button
        self.login_with_ilab_btn = QPushButton("  Login with iLab  ")  # <= connected in BigGui class
        self.login_with_ilab_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        email_pass_button_status_layout.addWidget(self.login_with_ilab_btn)
        email_pass_button_status_layout.setAlignment(self.login_with_ilab_btn, Qt.AlignCenter)  



        # authenticate user
        def gui_authenticate_user():
            print("...recording login event...")
            email = self.email_line_edit.text()
            password = self.pass_line_edit.text()
            print( "email, password:", email, password) 
            user_authenticated = User.authenticate_user(email, password)
            print("user_authenticated:", user_authenticated)
            if user_authenticated:
                # global mini_gui_window
                self.curr_user = User.from_database_by_email(email)
                if self.curr_user:
                    record_login_local_event()
                else:
                    print("Error from gui_authenticate_user(): failed to load user information from database.")
            else:
                print("Error from gui_authenticate_user(): Login failed. Invalid password.")
                login_status_label.setText('<font color="yellow">Login failed. Invalid password</font>')
                return None
            
        def record_login_local_event():
            print("User from db: curr_user.name:", self.curr_user.name)
            if self.curr_user: 
                # Record login event
                self.login_local_event = Event()
                self.login_local_event.email = self.curr_user.email
                self.login_local_event.login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.login_local_event.login_type = 'local'  
                self.login_event_id = self.login_local_event.record_login()   #reminder: record_login() returns lastrowid | None
                print(f"Login successful. Login event recorded with ID {self.login_event_id}")
                if self.login_event_id:
                    self.big_gui_ref.show_mini_gui(self.curr_user, self.login_local_event, self.config_dict)
                else:
                    print("Error recording login event.")
                    return None
                    # Handle the error as needed

        # trigger authenticate_user                
        login_button.clicked.connect(gui_authenticate_user)         # when clicking login    
        self.pass_line_edit.returnPressed.connect(gui_authenticate_user) # when pressing RETURN



        
        # TODO: test is_valid() function!
        def is_valid(email, verify=True):
            email = self.email_line_edit.text()
            # Regular expression for validating an email address
            regex_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            # pass the regular expression and the string into the fullmatch() method
            if(re.fullmatch(regex_email, email)):        
                is_valid = True
            else:
                is_valid =  False
            return is_valid

        
        
        # TODO: test set_status_login_btn()
        def set_status_login_btn():
            email = self.email_line_edit.text()
            # disablelogin button if email address not valid
            if is_valid(email) or email.lower() == "admin" or email == '':
                login_button.setEnabled(True)
                login_button.setStyleSheet('color: white;')
                login_status_label.setText('')
            else:
                login_button.setEnabled(False)
                login_button.setStyleSheet('color: gray;')
                login_status_label.setText('Invalid email.')

        # set the status
        set_status_login_btn()  
        self.email_line_edit.textChanged.connect(set_status_login_btn)



class BigGui(QMainWindow):
    def __init__(self, config_dict):
    # def __init__(self, device_name, device_type, calendar_string, landing_url):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        big_gui_ref = self      # set the reference to big_gui
        self.config_dict = config_dict
        # self.logged_in_iLab_flag = False                                                 # COMMENTED 21DEC2023 1126

        self.landing_url = config_dict["landing_url"]
        # get the geometry of all available screens; cover all screens
        combined_geometry, screen_0_geometry = get_screen_geometry()
        self.setGeometry(combined_geometry)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a QHBoxLayout for the central widget
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignTop)  
        
        ###  DEVICE_LOGIN_PANEL  ###
        ## the DEVICE_LOGIN_PANEL contains: device_panel and login_panel

        device_login_panel = QFrameWithBoxLayout("vertical") 
        main_layout.addWidget(device_login_panel)
        device_login_panel_width = min(500, screen_0_geometry.width() / 3)
        device_login_panel.setMaximumWidth(device_login_panel_width)

        device_panel = DevicePanel(config_dict["device_name"], config_dict["device_type"])
        device_login_panel.layout.addWidget(device_panel)
        device_panel.setFixedHeight(screen_0_geometry.height() * 0.5 )
        
        # qss = consider using qss for formatting
        blue_0 = Colors.blue_0.name()                                                                # <-- qss
        blue_4 = Colors.blue_4.name()                                                                # <-- qss

        login_panel = QFrameWithBoxLayout("vertical")
        device_login_panel.layout.addWidget(login_panel)
           
        login_panel.setStyleSheet(f"background-color: {blue_0}; color: {blue_4};")                  # <-- qss
        
        login_panel.layout.setSpacing(10)

        self.email_pass_button_frame = EmailPassButtonPanel(big_gui_ref, config_dict)  
        login_panel.layout.addWidget(self.email_pass_button_frame)

        # cancel_log_in_with_ilab_btn (this button unhides the local login elements which are hidden durring login with iLab)
        self.cancel_login_with_ilab_btn = QPushButton("  Cancel login with iLab  ") 

        self.browser = MicroBrowser(config_dict, big_gui_ref)
       
        login_panel.layout.addStretch()     # spacing
        

        self.cancel_login_with_ilab_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        login_panel.layout.addWidget(self.cancel_login_with_ilab_btn)
        login_panel.layout.setAlignment(self.cancel_login_with_ilab_btn, Qt.AlignCenter)
        self.cancel_login_with_ilab_btn.hide()


        # [Q]  Quit button (added for convenience while testing)
        btn_quit = QPushButton("       Quit       ")                                    # DELETE in final version
        btn_quit.clicked.connect(QGuiApplication.instance().quit)                       # DELETE in final version
        login_panel.layout.addWidget(btn_quit)                                          # DELETE in final version
        login_panel.layout.setAlignment(btn_quit, Qt.AlignCenter)                       # DELETE in final version
        bottom_spacer = QSpacerItem(20, 50, QSizePolicy.Minimum, QSizePolicy.Fixed)     # DELETE in final version
        login_panel.layout.addItem(bottom_spacer)                                       # DELETE in final version

        ### BROWSER PANEL ###
        browser_layout = QVBoxLayout()
        main_layout.addLayout(browser_layout)
        browser_layout.addWidget(self.browser)
        browser_frame_width = (screen_0_geometry.width() - device_login_panel_width)
        self.browser.setFixedWidth(browser_frame_width)
        self.browser.view.setFixedWidth(0.95 * browser_frame_width)

        ### EXTRA PANEL ###
        extra_panel = QFrameWithBoxLayout("vertical")
        extra_panel.setMaximumWidth(combined_geometry.width() - screen_0_geometry.width())
        main_layout.addWidget(extra_panel)

        self.email_pass_button_frame.login_with_ilab_btn.clicked.connect(self.browser.start_ilab_login)
        self.cancel_login_with_ilab_btn.clicked.connect(self.browser.cancel_ilab_login)
    


    def show_mini_gui(self, user, event, config_dict):
        # start mini_gui close big_gui;    NOTE: in the two lines below: must use 'self.'
        self.mini_gui = MiniGui(user, event, self.config_dict)
        self.mini_gui.show()
        self.close()

