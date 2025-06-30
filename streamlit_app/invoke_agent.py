import boto3
import uuid

agentId = "your-agent-id"
agentAliasId = "your-alias-id"
region = "us-west-2"

def invoke(query):
    client = boto3.client("bedrock-agent-runtime", region_name=region)
    session_id = str(uuid.uuid4())

    try:
        response_stream = client.invoke_agent(
            agentId=agentId,
            agentAliasId=agentAliasId,
            sessionId=session_id,
            inputText=query
        )

        # ✅ Now read the streaming response
        full_response = ""
        for chunk in response_stream["completion"]:
            if hasattr(chunk, "completion"):
                full_response += chunk.completion

        return {
            "message": full_response or "No response received.",
            "trace": "(Trace not available in this version)",
            "citations": []
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "message": "Apologies, there was an error while processing your request.",
            "trace": str(e),
            "citations": []
        }
