# This module cannot be called be_sqlite3 becaseu it does not import well (it needs the second underscore before 3)
import sqlite3
import os
from datetime import datetime
from backend.hash import get_salt_hash, authenticate
import csv


# define a dictionary that sets the attributes of the class User and the columns of the table 'users'
def init_user_dict():
    # the values are used simply to show the formatting. The User class is set with None values. 
    user_dict = {   'id'             : '123',
                    'email'          : 'John.Doe@mail.edu',         # previously named user_id 
                    'name'           : 'John Doe',                  # previously named user_name
                    'nickname'       : 'Nick',                      # previously named user_nickname
                    'title'          : 'PI | PhD student | Tech',    # the title is retried from iLab
                    'phone'          : '123-456-7890', 	            # previously user_phone
                    'pi_name'        : 'Dr. Pie',
                    'pi_phone'       : '555-555-5555',
                    'type'           : 'user | admin',              # previously user_type
                    'last_mod_type'  : 'iLab',
                    'last_mod'       : '2023-08-18 21:20:00',
                    'first_login'    : '2023-07-17 17:20:00',
                    'last_login'     : '2023-07-18 09:20:00',
                    'salt'           : '12345678901234567890',
                    'hash'           : 'ofiae98aeikjs;aelsij',
                    'login_attempts' : '1', 
                    'locked_after'   : '2024-12-31 00:00:00'  }
    return user_dict



# The functions below are outside of any class
# they should not need the @staticmethod decorator
def conn_cores_db(path_to_folder= None): 
    # if no path_to_folder is provided, use the script's folder
    if path_to_folder == None:
        path_to_folder = os.path.dirname(os.path.abspath(__file__)) 
    path_to_cores_db = os.path.join(path_to_folder, 'cores.db')
    
    # check if the file named cores.db already exists in path_to_cores_db 
    if os.path.exists(path_to_cores_db):
        conn = sqlite3.connect(path_to_cores_db)
        # print("Connected to 'cores.db' ...")             
        return conn
    
    # show warning and ask if user wants to create new DB
    else:
        print("WARNING: 'cores.db' not found.")
        user_input = input("Would you like to create a new database? (yes/no): ").upper() 

        # if yes, create cores.db file
        if (user_input == 'YES' or user_input == 'Y') : 
            try:
                conn = sqlite3.connect(path_to_cores_db)
                print("'cores.db' has been created.")
                create_tables(conn)         
                # create & add admin user when new db created 
                admin_user = User()
                admin_user.email = 'admin'
                admin_user.name = 'Admin User'
                admin_user.type = 'admin'
                admin_user.salt, admin_user.hash = get_salt_hash('admin', 'admin')
                admin_user.add_user()
                print('Admin user created.')
                return conn
            
            except sqlite3.Error as e:
                print("Error:", e)
                return False
        else:
            print("Aborted.")
            return False


def create_tables(conn):
    '''Create two tables ('users' and 'events') in cores.db, if they do not exist'''

    empty_user = User()
    user_dict = empty_user.__dict__
    del user_dict['id']   # remove the id key which will need to be handled differently

    event_dict = init_event_dict()
    del event_dict['id']  # remove the id key (handled differently)

    # add two table 'users' to cores.db
    try:
        # Create a cursor object using the cursor() method
        cursor = conn.cursor()

        # i) Create 'users' table with necessary columns
        sql_users_0 = ", ".join([f"{col} TEXT" for col in user_dict.keys()]) 
        sql_users = f"CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, {sql_users_0} )"
        cursor.execute(sql_users)
        conn.commit()
    except sqlite3.Error as e:
        print("Error while creating the 'users' table:", e)
        return False
    
    # add two table 'events' to cores.db
    try:
        # ii) Create 'logins' table with necessary columns
        sql_events_0 = ", ".join([f"{col} TEXT" for col in event_dict.keys()]) 
        sql_events = f"CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, {sql_events_0} )"
        cursor.execute(sql_events)
        conn.commit()
        conn.close
        print("Tables 'users' and 'logins' created successfully.")  
    except sqlite3.Error as e:
        print("Error while creating the 'logins' table:", e)
        return False

    return True

