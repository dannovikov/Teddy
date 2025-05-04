from google.adk.agents import Agent, LoopAgent
from google.adk.models.lite_llm import LiteLlm
import asyncio
import logging
import os

# Local imports
from encrypt_api import get_api_key
from utils import call_agent_async
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

# Setup

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
    run_pytest,
]


APP_NAME = "teddy"
USER_ID = "dan"
SESSION_ID = "1"

os.environ["OPENAI_API_KEY"] = get_api_key(0)

logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.basicConfig(
    filename="teddy.log",
    level=logging.INFO,
)


logging.info("Starting Teddy...")

# Agents

_planner = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="planner",
    description="You are a planner agent responsible for planning the big picture and tracking "
    "the little picture of the test-driven development process, setting each next step's goal. "
    "You are part of a larger cycle of agents [planner, specifier, coder, tester, reviewer]. "
    "In this process, the specifier details the implementation for one small step, the coder writes it, "
    "the tester writes tests immediately and runs them, the reviewer provides feedback. "
    "Through this cycle, we implement the plan. You must speak and reflect on whether the plan "
    "is progressing and what to do next. You set the high-level plan at the start of each iteration "
    "of the test-driven development loop.",
    instruction="Be brief. Do not ask any questions. Give orders and keep the process moving. "
    "Start by asking each of the agents to introduce themselves and what they do. You are the "
    "head of a chain of agents (planner - issues tasks, specifier-specifies requirements, "
    "coder-codes-designs tests, tester-writes and runs tests). Remember, direct one unit of code "
    "at a time, and one unit test. Steps should be given one step at a time. Define and track the "
    "plan. Where are we, and what's the concrete next step in this interative test-driven development process? \n"
    "Occasionally, the system gets stuck, and the agents keep passing the baton, telling you"
    " to proceed, without making progress. BREAK THESE LOOPS by issuing a new task.\n "
    "Lastly, only when the user's task is completely fulfilled, RUN PYTEST one more time, and"
    " if it passes, issue the termination token 'TASK_COMPLETE'. ",
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
    tools=[run_pytest],
)

_specifier = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="specifier",
    description="You are a specifier agent responsible for specifying how the current unit of"
    " planned code needs to be implemented, so that the coder has unambiguous instructions. "
    "You are part of a larger cycle of agents [planner, specifier, coder, tester, reviewer]. "
    "You take high-level implementation steps and break them down into concrete implementation "
    "requirements for a single unit of code for the coder.",
    instruction="Be brief. You are a specifier agent responsible for specifying how the current"
    " unit of planned code needs to be implemented, so that the coder has unambiguous instructions. "
    "You are part of a larger cycle of agents [planner, specifier, coder, tester, reviewer]. "
    "Your job is to take high-level implementation steps and break them down into detailed, "
    "actionable requirements for a single unit of code for the coder. Ensure that the requirements "
    "are modular and testable, and that you are specifying only one unit of code at a time. ",
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

_coder = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="coder",
    description="You are a coder agent responsible for programming the specification "
    "provided by the specifier. You only write one unit of code at a time by "
    "writing it in a file, then stop to allow for testing. ",
    instruction="You are a coder agent. You only write one unit of code, then stop and "
    "allow for testing by future agents. Write individual code files to disk for each unit. "
    "You are part of a larger cycle of agents [planner, specifier, coder, tester, reviewer]. "
    "If there is a pending request for code to be written, it is your job to write it in a "
    "file using the write_file function. No raw code, always use write_file to write code "
    "to the disk. To edit a file, read it using read_file, then write the modified content with write_file. ",
    tools=unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

_tester = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="tester",
    description="You are a tester agent responsible for both designing and running unit tests for the last unit of "
    "code written.You are part of a larger cycle of agents [planner, specifier, coder, tester, reviewer]. "
    "Your job is to first design a list of tests that verify the functionality of a given piece of code, write "
    "them to a file, and then execute those tests to ensure they pass.",
    instruction="Be brief. You are a tester agent responsible for both designing and running unit "
    "tests for the last unit of code written. First, design a list of tests that verify the functionality of "
    "the given piece of code, and write them to a file. Then, execute those tests using the run_pytest function "
    "and report the results, including any errors or failures. Do not attempt to fix code; focus solely on "
    "designing and running tests and providing detailed feedback.",
    tools=unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

_reviewer = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="reviewer",
    description="You are a reviewer agent responsible for verifying that the tests did indeed pass and the code "
    "does indeed look good. Provide feedback. Focus on ensuring that the code is modular, testable, and adheres "
    "to best practices. Do not write or execute code yourself.",
    instruction="Be brief. You are a reviewer agent responsible for verifying that the tests did indeed pass and "
    "the code does indeed look good. Provide feedback. You are part of a larger cycle of agents "
    "[planner, specifier, coder, tester, reviewer]. Your job is to review the code and test results "
    "to ensure they"" meet the required standards. Make sure a unit test was written for the current "
    "code and that it passed. If not, say so and insist that the planner makes the next cycle about "
    "creating a test for the last code. Suggest improvements if necessary and sign off on the code "
    "when it is ready to be committed to the codebase. Summarize how each step of the test-driven "
    "development process was successful. Focus on ensuring that the code is modular, testable, and "
    "adheres to best practices. Do not write or execute code yourself.",
    tools=unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

_loopbreaker = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="loopbreaker",
    description="You are a loopbreaker agent responsible for breaking the loop of agents that "
    "are stuck in a cycle. You are part of a larger cycle of agents [planner, specifier, coder, tester, reviewer]. "
    "Your job is to identify when the agents are stuck and issue a new task to break the loop.",
    instruction="Be brief. You are a loopbreaker agent responsible for breaking the loop of agents "
    "that are stuck in a cycle. Your job is to identify when the agents are stuck and let everyone know really "
    "loudly. If you detect that the agents are not making progress, passing the batton, saying they will "
    "do thing but not, then say in all caps, 'GUYS, YOU ARE STUCK IN A LOOP. PLANNER, ISSUE A NEW TASK TO A SPECIFIC AGENT.' "
    "Do not write or execute code yourself; focus solely on breaking the loop. If there is no loop, "
    "say `Continue` and nothing else. Don't let the agents ask eachother to run specific files or "
    "commands repeatedly. If the coder is speaking but not coding, say 'Coder, stop talking and code.' ",
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

system = LoopAgent(
    name="system",
    description="Loops Teddy 20 times, and then stops.",
    max_iterations=20,
    sub_agents=[_planner, _specifier, _coder, _tester, _reviewer, _loopbreaker],
)


async def task():
    task = "build a program that allows me to track my spending by exposing an interface "
    "where i can submit new transactions via the command line. These transactions are "
    "captured and added to the list of transactions upon which statistics will be calculated "
    "and a report will be generated. In testing, generate dummy data and ensure each step of "
    "the code works. For persistance, save the transactions in a csv on the hard drive."

    task += " Make your code very modular, and have 100% test coverage writing python pytest "
    "tests as test_* in the root directory such that the pytest command will pick them up. "
    "Code should never contain input statements, and should be able to run without any user input. "
    await call_agent_async(task, system, APP_NAME, USER_ID, SESSION_ID)


if __name__ == "__main__":
    try:
        # setup - this ini avoids import errors in pytest by adding the current directory to the python path
        with open("pytest.ini", "w") as f:
            f.write("[pytest]\npythonpath = .\n")

        # run
        asyncio.run(task())

        # # teardown
        # os.remove("pytest.ini")

    except Exception as e:
        # # teardown
        # os.remove("pytest.ini")
        logging.error(f"ERROR: {e}")
        raise e
