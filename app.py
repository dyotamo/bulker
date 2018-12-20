import os
import logging
logging.basicConfig(format='%(levelname)s\t- %(message)s', level=logging.DEBUG)

from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL') or 'sqlite:///sched.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROJECT_ID'] = 'PJ835f870fa34ebe32'
app.config['SECRET_KEY'] = '8W881_DEsGg3dde8GZLyl2pyMQSQPlDIvJmC'
app.config['WEBHOOK_KEY'] = 'GQZF3AL3ZGMLFGP4F7GAFLTMUZRLZ972'
app.config['FLASK_ADMIN_SWATCH'] = 'united'

db = SQLAlchemy(app)


class Contact(db.Model):
    """ represents the contact entity """
    id = db.Column(db.Integer, primary_key=True)
    contact = db.Column(db.String(13), unique=True, nullable=False)

    def __repr__(self):
        return '<Contact {}>'.format(self.contact)


class Message(db.Model):
    """ represents the message to send entity """
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(1000), unique=False, nullable=False)

    def __repr__(self):
        return '<Message {}>'.format(self.id)


# Flask admin interface
admin = Admin(app, name='Sched', template_mode='bootstrap3')
admin.add_view(ModelView(Contact, db.session))
admin.add_view(ModelView(Message, db.session))


def send_sms():
    import random
    import requests
    import json

    for contact in Contact.query:
        msg = get_random_msg()

        headers = {'Content-Type': 'application/json'}
        data = {'content': msg.message, 'to_number': contact.contact}

        requests.post(
            'https://api.telerivet.com/v1/projects/{}/messages/send'.format(
                app.config['PROJECT_ID']),
            auth=(app.config['SECRET_KEY'], ''),
            headers=headers,
            data=json.dumps(data))


sched = BackgroundScheduler(daemon=True)
sched.add_job(send_sms, 'interval', hours=1)
# sched.start()


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.form

    if data.get('secret') != app.config['WEBHOOK_KEY']:
        return jsonify({'error': 'invalid webhook key'}), 403

    if data.get('event') == 'incoming_message':
        content = data.get('content').upper()
        from_number = data.get('from_number')

        if content == 'JOIN':
            return subscribe(from_number)

        if content == 'STOP':
            return unsubscribe(from_number)

        return jsonify({
            'messages': [{
                'content':
                "Formato de mensagem inválido.\n\nUse JOIN para ativar "
                "ou STOP para cancelar a subscrição.\n\nObrigado."
            }]
        })


def get_contact(from_number):
    """ get the contact object by number """
    return Contact.query.filter_by(contact=from_number).first()


def get_random_msg():
    """ get random message """

    from sqlalchemy.sql.expression import func
    return Message.query.order_by(func.random()).first()


def subscribe(from_number):
    """ subscribe contact """
    if not get_contact(from_number):
        contact = Contact()
        contact.contact = from_number

        db.session.add(contact)
        db.session.commit()
        return jsonify({
            'messages': [{
                'content':
                "Obrigado pela subscrição.\n\nEm breve passará a receber "
                "mensagens sobre curiosidades diversas."
            }]
        })
    else:
        return jsonify({
            'messages': [{
                'content': "Contacto já subscrito.\n\nObrigado."
            }]
        })


def unsubscribe(from_number):
    """ unsubscribe contact """
    contact = get_contact(from_number)
    if contact:
        db.session.delete(contact)
        db.session.commit()
        return jsonify({
            'messages': [{
                'content':
                "A sua subscrição foi cancelada com sucesso.\n\nObrigado."
            }]
        })
    else:
        return jsonify({
            'messages': [{
                'content': "Contacto não subscrito.\n\nObrigado."
            }]
        })


# Web interface errors handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'internal server error'}), 500


if __name__ == '__main__':
    app.run()