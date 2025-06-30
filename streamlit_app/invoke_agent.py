import boto3
import uuid

agentId = "your-agent-id"         # ✅ your real agent ID
agentAliasId = "your-alias-id"    # ✅ your real alias ID
region = "us-west-2"

def invoke(query):
    client = boto3.client("bedrock-agent-runtime", region_name=region)
    session_id = str(uuid.uuid4())

    try:
        # Start agent invocation
        response_stream = client.invoke_agent(
            agentId=agentId,
            agentAliasId=agentAliasId,
            sessionId=session_id,
            inputText=query
        )

        # ✅ Extract completion from EventStream correctly
        full_response = ""
        for event in response_stream["completion"]:
            event_type = getattr(event, "event_type", None)

            if event_type == "completion":
                full_response += getattr(event, "completion", "")
            elif event_type == "trace":
                # You can log trace if needed
                pass

        if not full_response:
            full_response = "⚠️ Agent returned no content. Check fallback or KB linkage."

        return {
            "message": full_response,
            "trace": "(Trace not captured in this version)",
            "citations": []
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "message": "❌ Error occurred while processing your request.",
            "trace": str(e),
            "citations": []
        }
