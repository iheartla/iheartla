import iheartla.la_tools.la_helper as la_helper
from iheartla.la_tools.la_helper import DEBUG_MODE
from iheartla.la_tools.la_logger import LaLogger
import logging
import argparse


if __name__ == '__main__':
    LaLogger.getInstance().set_level(logging.DEBUG if DEBUG_MODE else logging.ERROR)
    arg_parser = argparse.ArgumentParser(description='I Heart LA')
    arg_parser.add_argument('-o', '--output', help='The output language', choices = ['numpy', 'eigen', 'latex','matlab'])
    # arg_parser.add_argument('-i', '--input', help='File name containing I heart LA source code')
    arg_parser.add_argument('--GUI', action='store_true', help='Launch the GUI editor')
    arg_parser.add_argument('--regenerate-grammar', action='store_true', help='Regenerate grammar files')
    arg_parser.add_argument('input', nargs='*', help='The I Heart LA files to compile.')
    args = arg_parser.parse_args()
    if args.regenerate_grammar:
        la_helper.DEBUG_PARSER = True
        import iheartla.la_tools.parser_manager
        iheartla.la_tools.parser_manager.recreate_local_parser_cache()
    else:
        from iheartla.compiler import show_gui
        from iheartla.la_parser.parser import compile_la_file, ParserTypeEnum
        if args.GUI:
            show_gui()
        elif args.input:
            # output all defaults (unless outputs present)
            parser_type = ParserTypeEnum.DEFAULT
            out_dict = {"numpy": ParserTypeEnum.NUMPY, "eigen": ParserTypeEnum.EIGEN, "latex": ParserTypeEnum.LATEX, "mathjax": ParserTypeEnum.MATHJAX, "matlab": ParserTypeEnum.MATLAB}
            if args.output:
                # when output args are present _only_ output those
                parser_type = ParserTypeEnum.INVALID
                out_list = args.output.split(",")
                for out in out_list:
                    assert out in out_dict, "Parameters after -o or --output can only be numpy, eigen, latex, or matlab"
                    parser_type = parser_type | out_dict[out]
            for input in args.input: compile_la_file(input, parser_type)
        else:
            show_gui()
