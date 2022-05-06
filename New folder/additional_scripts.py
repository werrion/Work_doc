from models.params import TimingVal
import os
import glob
import shutil
import subprocess
import psycopg2
import random
import xml.etree.ElementTree as elementTree

from pathlib import Path
from retry import retry
from datetime import timedelta, datetime
from models.init_logging import get_logger

# logging block
try:
    test_log = get_logger(__name__, file_name='test_logs')
except FileNotFoundError:
    test_log = get_logger(__name__, file_name='test_logs', log_local=True)

log = get_logger(__name__, file_name='test', log_local=True)

script_path = Path(os.getcwd()) / Path("ABUtility.exe")


def path_with_offset(path, level=0):
    # path = str(text)
    # lines = text.split('\\')
    # if level != 0:
    #     result = '\\'.join(lines[:level])
    # else:
    #     result = '\\'.join(lines[:])
    result = path.parents[level+1]
    return result


# environment block
# get parameters ip and port from project.xml
def get_config_xml_params():
    local_path = Path(os.getcwd())
    root_node = elementTree.parse(local_path / Path('data', 'project.xml')).getroot()
    list_tags = []
    for tag in root_node.findall('server'):
        ip = tag.get('host')
        port = tag.get('port')
        list_tags.append(ip)
        list_tags.append(port)
    return list_tags


# set logging tab depending on environment
def logging_tab():
    logging = ''
    if get_config_xml_params()[0] == '46.101.156.78' and get_config_xml_params()[1] == '9123':
        logging = 'logging'
    if get_config_xml_params()[0] == '46.101.156.78' and get_config_xml_params()[1] == '9023':
        logging = 'logging_UAT'
    return logging


# set profile tab depending on environment
def profile_tab():
    profile = ''
    if get_config_xml_params()[0] == '46.101.156.78' and get_config_xml_params()[1] == '9123':
        profile = 'defaultdb'
    if get_config_xml_params()[0] == '46.101.156.78' and get_config_xml_params()[1] == '9023':
        profile = 'profiles_UAT'
    return profile


# TODO need fix - change copy project.xml for change parameters in project.xml file
# save UAT or DEV project.xml to Tests\data
def change_project_xml_for_env(env):
    local_path = Path(os.getcwd())
    if env == 'DEV':
        shutil.copy2(local_path / Path('models', 'files__for_scripts', 'projectDEV.xml'),
                     local_path / Path('data', 'project.xml'))
        print("__________Change ENV for DEV!__________")
    if env == 'QA':
        shutil.copy2(local_path / Path('models', 'files__for_scripts', 'projectUAT.xml'),
                     local_path / Path('data', 'project.xml'))
        print("__________Change ENV for QA!__________")


def read_inf_result(text, check_cond='true'):
    fin_result = ''
    lines = text.split('\n')
    result = []
    if check_cond == 'true':
        for item in lines:
            result.append(item.split(' '))
            fin_result = result[:-1]
        return fin_result
    if check_cond == 'false':
        for item in lines:
            if item.count('Condition') <= 0:
                result.append(item.split(' '))
                fin_result = result[:-1]
        return fin_result


def read_inf_result_for_binary(text):
    fin_result = ''
    lines = text.split(' ')
    result = []
    for item in lines:
        result.append(item.split(' '))
        fin_result = result[:-1]
    return fin_result


# block scripts for clear before start test block


def del_test_file(param):
    if os.path.isfile(param):
        print(param)
        os.remove(param)


def del_all_profile_files(working_script_path='default'):
    if working_script_path == 'default':
        script_path_local = Path(os.getcwd())
    else:
        script_path_local = working_script_path

    print('\n' + "Remove all local User Profile data")
    files1 = glob.glob(str(script_path_local / Path('data', '*.dat')))
    files2 = glob.glob(str(script_path_local / Path('data', '*.idx')))
    order = [files1, files2]
    for step in order:
        for file in step:
            os.remove(file)


def check_dump_file_exist(dump='log_dump', working_script_path='default'):
    if working_script_path == 'default':
        script_path_local = Path(os.getcwd())
    else:
        script_path_local = working_script_path

    if dump == 'log_dump':
        return os.access(script_path_local / Path('data', 'dump', 'logger'), os.F_OK)
    if dump == 'var_dump':
        return os.access(script_path_local / Path('data', 'dump', 'varoffline'), os.F_OK)
    if dump == 'all':
        return os.access(script_path_local / Path('data', 'dump'), os.F_OK)


def del_log_dump_file(working_script_path='default'):
    if working_script_path == 'default':
        script_path_local = Path(os.getcwd())
    else:
        script_path_local = working_script_path

    order = []
    log_file = (glob.glob(str(script_path_local / Path('data', 'dump', 'logger'))))
    var_file = (glob.glob(str(script_path_local / Path('data', 'dump', 'varoffline'))))
    order.append(log_file)
    order.append(var_file)
    for step in order:
        for file in step:
            os.remove(file)
    if os.access(script_path_local / Path('data', 'dump'), os.F_OK) is True:
        os.removedirs(script_path_local / Path('data', 'dump'))


# block scripts for write temporary data thorough test


def read_from_temp_file():
    file = open('temp.txt', 'r')
    data = [line.strip() for line in file]
    file.close()
    return data


def copy_utility():
    local_path = Path(os.getcwd())
    shutil.copy2(local_path / Path('ABUtility', 'ABUtility.exe'),
                 local_path / Path('ABUtility.exe'))


def count_in_dump(param, dump='log_dump'):
    handle = ''
    local_path = Path(os.getcwd())
    if dump == 'log_dump':
        handle = open(local_path / Path('data', 'dump', 'logger'), 'r')
    if dump == 'var_dump':
        handle = open(local_path / Path('data', 'dump', 'varoffline'), 'r')
    data = handle.read()
    result = data.count(param)
    handle.close()
    return result


# request with output
# https://www.postgresql.org/docs/9.3/libpq-connect.html - keywords for psycopg2.connect
@retry(psycopg2.OperationalError, tries=2, delay=1, logger=log.debug(f"Retry by {psycopg2.OperationalError}"))
def connect_db(request, db, return_value='true', time=5):
    start_time = time_now()
    log.debug(f'Connection started at {datetime.now()} + {request}')
    con = psycopg2.connect(
        database=db,
        user="oleg.krivov",
        password="Gamer00ya32a",
        host="ab-postgresql-db1-do-user-9677929-0.b.db.ondigitalocean.com",
        port="25060",
        connect_timeout=3,
        keepalives=1,
        keepalives_idle=5,
        keepalives_interval=2,
        keepalives_count=2)
    log.debug(f'Connection established at {datetime.now()}')
    log.debug(f'Send query at {datetime.now()}')
    cur = con.cursor()
    cur.execute(request)

    if return_value == 'true':
        reg = cur.fetchall()
        log.debug(f'Data received at {datetime.now()}')
        con.close()
        log.debug(f'Result Query: {str(reg)}')
        log.debug(f'Connection closed at {datetime.now()}')
        log.debug("Connection execution time = " + str(time_now() - change_time(start_time, 'seconds', 0)) + '\n')
        assert time_now() <= change_time(start_time, 'seconds', time), f"""Time DB query takes too long! 
        Connection execution time = {time_now() - change_time(start_time, 'seconds', 0)} Must <={time}""" + '\n'
        return reg

    if return_value == 'false':
        con.commit()
        log.debug(f'Data deleting done at {datetime.now()}')
        con.close()
        log.debug(f'Connection closed (deleting data from db) at {datetime.now()}')
        log.debug("Connection execution (deleting data from db) time = " +
                  str(time_now() - change_time(start_time, 'seconds', 0)) + '\n')
        assert time_now() <= change_time(start_time, 'seconds', 3), """Time DB query takes too long! 
            Connection execution time = """ + str(
            time_now() - change_time(start_time, 'seconds', 0)) + f" Must <= 3sec " + '\n'


