from pygments.token import Token
from PIL import Image
from fpdf import FPDF
from pygments.styles import get_style_by_name
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

class PDF(FPDF):
    line_spacing: float = 1.15
    current_color: tuple[int, int, int]

    def __init__(self, *vargs, **kvargs):
        super().__init__(*vargs, **kvargs)

    def center_image(self, filename: str, w: float = 0, h: float = 0) -> None:
        if w == 0:
            im = Image.open(filename)
            w = im.size[0]

        self.image(
            filename,
            w = w,
            h = h,
            x = self.l_margin + (self.get_page_width() - self.l_margin - self.r_margin - w)/2
        )

    # TODO: Create a more feature complete markdown writer
    def write_basic_markdown(self, text: str):
        lexer = get_lexer_by_name("markdown")

        paragraph: list[str] = []
        for ttype, value in lexer.get_tokens(text):
            if ttype == Token.Keyword and value == "*":
                paragraph.append("•")
                continue
            paragraph.append(value)
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
    def hex_to_rgb(value: str):
        r = int(value[1:3], 16)
        g = int(value[3:5], 16)
        b = int(value[5:7], 16)
        return r, g, b

    def write(self, h: str = None, txt: str = None, link: str = None, syntax_highlighting: tuple[str, str] = None):
        if not syntax_highlighting:
            super().write(h, txt, link)
            return

        language, style_name = syntax_highlighting
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

