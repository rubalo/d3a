from multiprocessing import Manager
from d3a.models.market import Market


class MarketSerializer:
    def __init__(self, market):
        self.time_slot = market.time_slot
        self.readonly = market.readonly
        self.id = market.id
        self.offers = market.offers
        self.trades = market.trades
        self.ious = dict(market.ious)
        self.traded_energy = dict(market.traded_energy)
        self.actual_energy = dict(market.actual_energy)
        self.accumulated_actual_energy_agg = market.accumulated_actual_energy_agg
        self.min_trade_price = market.min_trade_price
        self._avg_trade_price = market._avg_trade_price
        self.max_trade_price = market.max_trade_price
        self.min_offer_price = market.min_offer_price
        self._avg_offer_price = market._avg_offer_price
        self.max_offer_price = market.max_offer_price
        self._sorted_offers = market._sorted_offers
        self.accumulated_trade_price = market.accumulated_trade_price
        self.accumulated_trade_energy = market.accumulated_trade_energy


def market_factory(serialized_market, area, broadcasts):
    market = Market(serialized_market.time_slot, area, broadcasts, serialized_market.readonly)
    market = update_market_from_serialized_market(serialized_market, market)
    return market


def update_market_from_serialized_market(serialized_market, market):
    assert serialized_market.time_slot == market.time_slot
    market.time_slot = serialized_market.time_slot
    market.readonly = serialized_market.readonly
    market.id = serialized_market.id
    market.offers = serialized_market.offers
    market.trades = serialized_market.trades
    market.ious.update(serialized_market.ious)
    market.traded_energy.update(serialized_market.traded_energy)
    market.actual_energy.update(serialized_market.actual_energy)
    market.accumulated_actual_energy_agg = serialized_market.accumulated_actual_energy_agg
    market.min_trade_price = serialized_market.min_trade_price
    market._avg_trade_price = serialized_market._avg_trade_price
    market.max_trade_price = serialized_market.max_trade_price
    market.min_offer_price = serialized_market.min_offer_price
    market._avg_offer_price = serialized_market._avg_offer_price
    market.max_offer_price = serialized_market.max_offer_price
    market._sorted_offers = serialized_market._sorted_offers
    market.accumulated_trade_price = serialized_market.accumulated_trade_price
    market.accumulated_trade_energy = serialized_market.accumulated_trade_energy
    return market


class MultiprocessMarketWrapper:
    def __init__(self):
        # Dict of dicts. Each area has its own markets, one per timeslot
        self.manager = Manager()
        self.markets = self.manager.dict()

    def read_markets(self, area, broadcasts):
        if area.name not in self.markets:
            return {}
        return \
            {timeslot: market_factory(m, area, broadcasts)
             for timeslot, m in self.markets[area.name].items()}

    def write_markets(self, area_name, markets):
        self.markets[area_name] = self.manager.dict()
        for m in markets:
            self.markets[area_name][m.time_slot] = MarketSerializer(m)

    def update_markets(self, area):
        try:
            for timeslot, serialized in self.markets[area.name].items():
                area_market = [m for t, m in area._markets.markets.items() if t == timeslot][0]
                update_market_from_serialized_market(serialized, area_market)
        except IndexError:
            area.markets = self.read_markets(
                area, area.dispatcher._broadcast_notification_sub_to_base_process_blocking
            )

    def read_market_from_main_process(self, area, broadcasts):
        return \
            {timeslot: market_factory(self.markets[area.name][timeslot], area, broadcasts)
             for timeslot in self.markets.keys()}

    def add_market_to_queue(self, queue, market):
        queue.put(MarketSerializer(market), block=False)

    def read_markets_from_subprocess(self, queue, area, broadcasts):
        if not queue.empty():
            markets = queue.get()
            return {market.time_slot: market_factory(market,
                                                     area,
                                                     broadcasts)
                    for market in markets}

    def append_market(self, area_name, timeslot, market):
        if area_name not in self.markets.keys():
            self.markets[area_name] = self.manager.dict()
        self.markets[area_name][timeslot] = MarketSerializer(market)
