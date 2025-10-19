# First Create your prime numbers
p = 5
q = 11

# Next, calculate the Modulus.
# This will be used in your public and private keys
modulus = p * q
print(modulus)

# Next Calculate the totient which will be used to
# determine the exponent of the Public key
totient = (p-1) * (q-1)
print(totient)

# Create a public key
# This should be less than the totient but also relatively prime
public_exp = 7

# Public Key
### Combining the Public exponent with the Modulus give us our public key
### public_key = (7, 55)

# Now, let's create the Private key
### Extended Euclidean Algorithm
private_exp = pow(public_exp, -1, totient)
print(private_exp)

# Private Key
### private_key = 23, 55)


# Testing the keys!
### Encryption
x = 3
encrypted_text = x**public_exp % modulus
print(encrypted_text)

### Decryption
decrypted_text = encrypted_text**private_exp % modulus
print(decrypted_text)