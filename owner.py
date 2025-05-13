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


# Base resources (excluding "others")
base_indexers = constants.I / (1 + constants.OTHER_RATIO)
base_producers = constants.S / (1 + constants.OTHER_RATIO)

# Allocate to main owners (whose ratios sum to 1)
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

if constants.MODE == Mode.ZONIA:
    others = Owner(
        name="others",
        number_of_indexers=int(constants.OTHER_RATIO * base_indexers),
        number_of_producers=int(constants.OTHER_RATIO * base_producers),
    )
    owners.append(others)

total_indexers = sum(owner.number_of_indexers for owner in owners)
total_producers = sum(owner.number_of_producers for owner in owners)

indexer_diff = constants.I - total_indexers
producer_diff = constants.S - total_producers

if owners:
    owners[-1].number_of_indexers += indexer_diff
    owners[-1].number_of_producers += producer_diff