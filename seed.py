import logging

from faker import Faker
from app import db, Contact, Message

fake = Faker("pt_BR")

logging.info("Creating database...")
db.create_all()
logging.info("Database created.")

logging.info("Adding messages...")
for _ in range(50):
    db.session.add(Message(message=fake.text()))

logging.info("Adding contacts...")
for _ in range(10):
    db.session.add(Contact(contact=fake.phone_number()))

db.session.commit()
logging.info("Finished execution.")
