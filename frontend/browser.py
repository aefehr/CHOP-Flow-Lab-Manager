from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QFrame, QLabel, QSpacerItem, QVBoxLayout, QHBoxLayout, QWidget, QProgressBar, QSizePolicy
from PySide6.QtCore import Qt, QUrl, Signal, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from backend.main import User, Event, get_id_of_most_recent_user, conn_cores_db
from backend.hash import get_salt_hash
from datetime import datetime
from frontend.funcs import make_js_code_for_get_property_with_xpath, set_labels_properties



class MicroBrowser(QMainWindow):
    # Custom signal emitting a string   
    # args_for_mini_gui = Signal(tuple)    # EMITTER 

    def __init__(self, config_dict, big_gui_ref):
        super().__init__()
        # class variables 
        self.config_dict = config_dict
        self.big_gui_ref = big_gui_ref
        self.device = config_dict['device_name']
        self.landing_url = config_dict['landing_url']
        self.calendar_url = config_dict['calendar_url']
        check_timer_interval = 1000
        timeout_timer_interval = 100000
        self.profile_info = {}      # dictionary to store profile info
        # QTimers
        self.check_timer = QTimer()
        self.check_timer.setInterval(check_timer_interval)
        self.timeout_timer = QTimer()
        self.timeout_timer.setInterval(timeout_timer_interval)  # 100 seconds timeout
        self.timeout_timer.setSingleShot(True)  # Only trigger once
        # GUI elements
        self.view = QWebEngineView()     
        self.url_bar = QLineEdit()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(5)
        self.progress_bar.setTextVisible(False)
        self.back_button = QPushButton("←")
        self.forward_button = QPushButton("→")
        self.home_button = QPushButton("🏠")    # other symbol "⌂"
        self.go_button = QPushButton("▶")
        self.login_with_ilab = QPushButton(" Login with iLab ")
        self.registration_panel_ilab = Registration_Panel_iLab()           # <--IMPORTED!

        # Connect signals
        self.registration_panel_ilab.set_pass_btn.clicked.connect(self.save_user_to_database)  # NOTE: connect button in registration panel
        self.registration_panel_ilab.set_cancel_btn.clicked.connect(self.hide_ilab_registration_panel)
        self.back_button.clicked.connect(self.view.back)
        self.forward_button.clicked.connect(self.view.forward)
        self.go_button.clicked.connect(self.navigate_to_url)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.view.urlChanged.connect(self.update_url)
        self.view.loadStarted.connect(lambda: self.progress_bar.setVisible(True))
        self.view.loadProgress.connect(self.progress_bar.setValue)
        self.home_button.clicked.connect(self.navigate_home)
        self.login_with_ilab.clicked.connect(self.start_ilab_login)

        self.view.loadFinished.connect(self.on_load_finished)
        self.check_timer.timeout.connect(self.check_if_logged_in)
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.statusBar().setStyleSheet("QStatusBar { color: dark-gray; }")
        self.statusBar().showMessage("Click [Login with iLab] button. After logging in, you will be prompted to set a password for faster access when you log in next time.")

        browser_layout = QVBoxLayout()
        
        buttons_layout = QHBoxLayout()  # Buttons/address bar layout
        self.buttons_list = [   self.back_button, 
                                self.forward_button, 
                                self.home_button, 
                                self.url_bar, 
                                self.go_button, 
                                self.login_with_ilab
                                ]
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for _ in self.buttons_list:
            _.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum),
            _.setStyleSheet("padding: 1px 5px;")  # first value is for vertical padding
            buttons_layout.addWidget(_)
        

        #  over-ride style sheet for login button
        self.login_with_ilab.setStyleSheet("background-color: rgb(33,133,208); color: white; padding: 1px 12px;")

        self.url_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)  # over-ride SizePolicy for address bar
        
        browser_layout.addLayout(buttons_layout)
        browser_layout.addWidget(self.view)
        browser_layout.addWidget(self.registration_panel_ilab)
        browser_layout.setAlignment(self.registration_panel_ilab, Qt.AlignCenter)

        browser_layout.addWidget(self.progress_bar)
        browser_layout.setAlignment(Qt.AlignCenter)
        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(browser_layout)
        self.setCentralWidget(central_widget)

        # Hide registration panel when the instance is generated 
        self.hide_ilab_registration_panel()   

        # open the calendar of the device
        self.navigate_home()

    def show_ilab_registration_panel(self):
        self.registration_panel_ilab.show()
        self.view.hide()
        self.progress_bar.hide()
        for _ in self.buttons_list: _.hide()     # hide the buttons and url bar at the top of the browser
        

    def hide_ilab_registration_panel(self):
        self.view.show()
        self.progress_bar.show()
        for _ in self.buttons_list: _.show()
        self.registration_panel_ilab.hide()
        

    def on_load_finished(self, ok):
        if ok:        
            self.progress_bar.setVisible(False)

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url
        self.view.setUrl(url)

    def update_url(self, url):  # <= triggered when set url changes
        self.url_bar.setText(url.toString())
    
    def set_browser_url(self, url):
        self.url_bar.setText(url)
        self.navigate_to_url()

    def navigate_home(self):
        home_url = self.calendar_url 
        self.set_browser_url(home_url)

    # LOGIN SPECIFIC FUNCTIONS        
    def start_ilab_login(self):
        self.url_bar.setText(self.landing_url)
        self.navigate_to_url()
        # hide buttons at the top of the browser
        for _ in self.buttons_list:
            _.hide()
        self.big_gui_ref.cancel_login_with_ilab_btn.show()

        self.statusBar().showMessage("Enter your iLab credentials to log in iLab...")
        self.big_gui_ref.email_pass_button_frame.hide()   #  hide the frame with email, password & login button

        self.view.loadFinished.connect(self.start_timers)

    def cancel_ilab_login(self):
        self.url_bar.setText(self.calendar_url)
        self.navigate_to_url()
        # show buttons at the top of the browser
        for _ in self.buttons_list:
            _.show()
        self.big_gui_ref.cancel_login_with_ilab_btn.hide()
        self.big_gui_ref.email_pass_button_frame.show()
        self.statusBar().showMessage("Enter your iLab credentials to log in iLab...")
        self.big_gui_ref.email_pass_button_frame.show()   #  hide the frame with email, password & login button
        self.hide_ilab_registration_panel()
        self.stop_timers(self)

    def start_timers(self):
        self.check_timer.start()
        self.timeout_timer.start()
        print("Login started...  ")
        self.view.loadFinished.disconnect(self.start_timers)     

    def on_timeout(self):
        print("Timeout occurred. Stop checking for login elements")
        self.stop_timers()
        self.navigate_home()
    
    def stop_timers(self):
        self.check_timer.stop()
        # self.check_timer.deleteLater()
        self.timeout_timer.stop()
        # self.timeout_timer.deleteLater()


    def check_if_logged_in(self):
        print("check_if_logged_in(self):... looking for user_dropdown element")
        js_code = """document.querySelector("div#user_dropdown").innerText"""                # <== WORKS # xpath_string = "//div/div[@id='user_dropdown']"
        self.view.page().runJavaScript(js_code, 0, self.handle_check_if_logged_in_result)    # <== WORKS 

    def handle_check_if_logged_in_result(self, result):
        print("handle_check_if_logged_in_result(self, result) -->", result, "<--")
        #  user is logged in if "div#user_dropdown" is found (result is not None)
        if result:
            self.stop_timers()
            self.goto_profile_page()
        else:
            print("user_dropdown element not found <=> not logged in.")

    def goto_profile_page(self):
        print("goto_profile_page(self):")
        profile_url = self.view.url().toString().split(".com/")[0] + ".com/about/show_profile"
        print("profile_url:", profile_url)
        self.view.loadFinished.connect(self.get_profile_info)
        self.set_browser_url(profile_url)

    def get_profile_info(self):
        print("get_profile_info(self):")
        for _ in ['name', 'email', 'phone', 'title']:
            js_code = make_js_code_for_get_property_with_xpath(f"//div/label[@for='{_}']/..", 'textContent')
            self.view.page().runJavaScript(js_code, 0, self.profile_handler)
    
    def profile_handler(self, result):
        print("profile_handler(self, result):", result)
        result_list = result.split("\n")
        for _ in range(len(result_list)):
            print(f"result_list[{_}]:", result_list[_])
        # NOTE: self.profile_info is a dictionary:  e.g. self.profile_info['Email'] = 'user@chop.edu'
        self.profile_info[result_list[1]] = (result_list[2].strip() + " " + result_list[3].strip()).strip()
        print("Profile info:", self.profile_info)
        if 'Title' in self.profile_info.keys():
        # if result_list[1] == "Title":  # NOTE: `Title` is the last item in the profile
            self.stop_timers()
            # self.navigate_home()
            
            
            user_name = self.profile_info["Name"]
            user_email = self.profile_info["Email"]
            # set the formatted text for user_name and user_email in the registration panel 
            self.registration_panel_ilab.user_info_label.setText(f"<i>&nbsp;user:</i>&nbsp;&nbsp;&nbsp;<b>{user_name}</b> <br> <i>email:</i>&nbsp;&nbsp;&nbsp;</><b>{user_email}</b>")
            self.show_ilab_registration_panel()


             

    def save_user_to_database(self):
        # check if there is an existing user registered with the email address
        user_email = self.profile_info['Email']
        user_id = get_id_of_most_recent_user(user_email)
        password = self.registration_panel_ilab.pass_1.text()
        if user_id:   # user found
            print(f'User with email: {user_email} already registered with id: {user_id}.')
            self.new_user = None
            self.existing_user = User.from_database(user_id)
                # replace existing info with current info
            self.existing_user.name = self.profile_info['Name']
            self.existing_user.phone = self.profile_info['Phone']
            self.existing_user.email = self.profile_info['Email']
            self.existing_user.title = self.profile_info['Title']
            self.existing_user.last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.existing_user.last_mod = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.existing_user.last_mod_type = 'iLab'
            self.existing_user.salt, self.existing_user.hash = get_salt_hash(self.existing_user.email, password)

            properties_to_update = ['name', 'title', 'phone', 'last_mod_type', 'last_mod', 'last_login', 'salt', 'hash']
            for _ in properties_to_update:
                self.existing_user.update_user_property(self.existing_user.id, _, self.existing_user.__dict__[_])

            print(f"User {self.existing_user.name} on row {user_id} has been updated.")
            
        else:   # user is new
            self.existing_user = None
            self.new_user = User()
            self.new_user.name = self.profile_info['Name']
            self.new_user.phone = self.profile_info['Phone']
            self.new_user.email = self.profile_info['Email']
            self.new_user.title = self.profile_info['Title']
            self.new_user.last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.new_user.last_mod = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.new_user.last_mod_type = 'iLab'
            self.new_user.first_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.new_user.salt, self.new_user.hash = get_salt_hash(self.new_user.email, password)
            row_id = self.new_user.add_user()
            # print(f"User added successfully on row {row_id}.")  # <-- printed by add_user() function

        self.record_login_ilab_event()  # record login EVENT

    def record_login_ilab_event(self):
        print('Recording login event ...')
        # Create an instance of Event and fill in the event details
        ilab_login_event = Event()
        ilab_login_event.email = self.profile_info['Email']
        ilab_login_event.device = self.device
        ilab_login_event.login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ilab_login_event.login_type = 'iLab'
        self.login_event_id = ilab_login_event.record_login()  # record login event to database

        # the if statements below are for merging `self.new_user` and `self.existing_user` into `current_user`
        if self.login_event_id:
            if self.new_user:
                current_user = self.new_user
            elif self.existing_user:
                current_user = self.existing_user
            else:
                print("Error fe_browser: current user = None ")
            
            self.big_gui_ref.show_mini_gui(current_user, ilab_login_event, self.config_dict)
        else:
            print("Error recording login event.")
            return None
            # Handle the error as needed




