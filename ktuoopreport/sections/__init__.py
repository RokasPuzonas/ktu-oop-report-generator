from abc import abstractmethod, ABC

from ktuoopreport.report import Report

from ..pdf import PDF

# TODO: Create themes for storing collections of theme font names and sizes

class SectionGenerator(ABC):

    @abstractmethod
    def generate(self, pdf: PDF, section: dict, report: Report):
        pass

    @abstractmethod
    def assert_fields(self, section: dict, report: Report):
        pass

    def has_required_fields(self, section: dict, report: Report) -> bool:
        return False