"""
Wipe test data from variable tables and logging tables all records 
or dell all records from indicated var tab for current user
"""


# del data all players data and add sections names for superUser
def del_data_all_tabs(arg):
    del_super_user_data()
    if arg == 'profile':
        connect_db("""DELETE FROM game_sessions Where player_id >= 0;
                       DELETE FROM login_sessions Where player_id >= 0;
                       DELETE FROM sections_int_values Where player_id >= 1;
                       DELETE FROM sections_int64_values Where player_id >= 1;
                       DELETE FROM sections_string_values Where player_id >= 1;
                       DELETE FROM sections_float_values Where player_id >= 1;
                       DELETE FROM sections_binary_values Where player_id >= 1;
                       DELETE FROM sections_bool_values Where player_id >= 1;
                       DELETE FROM sections_datetime_values Where player_id >= 1;
                       DELETE FROM players Where id >= 1;
                       DELETE FROM section_key_names Where id >= 1;
                       INSERT INTO section_key_names (id, name)
                       VALUES (1, 'UserProfile.super1');
                       INSERT INTO section_key_names (id, name)
                       VALUES (2, 'UserProfile.super2');
                       INSERT INTO section_key_names (id, name)
                       VALUES (3, 'UserProfile.super3');
                       INSERT INTO section_key_names (id, name)
                       VALUES (4, 'UserProfile.super4');
                       INSERT INTO section_key_names (id, name)
                       VALUES (5, 'UserProfile.super5');
                       INSERT INTO section_key_names (id, name)
                       VALUES (6, 'UserProfile.super6');
                       INSERT INTO section_key_names (id, name)
                       VALUES (7, 'UserProfile.super7');
                       INSERT INTO section_key_names (id, name)
                       VALUES (8, 'UserProfile.super8');
                       INSERT INTO section_key_names (id, name)
                       VALUES (9, 'UserProfile.super9');
                       INSERT INTO section_key_names (id, name)
                       VALUES (10, 'UserProfile.super10');
                       INSERT INTO section_key_names (id, name)
                       VALUES (11, 'UserProfile.super11');
                       INSERT INTO section_key_names (id, name)
                       VALUES (12, 'UserProfile.super12');
                       INSERT INTO section_key_names (id, name)
                       VALUES (13, 'UserProfile.super13');
                       INSERT INTO section_key_names (id, name)
                       VALUES (14, 'UserProfile.super14');
                       INSERT INTO section_key_names (id, name)
                       VALUES (15, 'UserProfile.super15');
                       INSERT INTO section_key_names (id, name)
                       VALUES (16, 'UserProfile.rules[0].name');
                       INSERT INTO section_key_names (id, name)
                       VALUES (17, 'UserProfile.rules[0].conditional');
                       INSERT INTO section_key_names (id, name)
                       VALUES (18, 'UserProfile.rules[0].enable');
                       INSERT INTO section_key_names (id, name)
                       VALUES (19, 'UserProfile.rules[0].onetime');""", profile_tab(), return_value='false')
        print("Clearing profile tables DONE + create name section for superuser tests")
    if arg == 'log':
        connect_db("""DELETE FROM log_custom WHERE player_id >= 0;
        DELETE FROM log_error WHERE player_id >= 0;
        DELETE FROM log_grind_end WHERE player_id >= 0;
        DELETE FROM log_debug WHERE player_id >= 0""", logging_tab(), return_value='false')
        print("Clearing logging tables DONE")


def create_new_player(working_script_path='default'):
    if working_script_path == 'default':
        script_path_local = script_path
    else:
        script_path_local = working_script_path / Path('ABUtility.exe')
    param = ["network", "1", "timing", "1", "waitto", "init", "2000", "get", "SystemLocal.sessions.login.userId",
             "get", "SystemLocal.sessions.game.id", "set", "UserProfile.money_super", "666"]
    result = subprocess.run([script_path_local, *param], stdout=subprocess.PIPE, timeout=20, encoding='utf-8')
    print("Create_new_player output: " + '\n' + str(result.stdout))
    check_exit_code(result)
    assert read_inf_result(result.stdout)[0][0] + " " + read_inf_result(result.stdout)[0][1] + " " +\
           read_inf_result(result.stdout)[0][2] != 'Event not completed', "Init not received!"
    assert float(read_inf_result(result.stdout)[0][3]) <= TimingVal.receiving_init_time, \
        "Init received time is longer than expected"
    assert quantity_output_lines(result.stdout) == 6, "Unexpected output, more lines than expected"


def register_random_player(working_script_path='default'):
    if working_script_path == 'default':
        script_path_local = script_path
    else:
        script_path_local = working_script_path / Path('ABUtility.exe')

    param = ["network", "1", "timing", "1", "waitto", "init", "2000", "register_user",
             str(random.random()), "Random_Petya", "111", "set", "UserProfile.money", "666"]
    result = subprocess.run([script_path_local, *param], stdout=subprocess.PIPE, timeout=20, encoding='utf-8')

    print('\n' + "register_random_player_output: "'\n' + str(result.stdout))
    check_exit_code(result)
    assert read_inf_result(result.stdout)[0][0] + " " + read_inf_result(result.stdout)[0][1] + " " +\
           read_inf_result(result.stdout)[0][2] != 'Event not completed', "Init not received!"
    assert float(read_inf_result(result.stdout)[0][3]) <= TimingVal.receiving_init_time, \
        "Receiving init time is longer than expected"
    assert read_inf_result(result.stdout)[1][0] + " " + read_inf_result(result.stdout)[1][2] == \
           'user registered', "Error with register random player"
    assert float(read_inf_result(result.stdout)[2][3]) <= TimingVal.register_change_user_time, \
        "Register time is longer than expected"
    assert quantity_output_lines(result.stdout) == 4, "Expected output does not match"
    if working_script_path == 'default':
        player_id = str(get_required_id('userId'))
    else:
        player_id = str(get_required_id('userId', working_script_path=working_script_path))
    print("User_id_random_player is ", player_id)


# get user params from local profile
def get_required_id(arg, working_script_path='default'):
    if working_script_path == 'default':
        script_path_local = script_path
    else:
        script_path_local = working_script_path / Path('ABUtility.exe')
    param = ''
    if arg == 'gameSessionId':
        param = 'SystemLocal.sessions.game.id'
    elif arg == 'userId':
        param = 'SystemLocal.sessions.login.userId'
    elif arg == 'loginSessionId':
        param = 'SystemLocal.sessions.login.sessionId'
    elif arg == 'email':
        param = 'SystemLocal.sessions.login.email'
    else:
        print("Need specify name of needed ID - for example gameSessionId or userId or loginSessionId ... ")
    key_param = ["network", "0", "timing", "1"]
    command = 'get'
    section_var = param
    result = subprocess.run([script_path_local, *key_param, command, section_var],
                            stdout=subprocess.PIPE, timeout=20, encoding='utf-8')
    # print("Output get_required_id: " + (param.split('.'))[3] + '\n' + str(result.stdout))
    print('\n' + "get_required_id: "'\n' + str(result.stdout))
    check_exit_code(result)
    return read_inf_result(result.stdout, check_cond='false')[0][0]


# time scripts block
"""
Time_unit - can be weeks, days, hours, minutes, seconds 
value can be - positive and negative, for example 1, -2 and other
for example change_time('2021-10-06 15:20:21', "seconds", -20) or change_time(get_system_time(), "seconds", -20)
"""


