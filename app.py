import os
from flask import Flask, jsonify, request, Response
from faker import Factory
from twilio.rest import Client
import json
from twilio.twiml.voice_response import VoiceResponse, Dial, Conference
from twilio.jwt.access_token import AccessToken
from twilio.jwt.client import ClientCapabilityToken
from twilio.jwt.access_token.grants import (
    SyncGrant,
    VideoGrant,
    ChatGrant
)
from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname
from inflection import underscore


# Convert keys to snake_case to conform with the twilio-python api definition contract
def snake_case_keys(somedict):
    snake_case_dict = {}
    for key, value in somedict.items():
        snake_case_dict[underscore(key)] = value
    return snake_case_dict

app = Flask(__name__)
fake = Factory.create()
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

Moderator = os.environ['PHONE_NUMBER']
agent_sid = ''
customer_sids = []
conference_sid = ''

@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/sync/')
def sync():
    return app.send_static_file('sync/index.html')

@app.route('/notify/')
def notify():
    return app.send_static_file('notify/index.html')

@app.route('/inbound_call', methods=['GET','POST'])
def inbound_call():
    response = VoiceResponse()
    with Dial() as dial:
        if request.values.get('From') == Moderator:
            global agent_sid


            agent_sid = request.values.get('CallSid')
            print(agent_sid + ' is the agent sid')
            dial.conference('AgentConference', start_conference_on_enter=True, end_conference_on_exit=False, status_callback="https://d1395065.ngrok.io/statuscallback", status_callback_event="start end join leave mute hold")
        else:
            global customer_sids
            customer_sids.append(request.values.get('CallSid'))
            print(customer_sids[0] + ' is the customer sid')
            dial.conference('AgentConference', start_conference_on_enter=False, status_callback="https://d1395065.ngrok.io/statuscallback", status_callback_event="start end join leave mute hold")

    response.append(dial)

    return str(response)

@app.route("/monitor_call", methods=["GET", "POST"])
def monitor():

    response = VoiceResponse()
    dial = Dial()

    dial.conference('AgentConference', muted=True, beep=False, status_callback="https://d1395065.ngrok.io/statuscallback", status_callback_event="start end join leave mute hold")

    response.append(dial)

    return str(response)



@app.route("/capabilitytoken" , methods=["GET"])
def capability_token():
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token=os.environ['AUTH_TOKEN']
    application_sid = os.environ['APPLICATION_SID']


    capability = ClientCapabilityToken(account_sid, auth_token)
    capability.allow_client_outgoing(application_sid)
    print(capability)
    token = capability.to_jwt()

    return jsonify(token=token.decode('utf-8'))



@app.route('/statuscallback', methods=['GET','POST'])
def statuscallback():
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token=os.environ['AUTH_TOKEN']
    sync_service_sid=os.environ['TWILIO_SYNC_SERVICE_SID']

    client = Client(account_sid, auth_token)

    status = request.values.get('StatusCallbackEvent')

    print(request.values.get('ConferenceSid') + ' is the conference sid')
    global conference_sid
    conference_sid = request.values.get('ConferenceSid')


    this_call = request.values.get('CallSid');

    if this_call == agent_sid:
        new_data = {
            "agent_sid" : agent_sid,
            "conference_sid" : conference_sid
        }

        document = client.sync \
            .services(sync_service_sid) \
            .documents("AgentData") \
            .update(data=new_data)

    return ''

# Basic health check - check environment variables have been configured
# correctly
@app.route('/config')
def config():
    return jsonify(
        TWILIO_ACCOUNT_SID=os.environ['TWILIO_ACCOUNT_SID'],
        TWILIO_NOTIFICATION_SERVICE_SID=os.environ.get('TWILIO_NOTIFICATION_SERVICE_SID', None),
        TWILIO_API_KEY=os.environ['TWILIO_API_KEY'],
        TWILIO_API_SECRET=bool(os.environ['TWILIO_API_SECRET']),
        TWILIO_CHAT_SERVICE_SID=os.environ.get('TWILIO_CHAT_SERVICE_SID', None),
        TWILIO_SYNC_SERVICE_SID=os.environ.get('TWILIO_SYNC_SERVICE_SID', None),
    )

@app.route('/token', methods=['GET'])
def randomToken():
    return generateToken(fake.user_name())


@app.route('/token', methods=['POST'])
def createToken():
    # Get the request json or form data
    content = request.get_json() or request.form
    # get the identity from the request, or make one up
    identity = content.get('identity', fake.user_name())
    return generateToken(identity)

@app.route('/token/<identity>', methods=['POST', 'GET'])
def token(identity):
    return generateToken(identity)

def generateToken(identity):
    # get credentials for environment variables
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    api_key = os.environ['TWILIO_API_KEY']
    api_secret = os.environ['TWILIO_API_SECRET']
    sync_service_sid = os.environ.get('TWILIO_SYNC_SERVICE_SID', 'default')
    chat_service_sid = os.environ.get('TWILIO_CHAT_SERVICE_SID', None)

    # Create access token with credentials
    token = AccessToken(account_sid, api_key, api_secret, identity=identity)

    # Create a Sync grant and add to token
    if sync_service_sid:
        sync_grant = SyncGrant(service_sid=sync_service_sid)
        token.add_grant(sync_grant)

    # Create a Video grant and add to token
    # video_grant = VideoGrant()
    # token.add_grant(video_grant)

    # Create an Chat grant and add to token
    # if chat_service_sid:
    #     chat_grant = ChatGrant(service_sid=chat_service_sid)
    #     token.add_grant(chat_grant)

    # Return token info as JSON
    return jsonify(identity=identity, token=token.to_jwt().decode('utf-8'))




# Notify - create a device binding from a POST HTTP request
# @app.route('/register', methods=['POST'])
# def register():
#     # get credentials for environment variables
#     account_sid = os.environ['TWILIO_ACCOUNT_SID']
#     api_key = os.environ['TWILIO_API_KEY']
#     api_secret = os.environ['TWILIO_API_SECRET']
#     service_sid = os.environ['TWILIO_NOTIFICATION_SERVICE_SID']
#
#     # Initialize the Twilio client
#     client = Client(api_key, api_secret, account_sid)
#
#     # Body content
#     content = request.get_json()
#
#     content = snake_case_keys(content)
#
#     # Get a reference to the notification service
#     service = client.notify.services(service_sid)
#
#     # Create the binding
#     binding = service.bindings.create(**content)
#
#     print(binding)
#
#     # Return success message
#     return jsonify(message="Binding created!")

# # Notify - send a notification from a POST HTTP request
# @app.route('/send-notification', methods=['POST'])
# def send_notification():
#     # get credentials for environment variables
#     account_sid = os.environ['TWILIO_ACCOUNT_SID']
#     api_key = os.environ['TWILIO_API_KEY']
#     api_secret = os.environ['TWILIO_API_SECRET']
#     service_sid = os.environ['TWILIO_NOTIFICATION_SERVICE_SID']
#
#     # Initialize the Twilio client
#     client = Client(api_key, api_secret, account_sid)
#
#     service = client.notify.services(service_sid)
#
#     # Get the request json or form data
#     content = request.get_json() if request.get_json() else request.form
#
#     content = snake_case_keys(content)
#
#     # Create a notification with the given form data
#     notification = service.notifications.create(**content)
#
#     return jsonify(message="Notification created!")

@app.route('/<path:path>')
def static_file(path):
    return app.send_static_file(path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
