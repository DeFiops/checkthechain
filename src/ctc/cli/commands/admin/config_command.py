from __future__ import annotations

import os
import typing

import toolcli
import toolstr

import ctc.config


def get_command_spec() -> toolcli.CommandSpec:
    return {
        'f': config_command,
        'help': 'print current config information',
        'args': [
            {
                'name': '--reveal',
                'action': 'store_true',
                'help': 'show sensitive information in config',
            },
            {
                'name': '--json',
                'help': 'output config as json',
                'dest': 'as_json',
                'action': 'store_true',
            },
        ],
        'examples': [
            '',
            '--reveal',
            '--json',
        ],
    }


def config_command(reveal: bool, as_json: bool) -> None:

    env_var = ctc.config.config_path_env_var

    if as_json:
        import rich

        config: typing.Mapping[str, typing.Any] = ctc.config.get_config()
        rich.print(config)

    else:

        print('# Config Summary')
        print('- config env variable:', env_var)
        if env_var not in os.environ:
            print('-', env_var, 'not set')
        else:
            env_value = os.environ[env_var]
            if env_value is None or env_value == '':
                print('-', env_var, 'set to null')
            else:
                print('-', env_var, 'set to:', env_value)
        print('- config path:', ctc.config.get_config_path(raise_if_dne=False))

        print()
        print('## Config Values')
        config = typing.cast(
            typing.Mapping[str, typing.Any], ctc.config.get_config()
        )
        for key in sorted(config.keys()):

            if key == 'networks':
                print('-', key + ':')
                rows = []
                for chain_id, network_metadata in config[key].items():
                    row = [
                        network_metadata['name'],
                        str(network_metadata['chain_id']),
                        network_metadata['block_explorer'],
                    ]
                    rows.append(row)
                labels = ['name', 'chain_id', 'block_explorer']
                toolstr.print_table(rows, labels=labels, indent=4)
                print()

            elif key == 'providers':
                print('-', key + ':')
                if len(config[key]) == 0:
                    continue
                if reveal:
                    labels = list(config[key][0])
                else:
                    labels = ['name', 'network', 'url']
                rows = []
                for provider in config[key].values():
                    row = []
                    for label in labels:
                        if label == 'url' and not reveal:
                            cell = '*' * 8
                        else:
                            cell = provider[label]
                        row.append(cell)
                    rows.append(row)
                toolstr.print_table(rows, labels=labels, indent=4)
                if not reveal:
                    print()
                    print('    (use --reveal to reveal sensitive provider information)')

            elif isinstance(config[key], dict) and len(config[key]) > 0:
                print('-', str(key) + ':')
                for subkey, subvalue in config[key].items():
                    if isinstance(subvalue, dict) and len(subvalue) > 0:
                        print('    -', str(subkey) + ':')
                        for subsubkey, subsubvalue in subvalue.items():
                            if (
                                (not reveal)
                                and key == 'providers'
                                and subsubkey == 'url'
                            ):
                                subsubvalue = '********'
                            print(
                                '        -', str(subsubkey) + ':', subsubvalue
                            )
                    else:
                        print('    -', str(subkey) + ':', subvalue)
            else:
                print('-', str(key) + ':', config[key])
