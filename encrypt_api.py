# this file defines a function that accepts a string and a password and encrypts the string in a file called api_key.txt. It also defines another function that allows you to get api key and accepts a password, reads this file and decodes the api key and reutrns it as a string
import base64  # used for encoding and decoding
from cryptography.fernet import Fernet  # used for encryption and decryption
from getpass import getpass  # used for getting password from user


def encrypt_api_key(api_key: str, password: str) -> None:
    """
    Encrypts the API key and saves it to a file called api_key.txt.

    :param api_key: The API key to encrypt.
    :param password: The password to use for encryption.
    """
    # Generate a key from the password
    key = base64.urlsafe_b64encode(password.encode("utf-8").ljust(32)[:32])
    fernet = Fernet(key)

    # Encrypt the API key
    encrypted_api_key = fernet.encrypt(api_key.encode("utf-8"))

    # Save the encrypted API key to a file
    with open("api_key.txt", "wb") as file:
        file.write(encrypted_api_key)


def decrypt_api_key(password: str) -> str:
    """
    Decrypts the API key from the file api_key.txt.

    :param password: The password to use for decryption.
    :return: The decrypted API key.
    """
    # Generate a key from the password
    key = base64.urlsafe_b64encode(password.encode("utf-8").ljust(32)[:32])
    fernet = Fernet(key)

    # Read the encrypted API key from the file
    with open("api_key.txt", "rb") as file:
        encrypted_api_key = file.read()

    # Decrypt the API key
    decrypted_api_key = fernet.decrypt(encrypted_api_key)

    return decrypted_api_key.decode("utf-8")


def get_api_key(pw=False) -> str:
    """
    Prompts the user for a password and retrieves the decrypted API key.

    :return: The decrypted API key.
    """
    password = str(pw)  # or isinstance(pw, int) or getpass("Enter the password: ")
    try:
        api_key = decrypt_api_key(password)
        return api_key
    except Exception as e:
        print(f"Failed to decrypt API key: {e}")
        return None


if __name__ == "__main__":
    if input("get or set? (g/s): ").lower() == "g":
        api_key = get_api_key()
        if api_key:
            print(f"Decrypted API key: {api_key}")
        else:
            print("Failed to retrieve API key.")
    else:
        key = input("Enter the API key: ")
        password = getpass("Enter the password: ")
        encrypt_api_key(key, password)
        print("API key encrypted and saved to api_key.txt.")