def change_time(time, time_unit, value):
    if isinstance(time, datetime):
        time = str(time)
    new_time = ''
    type_date = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
    if time_unit == "weeks":
        new_time = type_date + timedelta(weeks=value)
    if time_unit == "days":
        new_time = type_date + timedelta(days=value)
    if time_unit == "hours":
        new_time = type_date + timedelta(hours=value)
    if time_unit == "minutes":
        new_time = type_date + timedelta(minutes=value)
    if time_unit == "seconds":
        new_time = type_date + timedelta(seconds=value)
    return new_time


def get_system_time(working_script_path='default'):
    if working_script_path == 'default':
        script_path_local = script_path
    else:
        script_path_local = working_script_path / Path('ABUtility.exe')

    key_param = ["network", "0", "timing", "1"]
    command = 'get'
    section_var = 'system.time'
    result = subprocess.run([script_path_local, *key_param, command, section_var],
                            stdout=subprocess.PIPE, timeout=20, encoding='utf-8')
    check_exit_code(result)
    return read_inf_result(result.stdout, check_cond='false')[0][0] + " " \
        + read_inf_result(result.stdout, check_cond='false')[0][1]


# where -10750 - different with UTS in sec and offset for test execute time
def time_test_with_offset(param, time_offset=0, working_script_path='default'):
    if param == 'before':
        if working_script_path == 'default':
            return change_time(get_system_time(), 'seconds', -10750 + time_offset)
        if working_script_path != 'default':
            return change_time(get_system_time(working_script_path=working_script_path),
                               'seconds', -10750 + time_offset)
    if param == 'after':
        if working_script_path == 'default':
            return change_time(get_system_time(), 'seconds', -10850 + time_offset)
        if working_script_path != 'default':
            return change_time(get_system_time(working_script_path=working_script_path),
                               'seconds', -10850 + time_offset)


def time_now():
    initial_time = datetime.now()
    time = initial_time.strftime("%Y-%m-%d %H:%M:%S")
    final_time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
    return final_time


"""Temporary script before fix spam errors on exit"""


# output with ignore log connection closed errorS (FW-808 - Execute time: add unnecessary string  )
# def quantity_output_lines(output):
#     quantity = len(read_inf_result(output))
#     strings = output.split('\n')
#     for string in strings:
#         if string == ErrorsWarning.exit_error:
#             quantity -= 1
#         elif string == ErrorsWarning.exit_error1:
#             quantity -= 1
#         elif string == ErrorsWarning.exit_error2:
#             quantity -= 1
#         elif string == ErrorsWarning.exit_error3:
#             quantity -= 1
#         if string.find("Execute time:") == 0:
#             quantity -= 1
#     return quantity

def quantity_output_lines(output, check_cond='true'):
    if check_cond == 'true':
        quantity = len(read_inf_result(output))
        return quantity
    if check_cond == 'false':
        quantity = len(read_inf_result(output, check_cond='false'))
        return quantity


# output with ignore log connection closed errors and received init event (for poor internet tests)
def quantity_output_lines_without_init(arg):
    quantity = len(read_inf_result(arg))
    strings = arg.split('\n')
    if strings[0] == 'Event not completed':
        quantity -= 1
    return quantity


def query_select_logging(log_tab, value, game_session='default'):
    player_id = str(get_required_id('userId'))
    game_session_id = ''
    assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"
    if game_session == 'default':
        game_session_id = str(get_required_id('gameSessionId'))
    if game_session != 'default':
        game_session_id = game_session

    print(f"""SELECT received_time FROM {log_tab} WHERE player_id = '{player_id}' 
                                   AND {log_tab}.game_session_id = '{game_session_id}' 
                                   AND info = '{value}'""")
    received_time = connect_db(f"""SELECT received_time FROM {log_tab} WHERE player_id = '{player_id}' 
                                   AND {log_tab}.game_session_id = '{game_session_id}' 
                                   AND info = '{value}'""", logging_tab())
    print("received_time", received_time)
    if len(str(received_time)) <= 2:
        print("___Empty received_time for this log in DB!___")
        return datetime.strptime('1000-01-01 01:01:01', "%Y-%m-%d %H:%M:%S")
    else:
        return received_time[0][0]


# for logs with different params
def query_select_logging_params(log_tab, params, time='default'):
    player_id = str(get_required_id('userId'))
    assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"
    game_session_id = str(get_required_id('gameSessionId'))

    print(f"""SELECT received_time FROM {log_tab} WHERE player_id = '{player_id}' 
              AND {log_tab}.game_session_id = '{game_session_id}' AND """ + params)

    if time != 'default':
        received_time = connect_db(f"""SELECT received_time FROM {log_tab} WHERE player_id = '{player_id}' 
                      AND {log_tab}.game_session_id = '{game_session_id}' AND """ + params, logging_tab(),
                                   time=int(time))
    else:
        received_time = connect_db(f"""SELECT received_time FROM {log_tab} WHERE player_id = '{player_id}' 
              AND {log_tab}.game_session_id = '{game_session_id}' AND """ + params, logging_tab())

    if str(received_time) == '[]':
        print("Empty received_time for this log in DB!")
        return 'none'
    else:
        return received_time[0][0]


# count log by type for this player
def get_count_log_id_from_table_by_player(log_tab, param='all', player_id='default'):
    if player_id == 'default':
        player_id = str(get_required_id('userId'))
    if player_id != 'default':
        player_id = player_id

    assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"
    if param == 'all':
        print(f"""SELECT count(id) FROM {log_tab} WHERE player_id = '{player_id}'""")
        return connect_db(f"""SELECT count(id) FROM {log_tab} WHERE player_id = {player_id}""", logging_tab())[0][0]
    if param == 'unique':
        print(f"""SELECT count(DISTINCT(info)) FROM {log_tab} WHERE player_id = {player_id}""")
        return connect_db(f"""SELECT count(DISTINCT(info)) FROM {log_tab} WHERE player_id = {player_id}""",
                          logging_tab())[0][0]


# if we get "none" - var not exist
# if we get "None" - var exist and have value=Null
def query_select_var(var_tab, section, time=3, player_id='default', working_script_path='default'):
    if player_id == 'default':
        if working_script_path != 'default':
            player_id = str(get_required_id('userId', working_script_path=working_script_path))
        if working_script_path == 'default':
            player_id = str(get_required_id('userId'))
        assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"
    if player_id == 'super_user':
        player_id = '1408'
    if player_id != 'super_user':
        assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"
    print("Querry query_select_var: ", f"""SELECT value FROM {var_tab}
                           INNER JOIN section_key_names ON section_key_names.id = sections_names_id
                           WHERE {var_tab}.player_id = {player_id} 
                           and section_key_names.name = '{section}'""")
    value = connect_db(f"""SELECT value FROM {var_tab}
                           INNER JOIN section_key_names ON section_key_names.id = sections_names_id
                           WHERE {var_tab}.player_id = {player_id} 
                           and section_key_names.name = '{section}'""", profile_tab(), time=time)
    if len(str(value)) == 2:
        return 'none'

    if len(str(value)) >= 3:
        return str(value[0][0])


