from posixpath import relpath
from ..utils import list_files
from ..report import Report
from . import SectionGenerator
from ..pdf import PDF
from bs4 import BeautifulSoup

class UpdatedInterfacePropertiesSection(SectionGenerator):
    table_label: str = "{filename}:"

    def __init__(
            self,
            field: str,
            included_files: list[str],
            excluded_files: list[str] = []
        ):
        super().__init__()
        self.field = field
        self.included_files = included_files
        self.excluded_files = excluded_files

    def generate(self, pdf: PDF, section: dict, report: Report):
        project_path = section[self.field]
        all_properties = {}
        for filename in list_files(project_path, self.included_files, self.excluded_files):
            relative_path = relpath(filename, project_path)
            all_properties[relative_path] = UpdatedInterfacePropertiesSection.get_updated_properties(filename)

        # If there is only 1 .aspx file, you don't need to specify a label
        if len(all_properties) <= 1:
            properties = list(all_properties.values())[0]
            pdf.newline()
            self.render_properties_table(pdf, properties)
        else:
            for filename, properties in all_properties.items():
                pdf.set_font("times-new-roman", 12)
                with pdf.labeled_block(self.table_label.format(filename=filename)):
                    self.render_properties_table(pdf, properties)

    def render_properties_table(self, pdf: PDF, all_properties: dict):
        pdf.set_font("times-new-roman", 12)
        line_height = pdf.font_size * 1.8
        col_width = pdf.epw / 3

        pdf.set_font("times-new-roman", 12, bold=True)
        pdf.set_draw_color((0, 0, 0))
        for header in ("Komponentas", "Savybė", "Reikšmė"):
            pdf.write(header, col_width, line_height, align="C", multiline=True, border=1, newlines=3, max_line_height=pdf.font_size)
        pdf.newline(line_height)

        pdf.set_font("times-new-roman", 12, bold=False)
        for element_name, properties in all_properties.items():
            pdf.write(element_name, col_width, line_height*len(properties), multiline=True, border=1, newlines=3, max_line_height=pdf.font_size)
            x = pdf.get_x()
            for key, value in properties.items():
                pdf.set_cursor(x)
                pdf.write(key, col_width, line_height, multiline=True, border=1, newlines=3, max_line_height=pdf.font_size)
                pdf.write(value, col_width, line_height, multiline=True, border=1, newlines=3, max_line_height=pdf.font_size)
                pdf.newline(line_height)

        pdf.newline()

    @staticmethod
    def get_updated_properties(filename: str) -> dict[str, dict]:
        contents = None
        with open(filename, "r", encoding="utf-8-sig") as f:
            # Skip first line of .aspx file that is full of C#
            # designer related stuff
            f.readline()
            contents = f.read()
        soup = BeautifulSoup(contents, features="xml")

        updated_properties = {}
        for widget in soup.find_all(ID=True, recursive=True):
            if len(widget.attrs) > 2:
                id = widget.attrs["ID"]
                del widget.attrs["ID"]
                del widget.attrs["runat"]
                updated_properties[id] = widget.attrs

        return updated_properties

    def has_required_fields(self, section: dict, report: Report) -> bool:
        return self.field in section

    def assert_fields(self, section: dict, _: Report):
        assert type(section.get(self.field)) == str, f"Expected field '{self.field}' in section to be str"
