from google.adk.agents import Agent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pprint import pprint as print
import asyncio
import logging
import os

from encrypt_api import get_api_key
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
    run_pytest,
    pip_install,
)

unix_tools = [
    cd,
    ls,
    mv,
    pwd,
    mkdir,
    touch,
    read_file,
    write_file,
    pip_install,
    run_python_file,
]

# Set up the environment
os.environ["OPENAI_API_KEY"] = get_api_key(0)

APP_NAME = "teddy"
USER_ID = "dan"
SESSION_ID = "1"

logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.basicConfig(
    filename="teddy.log",
    level=logging.INFO,
)

# Define the agents that comprise Teddy's test-driven development process.
_planner = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="planner",
    description="You are a planner agent responsible for planning the big picture and tracking the little picture of the test-driven development process, setting each next step's goal. You are part of a larger cycle of agents [planner, specifier, coder, test_designer, test_runner, reviewer]. In this process, the specifier details the implementation for one small step, the coder writes it, the test_designer writes tests immediately and teh test_runner runs them, the reviewer provides feedback. Through this cycle, we implement the plan. You must speak and reflect on whether the plan is progressing and what to do next. You set the high-level plan at the start of each iteration of the test-driven development loop.",
    instruction="You are the head of a chain of agents (planner - issues tasks, specifier-specifies requirements, coder-codes, test_designer-designs tests, test_runner-writes and runs tests). Remember, one feature, one unit test. Steps should be given one step at a time. Define and track the plan. Where are we, and what's the concrete next step in this interative test-driven development process? Lastly, once the user's task is completely fulfilled, issue the termination token 'TASK_COMPLETE'. ",
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

_specifier = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="specifier",
    description="You are a specifier agent responsible for specifying how the current unit of planned code needs to be implemented, so that the coder has unambiguous instructions. You are part of a larger cycle of agents [planner, specifier, coder, test_designer, test_runner, reviewer]. You take high-level implementation steps and break them down into concrete implementation requirements for a single unit of code for the coder.",
    instruction="You are a specifier agent responsible for specifying how the current unit of planned code needs to be implemented, so that the coder has unambiguous instructions. You are part of a larger cycle of agents [planner, specifier, coder, test_designer, test_runner, reviewer]. Your job is to take high-level implementation steps and break them down into detailed, actionable requirements for a single unit of code for the coder. "
    "Clearly specify which files to modify and provide precise implementation details. Do not write any code yourself. "
    "Ensure that the requirements are modular and testable, and align with the overall goal of achieving 100% test coverage.",
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

_coder = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="coder",
    description="You are a coder agent responsible for programming the specification provided by the specifier. You only implement one thing, then stop and allow for testing. You are part of a larger cycle of agents [planner, specifier, coder, test_designer, test_runner, reviewer]. You write and execute Python code to implement concrete implementation requirements in a specific file.",
    instruction="You are a coder agent responsible for programming the specification provided by the specifier. You only implement one thing, then stop and allow for testing. You are part of a larger cycle of agents [planner, specifier, coder, test_designer, test_runner, reviewer]. Your responsibility is to implement the provided requirements in Python. "
    "Write modular and testable code, ensuring that it adheres to the specifications provided by the specifier. "
    "Do not design tests or review code; focus solely on implementing the requirements. Use your tools to write the code to the specified file.",
    tools=unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

_test_designer = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="test_designer",
    description="You are a test designer agent responsible designing tests for the last unit written. You are part of a larger cycle of agents [planner, specifier, coder, test_designer, test_runner, reviewer]. You design a list of tests that verify the functionality of a given piece of code.",
    instruction="What kind of tests do we need to write for the last unit of code?",
    tools=unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

