from passlib.context import CryptContext

# Create a context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash a password
def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

# Verify a password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Example usage
if __name__ == "__main__":
    password = input("Enter your password: ")
    hashed = hash_password(password)
    print(f"\n🔐 Hashed password:\n{hashed}")

    # Optional: test verification
    verify = input("\nRe-enter password to verify: ")
    if verify_password(verify, hashed):
        print("✅ Password verified!")
    else:
        print("❌ Invalid password!")
