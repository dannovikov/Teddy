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
    mv,
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

unix_tools = [cd, ls, mv, pwd, mkdir, touch, read_file, write_file, pip_install]
_directory_navigator = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="directory_navigator",
    description="You are a directory navigator agent responsible for handling anything to do with directories and files. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. You manage and answer questions about the directory structure. "
    "You can create, move, and delete files and directories. You can also read the contents of files. Ensure that everything happens at the root directory. ",
    instruction="You are a directory navigator agent responsible for handling anything to do with directories and files. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. Your primary responsibility is to manage the directory structure. "
    "You can create, move, and delete files and directories, and read file contents. Always ensure that operations are performed at the root directory. "
    "Maintain a clean and organized structure to support modular and testable code development.",
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
    description="You are a specifier agent responsible for specifying anything that needs to be coded. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. You take high-level implementation steps and break them down into concrete implementation requirements for a single unit of code for the coder.",
    instruction="You are a specifier agent responsible for specifying anything that needs to be coded. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. Your job is to take high-level implementation steps and break them down into detailed, actionable requirements for a single unit of code for the coder. "
    "Clearly specify which files to modify and provide precise implementation details. Do not write any code yourself. "
    "Ensure that the requirements are modular and testable, and align with the overall goal of achieving 100% test coverage.",
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)


def specifier(query: str, tool_context: ToolContext) -> None:
    """
    Should not be called. tranfer_to_agent should be used instead.
    But if it is, it just calls the transfer to agent function instead.
    """
    tool_context.actions.transfer_to_agent = "specifier"
    return "WARNING: You called the agent as a tool. Don't do this. Use transfer_to_agent.\nTransfering to specifier agent..."


specifier = FunctionTool(func=specifier)

_coder = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="coder",
    description="You are a coder agent responsible for programming the specification provided by the specifier. You only implement one thing, then stop and allow for testing. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. You write and execute Python code to implement concrete implementation requirements in a specific file.",
    instruction="You are a coder agent responsible for programming the specification provided by the specifier. You only implement one thing, then stop and allow for testing. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. Your responsibility is to implement the provided requirements in Python. "
    "Write modular and testable code, ensuring that it adheres to the specifications provided by the specifier. "
    "Do not design tests or review code; focus solely on implementing the requirements. Use your tools to write the code to the specified file.",
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
    return "WARNING: You called the agent as a tool. Don't do this. Use transfer_to_agent.\nTransfering to coder agent..."


coder = FunctionTool(func=coder)

_test_designer = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="test_designer",
    description="You are a test designer agent responsible designing tests for the last unit written. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. You design a list of tests that verify the functionality of a given piece of code.",
    instruction="You are a test designer agent responsible designing tests for the last unit written. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. Your job is to design a comprehensive list of tests that verify the functionality of the provided code. "
    "Focus on edge cases and ensure that the tests cover all aspects of the code's behavior. "
    "Do not write the test code yourself; instead, specify the tests for the specifier and coder to implement. "
    "Ensure that the tests are structured for pytest and stored in the root directory for easy detection.",
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
    return "WARNING: You called the agent as a tool. Don't do this. Use transfer_to_agent.\nTransfering to test_designer agent..."


test_designer = FunctionTool(func=test_designer)

_test_runner = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="test_runner",
    description="You are a test runner agent responsible for running all the unit tests. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. You execute tests and report the results and errors.",
    instruction="You are a test runner agent responsible for running all the unit tests. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. Your responsibility is to execute all tests and report the results, including any errors or failures. "
    "Track the growing list of tests and ensure that all previous tests are re-executed after each change. "
    "Do not attempt to fix code or design tests; focus solely on running tests and providing detailed feedback.",
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
    return "WARNING: You called the agent as a tool. Don't do this. Use transfer_to_agent.\nTransfering to test_runner agent..."


test_runner = FunctionTool(func=test_runner)

_reviewer = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="reviewer",
    # description="You are a reviewer agent responsible for verifying that the tests did indeed pass and the code does indeed look good. Provide feedback. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. You review the code and suggest improvements if needed.",
    description="You are a reviewer agent responsible for verifying that the tests did indeed pass and the code does indeed look good. Provide feedback. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. Your job is to review the code and test results to ensure they meet the required standards. Make sure a unit test was written for the current code and that it passed. If not, say so and insist that the planner makes the next cycle about creating a test for the last code. "
    "Suggest improvements if necessary and sign off on the code when it is ready to be committed to the codebase. "
    "Before issuing the termination token 'TASK_COMPLETE', summarize how each step of the test-driven development process was successful. "
    "Focus on ensuring that the code is modular, testable, and adheres to best practices. Do not write or execute code yourself.",
    instruction="You are a reviewer agent responsible for verifying that the tests did indeed pass and the code does indeed look good. Provide feedback. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. Your job is to review the code and test results to ensure they meet the required standards. Make sure a unit test was written for the current code and that it passed. If not, say so and insist that the planner makes the next cycle about creating a test for the last code. "
    "Suggest improvements if necessary and sign off on the code when it is ready to be committed to the codebase. "
    "Before issuing the termination token 'TASK_COMPLETE', summarize how each step of the test-driven development process was successful. "
    "Focus on ensuring that the code is modular, testable, and adheres to best practices. Do not write or execute code yourself.",
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
    return "WARNING: You called the agent as a tool. Don't do this. Use transfer_to_agent.\nTransfering to reviewer agent..."


reviewer = FunctionTool(func=reviewer)


