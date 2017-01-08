from app import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    name = db.Column(db.String(80))
    surname = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(80))

    def __init__(self, id, username, name, surname, email, password):
        self.id = id
        self.username = username
        self.name = name
        self.surname = surname
        self.email = email
        self.password = password

    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def get_username(self):
        return self.username

    def get_name(self):
        return self.name

    def get_surname(self):
        return self.surname

    def get_email(self):
        return self.email

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    user_id = db.Column(db.Integer)

    def __init__(self, id, name, user_id):
        self.id = id
        self.name = name
        self.user_id = user_id

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    type = db.Column(db.String(1))
    credit_card_limit = db.Column(db.Float)
    is_active = db.Column(db.String(1))
    user_id = db.Column(db.Integer)

    def __init__(self, id, name, type, credit_card_limit, is_active, user_id):
        self.id = id
        self.name = name
        self.type = type
        self.credit_card_limit = credit_card_limit
        self.is_active = is_active
        self.user_id = user_id

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120))
    amount = db.Column(db.Float())
    transaction_date = db.Column(db.Date)
    account_id = db.Column(db.Integer)
    category_id = db.Column(db.Integer)
    type = db.Column(db.String(10))
    is_done = db.Column(db.String(1))
    attachment_filename = db.Column(db.String(120))
    user_id = db.Column(db.Integer)

    def __init__(self, id, description, amount, transaction_date, account_id, category_id, type, is_done, attachment_filename, user_id):
        self.id = id
        self.description = description
        self.amount = amount
        self.transaction_date = transaction_date
        self.account_id = account_id
        self.category_id = category_id
        self.type = type
        self.is_done = is_done
        self.attachment_filename = attachment_filename
        self.user_id = user_id

class CreditCardTransaction(db.Model):
    __tablename__ = 'credit_card_transactions'
    id = id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120))
    amount = db.Column(db.Float())
    transaction_date = db.Column(db.Date)
    invoice_date = db.Column(db.Date)
    credit_card_id = db.Column(db.Integer)
    type = db.Column(db.String(10))
    is_done = db.Column(db.String(1))
    payment_done = db.Column(db.String(1))
    user_id = db.Column(db.Integer)

    def __init__(self, id, description, amount, transaction_date, invoice_date, credit_card_id, type, is_done, payment_done, user_id):
        self.id = id
        self.description = description
        self.amount = amount
        self.transaction_date = transaction_date
        self.invoice_date = invoice_date
        self.credit_card_id = credit_card_id
        self.type = type
        self.is_done = is_done
        self.payment_done = payment_done
        self.user_id = user_id


