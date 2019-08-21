import requests
import json

from sqlalchemy.sql.expression import func
from flask import jsonify


def get_contact(contact_model, from_number):
    """ get the contact object by number """
    return contact_model.query.filter_by(contact=from_number).first()


def get_random_msg(message_model):
    """ get random message """
    return message_model.query.order_by(func.random()).first()


def subscribe(db, contact_model, from_number):
    """ subscribe contact """
    if not get_contact(contact_model, from_number):
        contact = contact_model()
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


def unsubscribe(db, contact_model, from_number):
    """ unsubscribe contact """
    contact = get_contact(contact_model, from_number)
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


def send_sms(contact_model, message_model, project_id, secret_key):

    for contact in contact_model.query:
        msg = get_random_msg(message_model)

        headers = {'Content-Type': 'application/json'}
        data = {'content': msg.message, 'to_number': contact.contact}

        requests.post(
            'https://api.telerivet.com/v1/projects/{}/messages/send'.format(
                project_id),
            auth=(secret_key, ''),
            headers=headers,
            data=json.dumps(data))
