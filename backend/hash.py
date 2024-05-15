import os
from hashlib import blake2b
from base64 import b64encode, b64decode

def get_salt_hash(email, password):
    '''generate salt and hash for email (used as username) and password'''
    msg = bytes((email + password), 'utf-8')
    salt_bytes = os.urandom(blake2b.SALT_SIZE)
    salt_string = b64encode(salt_bytes).decode('utf-8')     
    hash = blake2b(salt=salt_bytes)
    hash.update(msg)
    hash_string = hash.hexdigest()                          
    return salt_string, hash_string


def authenticate(email, password, salt_string, hash_string):
    '''The authenticate function does the following:
      - generate the hash using the id, password and salt
      - if (generated hash == hash stored in cores_db): return True
      - else: return False''' 
    # convert string id + password to bytes
    email_pass_bytes = bytes((email + password), 'utf-8')

    # convert salt from string to bytes
    salt_bytes = b64decode(salt_string)

    # Calculate the hash.  (blake2b.SALT_SIZE = 16)
    hash_check = blake2b(salt=salt_bytes)
    hash_check.update(email_pass_bytes)

    # convert hash to hex string
    hash_check_str = hash_check.hexdigest()

    # authenticate
    if hash_check_str == hash_string:
        return True
    else:
        return False
    
if __name__ == "__main__":
    from backend.main import User
    user = User()
    user.email = " "
    salt_string, hash_string = get_salt_hash(user.email, " ")
    user.name = "empty string user no pass"
    row_id = user.add_user()
    print("row_id:", row_id)

def check_default_password(email):
    salt, hash = get_salt_hash(email)
    return True if authenticate(email, 'chop1234', salt, hash) else False
