"""
    Copyright (C) 2022 - Rokas Puzonas <rokas.puz@gmail.com>

    This file is part of KTU OOP Report Generator.

    KTU OOP Report Generator is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    KTU OOP Report Generator is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with KTU OOP Report Generator. If not, see <https://www.gnu.org/licenses/>.
"""
from typing import Optional
import os.path as path
from glob import glob
import os
import subprocess
from subprocess import PIPE, CalledProcessError
import stat
from threading import Thread
from queue import Queue,Empty
import time
from shutil import copytree, rmtree
import contextlib
import time

@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    yield
    os.chdir(previous_dir)

def is_project_root(project_root: str) -> bool:
    """
    Returns true if given directory contains a .csproj file
    """
    return path.isdir(project_root) and len(glob(path.join(project_root, "*.csproj"))) > 0

def find_executable(directory: str) -> Optional[str]:
    """
    Find file which is executable in directory. Or try guess which file should
    be the executable by .dll ending.
    """
    # Try searching for a file which is marked as executable
    for filename in glob(path.join(directory, "*")):
        if os.access(filename, os.X_OK):
            return filename

    # If this is some older .NET version if it isin't marked, find .dll file
    # And mark it as executable
    possible_executables = glob(path.join(directory, "*.dll"))
    if len(possible_executables) > 0:
        executable = possible_executables[0]
        os.chmod(executable, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
        return executable

def build_project(project_root: str, output_directory: str, cli_args: list[str] = []) -> Optional[str]:
    """
    Build C# project using dotnet cli and output it to given directory
    """
    cmd = ["dotnet", "build", project_root, "-o", output_directory, *cli_args]
    process = subprocess.run(cmd, shell=False)

    # If failed to compile
    if process.returncode != 0:
        print(process.stderr)
        return None

    executable = find_executable(output_directory)
    if not executable:
        return None

    return executable

def simple_execute(executable: str, stdin_lines: list[str] = []):
    """
        Execute using subprocess.check_output, this will get the output from the
        process, but the output won't included anything that was provided through
        stdin.

        If you wan't to merge stdin and stdout, use `complex_execute`.
    """
    try:
        stdout = subprocess.check_output(
            ["./"+path.basename(executable)],
            input = "\n".join(stdin_lines).encode("utf-8")
        )

        return 0, stdout.decode("utf-8")
    except CalledProcessError as e:
        return e.returncode, e.output.decode("utf-8")

def read_bit(stdout, queue):
    for c in iter(lambda:stdout.read(1),''):
        queue.put(c)
    stdout.close()

def get_data(queue):
    r = ''
    while True:
        try:
            c = queue.get(False)
        except Empty:
            break
        else:
            r += c
    return r

def complex_execute(executable: str, stdin_lines: list[str] = []):
    proc = subprocess.Popen(["./"+path.basename(executable)], shell=False, universal_newlines=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    assert proc.stdin

    q = Queue()
    t = Thread(target=read_bit,args=(proc.stdout,q))
    t.daemon = True
    t.start()

    stdout = ""
    while True:
        time.sleep(0.2)
        stdout += get_data(q)
        if not t.is_alive or len(stdin_lines) == 0:
            break
        stdin = stdin_lines.pop()
        proc.stdin.write(stdin)
        proc.stdin.write('\n')
        stdout += stdin + '\n'
        proc.stdin.flush()

    return proc.returncode, stdout

def run_test(executable: str, test_folder: str):
    assert os.access(executable, os.X_OK), "Excpected to be able to run executable, insufficient permissions"
    assert path.isdir(test_folder), "Failed to verify that given test folder is a folder"

    working_directory = path.dirname(executable)

    # Remove unneeded files, that might still be around from last test
    for item in os.listdir(working_directory):
        if not item.startswith(executable):
            if path.isfile(item):
                os.remove(item)
            elif path.isdir(item):
                rmtree(item)

    # copy current test files
    copytree(test_folder, working_directory, dirs_exist_ok=True)

    # Run program
    with pushd(working_directory):

        # Check if stdin is given
        stdin_lines = []
        if path.isfile("stdin.txt"):
            with open("stdin.txt", "r") as f:
                stdin_lines = f.read().strip().splitlines()
            os.remove("stdin.txt")

        # The simple version is used, when you don't need to merge stdin
        # and stdout into a single text blob
        if len(stdin_lines) == 0:
            return simple_execute(executable)
        else:
            return complex_execute(executable, stdin_lines)

def list_test_files(executable: str) -> list[str]:
    working_directory = path.dirname(executable)

    test_files = []
    for root, _, files in os.walk(working_directory, topdown=True):
        for file in files:
            fullpath = path.join(root, file)
            if not fullpath.startswith(executable):
                test_files.append(fullpath)

    return test_files
