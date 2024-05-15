from datetime import datetime
from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QMessageBox, QTabWidget, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt
from backend.main import User, get_column_names, export_table_to_csv
from backend.hash import get_salt_hash
from itertools import islice

class EditUserGUI(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Edit User")
        layout = QVBoxLayout()

        # Initialize self.fields as a dictionary
        self.fields = {}
        for key, value in islice(self.user_data.items(), 1, 9):
            layout.addWidget(QLabel(f"{key.capitalize()}:"))
            edit = QLineEdit()
            edit.setText(str(value))
            layout.addWidget(edit)
            self.fields[key] = edit  

        self.update_button = QPushButton("Update User")
        self.update_button.setFixedSize(self.update_button.sizeHint())
        self.update_button.clicked.connect(self.on_update_user)
        layout.addWidget(self.update_button)

        self.status_label = QLabel("")  
        self.status_label.setAlignment(Qt.AlignCenter)  
        layout.addWidget(self.status_label) 

        self.setLayout(layout)

    def on_update_user(self):
        email = self.user_data['email']
        
        # Use from_database_by_email to get the user instance including the row_id
        user_instance = User.from_database_by_email(email)

        # Extract the row_id from the user_instance
        row_id = getattr(user_instance, 'id', None)
        
        if not row_id:
            self.status_label.setText('<font color="red">Could not find user ID.</font>')
            return
        
        for key in list(self.fields.keys())[1:9]:  
            # Set field value to None if empty, otherwise use the field's text
            new_value = self.fields[key].text() or None
            # Use the row_id with the update_user_property method to update each property
            success = user_instance.update_user_property(row_id, key, new_value)
            
            if not success:
                # Handle the case where the update fails
                self.status_label.setText(f'<font color="red">Failed to update {key}.</font>')
                return

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Finally, update 'last_mod' to current time
        success = user_instance.update_user_property(row_id, 'last_mod', current_time)
        if success:
            self.status_label.setText('<font color="green">User updated successfully.</font>')
        else:
            self.status_label.setText('<font color="red">Failed to update last modification time.</font>')
        


class AddUserGUI(QWidget):
    def __init__(self, email=None):
        super().__init__()
        self.email = email
        # Fetch column names for the 'users' table, excluding the first column ('id') and take next 8
        self.column_names = get_column_names("users")[1:9]
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Add New User")
        layout = QVBoxLayout()

        self.fields = {}
        # Create fields for user attributes based on the column names from the database
        for column_name in self.column_names:
            layout.addWidget(QLabel(f"{column_name.capitalize()}:"))
            edit = QLineEdit()
            # If the column is 'email', and an email was passed in, set its text to the passed-in email
            if column_name == 'email' and self.email:
                edit.setText(self.email)
            self.fields[column_name] = edit
            layout.addWidget(edit)

        self.add_button = QPushButton("Add User")
        self.add_button.setFixedSize(self.add_button.sizeHint())
        self.add_button.clicked.connect(self.on_add_user)
        layout.addWidget(self.add_button)

        self.status_label = QLabel("")  
        self.status_label.setAlignment(Qt.AlignCenter)  
        layout.addWidget(self.status_label) 

        self.setLayout(layout)

    def on_add_user(self):
        # Collect data from fields, setting empty fields to None
        new_user_data = {key: (edit.text() if edit.text() else None) for key, edit in self.fields.items() if key != "password"}
        
        # Handle password separately to generate salt and hash
        # Check if email is not None before attempting to hash the password
        if new_user_data['email']:
            password = 'chop1234'
            salt, hash_ = get_salt_hash(new_user_data['email'], password)
            
            # Update the user data with salt and hash instead of the password
            new_user_data.update({'salt': salt, 'hash': hash_})
        else:
            # If email is None or empty, show an error and return early
            self.status_label.setText('<font color="red">Email is required.</font>')
            return
        
        # Set the 'last_mod' field to the current time
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_user_data['last_mod'] = current_time
        
        # Use the User class method to add a new user to the database
        new_user = User()
        for key, value in new_user_data.items():
            setattr(new_user, key, value or None)
        row_id = new_user.add_user() 
        
        if row_id:
            self.status_label.setText('<font color="green">User added successfully.</font>')
        else:
            self.status_label.setText('<font color="red">Failed to add new user.</font>')
        


class AddOrEditUserGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Add or Edit User")
        layout = QVBoxLayout()

        desc = QLabel("Add a new user or edit existing user information.")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # Email field
        layout.addWidget(QLabel("User Email:"))
        self.email_edit = QLineEdit()
        layout.addWidget(self.email_edit)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Buttons
        self.lookup_button = QPushButton("Look up user")
        self.lookup_button.setFixedSize(self.lookup_button.sizeHint())
        self.add_button = QPushButton("Add user")
        self.add_button.setFixedSize(self.add_button.sizeHint())
        self.lookup_button.clicked.connect(self.on_lookup_user)
        self.add_button.clicked.connect(self.on_add_user)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.lookup_button)
        buttons_layout.addWidget(self.add_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def on_lookup_user(self):
        email = self.email_edit.text()
        user_exists, user_data = User.user_exists(email)
        if user_exists:
            self.edit_user_gui = EditUserGUI(user_data)
            self.edit_user_gui.show()
        else:
            self.status_label.setText('<font color="red">The user doesn\'t exist.</font>')

    def on_add_user(self):
        email = self.email_edit.text()
        user_exists, _ = User.user_exists(email)
        if not user_exists:
            self.add_user_gui = AddUserGUI(email=email)
            self.add_user_gui.show()
        else:
            self.status_label.setText('<font color="red">The user already exists.</font>')


class PasswordGUI(QWidget):
    def __init__(self, curr_user):
        super().__init__()
        self.curr_user = curr_user
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Reset Password")
        layout = QVBoxLayout()

        # Current password
        layout.addWidget(QLabel("Current Password:"))
        self.current_password_edit = QLineEdit()
        self.current_password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.current_password_edit)

        # New password
        layout.addWidget(QLabel("New Password:"))
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.new_password_edit)

        # Confirm new password
        layout.addWidget(QLabel("Confirm New Password:"))
        self.confirm_new_password_edit = QLineEdit()
        self.confirm_new_password_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.confirm_new_password_edit)

        # Submit button
        self.submit_btn = QPushButton("Submit")
        self.submit_btn.setFixedSize(self.submit_btn.sizeHint())
        self.submit_btn.clicked.connect(self.onSubmit)
        layout.addWidget(self.submit_btn)

        # Status Label for displaying messages
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def onSubmit(self):
        current_password = self.current_password_edit.text()
        new_password = self.new_password_edit.text()
        confirm_new_password = self.confirm_new_password_edit.text()

        if new_password != confirm_new_password:
            self.status_label.setText('<font color="red">New passwords do not match.</font>')
            return
        
        if not User.verify_user_password(self.curr_user.email, current_password, self.cursor):
            self.status_label.setText('<font color="red">Incorrect current password.</font>')
            return

        if User.update_user_password(self.curr_user.email, new_password, self.cursor):
            self.status_label.setText('<font color="green">Password updated successfully.</font>')
        else:
            self.status_label.setText('<font color="red">Password update failed.</font>')


