from .common import log, pasquill_gifford_classes
from .input import Input
from .results import Results
from .reference import Reference
import math


class Model:
    """Doses & dilution factor calculator based on 2 scenario in Руководство
    по безопасности при использовании атомной энергии «Рекомендуемые методы
    оценки и прогнозирования радиационных последствий аварий на объектах
    ядерного топливного цикла (РБ-134-17)"""

    def __init__(self, reference_data_db_name):
        self.__results = Results()
        self.__reference = Reference(reference_data_db_name)
        self.input = Input()

    @property
    def input(self):
        return self.__input

    @input.setter
    def input(self, value):
        self.__input = value

    def reset(self):
        self.results.drop_all()
        self.input = Input()

    def calculate(self):
        if self.__is_ready() is False:
            log("model instance is not ready for calculation")
            return

        for activity in self.input.activities:
            nuclide = activity["nuclide"]
            for atmospheric_class in pasquill_gifford_classes:
                if self.reference.nuclide_group(nuclide) != "IRG":
                    self.__calculate_e_inh(nuclide, atmospheric_class)
                    self.__calculate_e_surface(nuclide, atmospheric_class)
                self.__calculate_e_cloud(nuclide, atmospheric_class)
                self.__calculate_e_total_10(nuclide, atmospheric_class)

        self.__calculate_e_max_10()

    @property
    def results(self):
        return self.__results

    @property
    def reference(self):
        return self.__reference

    def __is_ready(self):
        return (
            self.input.initialized()
            and self.input.consistent()
            and self.__is_input_valid()
        )

    def __is_input_valid(self):
        nuclides = self.reference.all_nuclides()
        for activity in self.input.activities:
            if activity["nuclide"] not in nuclides:
                return False
        return True

    def __calculate_e_max_10(self):
        """РБ-134-17, p. 3, (1)"""

        e_total_10_sums = list()
        e_total_10_table = self.results.load_table("e_total_10")

        for atmospheric_class in pasquill_gifford_classes:
            e_total_10_sum = 0
            for nuclide in e_total_10_table:
                e_total_10_sum += nuclide[atmospheric_class]
            e_total_10_sums.append(e_total_10_sum)

        e_max_10 = max(e_total_10_sums)
        self.results["e_max_10"].insert(dict(e_max_10=e_max_10))

    def __calculate_e_total_10(self, nuclide, atmospheric_class):
        """РБ-134-17, p. 5, (3)"""

        e_total_10 = 0
        if "e_total_10" not in self.results.tables:
            self.results.create_e_total_10_table()

        e_cloud = self.results.load_table("e_cloud").find_one(nuclide=nuclide)[
            atmospheric_class
        ]
        e_total_10 += e_cloud
        if self.reference.nuclide_group(nuclide) != "IRG":
            e_inh = self.results.load_table("e_inh").find_one(nuclide=nuclide)[
                atmospheric_class
            ]
            e_surface = self.results.load_table("e_surface").find_one(
                nuclide=nuclide
            )[atmospheric_class]
            e_total_10 += e_inh + e_surface

        self.results["e_total_10"].upsert(
            {"nuclide": nuclide, atmospheric_class: e_total_10}, ["nuclide"]
        )

    def __calculate_e_cloud(self, nuclide, atmospheric_class):
        """РБ-134-17, p. 7, (5)"""

        dose_coefficicent = self.reference.cloud_dose_coeff(nuclide)

        concentration_integral = self.results.get_concentration_integral(
            nuclide, atmospheric_class
        )

        if "e_cloud" not in self.results.tables:
            self.results.create_e_cloud_table()

        value = dose_coefficicent * concentration_integral
        self.results["e_cloud"].upsert(
            {"nuclide": nuclide, atmospheric_class: value},
            ["nuclide"],
        )

    def __calculate_e_inh(self, nuclide, atmospheric_class):
        """РБ-134-17, p. 9, (8)"""

        respiration_rate = self.reference.respiration_rate(self.input.age)

        concentration_integral = self.results.get_concentration_integral(
            nuclide, atmospheric_class
        )

        dose_coefficicent = self.reference.inhalation_dose_coeff(nuclide)

        if "e_inh" not in self.results.tables:
            self.results.create_e_inh_table()

        value = respiration_rate * dose_coefficicent * concentration_integral
        self.results["e_inh"].upsert(
            {"nuclide": nuclide, atmospheric_class: value}, ["nuclide"]
        )

    def __calculate_e_surface(self, nuclide, atmospheric_class):
        """РБ-134-17, p. 8, (6)"""

        deposition = self.results.get_deposition(nuclide, atmospheric_class)

        dose_coefficicent = self.reference.surface_dose_coeff(nuclide)

        residence_time_coeff = self.__calculate_residence_time_coeff(nuclide)

        if "e_surface" not in self.results.tables:
            self.results.create_e_surface_table()

        value = deposition * dose_coefficicent * residence_time_coeff
        self.results["e_surface"].upsert(
            {"nuclide": nuclide, atmospheric_class: value}, ["nuclide"]
        )

    def __calculate_residence_time_coeff(self, nuclide):
        """РБ-134-17, p. 8, (7)"""

        decay_coeff_sum = (
            self.reference.radio_decay_coeff(nuclide)
            + Reference.dose_rate_decay_coeff()
        )

        return (
            1 - math.exp(-decay_coeff_sum * Reference.residence_time())
        ) / decay_coeff_sum