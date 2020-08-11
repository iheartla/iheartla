import wx
import wx.stc
import la_gui.base_ctrl as bc


class LaTextControl(bc.BaseTextControl):
    # Style IDs
    STC_STYLE_LA_DEFAULT, \
    STC_STYLE_LA_KW,\
    STC_STYLE_LA_IDENTIFIER,\
    STC_STYLE_LA_STRING,\
    STC_STYLE_LA_OPERATOR,\
    STC_STYLE_LA_NUMBER,\
    STC_STYLE_LA_ESCAPE_CHAR, \
    STC_STYLE_LA_ESCAPE_STR , \
    STC_STYLE_LA_ESCAPE_PARAMETER, \
    STC_STYLE_LA_ESCAPE_DESCRIPTION  = range(10)

    def __init__(self, parent):
        super().__init__(parent)
        self.SetEditable(True)
        self.keywords = ['where', 'trace', 'vec', 'diag', 'Id', 'eig', 'conj', 'Re', 'Im', 'inv', 'sqrt', 'exp',
                         'log', 'det', 'svd', 'rank', 'null', 'orth', 'qr', 'sum', 'symmetric', 'diagonal', 'if',
                         'otherwise', 'is', 'in']
        self.unicode_dict = {'R': 'ℝ', 'Z': 'ℤ', 'x': '×', 'inf': '∞', 'in': '∈', 'sum': '∑',
                             'had': '○', 'kro': '⨂', 'dot': '⋅', 'T': 'ᵀ', 'par': '∂', 'emp': '∅',
                             'arr': '→', 'int': '∫', 'dbl': '‖', 'pi': 'π', 'sig': 'σ', 'row': 'ρ',
                             'phi': 'ϕ', 'the': 'θ'}
        self.StyleSetSpec(self.STC_STYLE_LA_DEFAULT, "fore:#A9B7C6,back:{}".format(bc.BACKGROUND_COLOR))
        self.StyleSetSpec(self.STC_STYLE_LA_KW, "fore:#94558D,bold,back:{}".format(bc.BACKGROUND_COLOR))
        self.StyleSetSpec(self.STC_STYLE_LA_ESCAPE_STR, "fore:#6A8759,bold,back:{}".format(bc.BACKGROUND_COLOR))
        self.StyleSetSpec(self.STC_STYLE_LA_NUMBER, "fore:#9686F5,bold,back:{}".format(bc.BACKGROUND_COLOR))
        self.StyleSetSpec(self.STC_STYLE_LA_ESCAPE_PARAMETER, "fore:#CC7832,bold,back:{}".format(bc.BACKGROUND_COLOR))
        self.StyleSetSpec(self.STC_STYLE_LA_ESCAPE_DESCRIPTION, "fore:#6C7986,bold,back:{}".format(bc.BACKGROUND_COLOR))
        self.SetLexer(wx.stc.STC_LEX_CONTAINER)
        # evt handler
        self.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.Bind(wx.stc.EVT_STC_STYLENEEDED, self.OnStyleNeeded)

    def OnStyleNeeded(self, event):
        where_block = False
        last_styled_pos = self.GetEndStyled()
        line = self.LineFromPosition(last_styled_pos)
        start_pos = self.PositionFromLine(line)
        end_pos = event.GetPosition()
        start_pos = 0
        # print("line:{}, start_pos:{}, end_pos:{}".format(line, start_pos, end_pos))
        while start_pos < end_pos:
            self.StartStyling(start_pos)
            char = self.GetTextRange(start_pos, start_pos+1)
            style = self.STC_STYLE_LA_DEFAULT
            if char == '`':
                # identifier with description
                self.SetStyling(1, self.STC_STYLE_LA_ESCAPE_STR)
                start_pos += 1
                while start_pos < end_pos and self.GetTextRange(start_pos, start_pos+1) != '`':
                    self.StartStyling(start_pos)
                    self.SetStyling(1, self.STC_STYLE_LA_ESCAPE_STR)
                    start_pos += 1
                self.SetStyling(1, self.STC_STYLE_LA_ESCAPE_STR)
                start_pos += 1
                continue
            elif char == ':' and where_block:
                # parameters after where block
                cur_line = self.LineFromPosition(start_pos)
                line_pos = self.PositionFromLine(cur_line)
                # print("cur_line:{}, start_pos:{}, line_pos:{}", cur_line, start_pos, line_pos)
                if ':' not in self.GetTextRange(line_pos, start_pos):
                    self.StartStyling(line_pos)
                    self.SetStyling(start_pos-line_pos, self.STC_STYLE_LA_ESCAPE_PARAMETER)
                    self.StartStyling(start_pos)
                else:
                    line_end = self.GetLineEndPosition(cur_line)
                    if self.GetTextRange(line_pos, start_pos).count(':') == 1:
                        self.StartStyling(start_pos + 1)
                        self.SetStyling(line_end - start_pos + 1, self.STC_STYLE_LA_ESCAPE_DESCRIPTION)
                        start_pos = line_end
                        continue
            elif char == '\\':
                # unicode string
                match = False
                index = 1
                prefix = self.GetTextRange(start_pos, start_pos + index)
                unicode_str = ''
                while self.is_unicode_prefix(prefix) and start_pos + index < end_pos:
                    if self.is_unicode(prefix):
                        unicode_str = self.get_unicode(prefix)
                        match = True
                        break
                    index += 1
                    prefix = self.GetTextRange(start_pos, start_pos + index)
                if match:
                    self.DeleteRange(start_pos, index)
                    self.AddText(unicode_str)
                    start_pos += index
                    continue
            else:
                if char.isnumeric():
                    # numbers
                    style = self.STC_STYLE_LA_NUMBER
                else:
                    # keywords
                    index = 1
                    prefix = self.GetTextRange(start_pos, start_pos+index)
                    if start_pos > 1 and not self.GetTextRange(start_pos-1, start_pos).isalnum():
                        while self.is_keyword_prefix(prefix) and start_pos+index < end_pos:
                            index += 1
                            prefix = self.GetTextRange(start_pos, start_pos + index)
                        if index > 2 and start_pos+index+1 < end_pos:
                            if not self.GetTextRange(start_pos + index - 1, start_pos + index).isalnum():
                                prefix = self.GetTextRange(start_pos, start_pos + index - 1)
                                if self.is_keyword(prefix):
                                    self.SetStyling(index, self.STC_STYLE_LA_KW)
                                    start_pos += index - 1
                                    if prefix == 'where':
                                        where_block = True
                                    continue
            self.SetStyling(1, style)
            start_pos += 1

    def OnMarginClick(self, event):
        pass

    def is_keyword_prefix(self, prefix):
        for keyword in self.keywords:
            if keyword.startswith(prefix):
                return True
        return False

    def is_unicode_prefix(self, prefix):
        for unicode in self.unicode_dict:
            target = '\\' + unicode + '\\'
            if target.startswith(prefix):
                return True
        return False

    def get_unicode(self, unicode):
        return self.unicode_dict[unicode.replace('\\', '')]

    def is_keyword(self, key):
        return key in self.keywords

    def is_unicode(self, prefix):
        for unicode in self.unicode_dict:
            target = '\\' + unicode + '\\'
            if target == prefix:
                return True
        return False

