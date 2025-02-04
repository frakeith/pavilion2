from pavilion import unittest
from pavilion import arguments
from pavilion import plugins
from pavilion import commands


class ShowTests(unittest.PavTestCase):

    def test_show_cmds(self):

        arg_lists = [
            ('show', 'config'),
            ('show', 'config', '--template'),
            ('show', 'functions'),
            ('show', 'functions', '--detail', 'int'),
            ('show', 'hosts'),
            ('show', 'hosts', '--verbose'),
            ('show', 'hosts', '--vars', 'this'),
            ('show', 'hosts', '--config', 'this'),
            ('show', 'modes'),
            ('show', 'modes', '--verbose'),
            ('show', 'modes', '--vars', 'defaulted'),
            ('show', 'modes', '--config', 'defaulted'),
            ('show', 'module_wrappers'),
            ('show', 'module_wrappers', '--verbose'),
            ('show', 'pav_vars'),
            ('show', 'result_parsers'),
            ('show', 'result_parsers', '--doc=regex'),
            ('show', 'result_parsers', '--verbose'),
            ('show', 'sched'),
            ('show', 'sched', '--config'),
            ('show', 'sched', '--vars=slurm'),
            ('show', 'states'),
            ('show', 'suites'),
            ('show', 'suites', '--err'),
            ('show', 'suites', '--supersedes'),
            ('show', 'suites', '--verbose'),
            ('show', 'system_variables'),
            ('show', 'system_variables', '--verbose'),
            ('show', 'test_config'),
            ('show', 'tests'),
            ('show', 'tests', '--err'),
            ('show', 'tests', '--doc', 'hello_world.narf'),
            ('show', 'tests', '--hidden'),
            ('show', 'tests', '--verbose'),
        ]

        parser = arguments.get_parser()

        show_cmd = commands.get_command('show')
        show_cmd.silence()

        for arg_list in arg_lists:
            args = parser.parse_args(arg_list)
            show_cmd.run(self.pav_cfg, args)
