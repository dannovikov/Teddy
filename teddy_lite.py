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
if not os.path.exists("workdir"):
    os.mkdir("workdir")
os.chdir('workdir')

logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.basicConfig(
    filename="teddy_lite.log",
    level=logging.INFO,
)


logging.info("Starting Teddy...")


# Agents

_planner = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="planner",
    description="You plan and track the test-driven development process.",
    instruction=(
        "Write a global plan and then track each next step in the test-driven development process. "
        "Give clear, actionable instructions, always leaving the work to the other agents. "
        "The termination token is 'TASK_COMPLETE.'"
    ),
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
    tools=[cd, ls, pwd, read_file, run_pytest]
)

_coder = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="coder",
    description="You write one unit of code at a time by calling write_file.",
    instruction=(
        "Write one unit of code at a time. "
        "Use `write_file` to save code to disk. "
        "If editing, read the file first with `read_file` and then save changes with `write_file`. "
        "Stop after writing the code to allow testing."
    ),
    tools=unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)

_tester = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="tester",
    description="You design and run tests for the coder's work.",
    instruction=(
        "Write unit tests for the coder's code and save them to a file. "
        "Run the tests using `run_pytest` and report the results. "
        "Focus only on testing and providing feedback; do not fix the code."
    ),
    tools=unix_tools,
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)


_aligner = Agent(
    model=LiteLlm(model="openai/gpt-4.1-nano"),
    name="aligner",
    description="You break loops and get the system unstuck.",
    instruction=(
        "If agents are stuck (e.g., repeating tasks, asking questions, or not acting), "
        "say: 'GUYS, YOU ARE STUCK IN A LOOP. PLANNER, ISSUE A NEW TASK TO A SPECIFIC AGENT.' "
        "If no loop is detected, say `Continue` and nothing else."
    ),
    disallow_transfer_to_peers=True,
    disallow_transfer_to_parent=True,
)


system = LoopAgent(
    name="system",
    description="Loops Teddy 20 times, and then stops.",
    max_iterations=20,
    sub_agents=[_planner, _coder, _tester,_aligner],
)


async def task():

    task = "Create a python program thats takes two locations (say, nyc to chicago), "
    "and gives the weather along the road trip route between those locations. "
    "First, it should get the route from google maps. Then, it should collect locations at one hour intervals along the route. "
    "Then, it should get the weather for each of those locations. Finally, it should print the hour and the weather for each location. "
    task += " Make your code very modular, and pytest testable with complete code coverage. At least 3 tests. Code should never contain input statements, no GUIs, no servers or other blocking code. It should always run without any user input. "
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
