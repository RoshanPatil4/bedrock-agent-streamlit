import os
import json
import base64
import io
import sys
import boto3
import re

from boto3.session import Session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from requests import request

# ---------------------------------------------------------------------
# Replace with your actual Agent ID and Alias ID below:
# ---------------------------------------------------------------------
agentId = "<YOUR AGENT ID>"  # <-- Replace this
agentAliasId = "<YOUR AGENT ALIAS ID>"  # <-- Replace this

# ---------------------------------------------------------------------
# REGION CONFIGURATION:
# ---------------------------------------------------------------------
theRegion = "us-west-2"
os.environ["AWS_REGION"] = theRegion

# ---------------------------------------------------------------------
# HELPER FUNCTION TO GET AWS CREDENTIALS SAFELY
# ---------------------------------------------------------------------
def get_frozen_credentials():
    session = Session()
    creds = session.get_credentials()
    if not creds:
        raise EnvironmentError("No AWS credentials found.")
    return creds.get_frozen_credentials()

# ---------------------------------------------------------------------
# SIGNED REQUEST FUNCTION
# ---------------------------------------------------------------------
def sigv4_request(url, method='GET', body=None, params=None, headers=None, service='execute-api', region=None, credentials=None):
    if region is None:
        region = os.environ.get("AWS_REGION", "us-west-2")
    if credentials is None:
        credentials = get_frozen_credentials()

    req = AWSRequest(method=method, url=url, data=body, params=params, headers=headers)
    SigV4Auth(credentials, service, region).add_auth(req)
    prepared_req = req.prepare()

    return request(
        method=prepared_req.method,
        url=prepared_req.url,
        headers=prepared_req.headers,
        data=prepared_req.body
    )

# ---------------------------------------------------------------------
# ASK QUESTION / INVOKE AGENT
# ---------------------------------------------------------------------
def askQuestion(question, url, endSession=False):
    myobj = {
        "inputText": question,
        "enableTrace": True,
        "endSession": endSession
    }

    response = sigv4_request(
        url,
        method='POST',
        service='bedrock',
        headers={
            'content-type': 'application/json',
            'accept': 'application/json',
        },
        region=theRegion,
        body=json.dumps(myobj)
    )

    return decode_response(response)

# ---------------------------------------------------------------------
# DECODE RESPONSE FROM STREAM
# ---------------------------------------------------------------------
def decode_response(response):
    captured_output = io.StringIO()
    sys.stdout = captured_output

    string = ""
    for line in response.iter_content():
        print("Raw chunk:", line)
        try:
            string += line.decode(encoding='utf-8')
        except:
            continue

    print("Decoded response:", string)
    split_response = string.split(":message-type")
    final_response = ""

    for idx in range(len(split_response)):
        if "bytes" in split_response[idx]:
            encoded = split_response[idx].split("\"")[3]
            decoded = base64.b64decode(encoded)
            final_response_chunk = decoded.decode('utf-8')
            print(final_response_chunk)
        else:
            print(split_response[idx])

    last_response = split_response[-1]
    if "bytes" in last_response:
        encoded = last_response.split("\"")[3]
        decoded = base64.b64decode(encoded)
        final_response = decoded.decode('utf-8')
    else:
        try:
            part1 = string[string.find('finalResponse') + len('finalResponse":'):]
            part2 = part1[:part1.find('"}') + 2]
            final_response = json.loads(part2)['text']
        except:
            final_response = "No response received."

    final_response = final_response.replace("\"", "").replace("{input:{value:", "").replace(",source:null}}", "")
    sys.stdout = sys.__stdout__
    captured_string = captured_output.getvalue()

    return captured_string, final_response

# ---------------------------------------------------------------------
# EXTRACT CITATIONS
# ---------------------------------------------------------------------
def extract_citations_from_trace(trace_text):
    citations = []
    try:
        doc_blocks = re.findall(r'\{[^{}]*documentTitle[^{}]*\}', trace_text)
        for block in doc_blocks:
            title_match = re.search(r'documentTitle[\'"]?\s*:\s*[\'"]([^\'"]+)[\'"]', block)
            link_match = re.search(r'documentLocation[\'"]?\s*:\s*[\'"]([^\'"]+)[\'"]', block)
            title = title_match.group(1) if title_match else "Untitled Document"
            link = link_match.group(1) if link_match else "#"
            citations.append({"documentTitle": title, "documentLink": link})
    except Exception as e:
        print("Citation parsing error:", e)
    return citations

# ---------------------------------------------------------------------
# LAMBDA HANDLER (for local or Lambda use)
# ---------------------------------------------------------------------
def lambda_handler(event, context):
    sessionId = event["sessionId"]
    question = event["question"]
    endSession = event.get("endSession", False)

    print(f"Session: {sessionId} asked: {question}")

    url = f'https://bedrock-agent-runtime.{theRegion}.amazonaws.com/agents/{agentId}/agentAliases/{agentAliasId}/sessions/{sessionId}/text'

    try:
        trace_data, response = askQuestion(question, url, endSession)
        citations = extract_citations_from_trace(trace_data)

        return {
            "status_code": 200,
            "body": json.dumps({
                "response": response,
                "trace_data": trace_data,
                "citations": citations
            })
        }
    except Exception as e:
        return {
            "status_code": 500,
            "body": json.dumps({
                "error": str(e),
                "trace_data": "",
                "citations": []
            })
        }
