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

    def write_markdown(self, text: str):
        text_sections: list[str] = []

        for ttype, value in self.markdown_lexer.get_tokens(text):
            if ttype == Token.Text:
                text_sections.append(value)
            elif ttype == Token.Keyword:
                if value == "*":
                    text_sections.append('•')
                else:
                    text_sections.append(value)

        self.multi_cell(0, txt="".join(text_sections))

    def write_csharp(self, text: str):
        for ttype, value in self.csharp_lexer.get_tokens(text):
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

