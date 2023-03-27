from flask import Flask, request
import functions_framework
from google.cloud import pubsub_v1
import logging
logging.basicConfig(level=logging.INFO)
import json
import os
import hashlib
import datetime

PROJECT_ID = os.environ.get('PROJECT_ID')

APP = Flask("internal")
EVENT_BUS = os.environ["EVENT_BUS"]
ENTITY = "user"
#with open("command.json") as fs:
#    ARGS_DEFINITION = json.load("commands.json")
ARGS_DEFINITION = {
    "create-user": {
        "args": {
            "userId": "undefined",
            "author": "undefined",
            "authorizedCommands": []
        },
        "endpoint":"https://user-commands-ai32xjq4va-ew.a.run.app/create"
    },
    "assign-conversation": {
        "args": {
            "author": "undefined",
            "conversationId": "undefined",
            "channel": "undefined",
            "userId": "undefined",
            "conversationList": "activeConversations"
        },
        "endpoint":"https://user-commands-ai32xjq4va-ew.a.run.app/assign-conversation"
    },
    "remove-conversation": {
        "args": {
            "author": "undefined",
            "conversationId": "undefined",
            "channel": "undefined",
            "userId": "undefined",
            "conversationList": "activeConversations"
        },
        "endpoint":"https://user-commands-ai32xjq4va-ew.a.run.app/remove-conversation"
    },
    "retrieve-spoke": {
        "args": {
            "author": "undefined",
            "spokeId": "undefined",
            "brain": "gpt-3.5-turbo"
        },
        "endpoint":"https://user-commands-ai32xjq4va-ew.a.run.app/retrieve-spoke"
    }
}

def publish_message(author:str, operation:str, entityId:str, payload:str):
    """
    This function publishes the message.
    Parameters:
        conversation_id: The ID of the conversation
        author: Who is publishing the message (user_id)
        message: The message to publish
    """
    message = {
        "author": author,
        "entity": ENTITY,
        "entityId": entityId,
        "operation": operation,
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "payload": payload
    }
    message_json = json.dumps(message).encode("utf-8")
    print("Publishing ", message_json)
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, EVENT_BUS)
    publish_future = publisher.publish(topic_path,
                                        data=message_json)
    publish_future.result()

@APP.route('/', methods=['GET', 'POST'])
def unknown_operation():
    response = APP.response_class(
        response="Incomplete path, please select an operation",
        status=400,
        mimetype='text/plain')
    return response

@APP.route('/create', methods=['POST', ])
def create_user():
    logging.info("Received request to create user: {}".format(request))
    request_json = json.loads(request.data)
    author = request_json['author']
    authorizedCommands = request_json['authorizedCommands']

    def _create_id():
        # Concatenate variables and timestamp
        data = author + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        # Hash the data
        return hashlib.sha256(data.encode()).hexdigest()
    
    user_id = request_json['userId'] if request_json['userId'] != "undefined" else _create_id()
    logging.info("Creating user: {} with auth commands {}".format(user_id, authorizedCommands))
    publish_message(author=author, entityId=user_id, operation="create",
                    payload=json.dumps({"authorizedCommands": authorizedCommands,
                                        **{key: request_json[key] for key in request_json.keys() if key not in ARGS_DEFINITION["create-user"]["args"].keys()}}))
    response = APP.response_class(
        response=json.dumps({"payload":{"userId": user_id}, "responseMessage":"Created user {id} with auth commands {comm}".format(id=user_id,comm=authorizedCommands)}),
        status=200,
        mimetype='application/json') 
    return response

@APP.route('/assign-conversation', methods=['POST', ])
def assign_conversation():
    logging.info("Received request to assign conversation: {}".format(request))
    request_json = json.loads(request.data)
    author = request_json['author']
    conversation_id = request_json['conversationId']
    user_id = request_json['userId']
    channel = request_json["channel"]
    conversation_list = request_json['conversationList']
    logging.info("Assigning conversation: {} to user: {} in list: {}".format(conversation_id, user_id, conversation_list))
    publish_message(author=author, entityId=user_id, operation="assignConversation",
                    payload=json.dumps({"channel": channel, "conversationId": conversation_id, "conversationList": conversation_list,
                                        **{key: request_json[key] for key in request_json.keys() if key not in ARGS_DEFINITION["assign-conversation"]["args"].keys()}}))
    response = APP.response_class(
        response=json.dumps({"payload":{"userId": user_id, "conversationId": conversation_id}, "responseMessage":"Assigned conversation {conv} to user {user} in channel {channel}".format(conv=conversation_id,user=user_id, channel=channel)}),
        status=200,
        mimetype='application/json') 
    return response

@APP.route('/retrieve-spoke', methods=['POST', ])
def retrieve_spoke():
    logging.info("Received request to assign conversation: {}".format(request))
    request_json = json.loads(request.data)
    author = request_json['author']
    user_id = request_json['userId']
    spokeId = request_json["spokeId"]
    brain = request_json['brain']
    logging.info("Assigning spoke: {} to user: {}".format(spokeId, user_id))
    publish_message(author=author, entityId=user_id, operation="retrieveSpoke",
                    payload=json.dumps({"spokeId": spokeId, "brain": brain,
                                        **{key: request_json[key] for key in request_json.keys() if key not in ARGS_DEFINITION["assign-conversation"]["args"].keys()}}))
    response = APP.response_class(
        response=json.dumps({"payload":{"userId": user_id, "spokeId": spokeId}, "responseMessage":"Assigned spoke {spokeId} to user {user}".format(spokeId=spokeId,user=user_id, channel=channel)}),
        status=200,
        mimetype='application/json') 
    return response
    
    
@functions_framework.http
def user_commands(request):
    internal_ctx = APP.test_request_context(path=request.full_path,
                                            method=request.method)
    internal_ctx.request.data = request.data
    internal_ctx.request.headers = request.headers
    internal_ctx.request.args = request.args
    
    APP.config['PRESERVE_CONTEXT_ON_EXCEPTION']=False
    
    return_value = APP.response_class(
        response="Invalid Request", 
        status=400,
        mimetype='text/plain')
    
    try:
        internal_ctx.push()
        return_value = APP.full_dispatch_request()
        logging.info("Request processed: {}".format(return_value))
        internal_ctx.pop()
    except Exception as e:
        logging.error(e)
    return return_value