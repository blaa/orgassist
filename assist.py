#!/usr/bin/env python3

import os
import sys
import logging
import logging.config
import argparse
from time import sleep

import schedule
import orgassist
from orgassist.config import Config, ConfigError
from orgassist.assistant import Assistant


def parse_args():
    "Parse arguments"
    p = argparse.ArgumentParser()
    p.add_argument("--config",
                   help="Path to the YAML config directory",
                   type=str,
                   default="config.yml")
    p.add_argument("--test",
                   help="Initialize, but don't start bots",
                   action="store_true",
                   default=False)
    p.add_argument("--generate-config",
                   help="Generate a new config file from a template",
                   type=str,
                   metavar="PATH",
                   default=None)

    """
    p.add_argument("--daemon",
                   help="Thread away to the background",
                   action="store_true",
                   default=False)
    """

    args = p.parse_args()
    return args


def setup_logging(cfg):
    "Configure logging"
    full_config = cfg.get('log',
                          required=False,
                          default={},
                          assert_type=dict,
                          wrap=False)
    if full_config:
        full_config = dict(full_config)
        full_config['version'] = 1
        logging.config.dictConfig(full_config)
    else:
        logging.basicConfig(level=logging.WARNING)


def generate_config(cfg_path):
    "Generate a new empty config file"
    template = os.path.dirname(os.path.abspath(orgassist.__file__))
    template = os.path.join(template, 'config.tmpl.yml')
    try:
        with open(template, 'r') as handler:
            content = handler.read()
    except IOError as ex:
        print("Error while reading config template:", ex)
        return -1

    try:
        with open(cfg_path, 'w') as handler:
            handler.write(content)
    except IOError as ex:
        print("Error while reading config template:", ex)
        return -1
    return 0


def register_plugins(cfg):
    "Register external plugins specified in the config file"
    import importlib

    # Add plugin directories to the module search path
    plugins_path = cfg.get_path('plugins_path', required=False)
    if plugins_path is not None and plugins_path not in sys.path:
        sys.path.append(plugins_path)

    # Import plugins - they will register using decorators.
    plugins = cfg.get('plugins', assert_type=list)
    for plugin in plugins:
        importlib.import_module(plugin)


def setup(args):
    "Setup logging"
    try:
        cfg = Config.from_file(args.config)
    except FileNotFoundError:
        print("Unable to read config file:", args.config)
        return None
    setup_logging(cfg)
    register_plugins(cfg)

    # Scheduler
    scheduler = schedule.Scheduler()

    # XMPP Bot / interface
    xmpp_bot = orgassist.bots.XmppBot(cfg.bots.xmpp)

    # Create instances of assistants
    assistants = []
    for assistant_name, assistant_config in cfg.assistants.items():

        assistant = Assistant(assistant_name,
                              assistant_config,
                              scheduler)

        assistant.register_xmpp_bot(xmpp_bot)
        # FUTURE: s.register_irc_bot(irc)

        assistants.append(assistant)

    unused = cfg.get_unused()
    if unused:
        print('The following config keys were unused and can be mistyped:')
        for key in unused:
            print("  -", key)

    return {
        'xmpp_bot': xmpp_bot,
        'assistants': assistants,
        'scheduler': scheduler,
    }


def main_loop(program):
    "Main loop - execute scheduled tasks"
    while True:
        program['scheduler'].run_pending()
        idle = program['scheduler'].idle_seconds
        # Limit wakeups and sleep long, but not too long: bot communication
        # works in separate thread and while we are sleeping user might cause
        # action which schedules something.

        # Try to sleep evenly, instead of doing jumps of 30s + 3s sleep for a
        # total 33s idle time (instead will sleep 17 + 16 seconds)
        target = 30 # seconds
        if idle > 2 * target:
            idle = target
        elif idle > target:
            idle = idle // 2 + 1
        elif idle < 0:
            idle = 0
        sleep(idle)
        try:
            program['scheduler'].run_pending()
        except:
            # In case something bad happens - boss should know.
            # For example a notification might not reach him in time.
            for assistant in program['assistants']:
                assistant.tell_boss("Scheduler just threw an exception - help me.")
            raise


def main():
    "Initialize environment"
    args = parse_args()
    if args.generate_config is not None:
        return generate_config(args.generate_config)

    try:
        program = setup(args)
        if program is None:
            return 4
    except ConfigError as ex:
        print("Error while parsing your configuration file:")
        print(ex.args[0])
        return 3
    except KeyboardInterrupt:
        print("Interrupted during initialization")
        return 2

    if args.test:
        # Just test
        return 0

    # Start processing in other threads
    program['xmpp_bot'].client.process()

    try:
        main_loop(program)
        # Unreachable, but keeps pylint happy
        return 5
    except KeyboardInterrupt:
        print("Keyboard interrupt")
        return 1
    finally:
        # Stop XMPP
        if program.get('xmpp_bot'):
            print("Stopping XMPP")
            program['xmpp_bot'].close()


if __name__ == "__main__":
    sys.exit(main())
