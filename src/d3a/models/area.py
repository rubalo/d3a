import warnings
import os
from collections import OrderedDict, defaultdict
from logging import getLogger
from random import random
from typing import Dict, List, Optional, Union  # noqa
from multiprocessing import Process, Queue, Event, Manager

from cached_property import cached_property
from pendulum import duration
from pendulum import DateTime
from slugify import slugify

from d3a.blockchain import BlockChainInterface
from d3a import TIME_ZONE
from d3a.exceptions import AreaException
from d3a.models.appliance.base import BaseAppliance
from d3a.models.appliance.inter_area import InterAreaAppliance
from d3a.models.config import SimulationConfig
from d3a.models.events import AreaEvent, MarketEvent, TriggerMixin
from d3a.models.market import Market, BalancingMarket
from d3a.models.strategy.base import BaseStrategy
from d3a.models.strategy.inter_area import InterAreaAgent, BalancingAgent
from d3a.util import TaggedLogWrapper
from d3a.models.strategy.const import ConstSettings
from d3a import TIME_FORMAT

log = getLogger(__name__)


DEFAULT_CONFIG = SimulationConfig(
    duration=duration(hours=24),
    market_count=1,
    slot_length=duration(minutes=15),
    tick_length=duration(seconds=1),
    cloud_coverage=ConstSettings.DEFAULT_PV_POWER_PROFILE,
    market_maker_rate=str(ConstSettings.DEFAULT_MARKET_MAKER_RATE),
    iaa_fee=ConstSettings.INTER_AREA_AGENT_FEE_PERCENTAGE
)


