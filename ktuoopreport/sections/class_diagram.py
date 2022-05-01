from ..utils import list_files
from classdiagramgen import extract_namespaces, merge_similar_namespaces, render_namespaces
from ..report import Report
from . import SectionGenerator
from ..pdf import PDF


class ClassDiagramSection(SectionGenerator):
    diagram_font_file: str = "fonts/arial.ttf"
    diagram_font_size: int = 32
    merge_same_diagrams: bool = False
    numbering_label: str = "{index} pav. \"{title}\" klasių diagrama"

    def __init__(self,
            field: str,
            included_files: list[str],
            excluded_files: list[str]=[],
        ) -> None:
        super().__init__()
        self.field = field
        self.included_files = included_files
        self.excluded_files = excluded_files

    def generate(self, pdf: PDF, section: dict, report: Report):
        diagrams = []
        for filename in list_files(section["project"], self.included_files, self.excluded_files):
            for diagram in extract_namespaces(filename):
                diagrams.append(diagram)

        if self.merge_same_diagrams:
            merge_similar_namespaces(diagrams)

        rendered_diagrams = render_namespaces(diagrams, self.diagram_font_file, self.diagram_font_size)
        with pdf.unbreakable() as pdf: # type: ignore
            pdf.newline()
            pdf.image(rendered_diagrams, w=pdf.epw)
            pdf.add_numbering(self.numbering_label.format(index="{index}", title=section["title"]))
            pdf.newline()

    def has_required_fields(self, section: dict, report: Report) -> bool:
        return self.field in section

    def assert_fields(self, section: dict, report: Report):
        assert type(section.get(self.field)) == str, f"Expected field '{self.field}' in section to be str"
