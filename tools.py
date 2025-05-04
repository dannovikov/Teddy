import os
import subprocess


def read_file(file_path: str) -> str:
    """
    Reads the contents of a file and returns it as a string.
    """
    if not os.path.exists(file_path):
        return f"Error: The file {file_path} does not exist."

    with open(file_path, "r") as file:
        return file.read()


def write_file(file_path: str, content: str) -> str:
    """
    Writes the given content to a file and returns a success message.
    """
    try:
        with open(file_path, "w") as file:
            file.write(content)
        return f"Content written to {file_path}"
    except Exception as e:
        return f"Error: Could not write to file {file_path}. {e}"


def cd(path: str) -> str:
    """
    Changes the current working directory to the specified path and returns the new path.
    """
    if not os.path.exists(path):
        return f"Error: The path {path} does not exist."
    try:
        os.chdir(path)
        return os.getcwd()
    except Exception as e:
        return f"Error: Could not change directory to {path}. {e}"


def ls(path: str) -> str:
    """
    Lists the contents of the specified directory as a single string.
    """
    if not path:
        path = "."
    if not os.path.exists(path):
        return f"Error: The path {path} does not exist."
    try:
        return "\n".join(os.listdir(path))
    except Exception as e:
        return f"Error: Could not list contents of {path}. {e}"


def pwd() -> str:
    """
    Returns the current working directory.
    """
    try:
        return os.getcwd()
    except Exception as e:
        return f"Error: Could not retrieve current working directory. {e}"


def mkdir(directory_path: str) -> str:
    """
    Creates a new directory at the specified path and returns a success message.
    """
    if os.path.exists(directory_path):
        return f"Error: The directory {directory_path} already exists."
    try:
        os.makedirs(directory_path)
        return f"Directory {directory_path} created."
    except Exception as e:
        return f"Error: Could not create directory {directory_path}. {e}"


def touch(file_path: str) -> str:
    """
    Creates an empty file at the specified path and returns a success message.
    """
    try:
        with open(file_path, "a"):
            pass
        return f"File {file_path} created."
    except Exception as e:
        return f"Error: Could not create file {file_path}. {e}"


def run_python_file(file_path: str) -> str:
    """
    Executes a Python file and returns the output or an error message.
    """
    if not os.path.exists(file_path):
        return f"Error: The file {file_path} does not exist."

    try:
        # run the python file and capture the output and return it
        result = subprocess.run(
            ["python", file_path],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error: Could not execute Python file {file_path}. {e}"


def run_tests() -> str:
    """
    Runs pytest command on the current directory and returns the output or an error message.
    """

    try:
        result = subprocess.run(["uv", "run", "pytest"], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error: Could not run tests. {e}"
"""

Creating the Tool¶
Define your generator function and wrap it using the LongRunningFunctionTool class:


from google.adk.tools import LongRunningFunctionTool

# Define your generator function (see example below)
def my_long_task_generator(*args, **kwargs):
    # ... setup ...
    yield {"status": "pending", "message": "Starting task..."} # Framework sends this as FunctionResponse
    # ... perform work incrementally ...
    yield {"status": "pending", "progress": 50}               # Framework sends this as FunctionResponse
    # ... finish work ...
    return {"status": "completed", "result": "Final outcome"} # Framework sends this as final FunctionResponse

# Wrap the function
my_tool = LongRunningFunctionTool(func=my_long_task_generator)
Intermediate Updates¶
Yielding structured Python objects (like dictionaries) is crucial for providing meaningful updates. Include keys like:

status: e.g., "pending", "running", "waiting_for_input"

progress: e.g., percentage, steps completed

message: Descriptive text for the user/LLM

estimated_completion_time: If calculable
-----------------


Using the above documentation, lets define this pytest run as a long running function tool.
I want to expose underlying process's output to the user, so they can see the progress of the tests as they run.
"""


def _run_tests():
    """
    Runs all test files in the current directory and returns the output or an error message.
    """
    if not os.path.exists("tests"):
        yield "Error: The tests directory does not exist."
        return
    if not os.path.isdir("tests"):
        yield "Error: The tests path is not a directory."
        return

    try:
        # run pytest in such a way as to stream the output back out here asynchronously
        # and yield each line of output as a separate message
        process = subprocess.Popen(
            ["uv", "run", "pytest", "tests"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                yield {"status": "running", "message": output.strip()}
        rc = process.poll()
        if rc == 0:
            yield {"status": "completed", "result": "All tests passed."}
        else:
            yield {"status": "failed", "result": f"Tests failed with return code {rc}."}
    except Exception as e:
        yield {"status": "error", "message": f"Error: Could not run tests. {e}"}

