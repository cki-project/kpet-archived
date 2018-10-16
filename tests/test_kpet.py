import unittest
import argparse
import kpet


class ArgumentParserTest(unittest.TestCase):
    def test_build_tree_command(self):
        parser = argparse.ArgumentParser()
        common_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser = parser.add_subparsers(dest="command")
        kpet.build_tree_command(cmd_parser, common_parser)
        args = parser.parse_args(['tree', 'list'])
        self.assertEqual('tree', args.command)
        self.assertEqual('list', args.action)

    def test_build_arch_command(self):
        parser = argparse.ArgumentParser()
        common_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser = parser.add_subparsers(dest="command")
        kpet.build_arch_command(cmd_parser, common_parser)
        args = parser.parse_args(['arch', 'list'])
        self.assertEqual('arch', args.command)
        self.assertEqual('list', args.action)

    def test_build_run_command(self):
        parser = argparse.ArgumentParser()
        common_parser = argparse.ArgumentParser(add_help=False)
        cmd_parser = parser.add_subparsers(dest="command")
        kpet.build_run_command(cmd_parser, common_parser)
        self.assertRaises(SystemExit, parser.parse_args, ['run', 'generate'])

        args = parser.parse_args(
            ['run', 'generate', '-t', 'foo', '-k', 'bar', 'mbox1', 'mbox2']
        )
        self.assertEqual('run', args.command)
        self.assertEqual('generate', args.action)
        self.assertEqual('foo', args.tree)
        self.assertEqual('bar', args.kernel)
        self.assertListEqual(['mbox1', 'mbox2'], args.mboxes)
