from models.additional_scripts import *
import os


def create_temp_test_folder(unique_name):
    path = Path('Temp', f'{unique_name}')
    local_path = Path(os.getcwd())
    if not os.path.exists(local_path / Path('Temp')):
        os.mkdir(local_path / Path('Temp'))
    if os.path.exists(local_path / Path('Temp', f'{unique_name}')):
        shutil.rmtree(local_path / Path('Temp', f'{unique_name}'))
    os.mkdir(local_path / Path('Temp', f'{unique_name}'))
    return path


def copy_test_data(test_path):
    local_path = Path(os.getcwd())
    shutil.copy2(local_path / Path('ABUtility', 'ABUtility.exe'),
                 local_path / Path(f'{test_path}', 'ABUtility.exe'))
    os.mkdir(local_path / Path(f'{test_path}', 'data'))
    shutil.copy2(local_path / Path('data', 'project.xml'),
                 local_path / Path(f'{test_path}', 'data', 'project.xml'))


def del_temp_test_folders(folder):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    shutil.rmtree(folder)
    print(f"Test folder {folder} was deleted!")


def prepare_to_isolated_start_test(path_system, test_name):
    os.chdir(path_system)
    create_temp_test_folder(f'{test_name}')
    test_path = Path('Temp', f'{test_name}')
    copy_test_data(test_path)
    return test_path


def return_working_directory_path(test_path):
    os.chdir(Path(os.getcwd()) / test_path)


def return_initial_directory_path(path_system):
    os.chdir(path_system)


def prepare_independent_start(test_name, path_system):
    prepare_to_isolated_start_test(path_system, test_name)
    return_working_directory_path(test_path=Path('Temp', f'{test_name}'))
    script_path_temp = Path(os.getcwd())
    return script_path_temp

