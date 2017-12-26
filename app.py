import os
from flask import Flask, jsonify, request, Response
from faker import Factory
from twilio.rest import Client
import json
from twilio.twiml.voice_response import VoiceResponse, Dial, Conference, Say, Play
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
customer_sid = ''
conference_sid = ''
manager_sid=''

@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/inbound_call', methods=['GET','POST'])
def inbound_call():
    response = VoiceResponse()
    with Dial() as dial:
        if request.values.get('From') == Moderator:
            global agent_sid


            agent_sid = request.values.get('CallSid')
            print(agent_sid + ' is the agent sid')
            dial.conference('AgentConference', status_callback="/statuscallback", status_callback_event="start end join leave mute hold")
        else:
            global customer_sid
            customer_sid = request.values.get('CallSid')
            print(customer_sid + ' is the customer sid')
            dial.conference('AgentConference', wait_url="/hold_message", end_conference_on_exit=True, status_callback="/statuscallback", status_callback_event="start end join leave mute hold")

    response.append(dial)

    return str(response)

@app.route("/hold_message", methods=['POST', 'GET'])
def hold_message():
    response = VoiceResponse()
    response.say("Thank you for calling customer service. We will connect you with an agent shortly", voice='alice')
    response.play("http://com.twilio.music.guitars.s3.amazonaws.com/Pitx_-_Long_Winter.mp3", loop=10)

    return str(response)


@app.route("/monitor_call", methods=["GET", "POST"])
def monitor():
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token=os.environ['AUTH_TOKEN']
    sync_service_sid=os.environ['TWILIO_SYNC_SERVICE_SID']

    client = Client(account_sid, auth_token)

    global manager_sid

    manager_sid = request.values.get('CallSid');
    print(manager_sid + ' is the manager_sid')

    new_data = {
        'manager_sid' : manager_sid
    }

    document = client.sync \
        .services(sync_service_sid) \
        .documents("AgentData") \
        .update(data=new_data)

    response = VoiceResponse()
    dial = Dial()

    dial.conference('AgentConference', muted=True, beep=False, status_callback="/statuscallback", status_callback_event="start end join leave mute hold")

    response.append(dial)

    return str(response)

@app.route("/barge", methods=['POST','GET'])
def barge():
    print("posted to barge doc")

    print(conference_sid + ' is my conference and ' + manager_sid + ' is the manager sid')
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token=os.environ['AUTH_TOKEN']

    client = Client(account_sid, auth_token)

    participant = client.conferences(conference_sid) \
                    .participants(manager_sid) \
                    .update(muted="False")

    return ''

@app.route('/update', methods=['POST'])
def update():
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token=os.environ['AUTH_TOKEN']

    client = Client(account_sid, auth_token)

    call = client.calls(manager_sid).update(url="/whisper", method="POST")

    return ''

@app.route('/whisper' , methods=['POST'])
def whisper():

    response = VoiceResponse()
    dial = Dial()

    dial.conference('AgentConference', beep=False, coach=agent_sid ,status_callback="/statuscallback", status_callback_event="start end join leave mute hold")

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

    call_status = request.values.get('StatusCallbackEvent')
    print(call_status)

    print(request.values.get('ConferenceSid') + ' is the conference sid')
    global conference_sid
    conference_sid = request.values.get('ConferenceSid')


    this_call = request.values.get('CallSid');

    if this_call == agent_sid:
        new_data = {
            "agent_sid" : agent_sid,
            "conference_sid" : conference_sid,
            "call_status" : call_status
        }
    else:
        new_data = {
            "customer_sid" : customer_sid,
            "call_status" : call_status
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

    return jsonify(identity=identity, token=token.to_jwt().decode('utf-8'))





@app.route('/<path:path>')
def static_file(path):
    return app.send_static_file(path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
