from ..report import Report
from . import SectionGenerator
from ..pdf import PDF

class MarkdownSection(SectionGenerator):
    def __init__(self, field: str):
        super().__init__()
        self.field = field

    def generate(self, pdf: PDF, section: dict, report: Report):
        pdf.set_font("times-new-roman", 12)
        pdf.write_markdown(section[self.field])
        pdf.newline()

    def has_required_fields(self, section: dict, report: Report) -> bool:
        return self.field in section

    def assert_fields(self, section: dict, _: Report):
        assert type(section.get(self.field)) == str, f"Expected field '{self.field}' in section to be str"
