import boto3
import uuid

# Replace these with actual values
agentId = "your-agent-id"
agentAliasId = "your-alias-id"
region = "us-west-2"

def invoke(query):
    client = boto3.client("bedrock-agent-runtime", region_name=region)
    session_id = str(uuid.uuid4())

    try:
        response = client.invoke_agent(
            agentId=agentId,
            agentAliasId=agentAliasId,
            sessionId=session_id,
            inputText=query
        )

        completion = response.get("completion", "No response received.")
        
        return {
            "message": completion,
            "trace": "(Trace not available in this version)",
            "citations": []  # Could be extracted from trace if needed later
        }

    except Exception as e:
        print("Error:", e)
        return {
            "message": "Apologies, there was an error while processing your request.",
            "trace": str(e),
            "citations": []
        }
