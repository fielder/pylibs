__all__ = [ \
    "cons",
    "number",
    "string",
    "symbol",
    "nil",
    "parse",
    "iterList",
]

import collections
import string as pystring


cons = collections.namedtuple("cons", "car cdr")
number = collections.namedtuple("number", "val")
string = collections.namedtuple("string", "text")
symbol = collections.namedtuple("symbol", "name")

nil = cons(None, None)


def parse(text):
    val, idx = _parse(text, 0)

    nval, idx = _parse(text, idx)
    if nval is None:
        # only 1 item available to parse
        ret = val
    else:
        # we have 2+ items; assume caller wants them in a list
        items = [val]
        while nval is not None:
            items.append(nval)
            nval, idx = _parse(text, idx)
        ret = None
        for val in reversed(items):
            ret = cons(val, ret)

    return ret


def iterList(lst):
    while lst is not None and lst.car is not None:
        yield lst.car
        lst = lst.cdr


# chars that end a symbol or number
_seq_terminate_chars = pystring.whitespace + "()"

def _parse(text, idx):
    idx = _skipwhites(text, idx)

    if idx == len(text):
        # end of input
        return (None, idx)

    elif text[idx] == "(":
        idx += 1
        items = []
        while 1:
            idx = _skipwhites(text, idx)
            if idx == len(text):
                raise ValueError("unterminated list")
            elif text[idx] == ")":
                idx += 1
                break
            else:
                item, idx = _parse(text, idx)
                items.append(item)
        ret = None
        for val in reversed(items):
            ret = cons(val, ret)
        if ret is None:
            ret = nil
        return (ret, idx)

    elif text[idx] == ")":
        raise ValueError("unexpected list terminator")

    elif text[idx] == "\"":
        s, idx = _parseQuotedString(text, idx)
        return (string(s), idx)

    elif _isNumber(text, idx):
        val, idx = _parseNumber(text, idx)
        return (number(val), idx)

    else:
        start = idx
        while idx < len(text) and text[idx] not in _seq_terminate_chars:
            idx += 1
        name = text[start:idx]
        if name.lower == "nil":
            # special short-hand
            return (nil, idx)
        return (symbol(name), idx)


def _skipwhites(text, idx):
    while 1:
        while idx < len(text) and text[idx] in pystring.whitespace:
            idx += 1
        if idx == len(text):
            break
        elif text[idx] == "#":
            # comment; skip to next line and continue
            while idx < len(text) and text[idx] not in "\r\n":
                idx += 1
        else:
            break
    return idx


def _isNumber(text, idx):
    if text[idx:idx+2].lower() in ("0b", "0o", "0x"):
        return True

    while idx < len(text) and text[idx] in "+-":
        idx += 1

    # 3 .3 0.3 7.3e2

    if idx >= len(text):
        return False
    if text[idx] in pystring.digits:
        return True
    if text[idx] != ".":
        return False
    # number starts with a . which must be followed w/ a digit
    idx += 1
    if idx >= len(text):
        return False
    return text[idx] in pystring.digits


def _parseNumber(text, idx):
    start = idx

    while idx < len(text) and text[idx] in "+-":
        idx += 1

    # 3 .3 0.3 7.3e2 .73e2 73.e2

    if text[idx:idx+2].lower() in ("0b", "0o", "0x"):
        idx += 2
        while idx < len(text) and text[idx] not in _seq_terminate_chars:
            idx += 1
        try:
            s = text[start:idx]

            for c in s[2:]:
                if c not in pystring.hexdigits:
                    # disallow things like eval("0xf+33") or possibly
                    # malicious stuff
                    raise SyntaxError()

            val = eval(s)
        except SyntaxError:
            raise ValueError("invalid number \"{}\"".format(s))
    else:
        while idx < len(text) and text[idx] not in _seq_terminate_chars:
            idx += 1
        try:
            s = text[start:idx]

            i = 0
            while i < len(s) and s[i] in "+-":
                i += 1
            for c in s[i:]:
                if c not in pystring.digits + "e.":
                    # disallow things like eval("3+3") or possibly
                    # malicious stuff
                    raise SyntaxError()

            val = eval(s)
        except SyntaxError:
            raise ValueError("invalid number \"{}\"".format(s))

    return (val, idx)


_escape_xlate = { "0": "\x00",
                  "a": "\a",
                  "b": "\b",
                  "t": "\t",
                  "n": "\n",
                  "v": "\v",
                  "f": "\f",
                  "r": "\r",
                  "e": "\x1b" }

def _parseQuotedString(text, start):
    idx = start + 1 # skip initial quote

    ret = ""
    while 1:
        start = idx
        while idx < len(text) and text[idx] not in "\\\"":
            idx += 1

        ret += text[start:idx]

        if idx == len(text):
            # no terminating quote
            raise ValueError("unterminated quoted string")
        elif text[idx] == "\"":
            # end of quoted string
            idx += 1
            break
        else:
            # escape character
            idx += 1
            if idx == len(text):
                raise ValueError("escape sequence terminated by eof")

            if text[idx] in _escape_xlate:
                ret += _escape_xlate[text[idx]]
            else:
                ret += text[idx]

            idx += 1

    return (ret, idx)

