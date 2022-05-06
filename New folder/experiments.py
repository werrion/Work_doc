import allure
import pytest
import os
import glob
import shutil
from datetime import timedelta, datetime, time
from time import sleep
from retry import retry
import random
from models.params import *
from models.additional_scripts import *
from models.additional_test_actions import *

# if __name__ == '__main__':
#
# here = os.path.abspath(os.path.dirname(__file__))
# print(here)
# dt_now = datetime.utcnow()
# dt_now_local = datetime.now()
# print(dt_now)
# print(dt_now_local)

#    t = os.path.getmtime(filename)
#     return datetime.datetime.fromtimestamp(t)
#
# file = open('test.txt', 'r')
# l = [line.strip() for line in file]
# print(l)
# print(len(l))
# print(l[1])

# internet on\off by scripts
# os.system('netsh interface set interface "Ethernet" enable')
# os.system('netsh interface set interface "Ethernet" disable')

# WORKDIR = '1'
# def first_f():
#     global WORKDIR
#     WORKDIR = 'test'
# def second_f():
#     print(WORKDIR)
#
# first_f()
# second_f()
from pathlib import Path
# filename = Path("some_file.txt")
# path = Path("C:/Users/sselt/Documents/blog_demo")
# print(path_with_offset(path, level=1))
# path = Path(os.getcwd())
# # print( path / filename )
# # print(os.path.abspath(os.path.join('..')))
# # script_path = Path(os.getcwd()) / Path("ABUtility.exe")
# # print(os.path.dirname(os.path.abspath(__file__)))
# print(os.getcwd())
# print(path)
# print(path.parent)
# print(path.parents[0])
# print(path.parents[3])
#
# generate 10k commands for set var or logs
# i = 0
# list_commands = []
# while i < 40000:
#     list_commands.append("log custom " + f"Test_test_test__test__test__Test_test__test__test__test__test__test_{i}")
#     i += 1
# file = open('logs1.txt', 'w')
# for item in list_commands:
#     file.write(item + '\n')
# file.close()
#
# check file size
# print(os.path.getsize(Values.binary_1))
#
# print(os.environ['PYTHONPATH'])
# print(os.environ['OS'])
# o_s = 'mac'
# if o_s == 'Windows_NT':
#     print(os.getcwd() + r"\ABUtility.exe")
# else:
#     print(os.getcwd() + r"/ABUtility.exe")
#
#
# workingDir = os.path.abspath
# print(workingDir)
# print(os.path)
#
# i = 0
# list_commands = []
# while i < 450:
#     list_commands.append("set UserProfile.var[0]" + f" Test_test_test_0{i}")
#     list_commands.append("set UserProfile.var[1]" + f" Test_test_test_1{i}")
#     list_commands.append("log error" + f" error_log_text__{i}")
#     i += 1
# file = open('logs1.txt', 'w')
# for item in list_commands:
#     file.write(item + '\n')
# file.close()

# ############################################################
# del_super_user_data()
# change_project_xml_for_env('QA')
# del_data_from_groups_and_groups_overrides()


# add_super_user_data_by_type('int', 'UserProfile.super10', '1')
# add_super_user_data_by_type('int64', 'UserProfile.super11', '11111111111111')
# add_super_user_data_by_type('bool', 'UserProfile.super12', 'True')
# add_super_user_data_by_type('datetime', 'UserProfile.super13', '2099-01-01 01:01:01')
# add_super_user_data_by_type('float', 'UserProfile.super15', '1.1')


############################################################
# local_path = os.path.abspath(os.path.dirname(__file__))
# print(type(local_path))
# check_utility_file_update()
print("Path ", Path('c:', 'workspace', 'workspace'))
boo = Path('c:', 'workspace', 'workspace')
foo = Path('c:/workspace/workspace')
print(boo)
print(foo)
if boo != foo:
    print("!=")
else:
    print("==")
