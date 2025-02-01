import hashlib

class User:
    def __init__(self, name, email, password, role):
        self.name = name
        self.email = email
        self.password = self.encrypt_password(password)
        self.role = role

    def encrypt_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def __repr__(self):
        return f"User(name={self.name}, email={self.email}, role={self.role})"


if __name__ == "__main__":
    user = User("Alice", "test@test.com", "password", "admin")