def query_select_player_params(tab, param, specific_id='none', player_id='default'):
    if player_id == 'default':
        player_id = str(get_required_id('userId'))
    assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"

    if tab == 'players':
        return connect_db(f"""SELECT {param} FROM {tab} WHERE id = '{player_id}'""", profile_tab())[0][0]
    if tab == 'login_sessions':
        return connect_db(f"""SELECT {param} FROM {tab} WHERE player_id = '{player_id}' 
        AND id = (SELECT MAX(id) FROM login_sessions WHERE player_id = '{player_id}')""", profile_tab())[0][0]
    if tab == 'game_sessions':
        max_id = connect_db(f"""SELECT MAX(id) FROM game_sessions WHERE player_id = '{player_id}'""",
                            profile_tab())[0][0]
        return connect_db(f"""SELECT {param} FROM {tab} WHERE player_id = '{player_id}' 
        AND game_sessions.id = '{max_id}'""", profile_tab())[0][0]
    if tab == 'groups_players':
        if specific_id == 'none':
            return connect_db(f"""SELECT {param} FROM {tab} WHERE player_id = {player_id}""", profile_tab())[0][0]
        else:
            return connect_db(f"""SELECT {param} FROM {tab} WHERE player_id = {player_id} 
            and group_id = {specific_id}""", profile_tab())[0][0]


def check_login_session_parameters(param, player_id='default', working_script_path='default'):
    if player_id == 'default':
        if working_script_path != 'default':
            player_id = str(get_required_id('userId', working_script_path=working_script_path))
        if working_script_path == 'default':
            player_id = str(get_required_id('userId'))
    assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"

    start_time = time_now()
    data_login_session = connect_db(
       f"""SELECT state, auth_key, start_time, auth_type FROM login_sessions WHERE player_id = '{player_id}'
        AND id = (SELECT MAX(id) FROM login_sessions WHERE player_id = '{player_id}')""", profile_tab())
    assert data_login_session[0][0] == 'Open', "Wrong received state for login session"
    assert len(data_login_session[0][1]) >= 50, "Wrong received auth_key for login session"
    assert data_login_session[0][2] > change_time(start_time, 'days', -365), "Wrong start_time for login session"
    if param == 'FW':
        assert data_login_session[0][3] == 'generic', "Wrong received auth_type for login session"
    if param == 'FB':
        assert data_login_session[0][3] == 'fb', "Wrong received auth_type for login session"
    print("check_login_session_parameters - OK")


def check_game_session_parameters(full_check='true', player_id='default', working_script_path='default'):
    if player_id == 'default':
        if working_script_path != 'default':
            player_id = str(get_required_id('userId', working_script_path=working_script_path))
        if working_script_path == 'default':
            player_id = str(get_required_id('userId'))
    assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"
    data_game_session = connect_db(
        f"""SELECT state, start_time, end_time FROM game_sessions WHERE player_id = '{player_id}' 
        AND id = (SELECT MAX(id) FROM game_sessions WHERE player_id = '{player_id}' )""",
        profile_tab())
    if full_check == 'true':
        assert data_game_session[0][0] == 'exited', "Wrong received state for game session"
        if working_script_path == 'default':
            assert time_test_with_offset('before') >= data_game_session[0][1] >= \
                   time_test_with_offset('after', time_offset=-200), "Wrong start_time game session!"
            assert time_test_with_offset('before') >= data_game_session[0][2] >= \
                   time_test_with_offset('after', time_offset=-200), "Wrong end_time game session!"
        if working_script_path != 'default':
            assert time_test_with_offset('before', working_script_path=working_script_path) >= \
                   data_game_session[0][1] >= time_test_with_offset('after', time_offset=-200,
                                                                    working_script_path=working_script_path), \
                   "Wrong start_time game session!"
            assert time_test_with_offset('before', working_script_path=working_script_path) >= \
                   data_game_session[0][2] >= time_test_with_offset('after', time_offset=-200,
                                                                    working_script_path=working_script_path), \
                   "Wrong end_time game session!"
    else:
        assert data_game_session[0][0] == 'exited' or data_game_session[0][0] == 'active', \
            "Wrong received state for game session"
        if working_script_path == 'default':
            assert time_test_with_offset('before', time_offset=500) >= data_game_session[0][1] >= \
                   time_test_with_offset('after', time_offset=-900), "Wrong start_time game session!"
        if working_script_path != 'default':
            assert time_test_with_offset('before', time_offset=500, working_script_path=working_script_path) >= \
                   data_game_session[0][1] >= time_test_with_offset('after', time_offset=-900,
                                                                    working_script_path=working_script_path),\
                   "Wrong start_time game session!"
    print("Check_game_session_parameters - OK")


def last_id_session_player(param):
    assert get_required_id('userId') != '', "Player has NO ID!"
    if param == 'game_sessions':
        return connect_db(f"""SELECT MAX(id) FROM game_sessions WHERE player_id = '{get_required_id('userId')}'""",
                          profile_tab())[0][0]
    if param == 'login_sessions':
        return connect_db(f"""SELECT MAX(id) FROM login_sessions WHERE player_id = '{get_required_id('userId')}'""",
                          profile_tab())[0][0]


def del_var_in_player(type_var, section, player_id=1408):  # was player_id=0
    connect_db(f"""UPDATE sections_{type_var}_values SET value=NULL WHERE player_id={player_id} AND id =
          (SELECT sections_{type_var}_values.id FROM sections_{type_var}_values
          INNER JOIN section_key_names ON section_key_names.id = sections_names_id
          WHERE sections_{type_var}_values.player_id = {player_id}
          and section_key_names.name = '{section}');
          
          UPDATE sections_{type_var}_values SET transaction_id=(SELECT nextval('current_transaction_id'))
          WHERE player_id={player_id} and id = (Select id from sections_string_values Where player_id = {player_id}
          and id = 
          (SELECT sections_{type_var}_values.id FROM sections_{type_var}_values
          INNER JOIN section_key_names ON section_key_names.id = sections_names_id
          WHERE sections_{type_var}_values.player_id = {player_id}
          and section_key_names.name = '{section}'))""", profile_tab(), return_value='false')

    assert query_select_var(f'sections_{type_var}_values', f'{section}', player_id=str(player_id)) == 'None', \
        "Var has not been deleted!"

    print('\n' + f"Deleting {section} from DB DONE (Value set null)" + '\n')


def del_super_user_data(player_id='1408'):
    connect_db(f"""DELETE FROM sections_string_values WHERE player_id = {player_id};
                   DELETE FROM sections_float_values WHERE player_id = {player_id};
                   DELETE FROM sections_int_values WHERE player_id = {player_id};
                   DELETE FROM sections_int64_values WHERE player_id = {player_id};
                   DELETE FROM sections_binary_values WHERE player_id = {player_id};
                   DELETE FROM sections_bool_values WHERE player_id = {player_id};
                   DELETE FROM sections_datetime_values WHERE player_id = {player_id};""", profile_tab(),
               return_value='false')
    print("Clearing Superuser profile DONE")


