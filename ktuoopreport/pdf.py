from contextlib import contextmanager
from copy import deepcopy
from pygments.token import Token
from PIL import Image
from fpdf import FPDF, FPDFException
from fpdf.recorder import FPDFRecorder
from fpdf.fpdf import ToCPlaceholder, DocumentState, FPDFRecorder
from pygments.styles import get_style_by_name
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
from pygments.util import ClassNotFound
from typing import Literal, Optional
import contextlib
from dataclasses import dataclass, field

# BUG: `.unbreakable` breaks when it's nested inside of other context managers.
# Doesn't matter if the nested context managers use unbreakable or not inside
# of themselves. By broke I mean that text dosen't get placed correctly into
# the next page, when at the end of a page.
# Heh the unbreakable broke, funny :D
#
# Example:
#   pdf.set_font("times-new-roman", 12)
#   with pdf.unbreakable() as pdf: # type: ignore
#       with pdf.labeled_block(self.console_label):
#           with pdf.numbered_block(self.console_numbering_label): # type: ignore
#               pdf.image(console_image, w=pdf.epw)

@dataclass
class FontStyle:
    name: str

    normal_font: Optional[str] = field(default = None)
    italic_font: Optional[str] = field(default = None)
    bold_font: Optional[str] = field(default = None)
    bold_italic_font: Optional[str] = field(default = None)

    unicode: bool = field(default = False)

class PatchedFPDF(FPDF):
    def __init__(
            self, original, orientation="portrait", unit="mm", format="A4", font_cache_dir=True
    ):
        super().__init__(orientation, unit, format, font_cache_dir)
        self.original = original

    def _insert_table_of_contents(self):
        prev_state = self.state
        tocp = self._toc_placeholder
        self.page = tocp.start_page # type: ignore
        # Doc has been closed but we want to write to self.pages[self.page] instead of self.buffer:
        self.state = DocumentState.GENERATING_PAGE
        self.y = tocp.y # type: ignore
        tocp.render_function(self.original, self._outline) # type: ignore
        expected_final_page = tocp.start_page + tocp.pages - 1 # type: ignore
        if self.page != expected_final_page:
            too = "many" if self.page > expected_final_page else "few"
            error_msg = f"The rendering function passed to FPDF.insert_toc_placeholder triggered too {too} page breaks: "
            error_msg += f"ToC ended on page {self.page} while it was expected to span exactly {tocp.pages} pages" # type: ignore
            raise FPDFException(error_msg)
        self.state = prev_state

