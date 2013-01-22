'''
Created on Oct 24, 2012 for Vernier Software and Technology

@author: mbergman at x-consulting dot net


Copyright (C) 2012 Matthew Bergman

Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
and associated documentation files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, 
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or 
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING 
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''

import subprocess
import re

def run_ipconfig():
    try:
        childStderrPath = 'stderr'
        childstderr = file(childStderrPath, 'a')
        childStdinPath = 'stdin'
        childstdin = file(childStdinPath, 'a')
        
        output = subprocess.check_output(["ipconfig", "/all"],stderr=childstderr,stdin=childstdin)
        output = output.replace("\r","")
        lines = output.split("\n")
    except:
        lines = []
    return lines


def get_netmask_for_adaptor(ip):
    ipconfig = run_ipconfig()
    
    found_ip = False
    netmask = ""
    regex = "([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"
    try:
        for line in ipconfig:
            if line == "":
                continue
            if found_ip == True:
                m = re.search(regex, line)
                if m == None:
                    return ""
                netmask = m.group(1)
                break
            if ip in line:
                found_ip = True
    except:
        netmask = ""
    return netmask