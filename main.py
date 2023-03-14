import os
import logging
import json
import firebase_admin
from firebase_admin import firestore
import functions_framework
from typing import Dict
import base64

PROJECT_ID = os.environ.get('PROJECT_ID')
EVENT_BUS = os.environ.get('EVENT_BUS')
ENTITY = "conversation"
APP = firebase_admin.initialize_app()

def _create_user(user_id:str, payload:Dict):
    logging.info("Creating user {}".format(user_id))
    firestore_client = firestore.client()
    firestore_client.collection(u'users').document(user_id).set({
        u'activeConversations': {},
        u'ownedConversations': {},
        u'authorizedCommands': payload['authorizedCommands']
    })
    logging.info("Created")

def _delete_conversation(user_id:str, conversation_list:str, conversation_id: str):
    logging.info("Deleting conversation from {}".format(conversation_list))
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection(u'users').document(user_id)
    doc = doc_ref.get().to_dict()
    doc.update({conversation_list:{key: doc[conversation_list][key] for key in doc[conversation_list].keys() if doc[conversation_list][key]!=conversation_id}})
    doc_ref.set(doc)
    logging.info("Deleted")

def _assign_conversation(user_id:str, conversation_list:str, conversation_id: str, channel:str):
    logging.info("Deleting conversation from {}".format(conversation_list))
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection(u'users').document(user_id)
    doc = doc_ref.get().to_dict()
    doc.update({conversation_list:{channel: conversation_id}})
    doc_ref.set(doc)
    logging.info("Deleted")

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def conversation_manager(cloud_event):
    event = json.loads(base64.b64decode(cloud_event.data["message"]["data"]).decode())
    if event['entity']==ENTITY:
        payload = json.loads(event['payload'])
        if event['operation']=="deleteConversation":
            _delete_conversation(user_id=event['entityId'], conversation_list=payload['conversationList'], conversation_id=payload["conversationId"])
        elif event['operation']=="assignConversation":
            _assign_conversation(user_id=event['entityId'], conversation_list=payload['conversationList'], conversation_id=payload["conversationId"], channel=payload["channel"])
        elif event['operation']=="create":
            _create_user(user_id=event['entityId'], payload=json.loads(event["payload"]))