from wg_tool.server.interface import start_interface as _start, stop_interface as _stop, restart_interface as _restart, remove_interface as _remove

def start_interface(name: str, enable: bool = True):
    return _start(name, enable=enable)

def stop_interface(name: str, disable: bool = False):
    return _stop(name, disable=disable)

def restart_interface(name: str):
    return _restart(name)

def remove_interface(name: str, remove_config: bool = True, clear_storage: bool = False):
    return _remove(name, remove_config=remove_config, clear_storage=clear_storage)
