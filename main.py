#!/usr/bin/env python
from math import ceil
from fpdf import FPDF, HTMLMixin, HTML2FPDF
from PIL import Image
from enum import Enum
from fpdf.fpdf import TitleStyle, ToCPlaceholder
from fpdf.outline import OutlineSection
from typing import Optional
from markdown import markdown
import click
import sys
from datetime import date
from pydantic.error_wrappers import ValidationError
import toml
from pydantic import BaseModel, Field

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class ReportProject(BaseModel):
    location: str
    program_files: list[str]
    tests: list[list[str]]

class ReportSection(BaseModel):
    title: str

    problem: Optional[str]
    project_location: Optional[str]
    professors_notes: Optional[str]

    def __str__(self) -> str:
        return f"ReportSection[{self.title}]"

class Report(BaseModel):
    title: str

    student_name: str
    student_gender: Gender

    professor_name: str
    professor_gender: Gender

    sections: list[ReportSection] = Field(default_factory=list)

    university_name: str = Field(default="Kauno technologijos universitetas")
    faculty_name: str = Field(default="Informatikos fakultetas")
    sub_title: str = Field(default="Laboratorinių darbų ataskaita")
    city_name: str = Field(default="Kaunas")
    year: int = Field(default=date.today().year)

    def __str__(self) -> str:
        return f"Report[{self.student_name}, {self.title}]"

class PDFReportStyle(BaseModel):
    toc_max_level: int = 2

COLOR_DICT = {
    "black": "#000000",
    "navy": "#000080",
    "darkblue": "#00008b",
    "mediumblue": "#0000cd",
    "blue": "#0000ff",
    "darkgreen": "#006400",
    "green": "#008000",
    "teal": "#008080",
    "darkcyan": "#008b8b",
    "deepskyblue": "#00bfff",
    "darkturquoise": "#00ced1",
    "mediumspringgreen": "#00fa9a",
    "lime": "#00ff00",
    "springgreen": "#00ff7f",
    "aqua": "#00ffff",
    "cyan": "#00ffff",
    "midnightblue": "#191970",
    "dodgerblue": "#1e90ff",
    "lightseagreen": "#20b2aa",
    "forestgreen": "#228b22",
    "seagreen": "#2e8b57",
    "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f",
    "limegreen": "#32cd32",
    "mediumseagreen": "#3cb371",
    "turquoise": "#40e0d0",
    "royalblue": "#4169e1",
    "steelblue": "#4682b4",
    "darkslateblue": "#483d8b",
    "mediumturquoise": "#48d1cc",
    "indigo": "#4b0082",
    "darkolivegreen": "#556b2f",
    "cadetblue": "#5f9ea0",
    "cornflowerblue": "#6495ed",
    "rebeccapurple": "#663399",
    "mediumaquamarine": "#66cdaa",
    "dimgray": "#696969",
    "dimgrey": "#696969",
    "slateblue": "#6a5acd",
    "olivedrab": "#6b8e23",
    "slategray": "#708090",
    "slategrey": "#708090",
    "lightslategray": "#778899",
    "lightslategrey": "#778899",
    "mediumslateblue": "#7b68ee",
    "lawngreen": "#7cfc00",
    "chartreuse": "#7fff00",
    "aquamarine": "#7fffd4",
    "maroon": "#800000",
    "purple": "#800080",
    "olive": "#808000",
    "gray": "#808080",
    "grey": "#808080",
    "skyblue": "#87ceeb",
    "lightskyblue": "#87cefa",
    "blueviolet": "#8a2be2",
    "darkred": "#8b0000",
    "darkmagenta": "#8b008b",
    "saddlebrown": "#8b4513",
    "darkseagreen": "#8fbc8f",
    "lightgreen": "#90ee90",
    "mediumpurple": "#9370db",
    "darkviolet": "#9400d3",
    "palegreen": "#98fb98",
    "darkorchid": "#9932cc",
    "yellowgreen": "#9acd32",
    "sienna": "#a0522d",
    "brown": "#a52a2a",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "lightblue": "#add8e6",
    "greenyellow": "#adff2f",
    "paleturquoise": "#afeeee",
    "lightsteelblue": "#b0c4de",
    "powderblue": "#b0e0e6",
    "firebrick": "#b22222",
    "darkgoldenrod": "#b8860b",
    "mediumorchid": "#ba55d3",
    "rosybrown": "#bc8f8f",
    "darkkhaki": "#bdb76b",
    "silver": "#c0c0c0",
    "mediumvioletred": "#c71585",
    "indianred": "#cd5c5c",
    "peru": "#cd853f",
    "chocolate": "#d2691e",
    "tan": "#d2b48c",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "thistle": "#d8bfd8",
    "orchid": "#da70d6",
    "goldenrod": "#daa520",
    "palevioletred": "#db7093",
    "crimson": "#dc143c",
    "gainsboro": "#dcdcdc",
    "plum": "#dda0dd",
    "burlywood": "#deb887",
    "lightcyan": "#e0ffff",
    "lavender": "#e6e6fa",
    "darksalmon": "#e9967a",
    "violet": "#ee82ee",
    "palegoldenrod": "#eee8aa",
    "lightcoral": "#f08080",
    "khaki": "#f0e68c",
    "aliceblue": "#f0f8ff",
    "honeydew": "#f0fff0",
    "azure": "#f0ffff",
    "sandybrown": "#f4a460",
    "wheat": "#f5deb3",
    "beige": "#f5f5dc",
    "whitesmoke": "#f5f5f5",
    "mintcream": "#f5fffa",
    "ghostwhite": "#f8f8ff",
    "salmon": "#fa8072",
    "antiquewhite": "#faebd7",
    "linen": "#faf0e6",
    "lightgoldenrodyellow": "#fafad2",
    "oldlace": "#fdf5e6",
    "red": "#ff0000",
    "fuchsia": "#ff00ff",
    "magenta": "#ff00ff",
    "deeppink": "#ff1493",
    "orangered": "#ff4500",
    "tomato": "#ff6347",
    "hotpink": "#ff69b4",
    "coral": "#ff7f50",
    "darkorange": "#ff8c00",
    "lightsalmon": "#ffa07a",
    "orange": "#ffa500",
    "lightpink": "#ffb6c1",
    "pink": "#ffc0cb",
    "gold": "#ffd700",
    "peachpuff": "#ffdab9",
    "navajowhite": "#ffdead",
    "moccasin": "#ffe4b5",
    "bisque": "#ffe4c4",
    "mistyrose": "#ffe4e1",
    "blanchedalmond": "#ffebcd",
    "papayawhip": "#ffefd5",
    "lavenderblush": "#fff0f5",
    "seashell": "#fff5ee",
    "cornsilk": "#fff8dc",
    "lemonchiffon": "#fffacd",
    "floralwhite": "#fffaf0",
    "snow": "#fffafa",
    "yellow": "#ffff00",
    "lightyellow": "#ffffe0",
    "ivory": "#fffff0",
    "white": "#ffffff",
}

