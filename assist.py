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
                          assert_type=dict)
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

    cfg = Config.from_file(args.config)
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
        # Sleep at most 30 seconds; bot communication works in separate
        # thread and while we are sleeping user might cause action which
        # schedules something.
        idle = min(30, idle)
        orgassist.log.debug("Scheduler sleeping %d seconds", idle)
        sleep(idle)
        program['scheduler'].run_pending()


def main():
    "Initialize environment"
    args = parse_args()
    if args.generate_config is not None:
        return generate_config(args.generate_config)

    try:
        program = setup(args)
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
