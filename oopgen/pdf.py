from pygments.lexers.markup import MarkdownLexer
from pygments.lexers.dotnet import CSharpLexer
from pygments.token import Token
from PIL import Image
from fpdf import FPDF

class PDF(FPDF):
    markdown_lexer: MarkdownLexer
    csharp_lexer: CSharpLexer

    def __init__(self, *vargs, **kvargs):
        super().__init__(*vargs, **kvargs)
        self.markdown_lexer = MarkdownLexer()
        self.csharp_lexer = CSharpLexer()

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
        paragraph: list[str] = []
        for ttype, value in self.markdown_lexer.get_tokens(text):
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

    def write_csharp(self, text: str):
        for ttype, value in self.csharp_lexer.get_tokens(text):
            pass

    def render_text_sections(self, text_sections: list[TextSection]):
        pass

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

