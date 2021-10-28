import configparser
import json
import sys

import requests

from chatbot import *


# Store credentials in a separate file
def gather_credentials():
    cp = configparser.ConfigParser()
    try:
        cp.read('credentials.ini')
        org_key = cp.get('meraki', 'key1')
        cam_key = cp.get('meraki', 'key2')
        if cam_key == '':
            cam_key = org_key
        org_id = cp.get('meraki', 'organization')
        labels = cp.get('meraki', 'cameras')
        if labels != '':
            labels = labels.split(',')
            cameras = [label.strip() for label in labels]
        else:
            cameras = []
        chatbot_token = cp.get('chatbot', 'token')
        user_email = cp.get('chatbot', 'email')
        lab_key = cp.get('provisioning', 'key')
        lab_org = cp.get('provisioning', 'org')
    except:
        print('Missing credentials or input file!')
        sys.exit(2)
    return org_key, cam_key, org_id, cameras, chatbot_token, user_email, lab_key, lab_org


# Main Lambda function
def lambda_handler(event, context):
    # Import user credentials
    (org_key, cam_key, org_id, cameras, chatbot_token, user_email, lab_key, lab_org) = gather_credentials()
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': f'Bearer {chatbot_token}'
    }
    session = requests.Session()

    # Webhook event/metadata received, so now retrieve the actual message for the event
    webhook_event = json.loads(event['body'])
    print(webhook_event)

    # Continue to process message
    message = get_message(session, webhook_event, headers)

    # Webhook event data
    chatbot_id = get_chatbot_id(session, headers)
    user_id = webhook_event['actorId']
    sender_emails = get_emails(session, user_id, headers)
    payload = {'roomId': webhook_event['data']['roomId']}
    
    # Process standard messages
    # Stop if last message was bot's own, or else loop to infinite & beyond!
    if user_id == chatbot_id:
        return {'statusCode': 204}

    # Prevent other users from using personal bot
    elif user_email not in sender_emails:
        post_message(session, headers, payload,
                    f'Hi **{get_name(session, user_id, headers)}**, I\'m not allowed to chat with you! ⛔️')
        return {'statusCode': 200}

    else:
        print(f'Message received: {message}')

        # Create & send response depending on input message
        if message_begins(message, ['hi', 'hello', 'hey', 'help', 'syn', 'test', 'meraki', '?']):
            post_message(session, headers, payload,
                        f'Hi **{get_name(session, user_id, headers)}**! _{message}_ ACKed. ✅')

        # Get org-wide device statuses
        elif message_contains(message, ['org', 'device', 'status', 'online']):
            try:
                # Yes, not PEP 8, but for the sake of modular components & CYOA...
                import status
                status.device_status(session, headers, payload, org_key)

            except ModuleNotFoundError:
                post_message(session, headers, payload, 'You need to include the **status** module first! 🙄')

        # Post camera snapshots
        elif message_contains(message, ['cam', 'photo', 'screen', 'snap', 'shot']):
            try:
                # Yes, not PEP 8, but for the sake of modular components & CYOA...
                import snapshot
                snapshot.return_snapshots(session, headers, payload, cam_key, org_id, message, cameras)

            except ModuleNotFoundError:
                post_message(session, headers, payload, 'You need to include the **snapshot** module first! 🤦')

        # Clear screen to reset demos
        elif message_begins(message, ['clear']):
            clear_screen(session, headers, payload)

        # Catch-all if bot doesn't understand the query!
        else:
            post_message(session, headers, payload, 'Make a wish! 🤪')

    # Let chat app know success
    return {
        'statusCode': 200,
        'body': json.dumps('message received')
    }