# teddy = Agent(
#     model=LiteLlm(model="openai/gpt-4.1-nano"),
#     name="Teddy",
#     description="You are Teddy, a programming assistant. You follow an iterative code, test, fix, review, repeat process to implement requests via your team of agents. ",
#     instruction="You are Teddy, the orchestrator of a programming team that follows an iterative code, test, fix, review loop to implement code. "
#     "Your primary goal is to ensure that every user request is implemented correctly, modularly, and with 100% test coverage.\n\n"
#     "Your workflow is as follows:\n"
#     "1. Plan: Break down the user request into smaller, manageable tasks and outline the steps to complete them.\n"
#     "2. Specify: Transfer the task to the 'specifier' agent to generate concrete implementation requirements.\n"
#     "3. Code: Transfer the requirements to the 'coder' agent to write the necessary code.\n"
#     "4. Test Design: Transfer the code to the 'test_designer' agent to create a list of tests that verify its functionality.\n"
#     "5. Test Specification: Transfer the test design to the 'specifier' agent to specify the implementation of the tests.\n"
#     "6. Test Implementation: Transfer the test specifications to the 'coder' agent to write the tests.\n"
#     "7. Test Execution: Transfer the tests to the 'test_runner' agent to execute them and report results.\n"
#     "8. Review: Transfer the code and test results to the 'reviewer' agent to review and suggest improvements.\n"
#     "9. Repeat: Iterate through the loop until the task is complete.\n\n"
#     "Important Notes:\n"
#     "- Don't do the work yourself. Always transfer tasks to the appropriate agents.\n"
#     "- Always ensure that tests are written in a pytest structure and stored in the root directory such that pytest can detect them and avoiding import issues.\n"
#     "- Maintain a growing list of tests that are executed after each change.\n"
#     "- Whenever you regain control, summarize the current progress and outline the next step.\n"
#     "- Use the termination token 'TASK_COMPLETE' when the task is fully implemented and verified. \n"
#     "- If it is, provide a summary of how every stop was followed alongside the termination token.\n"
#     "- A complete task will have 100% test coverage and be modular.\n"
#     "- Remember to instruct each agent to do a single small step only, so that we can test between each one.\n",
#     sub_agents=[
#         _directory_navigator,
#         _specifier,
#         _coder,
#         _test_designer,
#         _test_runner,
#         _reviewer,
#     ],
#     # tools=[directory_navigator, specifier, coder, test_designer, test_runner, reviewer],
# )

# system = LoopAgent(
#     name="system",
#     description="Loops Teddy 50 times, and then stops.",
#     max_iterations=20,
#     sub_agents=[teddy],
# )

planner = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="planner",
    description="You are a planner agent responsible for planning the big picture and tracking the little picture of the test-driven development process, setting each next step's goal. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. In this process, the specifier details the implementation for one small step, the coder writes it, the test_designer writes tests immediately and teh test_runner runs them, the reviewer provides feedback. Through this cycle, we implement the plan. You must speak and reflect on whether the plan is progressing and what to do next. You set the high-level plan at the start of each iteration of the test-driven development loop.",
    instruction="You are a planner agent responsible for planning the big picture and tracking the little picture of the test-driven development process, setting each next step's goal. You are part of a larger cycle of agents [planner, directory_navigator, specifier, coder, test_designer, test_runner, reviewer]. In this process, the specifier details the implementation for one small step, the coder writes it, the test_designer writes tests immediately and teh test_runner runs them, the reviewer provides feedback. Through this cycle, we implement the plan. You must speak and reflect on whether the plan is progressing and what to do next. Your responsibility is to set the high-level plan at the start of each iteration of the test-driven development loop. "
    "Break down the user request into smaller, manageable tasks and outline the steps to complete them. "
    "Ensure that the plan aligns with the goal of achieving modular, testable code with 100% test coverage."
    "Before issuing the termination token 'TASK_COMPLETE', summarize how each step of the test-driven development process was successful and confirm that the task is fully implemented and verified."
    "If we're stuck in a loop, with agents not making progress, suggest an action step for a specific agent to get us unstuck. Don't let agents ask for the contents of files, they have functions to read and write files. ",
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

system = LoopAgent(
    name="system",
    description="Loops Teddy 20 times, and then stops.",
    max_iterations=20,
    sub_agents=[planner,_directory_navigator, _specifier, _coder, _test_designer, _test_runner, _reviewer],
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
                        print(f"[{event.author}]{part.text.strip()}", compact=True)
                    elif part.function_response:
                        print(
                            f"[{event.author}]Function response: {part.function_response.name, part.function_response.response}"
                        )
                    elif part.function_call:
                        if event.author == "coder":
                            print(
                                f"[{event.author}]Function call: {part.function_call.name, part.function_call.args}"
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
    # task = input("What would you like Teddy to build?\n>")
    # task = "Write a program that accepts a stock ticker (default AAPL) and plots its daily closing price history in the terminal as ascii art."
    task = "build a program that allows me to track my spending by exposing an interface where i can submit new transactions via the command line. These transactions are captured and added to the list of transactions upon which statistics will be calculated and a report will be generated. In testing, generate dummy data and ensure each step of the code works. For persistance, save the transactions in a csv on the hard drive."
    task += " Make your code very modular, and have 100% test coverage writing python pytest tests as test_* in the root directory such that the pytest command will pick them up. Code should never contain input statements, and should be able to run without any user input. "
    await call_agent_async(task)


asyncio.run(main())
