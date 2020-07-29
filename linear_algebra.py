from la_gui.frame import *
from la_parser.parser import compile_la_file
from la_tools.la_logger import LaLogger, LoggerTypeEnum
import logging
import argparse


def show_gui():
    app = wx.App(False)
    MainWindow(None, "I heart LA")
    app.MainLoop()


if __name__ == '__main__':
    LaLogger.getInstance().set_level(logging.INFO)
    arg_parser = argparse.ArgumentParser(description='I heart LA')
    arg_parser.add_argument('-o', '--output', help='Type of output languages')
    # arg_parser.add_argument('-i', '--input', help='File name containing I heart LA source code')
    arg_parser.add_argument('--gui', action='store_true', help='Editor for I heart LA')
    arg_parser.add_argument('input', nargs='?')
    args = arg_parser.parse_args()
    if args.gui:
        show_gui()
    elif args.input:
        parser_type = ParserTypeEnum.DEFAULT
        out_dict = {"numpy": ParserTypeEnum.NUMPY, "eigen": ParserTypeEnum.EIGEN, "latex": ParserTypeEnum.LATEX}
        if args.output:
            out_list = args.output.split(",")
            for out in out_list:
                assert out in out_dict, "Parameters after -o or --output can only be numpy, eigen or latex"
                parser_type = parser_type | out_dict[out]
        compile_la_file(args.input, parser_type)
    else:
        show_gui()