def asserts_log_dump_and_superuser_check(fw_error='fw_error', dump='dump', working_script_path='default',
                                         player_id='default'):
    if fw_error == 'fw_error':
        assert get_count_log_id_from_table_by_player('log_fw_error', player_id=player_id) == 0, \
            "New error in log_fw_errors!"
    if dump == 'dump':
        if working_script_path == 'default':
            assert check_dump_file_exist(dump='all') is False, "Dump exited but shouldn't!"
        if working_script_path != 'default':
            assert check_dump_file_exist(dump='all', working_script_path=working_script_path) is False, \
                "Dump exited but shouldn't!"

    super_user_data_count = connect_db("""WITH tmp AS 
             (SELECT 'sections_string_values' AS table_name, CAST("value" AS text) AS value, name
             FROM sections_string_values
             INNER JOIN section_key_names ON section_key_names.id = sections_names_id
             WHERE player_id = 1408
             union all
             SELECT 'sections_int_values' AS table_name, CAST("value" AS text) AS value, name
             FROM sections_int_values
             INNER JOIN section_key_names ON section_key_names.id = sections_names_id
             WHERE player_id = 1408
             union all
             SELECT 'sections_float_values' AS table_name, CAST("value" AS text) AS value, name
             FROM sections_float_values
             INNER JOIN section_key_names ON section_key_names.id = sections_names_id
             WHERE player_id = 1408
             union all
             SELECT 'sections_binary_values' AS table_name, CAST("value" AS text) AS value, name
             FROM sections_binary_values
             INNER JOIN section_key_names ON section_key_names.id = sections_names_id
             WHERE player_id = 1408
             union all
             SELECT 'sections_datetime_values' AS table_name, CAST("value" AS text) AS value, name
             FROM sections_datetime_values
             INNER JOIN section_key_names ON section_key_names.id = sections_names_id
             WHERE player_id = 1408
             union all
             SELECT 'sections_bool_values' AS table_name, CAST("value" AS text) AS value, name
             FROM sections_bool_values
             INNER JOIN section_key_names ON section_key_names.id = sections_names_id
             WHERE player_id = 1408
             union all
             SELECT 'sections_int64_values' AS table_name, CAST("value" AS text) AS value, name
             FROM sections_int64_values
             INNER JOIN section_key_names ON section_key_names.id = sections_names_id
             WHERE player_id = 1408)

             SELECT *
             FROM tmp
             WHERE name NOT like '%SystemGlobal%' and name NOT like '%UserProfile.super%' 
             and name NOT like '%UserProfile.rules%'""", profile_tab())

    if len(super_user_data_count) != 0:
        print("Super User data in DB: ")
        for item in super_user_data_count:
            item = ''.join(c for c in str(item) if c not in '(),\'')
            print(item)
        raise Exception("Set data in super user!")
    else:
        print("Check for super user data - OK!")
        log.debug(f'Super User is empty! {datetime.now()}')

    # check for not set to old superuser with wrong id =0
    count_vars_old_super = connect_db(f"""SELECT count(name) FROM public."Profiles" Where player_id = 0""",
                                      profile_tab())[0][0]
    assert count_vars_old_super == 0, f"Set data to old super user (Id=0)! Have {count_vars_old_super} vars"


def add_super_user_data_by_type(data_type, section, value, working_script_path='default'):
    if working_script_path == 'default':
        script_path_local = script_path
    else:
        script_path_local = working_script_path / Path('ABUtility.exe')

    command = ''
    if data_type == 'int':
        command = ["set", "-t", "int"]
    if data_type == 'int64':
        command = ["set", "-t", "int64"]
    if data_type == 'float':
        command = ["set", "-t", "float"]
    if data_type == 'bool':
        command = ["set", "-t", "bool"]
    if data_type == 'datetime':
        command = ["set", "-t", "date"]
    if data_type == 'binary':
        command = ["set", "-t", "binary"]
    if data_type == 'string':
        command = ["set", "-t", "string"]

    param = ["network", "1", "timing", "1", "waitto", "init", "2000", "get", "SystemLocal.sessions.login.userId",
             "change_user", "#system", "admin", *command, section, value]
    result = subprocess.run([script_path_local, *param], stdout=subprocess.PIPE, timeout=20, encoding='utf-8')
    print('\n' + "Set superuser var output: " + data_type, section, str(value) + '\n' + str(result.stdout))
    check_exit_code(result)
    assert read_inf_result(result.stdout)[0][0] + " " + read_inf_result(result.stdout)[0][1] + " " + \
           read_inf_result(result.stdout)[0][2] != 'Event not completed', "Init not received!"
    assert float(read_inf_result(result.stdout)[0][3]) <= TimingVal.receiving_init_time, \
        "Receiving init time is longer than expected"
    assert read_inf_result(result.stdout)[3][0] + " " + read_inf_result(result.stdout)[3][1] + " " + \
           read_inf_result(result.stdout)[3][2] == 'user #system changed', "Error with change player to superuser!"
    assert float(read_inf_result(result.stdout)[4][3]) <= TimingVal.register_change_user_time, \
        "Change user time is longer than expected!"
    assert float(read_inf_result(result.stdout)[5][3]) <= 10, "Execute set var time is longer than expected!"
    assert quantity_output_lines(result.stdout) == 6, "Expected output does not match"

    # we change superuser id from 0 to 1408
    player_id = ''
    if working_script_path == 'default':
        player_id = str(get_required_id('userId'))
    if working_script_path != 'default':
        player_id = str(get_required_id('userId', working_script_path=working_script_path))
    # player_id = str(get_required_id('userId'))
    assert player_id == '1408', f"Wrong player ID! Must be 1408! - now ({player_id})"

    if data_type == 'binary':
        super_user_var_in_db = connect_db(f"""SELECT value FROM sections_{data_type}_values
             INNER JOIN section_key_names ON section_key_names.id = sections_names_id
             WHERE sections_{data_type}_values.player_id = {player_id} and section_key_names.name = '{section}'""",
                                          profile_tab())
        assert str(super_user_var_in_db[0][0])[0] + str(super_user_var_in_db[0][0])[1] + \
               str(super_user_var_in_db[0][0])[2] == '<me',\
               f"Wrong data set in super! In DB now - ({super_user_var_in_db})"
        print(f"Var for superuser set success in DB ({super_user_var_in_db})")
    else:
        super_user_var_in_db = connect_db(f"""SELECT value FROM sections_{data_type}_values
        INNER JOIN section_key_names ON section_key_names.id = sections_names_id
        WHERE sections_{data_type}_values.player_id = {player_id} and section_key_names.name = '{section}'""",
                                          profile_tab())
        assert str(super_user_var_in_db[0][0]) == value, \
            f"Wrong data set in super! In DB now - ({super_user_var_in_db})"
        print(f"Var for superuser set success in DB ({super_user_var_in_db})")
    del_all_profile_files()


def create_util_command_from_test(param):
    # result = ''.join(c for c in param if c not in '\',')
    del_different_symbols = ''.join(c for c in param if c not in '\',')
    del_first_symbol = del_different_symbols.replace("[", "", 1)
    # del_last_symbol = del_first_symbol.replace("]", "", last_index)
    list1 = list(del_first_symbol)
    list1.pop(-1)
    res = "".join(list1)
    print('\n' + "Utility command: ABUtility", res)


def create_group_for_cohort_db(group_name, enter_condition, description, state, multiple_entrance):
    connect_db(f"""INSERT INTO groups (name, enter_condition, description, state, multiple_entrance) 
               VALUES ('{group_name}', '{enter_condition}', '{description}', '{state}', {multiple_entrance});""",
               profile_tab(), return_value='false')
    assert connect_db(f"""SELECT id from groups Where name = '{group_name}'""", profile_tab())[0][0] >= 0, \
        "Do not create cohort group!"
    print(f"Set group data DONE - {group_name}")


def set_data_for_group_overrides(group_name, group_overrides_type, name, value, stage):
    group_id = connect_db(f"""SELECT id from groups Where name = '{group_name}'""", profile_tab())[0][0]
    connect_db(f"""INSERT INTO groups_overrides (group_id, type, name, value, stage) 
               VALUES ('{group_id}', '{group_overrides_type}', '{name}', '{value}', '{stage}');""",
               profile_tab(), return_value='false')

    print(f"Set group_overrides DONE, group_id = {group_id}" + '\n')


def check_init_event_time(output, time):
    assert read_inf_result(output, check_cond='false')[0][0] + " " + read_inf_result(output, check_cond='false')[0][1] \
           + " " + read_inf_result(output, check_cond='false')[0][2] != 'Event not completed', "Init not received!"
    assert float(read_inf_result(output, check_cond='false')[0][3]) <= time, "Init received time too long!"


