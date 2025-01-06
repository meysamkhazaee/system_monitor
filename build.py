import os
import subprocess
import system_monitor  # Import your script to access __version__

# Get the version
version = system_monitor.__version__

# Define the output executable name
exe_name = f"system_monitor_{version}"

# Build the command for pyinstaller
command = [
    "pyinstaller",
    "--onefile",
    f"--name={exe_name}",
    "system_monitor.py"
]

# Run the command
subprocess.run(command)

print(f"Executable generated: dist/{exe_name}")
