from google.adk.agents import Agent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool, ToolContext
from google.genai import types
from tools import (
    read_file,
    write_file,
    cd,
    ls,
    pwd,
    mkdir,
    touch,
    run_python_file,
    run_tests,
    pip_install,
)
import asyncio
from pprint import pprint as print


from encrypt_api import get_api_key
import os

APP_NAME = "teddy"
USER_ID = "dan"
SESSION_ID = "1"

os.environ["OPENAI_API_KEY"] = get_api_key(0)

unix_tools = [cd, ls, pwd, mkdir, touch, read_file, write_file, pip_install]
_directory_navigator = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="directory_navigator",
    description="Can be transfered to using transfer_to_agent. You are a directory navigator agent. You manage and answer questions about the directory structure. "
    "You can create, move, and delete files and directories. You can also read the contents of files. Ensure that everything happens at the root directory. ",
    tools=unix_tools,
    instruction="You are a directory navigator agent. You manage and answer questions about the directory structure. "
    "You can create, move, and delete files and directories. You can also read the contents of files. Ensure that everything happens at the root directory. ",
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)


def directory_navigator(query: str, tool_context: ToolContext) -> None:
    """
    Should not be called. tranfer_to_agent should be used instead.
    But if it is, it just calls the transfer to agent function instead.
    """
    tool_context.actions.transfer_to_agent = "directory_navigator"
    return "WARNING: You called the agent as a tool. Don't do this. Use transfer_to_agent.\nTransfering to directory_navigator agent..."


directory_navigator = FunctionTool(func=directory_navigator)


_specifier = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="specifier",
    description="Can be transfered to using transfer_to_agent. You are a specifier agent. You take high level implementation steps and break them down into more concrete implementation requirements for the coder.",
    instruction="You are a specifier agent. You take high level implementation steps and break them down into more concrete implementation requirements for the coder. The coder needs to know which files he is modifying and what exactly the implementation requiremts are. Your job is to bridge the high level instructions into concrete code requirements. But, do not write any code yourself. Just say your specification and leave that to the coder.",
    tools=[cd, ls, pwd, read_file],
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)


def specifier(query: str, tool_context: ToolContext) -> None:
    """
    Should not be called. tranfer_to_agent should be used instead.
    But if it is, it just calls the transfer to agent function instead.
    """
    tool_context.actions.transfer_to_agent = "specifier"
    return "Transfering to specifier agent..."


specifier = FunctionTool(func=specifier)

_coder = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="coder",
    description="Can be transfered to using transfer_to_agent. An agent that writes and executes Python code to implement concrete implementation requirements in a specific file.",
    instruction="""You are a code agent.
    You will be given a concrete implementation requirement and a file in which to write it,
    Your job is to generate code to implement those requirements in Python.
    Implement the requirements and write the code to the file by using your tools.
    Testing will be done by other agents. Ensure your code is modular and testable.
    """,
    tools=unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)


def coder(query: str, tool_context: ToolContext) -> None:
    """
    Should not be called. tranfer_to_agent should be used instead.
    But if it is, it just calls the transfer to agent function instead.
    """
    tool_context.actions.transfer_to_agent = "coder"
    return "Transfering to coder agent..."


coder = FunctionTool(func=coder)

_test_designer = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="test_designer",
    description="Can be transfered to using transfer_to_agent. You are a test designer agent. You take a piece of code and design a list of tests that verify its functionality. "
    "You leave the implementation details to the specifier and coder. Ensure these tests get written to a file by coder.",
    instruction="You are a test designer. You take a piece of code and design a list of tests that verify its functionality. "
    "You leave the implementation details to the specifier and coder. Do not attempt to write the code. Specify the tests and leave that to the other agents.",
    tools=unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)


def test_designer(query: str, tool_context: ToolContext) -> None:
    """
    Should not be called. tranfer_to_agent should be used instead.
    But if it is, it just calls the transfer to agent function instead.
    """
    tool_context.actions.transfer_to_agent = "test_designer"
    return "Transfering to test_designer agent..."


test_designer = FunctionTool(func=test_designer)

_test_runner = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="test_runner",
    description="Can be transfered to using transfer_to_agent. You are a test runner agent. You run the tests and report the results and errors. Can also be used to run a python file."
    "You track the growing list of tests and run all previous tests.",
    instruction="You are a test runner. You run the tests and report the results and errors. Do not attempt to fix the code. Leave that to the other agents."
    "You track the growing list of tests and run all previous tests.",
    tools=[run_python_file, run_tests] + unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)


def test_runner(query: str, tool_context: ToolContext) -> None:
    """
    Should not be called. tranfer_to_agent should be used instead.
    But if it is, it just calls the transfer to agent function instead.
    """
    tool_context.actions.transfer_to_agent = "test_runner"
    return "Transfering to test_runner agent..."


test_runner = FunctionTool(func=test_runner)

_reviewer = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="reviewer",
    description="Can be transfered to using transfer_to_agent. You are a reviewer agent. You review the code and suggest improvements if needed. "
    "You sign off on a piece of code and commit it to the codebase.",
    instruction="You are a reviewer. You review the code and suggest improvements if needed. "
    "You sign off on a piece of code and commit it to the codebase.",
    tools=unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)


