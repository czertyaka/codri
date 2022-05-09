from ..database import InMemoryDatabase
from .common import pasquill_gifford_classes


class Results(InMemoryDatabase):
    """ORM class for model calculation results"""

    def __init__(self):
        super(Results, self).__init__()

    def create_e_total_10_table(self):
        return self.__create_nuclide_vs_atmospheric_class_empty_table(
            "e_total_10"
        )

    def create_e_cloud_table(self):
        return self.__create_nuclide_vs_atmospheric_class_empty_table(
            "e_cloud"
        )

    def create_e_inh_table(self):
        return self.__create_nuclide_vs_atmospheric_class_empty_table("e_inh")

    def create_e_surface_table(self):
        return self.__create_nuclide_vs_atmospheric_class_empty_table(
            "e_surface"
        )

    def create_concentration_integrals_table(self):
        return self.__create_nuclide_vs_atmospheric_class_empty_table(
            "concentration_integrals"
        )

    def get_concentration_integral(self, nuclide, atmospheric_class):
        return self.__get_nuclide_vs_atmospheric_class_table_item(
            "concentration_integrals", nuclide, atmospheric_class
        )

    def create_deposition_table(self):
        return self.__create_nuclide_vs_atmospheric_class_empty_table(
            "depositions"
        )

    def get_deposition(self, nuclide, atmospheric_class):
        return self.__get_nuclide_vs_atmospheric_class_table_item(
            "depositions", nuclide, atmospheric_class
        )

    def __create_nuclide_vs_atmospheric_class_empty_table(self, name):
        table = self.create_table(
            name,
            primary_id="nuclide",
            primary_type=self.types.string(7),
        )
        for a_class in pasquill_gifford_classes:
            table.create_column(a_class, type=self.types.float, default=0)
        return table

    def __get_nuclide_vs_atmospheric_class_table_item(
        self, table_name, nuclide, atmospheric_class
    ):
        table = self.load_table(table_name)
        return table.find_one(nuclide=nuclide)[atmospheric_class]