"""
for getting id from different tab (game or login sessions) for previous session
item_position - if we need previous from last item_position = -2, if we need first from 3 session item_position = -3
example received_id_from_session(-2, game_sessions) - penultimate id session received
"""


def received_id_from_session(item_position, tab):
    player_id = str(get_required_id('userId'))
    assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"
    print(f"""SELECT id FROM {tab} WHERE player_id = '{player_id}'""")
    all_sessions = connect_db(f"""SELECT id FROM {tab} WHERE player_id = '{player_id}'""", profile_tab())
    all_sessions_convert_to_lst = [*(x for elem in all_sessions for x in elem)]
    all_sessions_convert_to_lst.sort()
    session_id = all_sessions_convert_to_lst[item_position]
    if len(all_sessions) <= 1:
        raise Exception(f"Not have previous session! Count session = {len(all_sessions)}")
    else:
        print("Previous session_id = ", session_id)
        print("ID all session = ", all_sessions)
        return session_id


# count how much session player have
def count_id_in_db(tab, super_user='false'):
    if super_user == 'true':
        count_id = connect_db(f"""SELECT count(id) FROM {tab} WHERE player_id = 1408""", profile_tab())[0][0]
        return count_id
    if super_user == 'false':
        player_id = str(get_required_id('userId'))
        assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"
        print(f"""SELECT count(id) FROM {tab} WHERE player_id = '{player_id}'""")
        count_sessions = connect_db(f"""SELECT count(id) FROM {tab} WHERE player_id = '{player_id}'""",
                                    profile_tab())[0][0]
        print(f"Player have {count_sessions} {tab}")
        return count_sessions


# for poor internet tests
def check_integrity_string_from_db(player_id, param):
    data = ''
    if param == 'log' and player_id != '':
        data = connect_db(f"""SELECT info FROM log_custom WHERE player_id = {player_id}""", logging_tab(), time=10)
    if param == 'var' and player_id != '':
        data = connect_db(f"""SELECT value FROM sections_string_values WHERE player_id = {player_id}""", profile_tab(),
                          time=10)

    file = open('logs_strings_check.txt', 'w')
    file.write(str(data))
    file.close()
    final_file = open('logs_strings_check.txt', 'r')
    info_from_logs = final_file.read()
    string_count = info_from_logs.count('test_string')
    start_count = info_from_logs.count('start')
    end_count = info_from_logs.count('end')
    count_block_data_set_in_db = string_count / 30
    final_file.close()
    print(f"Set count {param} in db = " + str(int(count_block_data_set_in_db)))
    assert string_count % 30 == 0, "Wrong string from DB!"
    assert start_count == end_count == count_block_data_set_in_db, "Wrong string from DB!"
    print("Data in DB after test - OK" + '\n')
    os.remove('logs_strings_check.txt')


def get_offline_vars_from_local_profile(section, encoding='utf-8', binary='false', working_script_path='default'):
    if working_script_path == 'default':
        script_path_local = script_path
    else:
        script_path_local = working_script_path / Path('ABUtility.exe')

    key_param = ["network", "0", "timing", "1"]
    result = subprocess.run([script_path_local, *key_param, 'get', section],
                            stdout=subprocess.PIPE, timeout=20, encoding=encoding)
    print("Offline var output: " + '\n' + str(result.stdout))
    check_exit_code(result)
    output = str(result.stdout)
    if binary == 'true':
        assert output.find('TIME') and output.find('SPENT'), "No time line spend!"
        return str(result.stdout)
    if binary == 'false':
        assert quantity_output_lines(result.stdout, check_cond='false') == 2, \
            "Unexpected output, more lines than expected"
        return read_inf_result(result.stdout, check_cond='false')[0][0]


# for poor internet tests
# need add device_id and other params for test on new comp
def check_player_and_sessions_parameters(player_id):
    assert get_required_id('userId') != '', "Player has NO ID!"
    start_time = time_now()
    data_login_session = connect_db(
        f"""SELECT state, auth_key, start_time, auth_type FROM login_sessions WHERE player_id = '{player_id}'
        AND id = (SELECT MAX(id) FROM login_sessions WHERE player_id = '{player_id}')""",
        profile_tab(), time=20)
    assert data_login_session[0][0] == 'Open', "Wrong received state for login session"
    assert len(data_login_session[0][1]) >= 50, "Wrong received auth_key for login session"
    assert data_login_session[0][2] > change_time(start_time, 'days', -365), "Wrong start_time for login session"
    assert data_login_session[0][3] == 'generic', "Wrong received auth_type for login session"
    player_email = connect_db(f"""SELECT email FROM players WHERE id = '{player_id}'""", profile_tab())
    assert '#anonymous_mail_' in str(player_email), f"Wrong email anonymous user! ({player_email})"
    data_game_session = connect_db(
        f"""SELECT state, start_time, country_id, device_id, device_name, platform, language_id, connection_type 
        FROM game_sessions WHERE player_id = '{player_id}' 
        AND id = (SELECT MAX(id) FROM game_sessions WHERE player_id = '{player_id}')""", profile_tab(), time=20)
    assert data_game_session[0][0] == 'exited' or data_game_session[0][0] == 'active', \
        "Wrong received state for game session"
    assert time_test_with_offset('before') >= data_game_session[0][1] >= \
           time_test_with_offset('after', time_offset=-300), "Wrong start_time game session!"
    assert str(data_game_session[0][2]) == '230', f"Wrong country_id in game session! ({data_game_session[0][2]})"
    assert data_game_session[0][3] == '496ff70a-1cde-4676-a818-0dd738e197c6' or data_game_session[0][3] ==\
           'd4d6c50c-3511-4933-9185-9354cfecec68' or data_game_session[0][3] == '60fa36e1-b918-4d4a-b215-ded5d01086f3',\
           "Wrong device_id in game session!"
    assert data_game_session[0][4] == 'pc', "Wrong device_name in game session!"
    assert data_game_session[0][5] == 'windows', "Wrong platform in game session!"
    assert data_game_session[0][6] == 5, "Wrong language_id in game session!"
    assert data_game_session[0][7] == 'lan' or data_game_session[0][7] == 'wifi', \
        "Wrong connection_type in game session!"


def save_output_to_file(output):
    file = open('test_output.txt', 'w')
    file.write(str(output))
    file.close()
    print("Output save in file!")


