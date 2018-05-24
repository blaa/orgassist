#!/usr/bin/env python3

import logging
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
    level = cfg.get('log.level',
                    required=False,
                    default='INFO')
    level_map = {
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'WARN': logging.WARNING,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
    }
    logging.basicConfig(level=level_map.get(level))

def setup():
    "Setup logging"
    args = parse_args()

    cfg = Config.from_file(args.config)

    setup_logging(cfg)

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
        'args': args,
    }

def main_loop(program):
    "Main loop - execute scheduled tasks"
    while True:
        program['scheduler'].run_pending()
        idle = program['scheduler'].idle_seconds
        idle = min(30, idle)
        print("Waiting %d seconds for next task" % idle)
        sleep(idle)
        program['scheduler'].run_pending()


def main():
    "Initialize environment"

    try:
        program = setup()
    except ConfigError as ex:
        print("Error while parsing your configuration file:")
        print(ex.args[0])
        return
    except KeyboardInterrupt:
        print("Interrupted during initialization")
        return

    if program['args'].test:
        # Just test
        return

    # Start processing in other threads
    program['xmpp_bot'].client.process()

    try:
        main_loop(program)
    except KeyboardInterrupt:
        print("Keyboard interrupt")
    finally:
        # Stop XMPP
        if program.get('xmpp_bot'):
            print("Stopping XMPP")
            program['xmpp_bot'].close()


if __name__ == "__main__":
    main()
