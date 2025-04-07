import base64

def encode_text():
    text = input("Enter the text to encode: ")
    # Convert string to bytes and then encode to base64
    encoded = base64.b64encode(text.encode('utf-8'))
    # Convert bytes back to string for printing
    print("\nBase64 encoded result:")
    print(encoded.decode('utf-8'))

def decode_text():
    text = input("Enter the base64 string to decode: ")
    try:
        # Decode base64 string to bytes and then to string
        decoded = base64.b64decode(text.encode('utf-8')).decode('utf-8')
        print("\nDecoded result:")
        print(decoded)
    except Exception as e:
        print("\nError: Invalid base64 string")

if __name__ == "__main__":
    while True:
        choice = input("\nDo you want to encode or decode? (type 'encode', 'decode', or 'exit'): ").lower()
        
        if choice == "encode":
            encode_text()
        elif choice == "decode":
            decode_text()
        elif choice == "exit":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please type 'encode', 'decode', or 'exit'.")