def check_system_vars_in_local_profile(player_id='exist', game_session_id='exist', login_session_id='exist',
                                       email='exist', working_script_path='default'):
    if working_script_path == 'default':
        script_path_local = script_path
    else:
        script_path_local = working_script_path / Path('ABUtility.exe')

    correction_index = 0
    key_param = ["network", "0", "timing", "1"]
    result = subprocess.run([script_path_local, *key_param,
                             'get', 'SystemLocal.sessions.login.userId',     # player_id
                             'get', 'SystemLocal.sessions.login.sessionId',  # login_session_id
                             'get', 'SystemLocal.sessions.game.id',          # game_session_id
                             'get', 'SystemLocal.sessions.login.email',      # player email
                             'get', 'SystemLocal.sessions.login.authType',   # player authType - generic or FW etc
                             'get', 'SystemLocal.sessions.login.authKey'],   # player authKey
                            stdout=subprocess.PIPE, timeout=20, encoding='utf-8')
    check_exit_code(result)

    if read_inf_result(result.stdout, check_cond='false')[0][0] == 'Condition':
        correction_index = 1

    if player_id != 'exist':
        current_local_player_id = read_inf_result(result.stdout, check_cond='false')[0 + correction_index][0]
        assert current_local_player_id == player_id,\
            f"Wrong player id! Now - ({current_local_player_id}) but must be ({player_id})!"
    if player_id == 'exist':
        current_local_player_id = read_inf_result(result.stdout, check_cond='false')[0 + correction_index][0]
        assert int(current_local_player_id) >= 10001, f"Wrong player id! Now - ({current_local_player_id})"

    if login_session_id != 'exist':
        current_local_login_session_id = read_inf_result(result.stdout, check_cond='false')[2 + correction_index][0]
        assert current_local_login_session_id == login_session_id, \
            f"Wrong login_session_id! Now - ({current_local_login_session_id}) but must be ({login_session_id})!"
    if login_session_id == 'exist':
        current_local_login_session_id = read_inf_result(result.stdout, check_cond='false')[2 + correction_index][0]
        assert int(current_local_login_session_id) >= 10001, \
            f"Wrong login_session_id! Now - ({current_local_login_session_id})"

    if game_session_id != 'exist':
        current_local_game_session_id = read_inf_result(result.stdout, check_cond='false')[4 + correction_index][0]
        assert current_local_game_session_id == game_session_id,\
            f"Wrong game_session_id! Now - ({current_local_game_session_id}) but must be ({game_session_id})!"
    if game_session_id == 'exist':
        current_local_game_session_id = read_inf_result(result.stdout, check_cond='false')[4 + correction_index][0]
        assert int(current_local_game_session_id) >= 10001, \
            f"Wrong game_session_id! Now - ({current_local_game_session_id})"

    if email != 'exist':
        current_local_email = read_inf_result(result.stdout, check_cond='false')[6 + correction_index][0]
        assert current_local_email == email,\
            f"Wrong player email! Now - ({current_local_email} but must be ({email})!"
    # if email == 'exist':
    #     current_local_email = read_inf_result_without_conditions(result.stdout)[6 + correction_index][0]
    #     assert current_local_email != '', f"Wrong player id! Now - ({current_local_email})"

    current_local_auth_type = read_inf_result(result.stdout, check_cond='false')[8 + correction_index][0]
    assert current_local_auth_type == 'generic', f"Wrong authType! Now ({current_local_auth_type}) But must be generic!"

    current_local_auth_key = read_inf_result(result.stdout, check_cond='false')[10 + correction_index][0]
    assert current_local_auth_key != '', f"Wrong authType! Now - ({current_local_auth_key}) But must be not empty!"


def check_exit_code(output):
    exit_code = output.returncode
    error_status = str(output.stderr)
    if error_status != 'None':
        print('\n' + "Errors is ", output.stderr)
    assert exit_code == 0, f"Wrong exit code! ({exit_code})"


# For check several vars from db in one querry for this player
def check_vars_in_db(list_vars, player_id='default', working_script_path='default'):
    if player_id == 'default':
        if working_script_path != 'default':
            player_id = str(get_required_id('userId', working_script_path=working_script_path))
        if working_script_path == 'default':
            player_id = str(get_required_id('userId'))
    assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"

    result_querry = connect_db(f"""WITH tmp AS 
                 (SELECT 'sections_string_values' AS table_name, CAST("value" AS text) AS value, name
                 FROM sections_string_values
                 INNER JOIN section_key_names ON section_key_names.id = sections_names_id
                 WHERE player_id = {player_id}
                 union all
                 SELECT 'sections_int_values' AS table_name, CAST("value" AS text) AS value, name
                 FROM sections_int_values
                 INNER JOIN section_key_names ON section_key_names.id = sections_names_id
                 WHERE player_id = {player_id}
                 union all
                 SELECT 'sections_float_values' AS table_name, CAST("value" AS text) AS value, name
                 FROM sections_float_values
                 INNER JOIN section_key_names ON section_key_names.id = sections_names_id
                 WHERE player_id = {player_id}
                 union all
                 SELECT 'sections_binary_values' AS table_name, CAST("value" AS text) AS value, name
                 FROM sections_binary_values
                 INNER JOIN section_key_names ON section_key_names.id = sections_names_id
                 WHERE player_id = {player_id}
                 union all
                 SELECT 'sections_datetime_values' AS table_name, CAST("value" AS text) AS value, name
                 FROM sections_datetime_values
                 INNER JOIN section_key_names ON section_key_names.id = sections_names_id
                 WHERE player_id = {player_id}
                 union all
                 SELECT 'sections_bool_values' AS table_name, CAST("value" AS text) AS value, name
                 FROM sections_bool_values
                 INNER JOIN section_key_names ON section_key_names.id = sections_names_id
                 WHERE player_id = {player_id}
                 union all
                 SELECT 'sections_int64_values' AS table_name, CAST("value" AS text) AS value, name
                 FROM sections_int64_values
                 INNER JOIN section_key_names ON section_key_names.id = sections_names_id
                 WHERE player_id = {player_id})

        SELECT value, name, table_name FROM tmp """, profile_tab())
    print(f"Player {player_id} have {len(result_querry)} vars: {result_querry}")
    if len(str(result_querry)) <= 2:
        print("Nothing have in DB from this player!")
        # raise Exception("Nothing have in DB from this player!")
    if len(str(result_querry)) > 2:
        for element in list_vars:
            value = element[0]
            name = element[1]
            var_type = element[2]
            # print(f"'{value}', '{name}', 'sections_{var_type}_values'" + '\n')
            result_querry = str(result_querry)
            if value == 'none':
                assert result_querry.count(f"'{name}', 'sections_{var_type}_values'") == 0,\
                    f"No var in DB: Name = '{name}', Value = '{value}', Section = 'sections_{var_type}_values'" + '\n'
            elif value == 'None':
                # print(result_querry.count(f"{value}, '{name}', 'sections_{var_type}_values'"))
                assert result_querry.count(f"{value}, '{name}', 'sections_{var_type}_values'") == 1,\
                    f"No var in DB: Name = '{name}', Value = '{value}', Section = 'sections_{var_type}_values'" + '\n'
            else:  # value != 'none'
                assert result_querry.count(f"'{value}', '{name}', 'sections_{var_type}_values'") == 1,\
                    f"No var in DB: Name = '{name}', Value = '{value}', Section = 'sections_{var_type}_values'" + '\n'
    print("Check_vars_in_db - OK")


# old script for del var directly
def change_var_in_player(type_var, section, value, player_id='default'):
    if player_id == 'default':
        player_id = str(get_required_id('userId'))
        assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"
    connect_db(f"""UPDATE sections_{type_var}_values SET value='{value}' WHERE player_id={player_id} AND id =
          (SELECT sections_{type_var}_values.id FROM sections_{type_var}_values
          INNER JOIN section_key_names ON section_key_names.id = sections_names_id
          WHERE sections_{type_var}_values.player_id = {player_id}
          and section_key_names.name = '{section}');

          UPDATE sections_{type_var}_values SET transaction_id=(SELECT nextval('current_transaction_id'))
          WHERE player_id={player_id} and id = (Select id from sections_string_values Where player_id = {player_id}
          and id = 
          (SELECT sections_{type_var}_values.id FROM sections_{type_var}_values
          INNER JOIN section_key_names ON section_key_names.id = sections_names_id
          WHERE sections_{type_var}_values.player_id = {player_id}
          and section_key_names.name = '{section}'))""", profile_tab(), return_value='false')

    value_var = query_select_var(f'sections_{type_var}_values', f'{section}', player_id=player_id)
    assert value_var == value, f"Var has not been updated! now value = {value_var}"
    print('\n' + f"Update {section} in DB DONE (Value set {value}) for player = {player_id}" + '\n')


