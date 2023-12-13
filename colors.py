from typing import *
def esc(*codes: Union[int, str]) -> str:
    if not codes:
        return ''
    codes_str = ';'.join(str(c) for c in codes)
    return f'\x1b[{codes_str}m'


def make_color(start, end: str) -> Callable[[str], str]:
    def color_func(s: str) -> str:
        return start + s + end
    return color_func


END = esc(0)

FG_END = esc(39)
red = make_color(esc(31), FG_END)
green = make_color(esc(32), FG_END)
blue = make_color(esc(34), FG_END)
magenta = make_color(esc(35), FG_END)
cyan = make_color(esc(36), FG_END)
white = make_color(esc(37), FG_END)


HL_END = esc(22, 27, 39)
HL_END = esc(22, 27, 0)
green_hl = make_color(esc(1, 32, 7), HL_END)
white_hl = make_color(esc(1, 37, 7), HL_END)


    