def get_column_names(table_name):
        """
        Fetches the column names of a specified table.

        Args:
            cursor: Database cursor for executing queries.
            table_name (str): Name of the table to fetch column names for.

        Returns:
            list: A list of column names for the specified table.
        """
        conn = conn_cores_db()   
        with conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns_info = cursor.fetchall()
                column_names = [info[1] for info in columns_info]  
                return column_names
            
            except sqlite3.Error as e:
                print("Error:", e)
                return None

def export_table_to_csv(table_name):
    # Get today's date to append to the file name
    today = datetime.now().strftime('%Y_%m_%d')
    file_name = f"{table_name}_{today}.csv"
    
    # Define a path to save the file in the user's home directory
    home_dir = os.path.expanduser('~')  # Gets the user's home directory
    file_path = os.path.join(home_dir, 'Downloads', file_name)  # Saves in the Downloads folder
    
    # Connect to the database and fetch the data
    conn = conn_cores_db()  # Ensure conn_cores_db() is accessible
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    # Fetch the column headers
    column_names = [description[0] for description in cursor.description]
    
    try:
        # Write the data to a CSV file
        with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(column_names)  # Write the headers first
            csv_writer.writerows(rows)
        
        print(f"Exported {table_name} to {file_path}")
        return True
    except Exception as e:
        print(f"Failed to export {table_name} to {file_path}: {e}")
        return False

