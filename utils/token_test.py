from jose import jwt

# Data for fill in the token
payload = {"sub": "1234567890", "name": "John Doe"}

# Create token with symmetrical key
encoded = jwt.encode(payload, "secret_key", algorithm="HS256")
print(encoded)

# Check token
decoded = jwt.decode(encoded, "secret_key", algorithms=["HS256"])
print(decoded)
