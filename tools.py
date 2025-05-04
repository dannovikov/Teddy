import os
import subprocess
import logging


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


def mv(src: str, dest: str) -> str:
    """
    Moves a file or directory from src to dest and returns a success message.
    """
    if not os.path.exists(src):
        return f"Error: The source {src} does not exist."
    try:
        os.rename(src, dest)
        return f"Moved {src} to {dest}"
    except Exception as e:
        return f"Error: Could not move {src} to {dest}. {e}"


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
            ["uv", "run", file_path],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error: Could not execute Python file {file_path}. {e}"


def run_pytest(tests_dir: str) -> str:
    """
    Runs pytest command on the current directory and returns the output or an error message.
    tests_dir:str - The directory containing the tests to run. Defaults to current directory if an empty string is passed.
    If the directory does not exist, it runs pytest on the current directory.This is common if the tests are at the root level.
    """

    try:
        if not tests_dir:
            tests_dir = "."
        if tests_dir != "." and os.path.exists(tests_dir):
            result = subprocess.run(
                ["uv", "run", "pytest", tests_dir], capture_output=True, text=True
            )
            logging.debug(f"tests/ output: {result.stdout.strip()}")
            return (
                "Output:\n"
                + result.stdout.strip()
                + "\nErrors:\n"
                + result.stderr.strip()
            )
        else:
            result = subprocess.run(
                ["uv", "run", "pytest"], capture_output=True, text=True
            )
            logging.debug(f"output: {result.stdout.strip()}")
            return (
                "Output:\n"
                + result.stdout.strip()
                + "\nErrors:\n"
                + result.stderr.strip()
            )
    except Exception as e:
        return f"Error: Could not run tests. {e}"


def pip_install(package: str) -> str:
    """
    Installs a Python package using pip and returns the output or an error message.
    """
    try:
        result = subprocess.run(["uv", "add", package], capture_output=True, text=True)
        if result.returncode == 0:
            return f"Package {package} installed successfully."
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error: Could not install package {package}. {e}"
