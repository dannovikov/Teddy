from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pprint import pprint as print
import logging


# Function that runs the agent and parses and logs its events.
async def call_agent_async(query, agent, app_name, user_id, session_id):
    # Create a Runner
    session_service = InMemorySessionService()
    session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)

    content = types.Content(role="user", parts=[types.Part(text=query)])
    logging.info(f"Running query: {query}")
    print(f"\n--- Running Query: {query} ---")
    final_response_text = "No final text response captured."
    try:
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            has_specific_part = False
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text and not part.text.isspace():
                        if "TASK_COMPLETE" in part.text:
                            logging.info(f"[{event.author}] Task Complete: {part.text.strip()}")
                            print(f"[{event.author}] Task Complete: {part.text.strip()}")
                            return
                        logging.info(f"[{event.author}] {part.text.strip()}")
                        print(f"[{event.author}]{part.text.strip()}", compact=True)
                    elif part.function_response:
                        logging.info(
                            f"[{event.author}]Function response: {part.function_response.name, part.function_response.response}"
                        )
                        print(
                            f"[{event.author}]Function response: {part.function_response.name, part.function_response.response}"
                        )
                    elif part.function_call:
                        if event.author == "coder":
                            logging.info(
                                f"[{event.author}]Function call: {part.function_call.name, part.function_call.args}"
                            )
                            print(f"[{event.author}]Function call: {part.function_call.name, part.function_call.args}")
                        else:
                            logging.info(
                                f"[{event.author}]Function call: {part.function_call.name, part.function_call.args}"
                            )
                            print(f"[{event.author}]Function call: {part.function_call.name, part.function_call.args}")
            if not has_specific_part and event.is_final_response():
                if event.content and event.content.parts and event.content.parts[0].text:
                    final_response_text = event.content.parts[0].text.strip()
                    logging.info(f"[{event.author}]==> Final Agent Response: {final_response_text}")
                    print(f"[{event.author}]==> Final Agent Response: {final_response_text}")
                else:
                    logging.info(f"[{event.author}]==> Final Agent Response: [No text content in final event]")
                    print(f"[{event.author}]==> Final Agent Response: [No text content in final event]")
            logging.info("" * 50)
            print("-" * 50)

    except Exception as e:
        logging.error(f"ERROR during agent run: {e}")
        print(f"ERROR during agent run: {e}")
    logging.info("-" * 50)
    print("-" * 50)
