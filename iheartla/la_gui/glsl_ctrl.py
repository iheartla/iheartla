import wx
import wx.stc as stc
from ..la_gui import base_ctrl as bc


class GLSLTextControl(bc.BaseTextControl):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetLexer(wx.stc.STC_LEX_CPP)
        kwlist = u"Asm auto bool break case catch char class const_cast	continue default delete	do double else " \
                 u"enum	dynamic_cast extern	false float for	union unsigned using friend goto if	"\
                 u"inline int long mutable virtual namespace new operator private protected	public " \
                 u"register	void reinterpret_cast return short signed sizeof static	static_cast	volatile " \
                 u"struct switch template this throw true try typedef typeid unsigned wchar_t while "
        self.SetKeyWords(0, kwlist)
        # background
        self.StyleSetBackground(wx.stc.STC_C_DEFAULT, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_COMMENT, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_COMMENTLINE, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_COMMENTDOC, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_NUMBER, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_WORD, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_STRING, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_CHARACTER, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_UUID, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_PREPROCESSOR, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_OPERATOR, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_IDENTIFIER, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_STRINGEOL, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_VERBATIM, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_REGEX, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_COMMENTLINEDOC, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_WORD2, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_COMMENTDOCKEYWORD, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_COMMENTDOCKEYWORDERROR, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_GLOBALCLASS, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_STRINGRAW, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_TRIPLEVERBATIM, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_HASHQUOTEDSTRING, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_PREPROCESSORCOMMENT, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_PREPROCESSORCOMMENTDOC, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_USERLITERAL, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_TASKMARKER, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_C_ESCAPESEQUENCE, bc.BACKGROUND_COLOR)

        # Default
        self.StyleSetSpec(stc.STC_C_DEFAULT, "fore:#A9B7C6," + self.fonts)

        # Character
        self.StyleSetSpec(stc.STC_C_CHARACTER, "fore:#9686F5," + self.fonts)
        # Number
        self.StyleSetSpec(stc.STC_C_NUMBER, "fore:#9686F5," + self.fonts)
        # Keyword
        self.StyleSetSpec(stc.STC_C_WORD, "fore:#FC5FA3,bold," + self.fonts)
        # String
        self.StyleSetSpec(stc.STC_C_STRING, "fore:#FC6A5D," + self.fonts)
        # Preprocessor
        self.StyleSetSpec(stc.STC_C_PREPROCESSOR, "fore:#FD8F3F," + self.fonts)
        self.StyleSetSpec(stc.STC_C_PREPROCESSORCOMMENT, "fore:#FD8F3F," + self.fonts)
        self.StyleSetSpec(stc.STC_C_PREPROCESSORCOMMENTDOC, "fore:#FD8F3F," + self.fonts)
        # Comments
        self.StyleSetSpec(stc.STC_C_COMMENT, "fore:#6C7986," + self.fonts)
        # Comment-blocks
        self.StyleSetSpec(stc.STC_C_COMMENTLINE, "fore:#6C7986," + self.fonts)
        self.StyleSetSpec(stc.STC_C_COMMENTDOC, "fore:#6C7986," + self.fonts)
        self.StyleSetSpec(stc.STC_C_COMMENTLINEDOC, "fore:#6C7986," + self.fonts)
        self.StyleSetSpec(stc.STC_C_COMMENTDOCKEYWORD, "fore:#6C7986," + self.fonts)
        self.StyleSetSpec(stc.STC_C_COMMENTDOCKEYWORDERROR, "fore:#6C7986," + self.fonts)
        self.StyleSetSpec(stc.STC_C_OPERATOR, "fore:#A9B7C6,bold," + self.fonts)
        self.StyleSetSpec(stc.STC_C_IDENTIFIER, "fore:#A9B7C6,bold," + self.fonts)

        ####
        self.StyleSetSpec(stc.STC_C_UUID, "fore:#629755," + self.fonts)
        self.StyleSetSpec(stc.STC_C_GLOBALCLASS, "fore:#91D462," + self.fonts)
        self.StyleSetSpec(stc.STC_C_STRINGRAW, "fore:#629755," + self.fonts)
        self.StyleSetSpec(stc.STC_C_TRIPLEVERBATIM, "fore:#629755," + self.fonts)
        self.StyleSetSpec(stc.STC_C_HASHQUOTEDSTRING, "fore:#629755," + self.fonts)
        self.StyleSetSpec(stc.STC_C_USERLITERAL, "fore:#629755," + self.fonts)
        self.StyleSetSpec(stc.STC_C_TASKMARKER, "fore:#629755," + self.fonts)
        self.StyleSetSpec(stc.STC_C_ESCAPESEQUENCE, "fore:#629755," + self.fonts)
        # End of line where string is not closed
        self.StyleSetSpec(stc.STC_C_STRINGEOL, "fore:#629755,eol," + self.fonts)