class Registration_Panel_iLab(QFrame):
    def __init__(self):  
        super().__init__() 
        # self.setStyleSheet("background-color: pink;")
        # NOTE: self is a QFrame!!!
        self.setMaximumWidth(600)
        # self.setStyleSheet("background-color: LightBlue;")

        # set layout for new password (QLabels, QLineEdits) and buttons (Set Password and Cancel)         
        self.user_name = 'name placeholder'
        self.user_email = 'email placeholder'
        self.user_phone = 'phone placeholder'
        self.title = 'title placeholder'
        new_pass_btn_layout = QVBoxLayout(self)
        new_pass_btn_layout.setAlignment(Qt.AlignCenter)
        new_pass_btn_layout.setSpacing(5)
        new_pass_btn_layout.addStretch()
        iLab_login_success_label = QLabel("<strong>iLab login successful!</strong>")
        new_pass_btn_layout.addWidget(iLab_login_success_label, alignment=Qt.AlignCenter)
        # use formatted text for the user_info_label 
        self.user_info_label = QLabel(f"<i>&nbsp;User:</i>&nbsp;&nbsp;&nbsp;<b>{self.user_name}</b> <br> <i>Email:</i>&nbsp;&nbsp;&nbsp;</><b>{self.user_email}</b>")
        new_pass_btn_layout.addWidget(self.user_info_label, alignment=Qt.AlignCenter)


        instruction_label = QLabel("\nSet up a password for faster access when you will log in next time.")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("color: gray;")
        new_pass_btn_layout.addWidget(instruction_label)

        # Add a spacer 
        spacer_item = QSpacerItem(1, 7, QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_pass_btn_layout.addItem(spacer_item)

        h_layout = QHBoxLayout()
        new_pass_btn_layout.addLayout(h_layout)
        pass_1_pass_2_layout = QVBoxLayout()
        h_layout.addLayout(pass_1_pass_2_layout)
        pass_1_layout = QHBoxLayout()
        pass_2_layout = QHBoxLayout()
        pass_1_pass_2_layout.addLayout(pass_1_layout)
        pass_1_pass_2_layout.addLayout(pass_2_layout)

        label_1 = QLabel("Password:")
        self.pass_1 = QLineEdit()

        # pass_1.setStyleSheet("background-color: LightBlue;")
        self.pass_1.setPlaceholderText("enter password ... ")
        label_2 = QLabel("Re-enter password:")
        self.pass_2 = QLineEdit()
        self.pass_2.setPlaceholderText("re-enter password ... ")
        for _ in [self.pass_1, self.pass_2]: _.setEchoMode(QLineEdit.Password)
        set_labels_properties(label_1, label_2)

        for _ in [self.pass_1, self.pass_2]: _.setStyleSheet("background-color: White;")
        for _ in [label_1, self.pass_1]: pass_1_layout.addWidget(_)        
        for _ in [label_2, self.pass_2]: pass_2_layout.addWidget(_)


        self.set_pass_btn = QPushButton("Set password")                                  # <-- set font bold qss 
        self.set_pass_btn.setEnabled(False)      
        h_layout.addWidget(self.set_pass_btn)
        self.set_pass_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum) 
        self.set_cancel_btn = QPushButton("Cancel")                                      # <-- set font bold qss
        h_layout.addWidget(self.set_cancel_btn)
        self.set_cancel_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum) 
        
        
        # Define a list of restricted characters in password
        self.restricted_chars = ['[', "[", "*", "{", "}", "'", '\\', "|", "$"]      # """[]{}*'\|$"""
        restricted_chars_text = "Restricted characters:  " + """] [ } { * ' \ | $ """
        self.restricted_characters_label = QLabel(restricted_chars_text, alignment=Qt.AlignCenter) 
        self.restricted_characters_label.setStyleSheet("color: darkred;")
        self.restricted_characters_label.hide()
        
        new_pass_btn_layout.addWidget(self.restricted_characters_label)

        # warning when the passwords do not match
        self.password_mismatch_label = QLabel(" ", alignment=Qt.AlignCenter) 
        self.password_mismatch_label.setStyleSheet("color: red;")
        new_pass_btn_layout.addWidget(self.password_mismatch_label)
        # Connect the editingFinished signal to a custom function
        # self.pass_1.editingFinished.connect(self.on_line_edit_finished)
        # self.pass_2.editingFinished.connect(self.on_line_edit_finished)
        self.pass_1.textChanged.connect(self.on_line_edit_changed)
        self.pass_2.textChanged.connect(self.on_line_edit_changed)
        # self.set_pass_btn.clicked.connect(...)  <== connected in fe_browser
        self.set_cancel_btn.clicked.connect(self.cancel)

        # Add a spacer 
        spacer_item = QSpacerItem(1, 10, QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_pass_btn_layout.addItem(spacer_item)
        
        error_message_label = QLabel("")
        error_message_label.setStyleSheet("color: red;")
        confirmation_text = f"Click <strong>Cancel</strong> if the information listed above is incorrect. <br> Click <Strong>Set password</strong> to continue..."
        confirmation_label = QLabel(confirmation_text, alignment=Qt.AlignCenter)
        new_pass_btn_layout.addWidget(confirmation_label)          
        new_pass_btn_layout.addStretch()

    def cancel(self):
        self.pass_1.setText('')
        self.pass_2.setText('')
        self.hide()

    def on_line_edit_changed(self, text):
        # do not show the mismatch red label if user is typing
        # Check if the last typed character is in the list of restricted characters
        self.restricted_characters_label.hide()
        last_char = text[-1] if text else ''
        if last_char in self.restricted_chars:
            # Remove the last typed character if it is restricted
            self.pass_1.setText(text[:-1])
            self.restricted_characters_label.show()
        self.password_mismatch_label.setText(" ")

        if self.pass_1.text() == self.pass_2.text():
            self.set_pass_btn.setEnabled(True)
            self.password_mismatch_label.setText(" ")
        elif self.pass_1.text() != self.pass_2.text():
            self.set_pass_btn.setEnabled(False)
            self.password_mismatch_label.setText("The paswords are not identical.")             


if __name__ == "__main__":
    # main()
    

    config_dict = { "device_name"   :   "Aurora A",
                    "device_type"   :   "Spectral analyzer",
                    # "calendar_url"  :   "https://my.ilabsolutions.com/schedules/454376#/schedule/",
                    # "calendar_url"  :   "https://www.example.com",
                    "calendar_url"  :   "https://my.ilabsolutions.com/account/login",
                    # "landing_url"  :   "https://chop.ilab.agilent.com/landing/101",
                    "landing_url"   :   "https://my.ilabsolutions.com/account/login" }
    app = QApplication()
    app.setStyle("Fusion")
    user_info =[]
    
     
    fe_browser = MicroBrowser(config_dict)
    # connect_user_profile_to_handle(fe_browser)
    

    fe_browser.show()
    app.exec()






