import constants
from mode import Mode


class Owner:
    _next_id = 0

    def __init__(self, number_of_indexers: int, number_of_producers: int, name=None) -> None:
        self.name = name
        self.number_of_indexers = number_of_indexers
        self.number_of_producers = number_of_producers
        self.identifier = Owner._next_id
        Owner._next_id += 1

    def __str__(self):
        to_print = f"Owner #{self.identifier} "
        if self.name is not None:
            to_print += f"{self.name} "
        to_print += f" has {self.number_of_indexers} indexers and {self.number_of_producers} producers"
        return to_print

def set_farmers_insurance_owners() -> list[Owner]:
    base_indexers = constants.I
    base_producers = constants.S
    
    farmer = Owner(
        name="farmer",
        number_of_indexers=int(constants.FARMERS_RATIO * base_indexers),
        number_of_producers=int(constants.FARMERS_RATIO * base_producers),
    )
    insurance = Owner(
        name="insurance",
        number_of_indexers=int(constants.INSURANCE_RATIO * base_indexers),
        number_of_producers=int(constants.INSURANCE_RATIO * base_producers),
    )

    owners = [farmer, insurance]

    if constants.MODE == Mode.ZONIA and constants.OTHER_RATIO > 0.0:
        others = Owner(
            name="others",
            number_of_indexers=int(constants.OTHER_RATIO * base_indexers),
            number_of_producers=int(constants.OTHER_RATIO * base_producers),
        )
        owners.append(others)

    return owners
