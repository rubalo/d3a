from typing import Dict, List  # noqa

from collections import defaultdict
from d3a.models.market import Market, Offer  # noqa
from d3a.models.strategy.const import DEFAULT_RISK, ARRIVAL_TIME, DEPART_TIME
from d3a.models.strategy.storage import StorageStrategy


class ECarStrategy(StorageStrategy):
    def __init__(self, risk=DEFAULT_RISK):
        super().__init__()
        self.risk = risk
        self.offers_posted = {}  # type: Dict[str, Market]
        self.bought_offers = defaultdict(list)  # type: Dict[Market, List[Offer]]
        self.sold_offers = defaultdict(list)  # type: Dict[Market, List[Offer]]
        self.used_storage = 0.00
        self.blocked_storage = 0.00
        self.connected_to_grid = False

    def event_tick(self, *, area):
        arrival_time = self.area.now.start_of("day").hour_(ARRIVAL_TIME)
        depart_time = self.area.now.start_of("day").hour_(DEPART_TIME)

        # Car arrives at charging station at
        if self.area.now.diff(arrival_time).in_minutes() == 0:
            self.connected_to_grid = True
            self.sell_energy(self.used_storage)
        # Car departs from charging station at
        if self.area.now.diff(depart_time).in_minutes() == 0:
            self.connected_to_grid = False
            self.departure()

        if not self.connected_to_grid:
            # This means the car is driving around some where
            self.used_storage *= 0.9999
            return
        # Taking the cheapest offers in every market currently open and building the average
        # Same process as storage
        avg_cheapest_offer_price = self.find_avg_cheapest_offers()
        # Check if there are cheap offers to buy
        self.buy_energy(avg_cheapest_offer_price)
        # Check if any energy from the Car can be sold
        # Same process as Storage
        self.sell_energy(avg_cheapest_offer_price)

    def departure(self):
        for market, offer in self.offers_posted:
            market.delete_offer(offer.id)
            self.used_storage += offer.energy