def count_var_in_player(type_var, player_id='default'):
    if player_id == 'default':
        player_id = str(get_required_id('userId'))
    assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"

    if type_var == 'all':
        count_vars = connect_db(f"""SELECT count(name) FROM public."Profiles" Where player_id = {player_id}""",
                                profile_tab())[0][0]
        print(f"Player have {count_vars} vars in db, type = {type_var}")
        return count_vars

    else:
        count_id = connect_db(f"""SELECT count(id) FROM sections_{type_var}_values WHERE player_id = {player_id}""",
                              profile_tab())[0][0]
        print(f"Player have {count_id} vars in db, type = {type_var}")
        return count_id


def check_size(file):
    if file == 'log_dump':
        file = (os.path.getsize(Path(os.getcwd()) / Path('data', 'dump', 'logger')))
    if file == 'var_dump':
        file = (os.path.getsize(Path(os.getcwd()) / Path('data', 'dump', 'varoffline')))
    assert os.access(file, os.F_OK) is True, "File not exist!"

    size_file = (os.path.getsize(file)) / 1024  # get in KB size
    print(f"Test file have size {size_file}KB")
    return size_file


def get_name_vars_cohort_group_parameters_set_to_super(group_name, name_var):
    name = connect_db(f"""SELECT name from public."Profiles" 
                                        Where player_id=1408 and value = '{group_name}'""",
                      profile_tab())

    if len(str(name)) <= 2:
        raise Exception("Nothing have in DB for this group!")
    else:
        var_group_name = name[0][0]
        index = ''.join(c for c in var_group_name if c in '1234567890')
        if name_var == 'condition':
            return f'SystemGlobal.conditionals[{index}].conditional'
        if name_var == 'group_name_var':
            return f'SystemGlobal.groups[{index}].name'
        if name_var == 'condition_name_hash_var_name':
            return f'SystemGlobal.conditionals[{index}].name'
        if name_var == 'group_id':
            return connect_db(f"""SELECT id from groups Where name = '{group_name}'""", profile_tab())[0][0]
        if name_var == 'condition_name_hash':
            return str(connect_db(f"""SELECT value from public."Profiles" 
                              Where player_id=1408
                              and name = '{
            get_name_vars_cohort_group_parameters_set_to_super(f'{group_name}', 'condition_name_hash_var_name')}'""",
                                  profile_tab())[0][0])


# for allure env description
def create_env_file_report():
    initial_path = path_with_offset(Path(os.path.abspath(os.path.dirname(__file__))), level=-1)
    local_path = path_with_offset(initial_path, level=-1)
    if local_path != Path('c:/workspace/workspace'):
        # check for win worker env, not create for testing on own PC
        print("We on local PC, create environment.properties not needed")
    else:
        env = ''
        if not os.path.exists(initial_path / Path('results')):
            os.mkdir(initial_path / Path('results'))
        if get_config_xml_params()[0] == '46.101.156.78' and get_config_xml_params()[1] == '9123':
            env = 'DEV'
        if get_config_xml_params()[0] == '46.101.156.78' and get_config_xml_params()[1] == '9023':
            env = 'QA'
        file = open(initial_path / Path('results', 'environment.properties'), 'w')
        file.write(f'Environment = {env}')
        file.close()
        print("File environment.properties created!")


def offline_vars_from_local_profile(vars_list, command='get', working_script_path='default'):
    if working_script_path == 'default':
        script_path_local = script_path
    else:
        script_path_local = working_script_path / Path('ABUtility.exe')

    vars_names = []
    vars_values = []
    for element in vars_list:
        vars_values.append(element[0])
        vars_names.append(command)  # add command - for example 'get' or 'gettype'
        vars_names.append(element[1])
    print('Check offline vars: ABUtility network 0 timing 1 ' + ' '.join(vars_names))
    result = subprocess.run([script_path_local, 'network', '0', 'timing', '1', *vars_names],
                            stdout=subprocess.PIPE, timeout=15, encoding='utf-8')
    print('\n' + "Offline_vars_from_local_profile output: " + '\n' + str(result.stdout))
    check_exit_code(result)

    command_result = read_inf_result(result.stdout, check_cond='false')

    # do a variable check with the result of the output
    i = 0
    for element in vars_values:
        assert element == command_result[i][0], f"Wrong var value in local profile! " \
                                                f"Var ({vars_names[i + 1]}) have value in local profile " \
                                                f"({command_result[i][0]}) but must ({element})!"
        i += 2
    print("All offline var OK!" + '\n')


# count group which player enter
def check_player_count_cohort(count_group, player_id='default'):
    if player_id == 'default':
        player_id = str(get_required_id('userId'))
    assert player_id != '' or player_id != '1408' or player_id != '0', f"Player has wrong ID! ({player_id})"

    all_group_player = connect_db(f"""SELECT group_id FROM groups_players WHERE player_id = {player_id}""",
                                  profile_tab())
    number_of_groups = len(all_group_player)
    assert number_of_groups == count_group, f"Wrong player's group! Must be {count_group} have {number_of_groups}! " \
                                            f"Player enters group({all_group_player})"
    print(f"Player enters in {count_group} group - OK")


def deactivate_cohort_group(group_name):
    connect_db(f"""UPDATE groups SET state='delete' WHERE name='{group_name}'""", profile_tab(), return_value='false')
    print(f"Group {group_name} was disabled!")


def unique_random_num():
    random_num = str(random.random())
    unique_num = random_num.replace(".", "")
    return unique_num


def check_cohort_group_param(group_name, parameter, value):
    print(f"""SELECT {parameter} FROM groups Where name = '{group_name}'""")
    db_value = connect_db(f"""SELECT {parameter} FROM groups Where name = '{group_name}'""", profile_tab())[0][0]
    assert db_value == value, f"Wrong group parameter {parameter} in DB! Now \"{db_value}\" but must \"{value}\"!)"
    print(f"Check OK! Group parameter {parameter} in DB = {value}")


def check_utility_file_update():
    utility_build_file = path_with_offset(
        Path(os.path.abspath(os.path.dirname(__file__))), level=-1) / Path('ABUtility', 'ABUtility.exe')
    assert os.access(utility_build_file, os.F_OK) is True, "File not exist!"
    utility_test_file = path_with_offset(
        Path(os.path.abspath(os.path.dirname(__file__))), level=-1) / Path('ABUtility.exe')
    if os.access(utility_test_file, os.F_OK) is True:
        size_build_file = (os.path.getsize(utility_build_file))
        size_test_file = (os.path.getsize(utility_test_file))
        create_data_build_file = os.path.getmtime(utility_build_file)
        create_data_test_file = os.path.getmtime(utility_test_file)
        if size_build_file != size_test_file:
            local_path = path_with_offset(Path(os.path.abspath(os.path.dirname(__file__))), level=-1)
            shutil.copy2(local_path / Path('ABUtility', 'ABUtility.exe'),
                         local_path / Path('ABUtility.exe'))
            print("_________Utility was update!________")
        else:
            if create_data_build_file != create_data_test_file:
                local_path = path_with_offset(Path(os.path.abspath(os.path.dirname(__file__))), level=-1)
                shutil.copy2(local_path / Path('ABUtility', 'ABUtility.exe'),
                             local_path / Path('ABUtility.exe'))
                print("_________Utility was update!________")
            else:
                print("_________Utility up to date!________")
    else:
        local_path = path_with_offset(Path(os.path.abspath(os.path.dirname(__file__))), level=-1)
        shutil.copy2(local_path / Path('ABUtility', 'ABUtility.exe'),
                     local_path / Path('ABUtility.exe'))
        print("_________Utility was update!________")