_test_runner = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="test_runner",
    description="You are a test runner agent responsible for running all the unit tests. You are part of a larger cycle of agents [planner, specifier, coder, test_designer, test_runner, reviewer]. You execute tests and report the results and errors.",
    instruction="You are a test runner agent responsible for running all the unit tests. You are part of a larger cycle of agents [planner, specifier, coder, test_designer, test_runner, reviewer]. Your responsibility is to execute all tests and report the results, including any errors or failures. "
    "Track the growing list of tests and ensure that all previous tests are re-executed after each change. "
    "Do not attempt to fix code or design tests; focus solely on running tests and providing detailed feedback.",
    tools=[run_pytest] + unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

_reviewer = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="reviewer",
    # description="You are a reviewer agent responsible for verifying that the tests did indeed pass and the code does indeed look good. Provide feedback. You are part of a larger cycle of agents [planner, specifier, coder, test_designer, test_runner, reviewer]. You review the code and suggest improvements if needed.",
    description="You are a reviewer agent responsible for verifying that the tests did indeed pass and the code does indeed look good. Provide feedback. "
    "Focus on ensuring that the code is modular, testable, and adheres to best practices. Do not write or execute code yourself.",
    instruction="You are a reviewer agent responsible for verifying that the tests did indeed pass and the code does indeed look good. Provide feedback. You are part of a larger cycle of agents [planner, specifier, coder, test_designer, test_runner, reviewer]. Your job is to review the code and test results to ensure they meet the required standards. Make sure a unit test was written for the current code and that it passed. If not, say so and insist that the planner makes the next cycle about creating a test for the last code. "
    "Suggest improvements if necessary and sign off on the code when it is ready to be committed to the codebase. "
    "Summarize how each step of the test-driven development process was successful. "
    "Focus on ensuring that the code is modular, testable, and adheres to best practices. Do not write or execute code yourself.",
    tools=unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

system = LoopAgent(
    name="system",
    description="Loops Teddy 20 times, and then stops.",
    max_iterations=20,
    sub_agents=[_planner, _specifier, _coder, _test_designer, _test_runner, _reviewer],
)


# Create a Runner
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
)
runner = Runner(agent=system, app_name=APP_NAME, session_service=session_service)

async def task():
    task = "build a program that allows me to track my spending by exposing an interface where i can submit new transactions via the command line. These transactions are captured and added to the list of transactions upon which statistics will be calculated and a report will be generated. In testing, generate dummy data and ensure each step of the code works. For persistance, save the transactions in a csv on the hard drive."
    task += " Make your code very modular, and have 100% test coverage writing python pytest tests as test_* in the root directory such that the pytest command will pick them up. Code should never contain input statements, and should be able to run without any user input. "
    await call_agent_async(task)

# Function that runs the agent and parses and logs its events.
async def call_agent_async(query):
    content = types.Content(role="user", parts=[types.Part(text=query)])
    logging.info(f"Running query: {query}")
    print(f"\n--- Running Query: {query} ---")
    final_response_text = "No final text response captured."
    try:
        async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=content
        ):
            has_specific_part = False
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text and not part.text.isspace():
                        if "TASK_COMPLETE" in part.text:
                            logging.info(
                                f"[{event.author}] Task Complete: {part.text.strip()}"
                            )
                            print(
                                f"[{event.author}] Task Complete: {part.text.strip()}"
                            )
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
                            print(
                                f"[{event.author}]Function call: {part.function_call.name, part.function_call.args}"
                            )
                        else:
                            logging.info(
                                f"[{event.author}]Function call: {part.function_call.name, part.function_call.args}"
                            )
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
                    logging.info(
                        f"[{event.author}]==> Final Agent Response: {final_response_text}"
                    )
                    print(
                        f"[{event.author}]==> Final Agent Response: {final_response_text}"
                    )
                else:
                    logging.info(
                        f"[{event.author}]==> Final Agent Response: [No text content in final event]"
                    )
                    print(
                        f"[{event.author}]==> Final Agent Response: [No text content in final event]"
                    )
            logging.info("" * 50)
            print("-" * 50)

    except Exception as e:
        logging.error(f"ERROR during agent run: {e}")
        print(f"ERROR during agent run: {e}")
    logging.info("-" * 50)
    print("-" * 50)



asyncio.run(task())
