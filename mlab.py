""" Call matlab code from Python.
"""
import subprocess
import time

def call(matlab_cmd):
    """ Invoke Matlab through the windows Command Prompt
        No error handling, so this could break with no notice.
        (Sorry, future users)
    """
    shell_cmd = 'matlab -nodisplay -nosplash -nodesktop -r "{}" '
    cmd = shell_cmd.format(matlab_cmd)
    status = subprocess.check_output(cmd, shell=True)
    time.sleep(5) # Wait for everything to update
