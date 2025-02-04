import argparse
import io
import time

from pavilion import commands
from pavilion import plugins
from pavilion import schedulers
from pavilion import status_file
from pavilion.series.series import TestSeries
from pavilion.test_config import file_format
from pavilion.unittest import PavTestCase


class StatusCmdTests(PavTestCase):

    def setUp(self):
        plugins.initialize_plugins(self.pav_cfg)

    def tearDown(self):
        plugins._reset_plugins()

    def test_status_arguments(self):
        status_cmd = commands.get_command('status')

        parser = argparse.ArgumentParser()
        status_cmd._setup_arguments(parser)
        args = parser.parse_args(['test1', 'test2'])

        self.assertEqual(args.tests[0], 'test1')
        self.assertEqual(args.tests[1], 'test2')
        self.assertEqual(args.json, False)

        parser = argparse.ArgumentParser()
        status_cmd._setup_arguments(parser)
        args = parser.parse_args(['-j', 'test0', 'test9'])

        self.assertEqual(args.tests[0], 'test0')
        self.assertEqual(args.tests[1], 'test9')
        self.assertEqual(args.json, True)

    def test_status_command(self):
        """Test status command by generating a suite of tests."""

        config1 = file_format.TestConfigLoader().validate({
            'scheduler': 'raw',
            'cfg_label': 'test',
            'run': {
                'env': {
                    'foo': 'bar',
                },
                'cmds': ['echo "I $foo, punks"'],
            },
        })

        config1['name'] = 'run_test0'

        config2 = file_format.TestConfigLoader().validate({
            'scheduler': 'raw',
            'cfg_label': 'test',
            'run': {
                'env': {
                    'too': 'tar',
                },
                'cmds': ['echo "I $too, punks"'],
            },
        })

        config2['name'] = 'run_test1'

        config3 = file_format.TestConfigLoader().validate({
            'scheduler': 'raw',
            'cfg_label': 'test',
            'run': {
                'env': {
                    'too': 'tar',
                },
                'cmds': ['sleep 10'],
            },
        })

        config3['name'] = 'run_test2'

        configs = [config1, config2, config3]

        tests = [self._quick_test(cfg) for cfg in configs]

        for test in tests:
            test.RUN_SILENT_TIMEOUT = 1

        # Make sure this doesn't explode
        series = TestSeries(self.pav_cfg, None)
        for test in tests:
            series._add_test(test)
        test_str = " ".join([test.full_id for test in series.tests.values()])

        status_cmd = commands.get_command('status')
        status_cmd.outfile = io.StringIO()

        # Testing for individual tests with json output
        for test in series.tests.values():
            parser = argparse.ArgumentParser()
            status_cmd._setup_arguments(parser)
            arg_list = ['-j', test.full_id]
            args = parser.parse_args(arg_list)
            self.assertEqual(status_cmd.run(self.pav_cfg, args), 0)

        # Testing for multiple tests with json output
        parser = argparse.ArgumentParser()
        status_cmd._setup_arguments(parser)
        arg_list = ['-j'] + test_str.split()
        args = parser.parse_args(arg_list)
        self.assertEqual(status_cmd.run(self.pav_cfg, args), 0)

        # Testing for individual tests with tabular output
        for test in series.tests.values():
            parser = argparse.ArgumentParser()
            status_cmd._setup_arguments(parser)
            args = parser.parse_args([test.full_id])
            self.assertEqual(status_cmd.run(self.pav_cfg, args), 0)

        # Testing for multiple tests with tabular output
        parser = argparse.ArgumentParser()
        status_cmd._setup_arguments(parser)
        arg_list = test_str.split()
        args = parser.parse_args(arg_list)
        self.assertEqual(status_cmd.run(self.pav_cfg, args), 0)

    def test_set_status_command(self):
        """Test set status command by generating a suite of tests."""

        config1 = file_format.TestConfigLoader().validate({
            'scheduler': 'raw',
            'cfg_label': 'test',
            'run': {
                'env': {
                    'foo': 'bar',
                },
                'cmds': ['echo "I $foo, punks"'],
            },
        })

        config1['name'] = 'run_test0'

        config2 = file_format.TestConfigLoader().validate({
            'scheduler': 'raw',
            'cfg_label': 'test',
            'run': {
                'env': {
                    'too': 'tar',
                },
                'cmds': ['echo "I $too, punks"'],
            },
        })

        config2['name'] = 'run_test1'

        config3 = file_format.TestConfigLoader().validate({
            'scheduler': 'raw',
            'cfg_label': 'test',
            'run': {
                'env': {
                    'too': 'tar',
                },
                'cmds': ['sleep 10'],
            },
        })

        config3['name'] = 'run_test2'

        configs = [config1, config2, config3]

        tests = [self._quick_test(cfg) for cfg in configs]

        for test in tests:
            test.RUN_SILENT_TIMEOUT = 1

        set_status_cmd = commands.get_command('set_status')
        set_status_cmd.outfile = io.StringIO()

        # Testing for individual tests with json output
        for test in tests:
            start_status = test.status.current()
            parser = argparse.ArgumentParser()
            set_status_cmd._setup_arguments(parser)
            arg_list = ['-s', 'RUN_USER', '-n', 'tacos are delicious', test.full_id]
            args = parser.parse_args(arg_list)
            self.assertEqual(set_status_cmd.run(self.pav_cfg, args), 0,
                             "Invalid run return for test {}".format(test.full_id))
            end_status = test.status.current()

            self.assertNotEqual(end_status.state, start_status.state)
            self.assertNotEqual(end_status.note, start_status.note)
            self.assertEqual(end_status.state, 'RUN_USER')
            self.assertEqual(end_status.note, 'tacos are delicious')

    def test_status_command_with_sched(self):
        """Test status command when test is 'SCHEDULED'."""

        cfg = file_format.TestConfigLoader().validate({
            'scheduler': 'raw',
            'run': {
                'env': {
                    'foo': 'bar',
                },
                'cmds': ['sleep 1'],
            },
        })

        cfg['name'] = 'testytest'

        test = self._quick_test(cfg, build=False, finalize=False)

        test.build()
        sched = schedulers.get_plugin(test.scheduler)
        sched.schedule_tests(self.pav_cfg, [test])

        status_cmd = commands.get_command('status')
        status_cmd.silence()

        parser = argparse.ArgumentParser()
        status_cmd._setup_arguments(parser)
        args = parser.parse_args(['test.' + str(test.id)])
        test.status.set(status_file.STATES.SCHEDULED, "faker")
        self.assertEqual(status_cmd.run(self.pav_cfg, args), 0,
                         msg=status_cmd.clear_output())

        parser = argparse.ArgumentParser()
        status_cmd._setup_arguments(parser)
        args = parser.parse_args(['-j', 'test.{}'.format(test.id)])
        test.status.set(status_file.STATES.SCHEDULED, "faker")
        self.assertEqual(status_cmd.run(self.pav_cfg, args), 0)

        # TODO: Test that the above have actually been set.

    def test_status_summary(self):
        # Testing that status works with summary flag
        status_cmd = commands.get_command('status')
        status_cmd.silence()
        parser = argparse.ArgumentParser()
        status_cmd._setup_arguments(parser)
        arg_list = ['-s']
        args = parser.parse_args(arg_list)

        # Test that an empty working_dir fails correctly
        self.assertEqual(status_cmd.run(self.pav_cfg, args), 0)

        base_cfg = self._quick_test_cfg()
        test_cfg1 = base_cfg.copy()
        test_cfg1['name'] = 'test1'
        test_cfg2 = base_cfg.copy()
        test_cfg2['name'] = 'test2'
        test_cfg3 = base_cfg.copy()
        test_cfg3['name'] = 'test3'

        configs = [test_cfg1, test_cfg2, test_cfg3]
        tests = [self._quick_test(cfg) for cfg in configs]
        for test in tests:
            test.RUN_SILENT_TIMEOUT = 1

        # Testing that summary flags return correctly
        self.assertEqual(status_cmd.run(self.pav_cfg, args), 0)

    def test_status_history(self):
        # Testing that status works with history flag
        status_cmd = commands.get_command('status')
        out = io.StringIO()
        status_cmd.outfile = out

        parser = argparse.ArgumentParser()
        status_cmd._setup_arguments(parser)

        test = self._quick_test()
        raw = schedulers.get_plugin('raw')
        raw.schedule_tests(self.pav_cfg, [test])
        end = time.time() + 5
        while not test.complete and time.time() < end:
            time.sleep(.1)

        args = parser.parse_args(['--history', 'test.{}'.format(test.id)])
        self.assertEqual(status_cmd.run(self.pav_cfg, args), 0)

        out.seek(0)
        output = out.readlines()[4:]
        statuses = test.status.history()
        self.assertEqual(len(output), len(statuses), msg='output: {}, statuses: {}'
                         .format(output, statuses))
        for i in range(len(output)):
            self.assertTrue(statuses[i].state in output[i])