class PDF:
    """
        Acts as a standard interface to the fpdf2 library.
        This has been because I didn't like the design decisions in the library
        and wanted to add on my own features on top.

        The underlying fpdf2 object can still be accessed under `.fpdf`
    """
    fpdf: FPDF

    line_spacing: float = 1.15
    section_levels: list[int]
    font_stles: dict[str, FontStyle]

    numbering_index: int = 0

    numbering_font_family: str = "times-new-roman"
    numbering_font_style: str = "I"
    numbering_font_size: int = 12

    def __init__(
            self,
            orientation: str ="portrait",
            format: str ="A4",
            font_cache_dir: bool =True
        ):
        self.fpdf = PatchedFPDF(self, orientation, "cm", format, font_cache_dir)
        # self.fpdf = FPDF(orientation, "cm", format, font_cache_dir)
        self.section_levels = [1]
        self.font_styles = {}

    def add_font(self, style: FontStyle):
        assert style.name not in self.font_styles, "Style with this name already exists"
        self.font_styles[style.name] = style

        if style.normal_font is not None:
            self.fpdf.add_font(style.name, "", style.normal_font, style.unicode)

        if style.italic_font is not None:
            self.fpdf.add_font(style.name, "I", style.italic_font, style.unicode)

        if style.bold_font is not None:
            self.fpdf.add_font(style.name, "B", style.bold_font, style.unicode)

        if style.bold_italic_font is not None:
            self.fpdf.add_font(style.name, "BI", style.bold_italic_font, style.unicode)

    def set_font(self, name: str, size: float, bold: bool = False, italic: bool = False):
        assert name in self.font_styles, "Style not found"

        if italic and bold:
            self.fpdf.set_font(name, "BI", size)
        elif bold:
            self.fpdf.set_font(name, "B", size)
        elif italic:
            self.fpdf.set_font(name, "I", size)
        else:
            self.fpdf.set_font(name, "", size)

    def print(
            self,
            text: str,
            w: float = 0,
            h: Optional[float] = None,
            align: str = "",
            multiline: bool = False
        ):
        self.write(text, w, h, align, multiline)
        self.fpdf.ln()

    def write(
            self,
            text: str,
            w: float = 0,
            h: Optional[float] = None,
            align: Literal["L"]|Literal["R"]|Literal["C"]|Literal["J"] = "L",
            multiline: bool = False,
            border: int = 0,
            newlines: int = 0,
            max_line_height: Optional[int] = 0
        ):
        if h is None:
            h = self.fpdf.font_size * self.line_spacing # type: ignore

        if multiline:
            self.fpdf.multi_cell(w=w, h=h, txt=text, align=align, border=border, ln=newlines, max_line_height=max_line_height)
        else:
            self.fpdf.cell(w=w, h=h, txt=text, align=align, border=border, ln=newlines)

    # TODO: Create a more feature complete markdown writer
    # TODO: Feature: Only double \n\n create a \n
    def write_markdown(self, text: str):
        lexer = get_lexer_by_name("markdown")

        paragraph: list[str] = []
        prev_value = ""
        for ttype, value in lexer.get_tokens(text):
            # if ttype == Token.Generic.Strong:
                # pass
                # self.multi_cell(0, txt="".join(paragraph))
                # paragraph = []
                # self.set_font(style="B")
                # self.write(txt=value)
                # self.set_font(style="")
                # self.multi_cell(0, txt="".join(paragraph))
            if ttype == Token.Keyword and value == "*" and (prev_value == "\n" or prev_value == ""):
                paragraph.append("\n•")
            elif value == "\n" and prev_value == "\n":
                paragraph.append("\n")
            elif value != '\n':
                paragraph.append(value)
            prev_value = value

        self.fpdf.multi_cell(0, txt="".join(paragraph))

    def save_to_file(self, filename: str):
        self.fpdf.output(filename)

    def set_margins(self, left: float, top: float, right: float = -1):
        self.fpdf.set_margins(left, top, right)

    @property
    def left_margin(self):
        return self.fpdf.l_margin

    @property
    def right_margin(self):
        return self.fpdf.r_margin

    @property
    def top_margin(self):
        return self.fpdf.t_margin

    @property
    def bottom_margin(self):
        return self.fpdf.b_margin

    @property
    def font_size(self) -> int:
        return self.fpdf.font_size # type: ignore

    def get_y(self):
        return self.fpdf.y

    def get_x(self):
        return self.fpdf.x

    def line(self, x1: float, y1: float, x2: float, y2: float):
        self.fpdf.line(x1, y1, x2, y2)

    def set_auto_page_break(self, enabled, margin: float = 0):
        self.fpdf.set_auto_page_break(enabled, margin)

    def set_section_title_styles(
        self,
        level0,
        level1=None,
        level2=None,
        level3=None,
        level4=None,
        level5=None,
        level6=None,
    ):
        self.fpdf.set_section_title_styles(level0, level1, level2, level3, level4, level5, level6, )

    def add_page(self):
        self.fpdf.add_page()

    def move_cursor(self, dx: float = 0, dy: float = 0):
        x = self.fpdf.get_x()
        y = self.fpdf.get_y()
        self.fpdf.set_xy(x + dx, y + dy)

    def set_cursor(self, x: Optional[float] = None, y: Optional[float] = None):
        if y:
            self.fpdf.set_y(y)
        if x:
            self.fpdf.set_x(x)

    def reset_cursor(self):
        self.fpdf.x = self.fpdf.l_margin
        self.y = self.fpdf.t_margin

    def get_font_height(self, pt: Optional[float] = None):
        return (pt or self.fpdf.font_size_pt) / self.fpdf.k # type: ignore

    def image(
        self,
        image: Image.Image|str,
        w: float = 0,
        h: float = 0,
        centered: bool = False
    ):
        x = None
        if centered:
            if w == 0:
                if type(image) is str:
                    image = Image.open(image)
                w = image.size[0] # type: ignore
            x = self.fpdf.l_margin + (self.get_page_width() - self.fpdf.l_margin - self.fpdf.r_margin - w)/2

        return self.fpdf.image(image, x=x, w=w, h=h)

    @contextmanager
    def numbered_block(self, label: str):
        with self.unbreakable() as self: # type: ignore
            yield
            self.add_numbering(label)

    def add_numbering(self, label: str):
        self.numbering_index += 1
        self.fpdf.set_x(self.get_x() + 1.27) # type: ignore
        self.fpdf.set_font(self.numbering_font_family, self.numbering_font_style, self.numbering_font_size) # type: ignore
        self.fpdf.cell(  # type: ignore
            txt=label.format(index=self.numbering_index),
            ln=True
        )

    def newline(self, height: float = None):
        self.fpdf.ln(height)

    def get_page_width(self) -> float:
        return self.fpdf.dw_pt/self.fpdf.k

    def get_page_height(self) -> float:
        return self.fpdf.dh_pt/self.fpdf.k

    def get_page_size(self) -> tuple[float, float]:
        return self.get_page_width(), self.get_page_height()

    def set_draw_color(self, color: tuple[int, int, int]):
        self.fpdf.set_draw_color(*color)

    def insert_toc_placeholder(self, render_func, pages: int):
        self.fpdf.insert_toc_placeholder(render_func, pages)

        # BUG: Adjust starting page, because it's a bug
        # When the function creates a new placeholder page, it should start with
        # it, not the one before it.
        placeholder = self.fpdf._toc_placeholder
        assert placeholder
        self.fpdf._toc_placeholder = ToCPlaceholder(
            placeholder.render_function,
            placeholder.start_page+1,
            placeholder.y,
            placeholder.pages
        )

    @property
    def eph(self) -> float:
        return self.fpdf.eph

    @property
    def epw(self) -> float:
        return self.fpdf.epw

    @property
    def page_break_trigger(self) -> float:
        return self.fpdf.page_break_trigger

    @property
    def page(self) -> int:
        return self.fpdf.page

    @page.setter
    def page(self, new_page: int):
        self.fpdf.page = new_page

    @property
    def footer(self):
        return self.fpdf.footer

    @footer.setter
    def footer(self, new_footer):
        self.fpdf.footer = new_footer

    def get_string_width(self, text: str) -> float:
        return self.fpdf.get_string_width(text, True)

    def push_section(self, label: Optional[str] = None, *args, **kvargs):
        self.section_levels.append(1)
        if label:
            level = "".join(str(lvl)+"." for lvl in self.section_levels[:-1])
            label = label.format(level = level, *args, **kvargs)
        self.fpdf.start_section(label or "", len(self.section_levels)-2)

    def pop_section(self):
        self.section_levels.pop()
        self.section_levels[-1] += 1

    @contextmanager
    def section_block(self, label: Optional[str] = None, *args, **kvargs):
        self.push_section(label, *args, **kvargs)
        yield
        self.pop_section()

    def page_no(self) -> int:
        return self.fpdf.page_no()

    @contextlib.contextmanager
    def labeled_block(self, label: str):
        """
        Render label above block
        """
        # with self.unbreakable() as self: # type: ignore
        self.print(label)
        self.newline()
        yield
        self.newline()

    @staticmethod
    def hex_to_rgb(value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        r, g, b = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
        return (r, g, b)

    def set_text_color(self, r: float, g: float=-1, b: float=-1):
        self.fpdf.set_text_color(r, g, b)

    def write_syntax_highlighted(
            self,
            text: str,
            style_name: str,
            language: str
        ):
        lexer = None
        try:
            lexer = get_lexer_by_name(language)
        except ClassNotFound:
            lexer = get_lexer_for_filename(language)

        DEFAULT_COLOR = (0, 0, 0)

        self.fpdf.set_text_color(*DEFAULT_COLOR)

        style = get_style_by_name(style_name)
        for ttype, value in lexer.get_tokens(text):
            s = style.style_for_token(ttype)
            font_style = ""
            if s["bold"]:
                font_style += "B"
            if s["italic"]:
                font_style += "I"
            self.fpdf.set_font(style=font_style)
            if s['color'] != None:
                self.fpdf.set_text_color(*self.hex_to_rgb(s['color']))
            else:
                self.fpdf.set_text_color(*DEFAULT_COLOR)
            self.fpdf.write(txt=value)

        self.fpdf.set_text_color(*DEFAULT_COLOR)

    @contextmanager
    def unbreakable(self):
        prev_page, prev_y = self.fpdf.page, self.fpdf.y
        recorder = FPDFRecorder(self, accept_page_break=False)
        yield recorder
        y_scroll = recorder.fpdf.y - prev_y + (recorder.fpdf.page - prev_page) * self.eph # type: ignore
        if prev_y + y_scroll > self.page_break_trigger or recorder.fpdf.page > prev_page: # type: ignore
            recorder.rewind()
            # pylint: disable=protected-access
            # Performing this call through .pdf so that it does not get recorded & replayed:
            recorder.pdf.fpdf._perform_page_break()
            recorder.replay()

    def perform_page_break_if_need_be(self, h: float) -> bool:
        return self.fpdf._perform_page_break_if_need_be(h)

    def __deepcopy__(self, memo):
        id_self = id(self)
        _copy = memo.get(id_self)
        if _copy is None:
            _copy = type(self)()
            _copy.__dict__ = deepcopy(self.__dict__, memo)
            _copy.fpdf = deepcopy(self.fpdf, memo)
            _copy.fpdf.__dict__ = deepcopy(self.fpdf.__dict__, memo)
            memo[id_self] = _copy
        return _copy