class MarketSerializer:
    def __init__(self, market):
        self.time_slot = market.time_slot
        self.readonly = market.readonly
        self.market_id = market.market_id
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
    market.market_id = serialized_market.market_id
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
                area_market = [m for t, m in area.markets.items() if t == timeslot][0]
                update_market_from_serialized_market(serialized, area_market)
        except IndexError:
            area.markets = self.read_markets(
                area, area._broadcast_notification_sub_to_base_process_blocking
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


class Area:
    _area_id_counter = 1

    def __init__(self, name: str = None, children: List["Area"] = None,
                 strategy: BaseStrategy = None,
                 appliance: BaseAppliance = None,
                 config: SimulationConfig = None,
                 budget_keeper=None,
                 spawn_process=False,
                 balancing_spot_trade_ratio=ConstSettings.BALANCING_SPOT_TRADE_RATIO):
        self.balancing_spot_trade_ratio = balancing_spot_trade_ratio
        self.active = False
        self.log = TaggedLogWrapper(log, name)
        self.current_tick = 0
        self.name = name
        self.slug = slugify(name, to_lower=True)
        self.area_id = Area._area_id_counter
        Area._area_id_counter += 1
        self.parent = None
        self.children = children if children is not None else []
        for child in self.children:
            child.parent = self
        self.inter_area_agents = \
            defaultdict(list)  # type: Dict[Market, List[InterAreaAgent]]
        self.balancing_agents = \
            defaultdict(list)  # type: Dict[BalancingMarket, List[BalancingAgent]]
        self.strategy = strategy
        self.appliance = appliance
        self._config = config
        self.spawn_process = spawn_process
        self.budget_keeper = budget_keeper
        if budget_keeper:
            self.budget_keeper.area = self
        # Children trade in `markets`
        self.markets = OrderedDict()  # type: Dict[DateTime, Market]
        self.balancing_markets = OrderedDict()  # type: Dict[DateTime, BalancingMarket]
        # Past markets
        self.past_markets = OrderedDict()  # type: Dict[DateTime, Market]
        self.past_balancing_markets = OrderedDict()  # type: Dict[DateTime, BalancingMarket]
        self._bc = None  # type: BlockChainInterface
        self.listeners = []
        self._accumulated_past_price = 0
        self._accumulated_past_energy = 0
        self.spawn_process = spawn_process
        self.is_parent_process = True
        self.area_process = None
        if self.spawn_process:
            print(f"PARENT PROCESS PID: {os.getpid()}")
            self.market_wrapper = MultiprocessMarketWrapper()
            self.area_queue = Queue()
            self.event_processed_event = Event()
            self.return_event_queue = Queue()
            self.area_process = Process(target=self.process_event_loop,
                                        args=(self.area_queue,
                                              self.market_wrapper,
                                              self.event_processed_event))
            self.area_process.start()

    def process_event_loop(self, event_queue, market_wrapper, event):
        print(f"SUBPROCESS PID: {os.getpid()}")
        while True:
            self.is_parent_process = False
            if not event_queue.empty() and not event.is_set():
                area_event = event_queue.get()
                event_type = area_event[0]
                keywordargs = area_event[1]
                market_wrapper.update_markets(self)
                self.event_listener(event_type=event_type, **keywordargs)
                self._broadcast_notification(event_type=event_type, **keywordargs)
                market_wrapper.write_markets(self.name, self.markets.values())
                event.set()

    def activate(self, bc=None):
        if bc:
            self._bc = bc
        for attr, kind in [(self.strategy, 'Strategy'), (self.appliance, 'Appliance')]:
            if attr:
                if self.parent:
                    attr.area = self.parent
                    attr.owner = self
                else:
                    raise AreaException(
                        "{kind} {attr.__class__.__name__} "
                        "on area {s} without parent!".format(
                            kind=kind,
                            attr=attr,
                            s=self
                        )
                    )

            if self.budget_keeper:
                self.budget_keeper.activate()

        # Cycle markets without triggering it's own event chain.
        self._cycle_markets(_trigger_event=False)

        if not self.strategy and self.parent is not None:
            self.log.warning("No strategy. Using inter area agent.")
        self.log.info('Activating area')
        self.active = True

        if self.spawn_process is False:
            self._broadcast_notification(AreaEvent.ACTIVATE)
        elif self.is_parent_process:
            self._broadcast_notification_base_to_sub_process(AreaEvent.ACTIVATE)
        else:
            self._broadcast_notification(AreaEvent.ACTIVATE)

    def __repr__(self):
        return "<Area '{s.name}' markets: {markets}>".format(
            s=self,
            markets=[t.strftime(TIME_FORMAT) for t in self.markets.keys()]
        )

    @cached_property
    def current_market(self) -> Optional[Market]:
        """Returns the 'current' market (i.e. the one currently 'running')"""
        try:
            return list(self.past_markets.values())[-1]
        except IndexError:
            return None

    @property
    def next_market(self) -> Optional[Market]:
        """Returns the 'current' market (i.e. the one currently 'running')"""
        try:
            return list(self.markets.values())[0]
        except IndexError:
            return None

    @property
    def current_slot(self):
        return self.current_tick // self.config.ticks_per_slot

    @property
    def current_tick_in_slot(self):
        return self.current_tick % self.config.ticks_per_slot

    @property
    def config(self):
        if self._config:
            return self._config
        if self.parent:
            return self.parent.config
        return DEFAULT_CONFIG

    @property
    def bc(self) -> Optional[BlockChainInterface]:
        if self._bc is not None:
            return self._bc
        if self.parent:
            return self.parent.bc
        return None

    @property
    def _offer_count(self):
        return sum(
            len(m.offers)
            for markets in (self.past_markets, self.markets)
            for m in markets.values()
        )

    @property
    def _trade_count(self):
        return sum(
            len(m.trades)
            for markets in (self.past_markets, self.markets)
            for m in markets.values()
        )

    @property
    def historical_avg_rate(self):
        price = sum(
            market.accumulated_trade_price
            for market in self.markets.values()
        ) + self._accumulated_past_price
        energy = sum(
            market.accumulated_trade_energy
            for market in self.markets.values()
        ) + self._accumulated_past_energy
        return price / energy if energy else 0

    @property
    def cheapest_offers(self):
        cheapest_offers = []
        for market in self.markets.values():
            cheapest_offers.extend(market.sorted_offers[0:1])
        return cheapest_offers

    @property
    def market_with_most_expensive_offer(self):
        # In case of a tie, max returns the first market occurrence in order to
        # satisfy the most recent market slot
        return max(self.markets.values(),
                   key=lambda m: m.sorted_offers[0].price / m.sorted_offers[0].energy)

    @property
    def historical_min_max_price(self):
        min_max_prices = [
            (m.min_trade_price, m.max_trade_price)
            for markets in (self.past_markets, self.markets)
            for m in markets.values()
        ]
        return (
            min(p[0] for p in min_max_prices),
            max(p[1] for p in min_max_prices)
        )

    @cached_property
    def child_by_slug(self):
        slug_map = {}
        areas = [self]
        while areas:
            for area in list(areas):
                slug_map[area.slug] = area
                areas.remove(area)
                areas.extend(area.children)
        return slug_map

    def _cycle_markets(self, _trigger_event=True, _market_cycle=False):
        """
        Remove markets for old time slots, add markets for new slots.
        Trigger `MARKET_CYCLE` event to allow child markets to also cycle.

        It's important for this to happen from top to bottom of the `Area` tree
        in order for the `InterAreaAgent`s to be connected correctly

        `_trigger_event` is used internally to avoid multiple event chains during
        initial area activation.
        """
        if not self.children:
            # Since children trade in markets we only need to populate them if there are any
            return

        if self.budget_keeper and _market_cycle:
            self.budget_keeper.process_market_cycle()

        now = self.now
        time_in_hour = duration(minutes=now.minute, seconds=now.second)
        now = now.at(now.hour, minute=0, second=0) + \
            ((time_in_hour // self.config.slot_length) * self.config.slot_length)

        self.log.info("Cycling markets")

        # Move old and current markets & balancing_markets to
        # `past_markets` & past_balancing_markets. We use `list()` here to get a copy since we
        # modify the market list in-place
        changed, _ = self._market_rotation(current_time=now,
                                           markets=self.markets,
                                           past_markets=self.past_markets,
                                           area_agent=self.inter_area_agents)

        changed_balancing_market, _ = \
            self._market_rotation(current_time=now,
                                  markets=self.balancing_markets,
                                  past_markets=self.past_balancing_markets,
                                  area_agent=self.balancing_agents)

        self._accumulated_past_price = sum(
            market.accumulated_trade_price
            for market in self.past_markets.values()
        )
        self._accumulated_past_energy = sum(
            market.accumulated_trade_energy
            for market in self.past_markets.values()
        )
        # Clear `current_market` cache
        self.__dict__.pop('current_market', None)

        # Markets range from one slot to market_count into the future
        changed = self._create_future_markets(current_time=self.now, markets=self.markets,
                                              parent=self.parent,
                                              parent_markets=self.parent.markets
                                              if self.parent is not None else None,
                                              area_agent=self.inter_area_agents,
                                              parent_area_agent=self.parent.inter_area_agents
                                              if self.parent is not None else None,
                                              agent_class=InterAreaAgent,
                                              market_class=Market)

        changed_balancing_market = \
            self._create_future_markets(current_time=self.now, markets=self.balancing_markets,
                                        parent=self.parent,
                                        parent_markets=self.parent.balancing_markets
                                        if self.parent is not None else None,
                                        area_agent=self.balancing_agents,
                                        parent_area_agent=self.parent.balancing_agents
                                        if self.parent is not None else None,
                                        agent_class=BalancingAgent,
                                        market_class=BalancingMarket)

        # Force market cycle event in case this is the first market slot
        if (changed or len(self.past_markets.keys()) == 0) and _trigger_event:
            if self.spawn_process is False:
                self._broadcast_notification(AreaEvent.MARKET_CYCLE)
            elif self.is_parent_process:
                self.market_wrapper.write_markets(self.name, self.markets.values())
                self._broadcast_notification_base_to_sub_process(AreaEvent.MARKET_CYCLE)
            else:
                self._broadcast_notification(AreaEvent.MARKET_CYCLE)

        # Force balancing_market cycle event in case this is the first market slot
        if (changed_balancing_market or len(self.past_balancing_markets.keys()) == 0) \
                and _trigger_event:
            if self.spawn_process is False:
                self._broadcast_notification(AreaEvent.BALANCING_MARKET_CYCLE)
            elif self.is_parent_process:
                self._broadcast_notification_base_to_sub_process(AreaEvent.BALANCING_MARKET_CYCLE)
            else:
                self._broadcast_notification(AreaEvent.MARKET_CYCLE)

    def get_now(self) -> DateTime:
        """Compatibility wrapper"""
        warnings.warn("The '.get_now()' method has been replaced by the '.now' property. "
                      "Please use that in the future.")
        return self.now

    @property
    def now(self) -> DateTime:
        """
        Return the 'current time' as a `DateTime` object.
        Can be overridden in subclasses to change the meaning of 'now'.

        In this default implementation 'current time' is defined by the number of ticks that
        have passed.
        """
        return DateTime.now(tz=TIME_ZONE).start_of('day').add(
            seconds=self.config.tick_length.seconds * self.current_tick
        )

    @cached_property
    def available_triggers(self):
        triggers = []
        if isinstance(self.strategy, TriggerMixin):
            triggers.extend(self.strategy.available_triggers)
        if isinstance(self.appliance, TriggerMixin):
            triggers.extend(self.appliance.available_triggers)
        return {t.name: t for t in triggers}

    def tick(self):
        if self.current_tick % self.config.ticks_per_slot == 0:
            self._cycle_markets()

        if self.spawn_process is False:
            self._broadcast_notification(AreaEvent.TICK, area_id=self.area_id)
        else:
            if self.is_parent_process:
                self._broadcast_notification_base_to_sub_process(
                    AreaEvent.TICK, area_id=self.area_id
                )
        self.current_tick += 1

    def report_accounting(self, market, reporter, value, time=None):
        if time is None:
            time = self.now
        slot = market.time_slot
        if slot in self.markets or slot in self.past_markets:
            market.set_actual_energy(time, reporter, value)
        else:
            raise RuntimeError("Reporting energy for unknown market")

    def _broadcast_notification_base_to_sub_process(self,
                                                    event_type,
                                                    **kwargs):
        self.market_wrapper.write_markets(self.name, self.markets.values())
        self.area_queue.put([event_type, kwargs])

    def _broadcast_notification_sub_to_base_process_blocking(self,
                                                             event_type,
                                                             **kwargs):
        self.market_wrapper.write_markets(self.name, self.markets.values())
        self.return_event_queue.put([event_type, kwargs])

    def _broadcast_notification(self, event_type: Union[MarketEvent, AreaEvent], **kwargs):
        # Broadcast to children in random order to ensure fairness
        children_to_wait = []
        for child in sorted(self.children, key=lambda _: random()):
            child.event_listener(event_type, **kwargs)
            if child.spawn_process and child.is_parent_process:
                children_to_wait.append(child)

        for child in children_to_wait:
            child.event_processed_event.wait()
            child.event_processed_event.clear()
            child.market_wrapper.update_markets(child)

            child._dispatch_to_iaas_and_listeners(event_type, **kwargs)

            while not child.return_event_queue.empty():
                child_event = child.return_event_queue.get()
                event_type2 = child_event[0]
                keywordargs2 = child_event[1]
                child._dispatch_to_iaas_and_listeners(event_type2, **keywordargs2)
                child.market_wrapper.write_markets(child.name, child.markets.values())

        self._dispatch_to_iaas_and_listeners(event_type, **kwargs)

    def _dispatch_to_iaas_and_listeners(self, event_type, **kwargs):
        # Also broadcast to IAAs. Again in random order
        for market, agents in self.inter_area_agents.items():
            if market.time_slot not in self.markets:
                # exclude past IAAs
                continue
            for agent in sorted(agents, key=lambda _: random()):
                agent.event_listener(event_type, **kwargs)
        # Also broadcast to BAs. Again in random order
        for balancing_market, agents in self.balancing_agents.items():
            if balancing_market.time_slot not in self.balancing_markets:
                # exclude past BAs
                continue

            for agent in sorted(agents, key=lambda _: random()):
                agent.event_listener(event_type, **kwargs)
        for listener in self.listeners:
            listener.event_listener(event_type, **kwargs)

    def _fire_trigger(self, trigger_name, **params):
        for target in (self.strategy, self.appliance):
            if isinstance(target, TriggerMixin):
                for trigger in target.available_triggers:
                    if trigger.name == trigger_name:
                        return target.fire_trigger(trigger_name, **params)

    def add_listener(self, listener):
        self.listeners.append(listener)

    def event_listener(self, event_type: Union[MarketEvent, AreaEvent], **kwargs):
        if event_type is AreaEvent.TICK:
            self.tick()
        # TODO: Review this change. Make sure this trigger is not needed anywhere else
        elif event_type is AreaEvent.MARKET_CYCLE:
            self._cycle_markets(_market_cycle=True)
        elif event_type is AreaEvent.ACTIVATE:
            self.activate()
        if self.strategy:
            self.strategy.event_listener(event_type, **kwargs)
        if self.appliance:
            self.appliance.event_listener(event_type, **kwargs)

    def _market_rotation(self, current_time, markets, past_markets, area_agent):
        changed = False
        first = True
        for timeframe in list(markets.keys()):
            if timeframe < current_time:
                market = markets.pop(timeframe)
                market.readonly = True
                past_markets[timeframe] = market
                if not first:
                    # Remove inter area agent
                    area_agent.pop(market, None)
                else:
                    first = False
                changed = True
                self.log.debug("Moving {t:%H:%M} {m} to past"
                               .format(t=timeframe, m=past_markets[timeframe].area.name))
        return changed, first

    def _create_future_markets(self, current_time, markets, parent, parent_markets,
                               area_agent, parent_area_agent, agent_class, market_class):
        changed = False
        for offset in (self.config.slot_length * i for i in range(self.config.market_count)):
            timeframe = current_time + offset
            if timeframe not in markets:
                # Create markets for missing slots
                if self.spawn_process is False:
                    my_lambda = self._broadcast_notification
                elif self.area_process and self.is_parent_process:
                    my_lambda = self._broadcast_notification_base_to_sub_process
                else:
                    my_lambda = self._broadcast_notification_sub_to_base_process_blocking
                market = market_class(timeframe, self,
                                      notification_listener=my_lambda)
                if market not in area_agent:
                    if parent and timeframe in parent_markets and not self.strategy:
                        # Only connect an InterAreaAgent if we have a parent, a corresponding
                        # timeframe market exists in the parent and we have no strategy
                        iaa = agent_class(
                            owner=self,
                            higher_market=parent_markets[timeframe],
                            lower_market=market,
                            transfer_fee_pct=self.config.iaa_fee
                        )
                        # Attach agent to own IAA list
                        area_agent[market].append(iaa)
                        # And also to parents to allow events to flow form both markets
                        parent_area_agent[parent_markets[timeframe]].append(iaa)
                        if parent:
                            # Add inter area appliance to report energy
                            self.appliance = InterAreaAppliance(parent, self)
                markets[timeframe] = market
                changed = True
                self.log.debug("Adding {t:{format}} market".format(
                    t=timeframe,
                    format="%H:%M" if self.config.slot_length.total_seconds() > 60 else "%H:%M:%S"
                ))
        return changed
