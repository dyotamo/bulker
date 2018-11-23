#!/usr/bin/python3

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sched.db'
app.config['PROJECT_ID'] = 'PJ835f870fa34ebe32'
app.config['SECRET_KEY'] = '8W881_DEsGg3dde8GZLyl2pyMQSQPlDIvJmC'
app.config['FLASK_ADMIN_SWATCH'] = 'united'

db = SQLAlchemy(app)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact = db.Column(db.String(13), unique=True, nullable=False)

    def __repr__(self):
        return '<Contact %s>' % self.contact


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(1000), unique=False, nullable=False)

    def __repr__(self):
        return '<Message %s>' % self.id


admin = Admin(app, name='Sched', template_mode='bootstrap3')
admin.add_view(ModelView(Contact, db.session))
admin.add_view(ModelView(Message, db.session))


def send_sms():
    import random
    import requests
    import json

    query = Message.query
    index = random.randint(1, query.count())
    msg = query.get(index)

    for contact in Contact.query:
        headers = {'Content-Type': 'application/json'}
        data = {'content': msg.message, 'to_number': contact.contact}

        requests.post(
            'https://api.telerivet.com/v1/projects/%s/messages/send' %
            app.config['PROJECT_ID'],
            auth=(app.config['SECRET_KEY'], ''),
            headers=headers,
            data=json.dumps(data))


sched = BackgroundScheduler(daemon=True)
sched.add_job(send_sms, 'interval', minutes=60)
sched.start()


@app.route('/webhook', methods=['POST'])
def webhook():
    pass


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run(debug=True)