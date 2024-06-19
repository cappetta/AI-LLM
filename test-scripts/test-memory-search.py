import time
import os

def store_sensitive_info():
    password = "supersecretpassword"
    api_key = "12345-ABCDE-67890-FGHIJ"
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    print("Storing sensitive information in memory. PID:", os.getpid())
    while True:
        time.sleep(30)

if __name__ == "__main__":
    store_sensitive_info()
