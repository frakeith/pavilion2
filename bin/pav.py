# This is the core pavilion script.
# It shouldn't be run directly; use bin/pav instead.

from logging.handlers import RotatingFileHandler
from pavilion import arguments
from pavilion import commands
from pavilion import config
from pavilion import plugins
from pavilion import pav_vars
import logging
from pathlib import Path
import os
import sys
import traceback


def main():
    # Pavilion is compatible with python >= 3.4
    if sys.version_info[0] != 3 or sys.version_info[1] < 4:
        print("Pavilion requires python 3.4 or higher.", file=sys.stderr)
        sys.exit(-1)

    # Get the config, and
    try:
        pav_cfg = config.find()
    except Exception as err:
        print(err, file=sys.stderr)
        sys.exit(-1)

    root_logger = logging.getLogger()

    # Set up a directory for tracebacks.
    tracebacks_dir = Path(os.path.expanduser('~/.pavilion/tracebacks'))
    os.makedirs(str(tracebacks_dir), exist_ok=True)

    # Put the log file in the lowest common pav config directory we can write
    # to.
    for log_dir in reversed(pav_cfg.config_dirs):
        log_fn = log_dir/'pav.log'
        if not log_fn.exists():
            try:
                # 'Touch' the file, in case it doesn't exist. Makes it easier to
                # verify writability in a sec.
                log_fn.open('a').close()
            except OSError:
                # It's ok if we can't do this.
                pass
        if os.access(str(log_fn), os.W_OK):
            # Set up a rotating logfile than rotates when it gets larger
            # than 1 MB.
            file_handler = RotatingFileHandler(filename=str(log_fn),
                                               maxBytes=1024 ** 2,
                                               backupCount=3)
            file_handler.setFormatter(logging.Formatter(pav_cfg.log_format))
            file_handler.setLevel(getattr(logging,
                                          pav_cfg.log_level.upper()))
            root_logger.addHandler(file_handler)
            break

    # The root logger should pass all messages, even if the handlers
    # filter them.
    root_logger.setLevel(logging.DEBUG)

    # Setup the result logger.
    # Results will be logged to both the main log and the result log.
    result_logger = logging.getLogger('results')
    result_handler = RotatingFileHandler(filename=str(pav_cfg.result_log),
                                         # 20 MB
                                         maxBytes=20 * 1024 ** 2,
                                         backupCount=3)
    result_handler.setFormatter(logging.Formatter("{asctime} {message}",
                                                  style='{'))
    result_logger.setLevel(logging.INFO)
    result_logger.addHandler(result_handler)

    # This has to be done before we initialize plugins
    parser = arguments.get_parser()

    # Initialize all the plugins
    try:
        plugins.initialize_plugins(pav_cfg)
    except plugins.PluginError as err:
        print("Error initializing plugins: {}".format(err), file=sys.stderr)
        sys.exit(-1)

    pav_cfg.pav_vars = pav_vars.PavVars()

    # Parse the arguments
    try:
        args = parser.parse_args()
    except Exception:
        # TODO: Handle argument parsing errors correctly.
        raise

    # Add a stream to stderr if we're in verbose mode, or if no other handler
    # is defined.
    if args.verbose or not root_logger.handlers:
        result_handler = logging.StreamHandler(sys.stderr)
        result_handler.level(logging.DEBUG)
        result_handler.format(pav_cfg.log_format)
        root_logger.addHandler(result_handler)

    # Create the basic directories in the working directory
    for path in [pav_cfg.working_dir,
                 pav_cfg.working_dir/'builds',
                 pav_cfg.working_dir/'tests',
                 pav_cfg.working_dir/'downloads']:
        if not path.exists():
            try:
                path.mkdir()
            except OSError as err:
                # Handle potential race conditions with directory creation.
                if path.exists():
                    # Something else created the directory
                    pass
                else:
                    print("Could not create base directory '{}': {}"
                          .format(path, err))
                    sys.exit(1)

    if args.command_name is None:
        parser.print_help()
        sys.exit(0)

    try:
        cmd = commands.get_command(args.command_name)
    except KeyError:
        print("Unknown command {}.".format(args.command_name), file=sys.stderr)
        sys.exit(-1)

    try:
        sys.exit(cmd.run(pav_cfg, args))
    except Exception as err:
        print("Unknown error running command {}: {}."
              .format(args.command_name, err))
        traceback_file = tracebacks_dir/str(os.getpid())
        traceback.print_exc()

        with traceback_file.open('w') as tb:
            tb.write(traceback.format_exc())
        print("Traceback saved in {}".format(traceback_file))
        sys.exit(-1)


if __name__ == '__main__':
    main()
