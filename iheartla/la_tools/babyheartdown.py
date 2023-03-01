#!/usr/bin/env python3

import re

## Authoritative regexps in HeartDown: https://github.com/iheartla/markdown/blob/835cec5cde6b67a9a73790db101376873a3f00b5/markdown/extensions/iheartla_code.py

## Match string: ``` iheartla (context)
#FENCED_BLOCK_RE = re.compile(
#   dedent(r'''
#       (?P<fence>^(?:~{3,}|`{3,}))[ ]*                          # opening fence
#       iheartla\s*
#       (\((?P<module>[^\}\n]*)\))                        # required {module} 
#       \n                                                       # newline (end of opening fence)
#       (?P<code>.*?)(?<=\n)                                     # the code block
#       (?P=fence)[ ]*$                                          # closing fence
#   '''),
#   re.MULTILINE | re.DOTALL | re.VERBOSE
#)
## Match string: ❤️context: a=sin(θ)❤️
#INLINE_RE = re.compile(
#   dedent(r'''❤(?P<module>[a-zA-Z0-9\.\t\r\f\v ]*)(:)(?P<code>.*?)❤'''),
#   re.MULTILINE | re.VERBOSE
#)
## Match string: ❤ : context
#CONTEXT_RE = re.compile(
#   dedent(r'''(?<=(\n)*)([\t\r\f\v ]*)❤(\s*):(?P<context>[^\n❤]*)(?=\n)'''),
#   re.MULTILINE | re.VERBOSE
#)
#
## Match string: ``` iheartla
#RAW_CODE_BLOCK_RE = re.compile(
#   dedent(r'''
#       (?P<fence>^(?:~{3,}|`{3,}))[ ]*                          # opening fence
#       iheartla\s*
#       \n                                                       # newline (end of opening fence)
#   '''),
#   re.MULTILINE | re.DOTALL | re.VERBOSE
#)
## Match string: ``` iheartla_unnumbered
#RAW_NUM_CODE_BLOCK_RE = re.compile(
#   dedent(r'''
#       (?P<fence>^(?:~{3,}|`{3,}))[ ]*                          # opening fence
#       iheartla_unnumbered\s*
#       \n                                                       # newline (end of opening fence)
#   '''),
#   re.MULTILINE | re.DOTALL | re.VERBOSE
#)
## Match string: ❤ a=sin(θ)❤
#RAW_CODE_INLINE_RE = re.compile(
#   dedent(r'''❤(?P<code>[^❤]*)❤'''),
#   re.MULTILINE | re.VERBOSE
#)

CODE_BLOCK = re.compile( r'```\s*(?:iheartla|iheartla_unnumbered)\s*(?P<context>\(.*\))?\s*\n(?P<code>.*?)\s*```', re.DOTALL )
CODE_INLINE = re.compile( r'❤️\s*(?P<context>.+?:)?\s*(?P<code>.*?)❤️' )
CONTEXT_LINE = re.compile( r'^\s*❤️\s*:(?P<context>\s*[^\n❤️]+)\s*$', re.MULTILINE )

def heartdown2lines( text ):
    '''
    Extracts the I❤️LA code from H❤️rtDown text.
    
    Given:
        text: A string of H❤️rtDown
    Returns:
        d: A dictionary mapping from context names to strings suitable for the I❤️LA compiler.
           Code in an undeclared context is returned as the value for the `None` key.
    '''
    
    ## Find global contexts.
    for match in CONTEXT_LINE.finditer( text ):
        raise NotImplementedError("Contexts aren't supported")
    
    ## Store spans of iheartla code in `text`
    spans = []
    
    ## Find the code spans
    from itertools import chain
    for match in chain( CODE_BLOCK.finditer( text ), CODE_INLINE.finditer( text ) ):
        ## Error for contexts
        if match['context'] is not None:
            raise NotImplementedError("Contexts aren't supported")
        
        spans.append( match.span('code') )
    
    ## Sort the spans
    spans.sort()
    
    ## Output the code protected by newlines
    if len(spans) > 0:
        result = '\n'.join([ text[start:end].strip() for start,end in spans ])
    else:
        result = text
    return result

def test_heartdown2lines():
    
    import pytest
    
    ex = '''
This is text to ignore
❤️: foo
This is text to ignore
```iheartla
a+b
c*d
```
This is text to ignore
'''
    with pytest.raises(NotImplementedError) as e:
        heartdown2lines( ex )
    
    
    ex = '''This is text to ignore
```iheartla
a+b
c*d
```
This is text to ignore
'''
    assert heartdown2lines( ex ) == '''a+b
c*d'''
    
    ex = '''This is text to ignore
```iheartla(foo)
a+b
c*d
```
'''
    with pytest.raises(NotImplementedError) as e:
        heartdown2lines( ex )
    
    ex = '''
This is text ❤️math to keep❤️ text to ignore:
```iheartla
a+b
c*d
```
This is text to ignore
```iheartla
efg
```
This is text to ignore
'''
    assert heartdown2lines( ex ) == '''math to keep
a+b
c*d
efg'''
    
    ex = '''❤️foo:a+b❤️'''
    with pytest.raises(NotImplementedError) as e:
        heartdown2lines( ex )
    
    ex = '''❤️a+b❤️'''
    assert heartdown2lines( ex ) == 'a+b'

if __name__ == '__main__':
    import pytest
    print( "Debug the following by running: python -m pytest --pdb flat_metrics.py" )
    import pytest
    pytest.main([__file__])