def px2mm(px):
    return int(px) * 25.4 / 72

def color_as_decimal(color="#000000"):
    if not color:
        return None

    # Checks if color is a name and gets the hex value
    hexcolor = COLOR_DICT.get(color.lower(), color)

    if len(hexcolor) == 4:
        r = int(hexcolor[1] * 2, 16)
        g = int(hexcolor[2] * 2, 16)
        b = int(hexcolor[3] * 2, 16)
        return r, g, b

    r = int(hexcolor[1:3], 16)
    g = int(hexcolor[3:5], 16)
    b = int(hexcolor[5:7], 16)
    return r, g, b

class MyHTML2FPDF(HTML2FPDF):
    def __init__(self, *vargs, **kvargs):
        super().__init__(*vargs, **kvargs)
        self.ul_bullet_char = '●'

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("b", "i", "u"):
            self.set_style(tag, True)
        if tag == "a":
            self.href = attrs["href"]
        if tag == "br":
            self.pdf.ln(self.h)
        if tag == "p":
            self.pdf.ln(self.h)
            if attrs:
                self.align = attrs.get("align")
        if tag in self.heading_sizes:
            self.font_stack.append((self.font_face, self.font_size, self.font_color))
            self.heading_level = int(tag[1:])
            hsize = self.heading_sizes[tag]
            self.pdf.set_text_color(150, 0, 0)
            self.set_font(size=hsize)
            self.pdf.ln(self.h)
            if attrs:
                self.align = attrs.get("align")
        if tag == "hr":
            self.pdf.add_page(same=True)
        if tag == "pre":
            self.font_stack.append((self.font_face, self.font_size, self.font_color))
            self.set_font("courier", 11)
        if tag == "blockquote":
            self.pdf.set_text_color(100, 0, 45)
            self.indent += 1
            self.pdf.ln(3)
        if tag == "ul":
            self.indent += 1
            self.bullet.append(self.ul_bullet_char)
        if tag == "ol":
            self.indent += 1
            self.bullet.append(0)
        if tag == "li":
            self.pdf.ln(self.h + 0.2)
            self.pdf.set_text_color(190, 0, 0)
            bullet = self.bullet[self.indent - 1]
            if not isinstance(bullet, str):
                bullet += 1
                self.bullet[self.indent - 1] = bullet
                bullet = f"{bullet}. "
            self.set_text_color(*self.font_color)
            self.pdf.write(self.h, f"{' ' * self.li_tag_indent * self.indent}{bullet} ")
        if tag == "font":
            # save previous font state:
            self.font_stack.append((self.font_face, self.font_size, self.font_color))
            if "color" in attrs:
                color = color_as_decimal(attrs["color"])
                self.font_color = color
            if "face" in attrs:
                face = attrs.get("face").lower()
                try:
                    self.pdf.set_font(face)
                    self.font_face = face
                except RuntimeError:
                    pass  # font not found, ignore
            if "size" in attrs:
                self.font_size = int(attrs.get("size"))
            self.set_font()
            self.set_text_color(*self.font_color)
        if tag == "table":
            self.table = {k.lower(): v for k, v in attrs.items()}
            if "width" not in self.table:
                self.table["width"] = "100%"
            if self.table["width"][-1] == "%":
                w = self.pdf.w - self.pdf.r_margin - self.pdf.l_margin
                w *= int(self.table["width"][:-1]) / 100
                self.table_offset = (self.pdf.w - w) / 2
            self.table_col_width = []
            self.theader_out = self.tfooter_out = False
            self.theader = []
            self.tfooter = []
            self.thead = None
            self.tfoot = None
            self.pdf.ln()
        if tag == "tr":
            self.tr_index = 0 if self.tr_index is None else (self.tr_index + 1)
            self.tr = {k.lower(): v for k, v in attrs.items()}
            self.table_col_index = 0
            self.table_row_height = 0
            self.pdf.set_x(self.table_offset)
            # Adding an horizontal line separator between rows:
            if self.table_line_separators and self.tr_index > 0:
                self.output_table_sep()
        if tag == "td":
            self.td = {k.lower(): v for k, v in attrs.items()}
            if "width" in self.td and self.table_col_index >= len(self.table_col_width):
                assert self.table_col_index == len(
                    self.table_col_width
                ), f"table_col_index={self.table_col_index} #table_col_width={len(self.table_col_width)}"
                self.table_col_width.append(self.td["width"])
            if attrs:
                self.align = attrs.get("align")
            self._only_imgs_in_td = False
        if tag == "th":
            self.td = {k.lower(): v for k, v in attrs.items()}
            self.th = True
            if "width" in self.td and self.table_col_index >= len(self.table_col_width):
                assert self.table_col_index == len(
                    self.table_col_width
                ), f"table_col_index={self.table_col_index} #table_col_width={len(self.table_col_width)}"
                self.table_col_width.append(self.td["width"])
        if tag == "thead":
            self.thead = {}
        if tag == "tfoot":
            self.tfoot = {}
        if tag == "img" and "src" in attrs:
            width = px2mm(attrs.get("width", 0))
            height = px2mm(attrs.get("height", 0))
            if self.pdf.y + height > self.pdf.page_break_trigger:
                self.pdf.add_page(same=True)
            y = self.pdf.get_y()
            if self.table_col_index is not None:
                self._only_imgs_in_td = True
                # <img> in a <td>: its width must not exceed the cell width:
                td_width = self._td_width()
                if not width or width > td_width:
                    if width:  # Preserving image aspect ratio:
                        height *= td_width / width
                    width = td_width
                x = self._td_x()
                if self.align and self.align[0].upper() == "C":
                    x += (td_width - width) / 2
            else:
                x = self.pdf.get_x()
                if self.align and self.align[0].upper() == "C":
                    x = self.pdf.w / 2 - width / 2
            LOGGER.debug(
                'image "%s" x=%d y=%d width=%d height=%d',
                attrs["src"],
                x,
                y,
                width,
                height,
            )
            self.pdf.image(
                self.image_map(attrs["src"]), x, y, width, height, link=self.href
            )
            self.pdf.set_x(x + width)
            if self.table_col_index is not None:
                # <img> in a <td>: we grow the cell height according to the image height:
                if height > self.table_row_height:
                    self.table_row_height = height
            else:
                self.pdf.set_y(y + height)
        if tag in ("b", "i", "u"):
            self.set_style(tag, True)
        if tag == "center":
            self.align = "Center"
        if tag == "toc":
            self.pdf.insert_toc_placeholder(
                self.render_toc, pages=int(attrs.get("pages", 1))
            )

    def set_font(self, face=None, size=None):
        if face:
            self.font_face = face
        if size:
            self.font_size = size
            self.h = size / 72 * 2.54
        style = "".join(s for s in ("b", "i", "u") if self.style.get(s)).upper()
        if (self.font_face, style) != (self.pdf.font_family, self.pdf.font_style):
            self.pdf.set_font(self.font_face, style, self.font_size)
        if self.font_size != self.pdf.font_size:
            self.pdf.set_font_size(self.font_size)