def reviewer(query: str, tool_context: ToolContext) -> None:
    """
    Should not be called. tranfer_to_agent should be used instead.
    But if it is, it just calls the transfer to agent function instead.
    """
    tool_context.actions.transfer_to_agent = "reviewer"
    return "Transfering to reviewer agent..."


reviewer = FunctionTool(func=reviewer)


teddy = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="Teddy",
    description="You are Teddy, a programming assistant. You follow an iterative code, test, fix, review, repeat process to implement requests via your team of agents. ",
    instruction="You are Teddy, the orchestrator of a programming team that follows an iterative code, test, fix, review loop to implement code. "
    "Your primary goal is to ensure that every user request is implemented correctly, modularly, and with 100% test coverage.\n\n"
    "Your workflow is as follows:\n"
    "1. Plan: Break down the user request into smaller, manageable tasks and outline the steps to complete them.\n"
    "2. Specify: Transfer the task to the 'specifier' agent to generate concrete implementation requirements.\n"
    "3. Code: Transfer the requirements to the 'coder' agent to write the necessary code.\n"
    "4. Test Design: Transfer the code to the 'test_designer' agent to create a list of tests that verify its functionality.\n"
    "5. Test Specification: Transfer the test design to the 'specifier' agent to specify the implementation of the tests.\n"
    "6. Test Implementation: Transfer the test specifications to the 'coder' agent to write the tests.\n"
    "7. Test Execution: Transfer the tests to the 'test_runner' agent to execute them and report results.\n"
    "8. Review: Transfer the code and test results to the 'reviewer' agent to review and suggest improvements.\n"
    "9. Repeat: Iterate through the loop until the task is complete.\n\n"
    "Important Notes:\n"
    "- Don't do the work yourself. Always transfer tasks to the appropriate agents.\n"
    "- Always ensure that tests are written in a pytest structure and stored in the root directory such that pytest can detect them and avoiding import issues.\n"
    "- Maintain a growing list of tests that are executed after each change.\n"
    "- Whenever you regain control, summarize the current progress and outline the next step.\n"
    "- Use the termination token 'TASK_COMPLETE' when the task is fully implemented and verified. \n"
    "- If it is, provide a summary of how every stop was followed alongside the termination token.\n"
    "- A complete task will have 100% test coverage and be modular.\n"
    "- Remember to instruct each agent to do a single small step only, so that we can test between each one.\n",
    sub_agents=[
        _directory_navigator,
        _specifier,
        _coder,
        _test_designer,
        _test_runner,
        _reviewer,
    ],
    tools=[directory_navigator, specifier, coder, test_designer, test_runner, reviewer],
)

system = LoopAgent(
    name="system",
    description="Loops Teddy 50 times, and then stops.",
    max_iterations=20,
    sub_agents=[teddy],
)


session_service = InMemorySessionService()
session = session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
)
runner = Runner(agent=system, app_name=APP_NAME, session_service=session_service)


# Agent Interaction (Async)
async def call_agent_async(query):
    content = types.Content(role="user", parts=[types.Part(text=query)])
    print(f"\n--- Running Query: {query} ---")
    final_response_text = "No final text response captured."
    try:
        # Use run_async
        async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=content
        ):
            has_specific_part = False
            if event.content and event.content.parts:
                for part in event.content.parts:  # Iterate through all parts
                    if part.text and not part.text.isspace():
                        if "TASK_COMPLETE" in part.text:
                            print(
                                f"[{event.author}] Debug: Task Complete: {part.text.strip()}"
                            )
                            return
                        print(f"[{event.author}]{part.text.strip()}")
                    elif part.function_response:
                        print(
                            f"[{event.author}]Function response: {part.function_response.name, part.function_response.response}"
                        )
                    elif part.function_call:
                        if event.author == "coder":
                            print(
                                f"[{event.author}]Function call: {part.function_call.name, part.function_call.args.keys()}"
                            )
                        else:
                            print(
                                f"[{event.author}]Function call: {part.function_call.name, part.function_call.args}"
                            )
            if not has_specific_part and event.is_final_response():
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    final_response_text = event.content.parts[0].text.strip()
                    print(
                        f"[{event.author}]==> Final Agent Response: {final_response_text}"
                    )
                else:
                    print(
                        f"[{event.author}]==> Final Agent Response: [No text content in final event]"
                    )

    except Exception as e:
        print(f"ERROR during agent run: {e}")
    print("-" * 30)


# Main async function to run the examples
async def main():
    # await call_agent_async(
    #     "Write a program main.py to calculate the value of (1+1) * 2 the quantity factorial using only for loops and addition. Make your code very modular, and have 100% test coverage writing python pytest tests as test_* in the root directory such that the pytest command will pick them up. Feel free to use more common methods to generate test cases, but the codebase must not use these methods besides for loops and addition. Be careful as factorial takes a long time, so never test with more than 6!"
    # )
    # lets try a more complex example
    task = "Write a program that accepts a stock ticker (default AAPL) and plots its daily closing price history in the terminal as ascii art."
    task += " Make your code very modular, and have 100% test coverage writing python pytest tests as test_* in the root directory such that the pytest command will pick them up. "
    await call_agent_async(task)


asyncio.run(main())
