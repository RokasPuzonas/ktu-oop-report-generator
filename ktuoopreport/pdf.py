"""
    Copyright (C) 2021 - Rokas Puzonas <rokas.puz@gmail.com>

    This file is part of KTU OOP Report Generator.

    KTU OOP Report Generator is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    KTU OOP Report Generator is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with KTU OOP Report Generator. If not, see <https://www.gnu.org/licenses/>.
"""

from contextlib import contextmanager
from copy import deepcopy
from pygments.token import Token
from PIL import Image
from fpdf import FPDF
from pygments.styles import get_style_by_name
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from typing import Iterator, Union, Optional

class PDF(FPDF):
    line_spacing: float = 1.15
    current_color: tuple[int, int, int]

    numbering_index: int = 0
    numbering_font_family: str
    numbering_font_style: str
    numbering_font_size: int

    section_levels: list[int]

    def __init__(self, *vargs, **kvargs):
        super().__init__(*vargs, **kvargs)
        self.section_levels = [1]

    def image(
        self,
        name,
        x=None,
        y=None,
        w=0,
        h=0,
        type="",
        link="",
        title=None,
        alt_text=None,
        centered:bool=False,
        numbered:Union[str, bool]=False
    ):
        if centered:
            if w == 0:
                name = Image.open(name)
                w = name.size[0]
            x = self.l_margin + (self.get_page_width() - self.l_margin - self.r_margin - w)/2

        s = super()
        if not numbered:
            return s.image(name, x, y, w, h, type, link, title, alt_text)

        number_label = ""
        self.numbering_index += 1
        if isinstance(numbered, str):
            number_label = numbered.format(index=self.numbering_index)
        else:
            number_label = f"{self.numbering_index}."
        self.set_font(self.numbering_font_family, self.numbering_font_style, self.numbering_font_size)

        # TODO: REFACTOR THIS GARBAGE!!!
        def render():
            info = s.image(name, x, y, w, h, type, link, title, alt_text)
            self.set_x(self.get_x() + 1.27)
            self.cell(txt=number_label, ln=True)
            return info
        return self.unbreakable(render)

    def push_section(self, label: Optional[str] = None, *args, **kvargs):
        self.section_levels.append(1)
        if label:
            level = "".join(str(lvl)+"." for lvl in self.section_levels[:-1])
            label = label.format(level = level, *args, **kvargs)
        super().start_section(label or "", len(self.section_levels)-2)
    
    def pop_section(self):
        self.section_levels.pop()
        self.section_levels[-1] += 1

    @contextmanager
    def section_block(self, label: Optional[str] = None, *args, **kvargs):
        self.push_section(label, *args, **kvargs)
        yield
        self.pop_section()

    # TODO: REFACTOR THIS GARBAGE!!!
    # TODO: replace with contextmanager, when I figure out how to record append
    # replay function calls.
    def unbreakable(self, func, *vargs, **kvargs):
        """
        Ensures that all rendering performed in this context appear on a single page
        by performing page break beforehand if need be.

        Notes
        -----

        Using this method means to duplicate the FPDF `bytearray` buffer:
        when generating large PDFs, doubling memory usage may be troublesome.
        """
        initial = deepcopy(self.__dict__)
        prev_page, prev_y = self.page, self.y
        result = func(*vargs, **kvargs)
        y_scroll = self.y - prev_y + (self.page - prev_page) * self.eph
        if prev_y + y_scroll > self.page_break_trigger or self.page > prev_page:
            self.__dict__ = initial
            self._perform_page_break()
            result = func(*vargs, **kvargs)
        return result

    # TODO: Create a more feature complete markdown writer
    # TODO: Feature: Only double \n\n create a \n
    def write_basic_markdown(self, text: str):
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
            if ttype == Token.Keyword and value == "*" and prev_value == "\n":
                paragraph.append("\n•")
            elif value == "\n" and prev_value == "\n":
                paragraph.append("\n")
            elif value != '\n':
                paragraph.append(value)
            prev_value = value

        self.multi_cell(0, txt="".join(paragraph))
        # # Altenative that supports bolding and italics
        # # but can't do justify align.
        # for ttype, value in self.markdown_lexer.get_tokens(text):
        #     if ttype == Token.Keyword and value == "*":
        #         self.write(txt="•")
        #         self.x = self.x + self.get_string_width("•")
        #         continue
        #     elif ttype == Token.Generic.Emph:
        #         old_style = self.font_style
        #         self.set_font(style="I")
        #         self.write(txt=value[1:-1])
        #         self.set_font(style=old_style)
        #         continue
        #     elif ttype == Token.Generic.Strong:
        #         old_style = self.font_style
        #         self.set_font(style="B")
        #         self.write(txt=value[2:-2])
        #         self.set_font(style=old_style)
        #         continue
        #     self.write(txt=value)

    @staticmethod
    def hex_to_rgb(value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        r, g, b = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
        return (r, g, b)

    def write(
            self,
            h: str = None,
            txt: str = None,
            link: str = None,
            language: Optional[str] = None,
            style_name: Optional[str] = None
        ):
        if not (language and style_name):
            super().write(h, txt, link)
            return

        lexer = None
        try:
            lexer = get_lexer_by_name(language)
        except ClassNotFound:
            super().write(h, txt, link)
            return

        DEFAULT_COLOR = (0, 0, 0)
        
        self.set_text_color(*DEFAULT_COLOR)
        if not txt: return

        style = get_style_by_name(style_name)
        for ttype, value in lexer.get_tokens(txt):
            s = style.style_for_token(ttype)
            font_style = ""
            if s["bold"]:
                font_style += "B"
            if s["italic"]:
                font_style += "I"
            self.set_font(style=font_style)
            if s['color'] != None:
                self.set_text_color(*self.hex_to_rgb(s['color']))
            else:
                self.set_text_color(*DEFAULT_COLOR)
            self.write(txt=value)

        self.set_text_color(*DEFAULT_COLOR)

    def get_page_width(self) -> float:
        return self.dw_pt/self.k

    def get_page_height(self) -> float:
        return self.dh_pt/self.k

    def get_page_size(self) -> tuple[float, float]:
        return self.get_page_width(), self.get_page_height()

    def set_line_spacing(self, line_spacing: float) -> None:
        self.line_spacing = line_spacing

    def get_line_spacing(self) -> float:
        return self.line_spacing

    def cell(self, w:float=None, h:float=None, *args, x:float=None, y:float=None,  **kwargs) -> None:
        if h is None:
            h = self.font_size * self.line_spacing

        if x and y:
            self.set_xy(x, y)
        elif x:
            self.set_x(x)
        elif y:
            self.set_y(y)

        super().cell(w, h, *args, **kwargs)

