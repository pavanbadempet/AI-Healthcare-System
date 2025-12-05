try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash = pwd_context.hash("test")
    print(f"Hash success: {hash}")
except Exception as e:
    print(f"Error: {e}")