class User:
    def __init__(self, user_dict=init_user_dict()):
        # usage: user1 = User() will generate an empty instance
        for key, value in user_dict.items():
            setattr(self, key, None)

    
    def add_user(self):
        '''Method to add a user to the 'users' table.
           The recording of the login event should be handled separately.'''
        try:
            # Generate the dictionary of attribute names and values for user
            user_dict = self.__dict__
            # Generate the placeholders for SQL values   :id, :email, :name ...
            placeholders = ", ".join([f":{col}" for col in user_dict.keys()])  
            # Set the 'first_login' attribute to the current datetime
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.first_login = current_time
            self.last_login = current_time

            # Generate the SQL query using named placeholders
            sql = f"INSERT INTO users VALUES ({placeholders})"
            
            # connect to cores.db;  
            conn = conn_cores_db()   
            with conn:
                cursor = conn.cursor()
                cursor.execute(sql, user_dict)
                conn.commit()
                row_id = cursor.lastrowid
                
                # NOTE (FT): It is not practical to record a login event from the User class
                # because there is not enough data to do it properly
                
                # # Record the login event
                # login_event = Event()
                # login_event.email = self.email
                # # add device name 
                # login_event.login_time = current_time
                # login_event.login_type = "local" 
                # login_event.record_login()

            self.id = row_id
            print(f"User added successfully on row {row_id}.")
            
            # Return the row ID of the added user
            return row_id    # return row_id, login_event 
        
        except sqlite3.Error as e:
            print("Error:", e)
            return None  
        

    @classmethod
    def from_database(cls, row_id):
        # This method constructs a User instance with attributes values existing in the the 'users' table
        # The function does the following:
        #           - read a line from database; 
        #           - create an new instance of the User class; 
        #           - set the values read from database to the attributes of the instance;
        #           - return the instance
        # Usage: new_user = User.from_database(id)        
        # connect to cores.db;  

        conn = conn_cores_db()   
        with conn:
            cursor = conn.cursor()
            try:
                # Fetch the user's information from the database
                cursor.execute("SELECT * FROM users WHERE id=?", (row_id, ))
                user_info = cursor.fetchone()

                if user_info:
                    user_instance = cls()  # Create an empty instance of the class
                    # Create empty dict to put loaded user into
                    user_dict = {}

                    # Use zip to create something like ("id", 1), ...
                    for key, value in zip(user_instance.__dict__.keys(), user_info):
                        user_dict[key] = value
                    user_instance.__dict__.update(user_dict)   # the builtin update function is very convenient here!

                    print("User information loaded successfully.")
                    return user_instance
                else:
                    print("Error: User not found.")
                    return None

            except sqlite3.Error as e:
                print("Error:", e)
                return None
    
    @classmethod
    def from_database_by_email(cls, email):
        # Get the row ID for the given email; find existing user
        # NOTE: this function does not check if 
        row_id = get_rowid_for_email(email)
        
        # If row ID is found, call the generic method
        if row_id is not None:
            return cls.from_database(row_id)
        else:
            print(f"Error: User with email '{email}' not found.")
            return None


    # Update one property of one user with known rowid
    def update_user_property(self, id, column_name, new_value):
        try:
            sql = """--sql 
                UPDATE  users 
                SET     {}  = ? 
                WHERE   id == ?
            """.format(column_name)

            # connect to cores_db;   
            conn = conn_cores_db()
            with conn:
                cur = conn.cursor()
                cur.execute(sql, (new_value, id))
                conn.commit()
            print(f"User id: {id}, column: {column_name} updated successfully. New value: {new_value}")
            return True
        except sqlite3.Error as e:
            print("Error:", e)
            return False

    #============================================================================================================
    # NOTE: FUNCTION FOR UPDATING/ RE-WRITING AN EXISTING USER   <= !!! Might interfere with the ID/Autoincrement!! CHECK!!!
    # added on 22DEC2023
    def update_user(self):
        for _ in self.__dict__.keys():
            self.update_user_property(self.id, _, self.__dict__[_])
    #==============================================================================================================


    @staticmethod
    def authenticate_user(email, password) :
        # connect to cores_db;  
        conn = conn_cores_db()

        # get stored salt and hash in user's row 
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT salt, hash FROM users WHERE email=?", (email,))
                user_info = cursor.fetchone()
                print("user_info:", user_info)

                if user_info:
                    salt_db_str, hash_db_str = user_info
                else:
                    # User not found
                    return False

        except sqlite3.Error as e:
            print("Error while retrieving user info:", e)
            return False
        
        result = authenticate(email, password, salt_db_str, hash_db_str)

        # Update 'last_login' when login is successful
        if result:
            try:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET last_login=? WHERE email=?", (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), email))
                    conn.commit()
            except sqlite3.Error as e:
                print("Error while updating last_login:", e)
        
        return result
    


    def verify_user_password(email, plain_password, cursor):
        """
        Verifies if the given plain_password matches the hashed password in the database for the user identified by email.

        Args:
            email (str): The email of the user.
            plain_password (str): The plain text password to verify.
            cursor: Database cursor for executing queries.

        Returns:
            bool: True if the password matches, False otherwise.
        """

        conn = conn_cores_db()

        try:
            with conn:
                cursor = conn.cursor()
                # Query the database for the user's salt and hash
                cursor.execute("SELECT salt, hash FROM users WHERE email = ?", (email,))
                result = cursor.fetchone()
                if result:
                    salt_string, hash_string = result
                    # Use the authenticate function to check if the password is correct
                    return authenticate(email, plain_password, salt_string, hash_string)
                return False
            
        except sqlite3.Error as e:
            print("Error while retrieving user info:", e)
            return False

        

    def update_user_password(email, new_plain_password, cursor):
        """
        Updates the password for the user identified by email in the database.

        Args:
            email (str): The email of the user whose password will be updated.
            new_plain_password (str): The new password in plain text.
            cursor: Database cursor for executing queries.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        conn = conn_cores_db()

        try:
            with conn:
                cursor = conn.cursor()
                # Generate new salt and hash for the new password
                salt_string, hash_string = get_salt_hash(email, new_plain_password)

                # Update the user's salt and hash in the database
                try:
                    cursor.execute("UPDATE users SET salt = ?, hash = ? WHERE email = ?", (salt_string, hash_string, email))
                    cursor.connection.commit()
                    return True
                except Exception as e:
                    print(f"Failed to update password for {email}: {e}")
                    return False
            
        except sqlite3.Error as e:
            print("Error:", e)
            return False
     
    def get_user_data_by_email(email):
        """
        Fetches a user's data from the database by email.

        Args:
            email (str): Email of the user to fetch.

        Returns:
            tuple: (bool, dict) where bool indicates if the user exists,
                and dict contains user data if the user exists.
        """
        user_instance = User.from_database_by_email(email)
        if user_instance is not None:
            return True, user_instance.__dict__
        else:
            return False, {}


    def user_exists(email):
        """
        Checks if a user exists in the database by email.

        Args:
            email (str): Email of the user to check.

        Returns:
            tuple: (bool, dict) where bool indicates if the user exists,
                and dict contains user data if exists.
        """
        user_instance = User.from_database_by_email(email)
        if user_instance is not None:
            return True, user_instance.__dict__
        else:
            return False, {}




        





# the function below is not used any longer
# def get_rowid_for(email, pi_name):
#     # get the rowid of a user existing in the 'users' table, based on email and pi_name 
#     # connect to cores_db;  
#     conn = conn_cores_db()
#     with conn:
#         cur = conn.cursor()
#         cur.execute("SELECT id FROM users WHERE email=? AND pi_name=?", (email, pi_name))
#         user_ids = cur.fetchall()
#         print(user_ids, "  |  len(user_id):", len(user_ids))
    
#     if len(user_ids)==1:
#         (int_user_id,) = user_ids      
#         print('int_user_id:', int_user_id)
#         return int_user_id
#     elif len(user_ids)==0:
#         print('Error: no user found!')
#         return None
#     else:
#         print("WARNING: More than one user with the same email address and the same PI!")
#         return user_ids



def get_duplicates(email):
    ''' Returns a list of IDs or None'''
    row_ids_tuples = get_rowid(email)
    if row_ids_tuples:
        if len(row_ids_tuples) == 1:  # if single tuple
            ids_list = [item for item in row_ids_tuples]
        else:                         # if list of multiple tuples
            ids_list = [item for t in row_ids_tuples for item in t]
        return ids_list
    else:
        return None  # no users with `email` found

def get_id_of_most_recent_user(email):
    ''' Returns one ID as integer (not a list) or None'''
    ids_list = get_duplicates(email)
    if not ids_list:
        return None
    elif len(ids_list) == 1:
        unique_id = ids_list[0]
        return unique_id
    elif len(ids_list) > 1:
        most_recent_user_id = None
        last_mod_dt = datetime.now().replace(year = 1901)
        for id in ids_list:
            user = User.from_database(id)
            user_last_mod_dt = datetime.strptime(user.last_mod, '%Y-%m-%d %H:%M:%S')
            if user_last_mod_dt > last_mod_dt:
                last_mod_dt = user_last_mod_dt
                most_recent_user_id = user.id
        print('most_recent_user_id:', most_recent_user_id)
        return most_recent_user_id 

def remove_duplicates(email):
    id_duplicates_list = get_duplicates(email)
    print('id_duplicates_list:', id_duplicates_list)
    if id_duplicates_list:
        if len(id_duplicates_list) > 1:
            most_recent_user_id = get_id_of_most_recent_user(email)
            print('most_recent_user_id:', most_recent_user_id)
            id_duplicates_list.remove(most_recent_user_id) # remove most recent
            ids_to_delete_list = id_duplicates_list
            print('ids_to_delete_list:', ids_to_delete_list)
            conn = conn_cores_db()
            with conn:
                cur = conn.cursor()
                for id in ids_to_delete_list:
                    cur.execute("DELETE FROM users WHERE id = ?", (id,))
        else:
            print(f"Only one user has the email: {email}")
    else:
        print(f"No user with email {email} found.")
        return None




def get_rowid_for_email(email):
    # connect to cores_db;  
    conn = conn_cores_db()   
    with conn:
        cursor = conn.cursor()
        try:
            # Fetch the user's row ID from the database
            cursor.execute("SELECT id FROM users WHERE email=?", (email,))
            row_id = cursor.fetchone()

            if row_id:
                return row_id[0]
            else:
                print(f"Error: User with email '{email}' not found.")
                return None

        except sqlite3.Error as e:
            print("Error:", e)
            return None


def get_rowid(email):
    ' returns tuples'
    # get the rowid of a user existing in the 'users' table, based on email and check if unique 
    # connect to cores_db;  
    conn = conn_cores_db()
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        user_ids = cur.fetchall()
        print(user_ids, "  |  len(user_id):", len(user_ids))
    
    if len(user_ids)==1:
        int_user_id = user_ids[0]     
        return int_user_id
    elif len(user_ids)==0:
        print('Error: no user found!')
        return None
    else:
        print("WARNING: More than one user with the same email address!")
        return user_ids
    
def get_rowid_for_email(email):
    # connect to cores_db;  
    conn = conn_cores_db()   
    with conn:
        cursor = conn.cursor()
        try:
            # Fetch the user's row ID from the database
            cursor.execute("SELECT id FROM users WHERE email=?", (email,))
            row_id = cursor.fetchone()

            if row_id:
                return row_id[0]
            else:
                print(f"Error: User with email '{email}' not found.")
                return None

        except sqlite3.Error as e:
            print("Error:", e)
            return None
    


event_dict = {  'id'          : '123',
                'email'       : 'xyz@chop.edu',
                'device'      : 'Aurora alpha',
                'login_time'  : '2023-08-18 14:20:00',
                'login_type'  : 'local | iLab | EMERGENCY',
                'logout_time' : '2023-08-18 16:20:00',
                'logout_type' : 'by_user  | by_inactivity  | pending' }



# define a dictionary that sets the attributes of the class Event and the columns of the table 'events'
def init_event_dict():


    event_dict = {  'id'          : None,
                    'email'       : 'xyz@chop.edu',
                    'device'      : 'Device Name',
                    'login_time'  : '2023-08-18 14:20:00',
                    'login_type'  : 'local | iLab | EMERGENCY',
                    'logout_time' : '2023-08-18 16:20:00',
                    'logout_type' : 'by_user  | by_inactivity  | pending' }
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    event_dict['login_time'] = current_time
    event_dict['logout_time'] = current_time

    return event_dict


class Event:
    def __init__(self, event_dict=init_event_dict()):
        for key, value in event_dict.items():
            setattr(self, key, None)


    def record_login(self):
        # 3) Func: record_login():
        # Purpose: add one row to 'logins' table to record a login event
        # return row_id if successful
        # Usage:  current_event.record_login()
        print("... recording login ...")
        conn = conn_cores_db() 
        with conn:
            cursor = conn.cursor()
            # Generate the dictionary of attribute names and values for log
            event_dict = self.__dict__

            try:
                # Generate the placeholders for SQL values
                placeholders = ', '.join([f":{col}" for col in event_dict.keys()])
                print("placeholders: ", placeholders)
                # Generate the SQL query using named placeholders
                sql = f"INSERT INTO events VALUES ({placeholders})"
                cursor.execute(sql, event_dict)
                conn.commit()

                # Store lastrowid in the Event instance
                self.lastrowid = cursor.lastrowid

                print("Login event recorded successfully.")
                return self.lastrowid
            except sqlite3.Error as e:
                print("Error while recording login event:", e)
                return None
        
    def record_logout(self):
        # Function to record logout datetime using lastrowid

        if hasattr(self, 'lastrowid') and self.lastrowid is not None:
            conn = conn_cores_db()
            with conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("UPDATE events SET logout_time=? WHERE id=?", (datetime.now(), self.lastrowid))
                    cursor.execute("UPDATE events SET logout_type=? WHERE id=?", (self.logout_type, self.lastrowid))
                    conn.commit()
                    print("Logout event recorded successfully.")
                    return True
                except sqlite3.Error as e:
                    print("Error while recording logout event:", e)
                    return False
        else:
            print("Error: Cannot record logout event without a valid login event.")
            return False



    @classmethod
    def login_from_args(cls, email, device, type_string):
        ''' Alternative constructor for Event instance'''
        event = cls() # create Event instance
        event.id = None
        event.email = email
        event.device = device
        event.login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        event.login_type = type_string     # options: 'local | iLab | EMERGENCY'
        event.logout_time = 'N/A'
        event.logout_type = "PENDING"
        return event
        # Ex. use:  
        #   event =  setup_event(user.email, 'Aurora', 'login', 'local')
        #   event.record_event()




def initialize_database():
    # Set the path to the database (cores.db)
    script_directory = os.path.dirname(os.path.abspath(__file__))
    path_to_folder = os.path.dirname(os.path.abspath(__file__))
    conn = conn_cores_db(path_to_folder)

# # ===========================================================================================
if __name__ == "__main__":
    import time
    import sys
    from datetime import datetime
    # set the path for the database (cores.db) where this script is located 
    script_directory = os.path.dirname(os.path.abspath(__file__))
    
