import os
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, jsonify, request, redirect
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user

from utils import send_sms, subscribe, unsubscribe

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    format='%(asctime)s\t- %(levelname)s\t- %(message)s', level=logging.INFO)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL') or 'sqlite:///sched.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROJECT_ID'] = os.environ["PROJECT_ID"]
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
app.config['WEBHOOK_KEY'] = os.environ["WEBHOOK_KEY"]
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


class User(db.Model, UserMixin):
    """ represents the user entity """
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return '<User {}>'.format(self.id)


class DModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect("/users/login")


login = LoginManager(app)


@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# Flask admin interface
admin = Admin(app, name='Bulker', template_mode='bootstrap3')
admin.add_view(DModelView(Contact, db.session))
admin.add_view(DModelView(Message, db.session))

# Login views
@app.route("/users/login", methods=["GET"])
def login():
    login_user(User.query.first())
    return redirect("/admin")


@app.route("/users/logout", methods=["GET"])
def logout():
    logout_user()
    return redirect("/admin")


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


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.form

    if data.get('secret') != app.config['WEBHOOK_KEY']:
        return jsonify({'error': 'invalid webhook key'}), 403

    if data.get('event') == 'incoming_message':
        content = data.get('content').upper()
        from_number = data.get('from_number')

        if content == 'JOIN':
            return subscribe(db, Contact, from_number)

        if content == 'STOP':
            return unsubscribe(db, Contact, from_number)

        return jsonify({
            'messages': [{
                'content':
                "Formato de mensagem inválido.\n\nUse JOIN para ativar "
                "ou STOP para cancelar a subscrição.\n\nObrigado."
            }]
        })


sched = BackgroundScheduler(daemon=True)
sched.add_job(lambda: send_sms(Contact, Message, app.config["PROJECT_ID"],
                               app.config["SECRET_KEY"]), 'interval', hours=1)
sched.start()

if __name__ == '__main__':
    app.run(debug=True)