class MyHTMLMixin(HTMLMixin):
    HTML2FPDF_CLASS = MyHTML2FPDF

class PDFReport(FPDF, MyHTMLMixin):
    report: Report
    style: PDFReportStyle
    university_icon = "university-icon.png"
    line_spacing: float = 1.15

    toc_section_spacing_above = 0.21
    toc_section_spacing_below = 0.35

    def __init__(self, report: Report, style: PDFReportStyle = PDFReportStyle()) -> None:
        super().__init__("portrait", "cm", "A4")
        self.report = report
        self.style = style

        self.add_font("times-new-roman", "", "fonts/times-new-roman.ttf", True)
        self.add_font("times-new-roman", "B", "fonts/times-new-roman-bold.ttf", True)
        self.add_font("arial", "", "fonts/arial.ttf", True)
        self.add_font("arial", "B", "fonts/arial-bold.ttf", True)

        self.set_margins(2.5, 1, 1)
        self.set_auto_page_break(True, 1.5)

        self.set_section_title_styles(
            level0 = TitleStyle("arial", "B", 14, l_margin=self.l_margin+2.25-0.75, t_margin=0, b_margin=0.35),
            level1 = TitleStyle("arial", "B", 12, l_margin=self.l_margin+4-1, t_margin=0.35, b_margin=0.35),
            level2 = TitleStyle("arial", "B", 12, l_margin=self.l_margin+5.75-1.25, t_margin=0.35, b_margin=0.35),
        )

        self.add_title_page()
        self.add_toc_page()
        for i in range(len(report.sections)):
            self.add_section(i)

    def add_title_page(self) -> None:
        self.add_page()

        # Top part
        self.set_y(self.t_margin + 0.5 + 12/self.k)
        self.center_image(self.university_icon, 1.78, 2.04)

        self.set_font("times-new-roman", "B", 12)
        self.cell(0, self.font_size*1.5, txt=self.report.university_name, align="C", ln=True)

        self.set_font("times-new-roman", "", 12)
        self.cell(0, txt=self.report.faculty_name, align="C", ln=True)

        # Middle part (title)
        self.ln(self.font_size*15)

        self.set_font("times-new-roman", "B", 18)
        self.cell(0, txt=self.report.title, align="C", ln=True)
        
        self.set_font("times-new-roman", "", 14)
        self.cell(0, txt=self.report.sub_title, align="C", ln=True)

        # Student name and professort name section
        self.ln(self.font_size*4)

        w = self.get_page_width()

        y = self.get_y()
        self.set_draw_color(212, 175, 55)
        self.line(w/2, y, w-self.r_margin, y)
        self.ln(self.font_size*2)

        self.set_font("times-new-roman", "B", 12)
        self.cell(x=w/2, w=w/2, txt=self.report.student_name, align="L", ln=True)
        self.ln(self.font_size)

        self.set_font("times-new-roman", "", 12)
        if self.report.student_gender == Gender.MALE:
            self.cell(x=w/2, w=w/2, txt="Studentas", align="L", ln=True)
        else:
            self.cell(x=w/2, w=w/2, txt="Studentė", align="L", ln=True)

        self.ln(self.font_size*3)

        self.set_font("times-new-roman", "B", 12)
        self.cell(x=w/2, w=w/2, txt=self.report.professor_name, align="L", ln=True)
        self.ln(self.font_size)

        self.set_font("times-new-roman", "", 12)
        if self.report.professor_gender == Gender.MALE:
            self.cell(x=w/2, w=w/2, txt="Dėstytojas", align="L", ln=True)
        else:
            self.cell(x=w/2, w=w/2, txt="Dėstytoja", align="L", ln=True)
        self.ln(self.font_size)

        y = self.get_y() + self.font_size
        self.set_draw_color(212, 175, 55)
        self.line(w/2, y, w-self.r_margin, y)
        self.ln(self.font_size * self.line_spacing + 3.5)

        # Footer
        self.set_font("times-new-roman", "B", 12)
        self.set_y(-self.font_size*2-self.b_margin)
        self.cell(0, txt=f"{self.report.city_name} {self.report.year}", align="C")

    def add_section(self, index: int) -> None:
        section = self.report.sections[index]
        self.add_page()

        index += 1
        self.start_section(f"{index}. {section.title}")
        if section.problem:
            self.set_font("times-new-roman", "", 12)
            html = markdown(section.problem)
            html = "<font color='#000000' face='times-new-roman' size=12>" + html + "</font>"
            self.write_html(text=html)
            self.ln()
        self.start_section(f"{index}.1. Darbo užduotis", 1)
        self.start_section(f"{index}.2. Programos tekstas", 1)
        self.start_section(f"{index}.3. Pradiniai duomenys ir rezultatai", 1)
        if section.project_location:
            self.start_section(f"{index}.3.1. 1 Testas", 2)
            self.start_section(f"{index}.3.2. 2 Testas", 2)
        self.start_section(f"{index}.4. Dėstytojo pastabos", 1)

    def add_toc_page(self):
        toc_height = self.get_effective_toc_height(self.report.sections)
        # Adjust for title that is at the top of the page
        eph = self.eph - (0.5 + 12/self.k)
        toc_height += 12/self.k

        pages = max(1, ceil(toc_height / eph))
        self.insert_toc_placeholder(self.render_toc, pages)

        # Adjust starting page, because it's a bug
        # When the function creates a new placeholder page, it should start with
        # it, not the one before it.
        placeholder = self._toc_placeholder
        self._toc_placeholder = ToCPlaceholder(
            placeholder.render_function, placeholder.start_page+1, placeholder.y, placeholder.pages
        )

    # TODO: render_toc could use some refactoring
    def render_toc(self, pdf: FPDF, outline: list[OutlineSection]) -> None:
        page_top_y = pdf.t_margin + 0.5 + 12/pdf.k
        pdf.set_y(page_top_y)
        pdf.set_font("times-new-roman", "", 12)
        pdf.cell(0, txt="TURINYS", align="C", ln=True)
        pdf.ln()

        y = pdf.get_y()
        for i in range(len(outline)):
            outlineSection = outline[i]
            level = int(outlineSection.level)

            # Only render up to the specified number of levels levels
            if level > self.style.toc_max_level: continue

            # Update font
            y += self.toc_section_spacing_above
            if level == 0:
                pdf.set_font("times-new-roman", "B", 14)
            else:
                pdf.set_font("times-new-roman", "", 12)

            x = pdf.l_margin

            # Indent outline section
            if level > 0:
                x = x+1

            # Do a manual page break
            # TODO: find a better solution for this
            if y + pdf.font_size > pdf.page_break_trigger:
                pdf.page += 1
                y = page_top_y

            self.render_toc_section(pdf, x, y, outlineSection)

            y += pdf.font_size
            y += self.toc_section_spacing_below

    def render_toc_section(self, pdf: FPDF, x: float, y: float, outlineSection: OutlineSection):
        pdf.text(x, y, f"{outlineSection.name} (page {outlineSection.page_number})")

    # Used for determining how many pages should be inserted in placeholder
    def get_effective_toc_height(self, sections: list[ReportSection]) -> float:
        section_text_height = 14/self.k
        subsection_text_height = 12/self.k
        margins = self.toc_section_spacing_above + self.toc_section_spacing_below
        height = 0

        for section in sections:
            height += section_text_height + margins
            height += 4 * (subsection_text_height + margins)

            # If each test will be shown in toc, it will need more space
            if section.project_location and self.style.toc_max_level > 1:
                height += 2 * (subsection_text_height + margins)

        return height

    def add_page_number(self) -> None:
        self.set_font("times-new-roman", "", 12)
        self.set_y(-self.font_size*2-self.b_margin)
        self.cell(0, txt=str(self.page_no()), align="R")

    def footer(self) -> None:
        if self.page_no() > 1:
            self.add_page_number()

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

@click.command()
@click.argument("input", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.argument("output", type=click.Path(writable=True, dir_okay=False))
def main(input: str, output: str):
    report = None
    try:
        parsed_toml = toml.load(input)
        report = Report(**parsed_toml)
    except ValidationError as e:
        click.echo(click.style(f"Validation error from input file ({input}):", fg="red"))
        click.echo(click.style(e, fg="red"))
        sys.exit(1)
    except toml.TomlDecodeError as e:
        click.echo(click.style(f"Failed to decode input file ({input}):", fg="red"))
        click.echo(click.style(e, fg="red"))
        sys.exit(1)

    pdf = PDFReport(report)
    pdf.output(output)

if __name__ == "__main__":
    main()