class SettingsGUI(QWidget):
    def __init__(self, curr_user):
        super().__init__()
        self.curr_user = curr_user
        self.setWindowTitle('Settings')
        
        self.tabWidget = QTabWidget()
        self.initTabs()
        
        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)
        self.setLayout(layout)
        
        
    def initTabs(self):
        # Admin-specific tabs
        if self.curr_user.type == "admin":
            self.tabWidget.addTab(self.createUpdateDatabaseTab(), "Update Database")
            self.tabWidget.addTab(self.createAddOrEditUserTab(), "Add/Edit User")
            self.tabWidget.addTab(self.createExportDatabaseTab(), "Export Database")
        
        # Tab available for all users
        self.tabWidget.addTab(self.createResetPasswordTab(), "Reset Password")
    
    def createUpdateDatabaseTab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Description with center alignment
        desc = QLabel("Updates the database to the latest version.")
        desc.setAlignment(Qt.AlignCenter)  # Align the description text to center
        layout.addWidget(desc)

        # Button with center alignment using QHBoxLayout
        btnLayout = QHBoxLayout()  # Create a QHBoxLayout for the button to center it
        btnLayout.addStretch()  # Add stretchable space on the left
        updateDatabaseBtn = QPushButton('Update Database')
        updateDatabaseBtn.setFixedSize(updateDatabaseBtn.sizeHint())  # Adjust size to fit text
        btnLayout.addWidget(updateDatabaseBtn)  # Add the button to the horizontal layout
        btnLayout.addStretch()  # Add stretchable space on the right

        layout.addLayout(btnLayout)  # Add the horizontal layout containing the button to the main vertical layout
        # updateDatabaseBtn.clicked.connect(self.updateDatabase)  # Implement this method

        tab.setLayout(layout)
        return tab
    
    def createAddOrEditUserTab(self):
        tab = AddOrEditUserGUI()
        return tab
    
    def createExportDatabaseTab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Description with center alignment
        desc = QLabel("Exports and downloads the database as CSV files to the Downloads folder.")
        desc.setAlignment(Qt.AlignCenter)  # Align the description text to center
        layout.addWidget(desc)

        # Button with center alignment using QHBoxLayout
        btnLayout = QHBoxLayout()  # Create a QHBoxLayout for the button to center it
        btnLayout.addStretch()  # Add stretchable space on the left
        exportDatabaseBtn = QPushButton('Export Database')
        exportDatabaseBtn.setFixedSize(exportDatabaseBtn.sizeHint())  # Adjust size to fit text
        btnLayout.addWidget(exportDatabaseBtn)  # Add the button to the horizontal layout
        btnLayout.addStretch()  # Add stretchable space on the right
        layout.addLayout(btnLayout)  # Add the horizontal layout containing the button to the main vertical layout

        exportDatabaseBtn.clicked.connect(self.exportDatabase)  # Connect the button to its action
        
        tab.setLayout(layout)
        return tab
        
    def createResetPasswordTab(self):
        tab = PasswordGUI(self.curr_user)
        return tab
        
    def updateDatabase(self):
        print("Update Database clicked")

    def openAddOrEditUserGUI(self):
        self.addOrEditUserGUI = AddOrEditUserGUI()
        self.addOrEditUserGUI.show()

    def openPasswordGUI(self):
        self.passwordGUI = PasswordGUI()
        self.passwordGUI.show()
    
    def exportDatabase(self):
        # Attempt to export both tables and capture their success status
        success_users = export_table_to_csv('users')
        success_events = export_table_to_csv('events')
        if success_users and success_events:
            message = "Database exported successfully."
            QMessageBox.information(self, "Export Successful", message)
        else:
            message = "Failed to export database."
            QMessageBox.warning(self, "Export Failed", message)

   