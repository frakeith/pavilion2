"""Wait for the specified tests to finish, printing progress reports along
the way."""

import copy
import time
import os
from pathlib import Path
from typing import List

import pavilion.cmd_utils
from pavilion import commands
from pavilion import series
from pavilion import series_util
from pavilion.output import fprint
from pavilion import status_utils
from pavilion.status_file import STATES
from pavilion.test_run import TestRun


def check_pgid(pgid):
    """Checks if pgid still exists. Returns false if pgid does not exist."""

    try:
        # PGID needs to be negative
        if pgid > 0:
            pgid = -1*pgid

        # No signal is sent, but an OS Error will be raised if the PID doesn't
        # exist
        os.kill(pgid, 0)
    except OSError:
        return False
    else:
        return True


class WaitCommand(commands.Command):
    """A command to wait for test completion."""

    def __init__(self):
        super().__init__('wait', 'Wait for the specified test or series to '
                         'complete or fail and return the status.',
                         short_help="Wait for statuses of tests.")

        self.comp_list = [STATES.CREATION_ERROR,
                          STATES.SCHED_ERROR,
                          STATES.SCHED_CANCELLED,
                          STATES.BUILD_FAILED,
                          STATES.BUILD_TIMEOUT,
                          STATES.BUILD_ERROR,
                          STATES.ENV_FAILED,
                          STATES.RUN_TIMEOUT,
                          STATES.RUN_ERROR,
                          STATES.RESULTS_ERROR,
                          STATES.COMPLETE]

    OUT_SILENT = 'silent'
    OUT_SUMMARY = 'summary'

    def _setup_arguments(self, parser):

        parser.add_argument(
            '-t', '--timeout', action='store',
            help='Maximum time to wait for results in seconds. Default is to '
                 'wait indefinitely.'
        )
        parser.add_argument(
            'tests', nargs='*', action='store',
            help='The name(s) of the tests to check.  These may be any mix of '
                 'test IDs and series IDs.  If no value is provided, the most '
                 'recent series submitted by this user is checked.'
        )

        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '-s', '--silent',
            action='store_const', dest='out_mode', const=self.OUT_SILENT,
            help="No periodic status output."
        )
        group.add_argument(
            '--summary',
            action='store_const', dest='out_mode', const=self.OUT_SUMMARY,
            help="Prints a summary of the status."
        )

    def run(self, pav_cfg, args):
        """Wait for the requested tests to complete."""

        # get start time
        start_time = time.time()

        tests = []
        # if args.tests is empty, then retrieve the last series
        if not args.tests:
            series_id = series_util.load_user_series_id(pav_cfg)
            if series_id is not None:
                series_obj = series.TestSeries.load(pav_cfg, series_id)
                # if this is a series made from a series file, add the
                # whole series id to the list of tests
                if Path(series_obj.path/'series.pgid').exists():
                    tests.append(series_id)
                else:
                    tests.extend(pavilion.cmd_utils.get_tests_by_id(pav_cfg, args.tests,
                                                                    self.errfile))
            else:
                raise commands.CommandError(
                    "No tests specified and no last series found"
                )

        else:
            tests_cli = copy.deepcopy(args.tests)
            for test_id in tests_cli:
                if test_id.startswith('s'):
                    series_obj = series.TestSeries.load(pav_cfg, test_id)
                    if Path(series_obj.path/'series.pgid').exists():
                        tests.append(test_id)
                        args.tests.remove(test_id)

            tests.extend(pavilion.cmd_utils.get_tests_by_id(pav_cfg, args.tests,
                                                            self.errfile))

        # determine timeout time, if there is one
        end_time = None
        if args.timeout is not None:
            end_time = start_time + float(args.timeout)

        self.wait(pav_cfg, tests, end_time, args.out_mode)
        return 0

    STATUS_UPDATE_PERIOD = 5  # seconds

    def wait(self, pav_cfg, tests: List[int], end_time: float,
             out_mode: str) -> None:
        """Wait on each of the given tests to complete, printing a status
        message """

        status_time = time.time() + self.STATUS_UPDATE_PERIOD
        while (len(tests) != 0) and (end_time is None or
                                     time.time() < end_time):

            # Check which tests have completed or failed and move them to the
            # final list.
            temp_tests = copy.deepcopy(tests)
            for test_id in temp_tests:
                if str(test_id).startswith('s'):
                    series_obj = series.TestSeries.load(pav_cfg, test_id)
                    series_complete_file = series_obj.path/'SERIES_COMPLETE'
                    if series_complete_file.exists():
                        tests.remove(test_id)
                else:
                    test_obj = TestRun.load(pav_cfg, test_id)
                    run_complete_file = test_obj.path/'RUN_COMPLETE'
                    if run_complete_file.exists():
                        tests.remove(test_id)

            # print status every 5 seconds
            if time.time() > status_time:
                status_time = time.time() + self.STATUS_UPDATE_PERIOD

                stats = status_utils.get_statuses(pav_cfg, tests,
                                                  errfile=self.errfile)
                stats_out = []

                if out_mode == self.OUT_SILENT:
                    pass
                elif out_mode == self.OUT_SUMMARY:
                    states = {}
                    for test in stats:
                        if test['state'] not in states.keys():
                            states[test['state']] = 1
                        else:
                            states[test['state']] += 1
                    status_counts = []
                    for state, count in states.items():
                        status_counts.append(state + ': ' + str(count))
                    fprint(' | '.join(status_counts), file=self.outfile,
                           end='\r', width=None)
                else:
                    for test in stats:
                        stat = [str(time.ctime(time.time())), ':',
                                'test #',
                                str(test['test_id']),
                                test['name'],
                                test['state'],
                                test['note'],
                                "\n"]
                        stats_out.append(' '.join(stat))
                    fprint(''.join(map(str, stats_out)),
                           file=self.outfile, width=None)

        final_stats = status_utils.get_statuses(pav_cfg, tests,
                                                errfile=self.errfile)
        fprint('\n', file=self.outfile)
        status_utils.print_status(final_stats, self.outfile)
