import time, pytest, inspect
from utils import *

PORT_FROM_CONFIG_FILE = 12345
PORT_FROM_COMMAND_LINE = 12346

def test_running_two_braves_on_different_ports(run_brave, create_config_file):
    launch_brave_setting_port_in_config_file(run_brave, create_config_file)
    launch_brave_setting_port_in_environment_variable(run_brave)

    for port in [PORT_FROM_CONFIG_FILE, PORT_FROM_COMMAND_LINE]:
        response = api_get('/api/all', port=port)
        assert response.status_code == 200

    time.sleep(1)

def launch_brave_setting_port_in_config_file(run_brave, create_config_file):
    config = {'api_port': PORT_FROM_CONFIG_FILE}
    config_file = create_config_file(config)
    run_brave(config_file.name)
    check_brave_is_running()


def launch_brave_setting_port_in_environment_variable(run_brave):
    run_brave(port=PORT_FROM_COMMAND_LINE)
    check_brave_is_running()
