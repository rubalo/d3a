# flake8: noqa

import os
import logging
from d3a_api_client.redis_device import RedisDeviceClient
from d3a_api_client.redis_market import RedisMarketClient
from d3a_api_client.rest_market import RestMarketClient
from d3a_api_client.rest_device import RestDeviceClient
from d3a_api_client.aggregator import Aggregator
from pendulum import from_format
from d3a_interface.constants_limits import DATE_TIME_FORMAT
from d3a_api_client.utils import get_area_uuid_from_area_name_and_collaboration_id

# set login information
os.environ["API_CLIENT_USERNAME"] = "colin@gridsingularity.com" # TODO set username
os.environ["API_CLIENT_PASSWORD"] = "magrathea" # TODO set password

# set simulation parameters
RUN_ON_D3A_WEB = True # TODO set to true if joining collaboration through UI, false if running simulation locally
simulation_id = 'eb861cd1-50bc-42c4-9020-228faa60ee3f' # TODO update simulation id with experiment id
domain_name = 'https://d3aweb-dev.gridsingularity.com' # leave as is
websocket_domain_name = 'wss://d3aweb-dev.gridsingularity.com/external-ws' # leave as is

# Designate devices and markets to manage
market_names = ['Community 1']
load_names = ['Load 1', 'Load 2'] # e.g. ['h1-load-s', 'h2-load'], first load is 'master' strategy
pv_names = ['PV 1']
storage_names = ['Storage 1']

# set trading strategy parameters
market_maker_price = 30
feed_in_tariff_price = 11

# set market parameters
ticks = 10


class TestAggregator(Aggregator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_finished = False
        self.load_strategy = []
        self.pv_strategy = []
        self.batt_sell_strategy = []
        self.batt_buy_strategy = []

    def on_market_cycle(self, market_info):
        """
        Places a bid or an offer whenever a new market is created. The amount of energy
        for the bid/offer depends on the available energy of the PV, or on the required
        energy of the load.
        :param market_info: Incoming message containing the newly-created market info
        :return: None
        """
        if self.is_finished is True:
            return
        if "content" not in market_info:
            return

        # TODO extract device energy and market data for features
        print('----------------------------------')
        print("MARKET INFO:")
        print(market_info)

        # TODO extract market stats through aggregator
        # # request market stats
        # market_time = from_format(market_info['start_time'], DATE_TIME_FORMAT, tz=TIME_ZONE)
        # slots = []
        # times = [15, 30]  # sort most recent to oldest for later algo
        # for time in times:
        #     slots.append(market_time.subtract(minutes=time).format(DATE_TIME_FORMAT))
        # for market in self.markets:
        #     stats = market.list_market_stats(slots)

        # TODO predict market slot prices based on extracted market data and features
        # predict market slot prices
        pred_min_price = 12
        pred_avg_price = 18
        pred_med_price = 20
        pred_max_price = 30

        # TODO set bidding strategy for each tick
        # set pricing strategies
        self.load_strategy = []
        self.pv_strategy = []
        self.batt_sell_strategy = []
        self.batt_buy_strategy = []
        for i in range(0, ticks):
            if i < ticks-1:
                self.load_strategy.append(pred_min_price + (pred_max_price - pred_min_price) * (i/ticks))
                self.pv_strategy.append(pred_max_price - (pred_max_price - pred_min_price) * (i / ticks))
            else: # last tick guarantee match
                self.load_strategy.append(market_maker_price)
                self.pv_strategy.append(feed_in_tariff_price)
            self.batt_buy_strategy.append(pred_min_price + (pred_med_price - pred_min_price) * (i/ticks))
            self.batt_sell_strategy.append(pred_max_price - (pred_max_price - pred_med_price) * (i / ticks))


        # set initial bids and offers
        # TODO add print of bid / offer
        batch_commands = {}

        for device_event in market_info["content"]:

            # Load Strategy
            if "energy_requirement_kWh" in device_event["device_info"] and \
                    device_event["device_info"]["energy_requirement_kWh"] > 0.0:
                batch_commands[device_event["area_uuid"]] = [
                    {"type": "bid",
                     "price": self.load_strategy[0],
                     "energy": device_event["device_info"]["energy_requirement_kWh"]},
                    {"type": "list_bids"}]

            # PV Strategy
            if "available_energy_kWh" in device_event["device_info"] and \
                    device_event["device_info"]["available_energy_kWh"] > 0.0:
                batch_commands[device_event["area_uuid"]] = [
                    {"type": "offer",
                     "price": self.pv_strategy[0],
                     "energy": device_event["device_info"]["available_energy_kWh"]},
                    {"type": "list_offers"}]

            # Battery buy strategy
            if "energy_to_buy" in device_event["device_info"] and \
                    device_event["device_info"]["energy_to_buy"] > 0.0:
                batch_commands[device_event["area_uuid"]] = [
                    {"type": "bid",
                     "price": self.batt_buy_strategy[0],
                     "energy": device_event["device_info"]["energy_requirement_kWh"]},
                    {"type": "list_bids"}]

            # Battery sell strategy
            if "energy_to_sell" in device_event["device_info"] and \
                    device_event["device_info"]["energy_to_sell"] > 0.0:
                batch_commands[device_event["area_uuid"]] = [
                    {"type": "offer",
                     "price": self.batt_sell_strategy[0],
                     "energy": device_event["device_info"]["available_energy_kWh"]},
                    {"type": "list_offers"}]

        if batch_commands:
            response = self.batch_command(batch_commands)
            logging.debug(f"Batch command placed on the new market: {response}")

    def on_tick(self, tick_info):
        logging.debug(f"Progress information on the device: {tick_info}")
        print('--------', tick_info['slot_completion'], '--------')

        # TODO get tick number for index
        i = int(float(tick_info['slot_completion'].strip('%')) * ticks)

        # TODO manipulate tick strategy if required
        self.load_strategy = self.load_strategy
        self.pv_strategy = self.pv_strategy
        self.batt_buy_strategy = self.batt_buy_strategy
        self.batt_sell_strategy = self.batt_sell_strategy

        batch_commands = {}

        for device_event in tick_info["content"]:

            # Load Strategy
            if "energy_requirement_kWh" in device_event["device_info"] and \
                    device_event["device_info"]["energy_requirement_kWh"] > 0.0:
                batch_commands[device_event["area_uuid"]] = [
                    {"type": "delete_bid"},
                    {"type": "bid",
                     "price": self.load_strategy[i],
                     "energy": device_event["device_info"]["energy_requirement_kWh"]},
                    {"type": "list_bids"}]

            # PV Strategy
            if "available_energy_kWh" in device_event["device_info"] and \
                    device_event["device_info"]["available_energy_kWh"] > 0.0:
                batch_commands[device_event["area_uuid"]] = [
                    {"type": "delete_offer"},
                    {"type": "offer",
                     "price": self.pv_strategy[i],
                     "energy": device_event["device_info"]["available_energy_kWh"]},
                    {"type": "list_offers"}]

            # Battery buy strategy
            if "energy_to_buy" in device_event["device_info"] and \
                    device_event["device_info"]["energy_to_buy"] > 0.0:
                batch_commands[device_event["area_uuid"]] = [
                    {"type": "delete_bid"},
                    {"type": "bid",
                     "price": self.batt_buy_strategy[i],
                     "energy": device_event["device_info"]["energy_requirement_kWh"]},
                    {"type": "list_bids"}]

            # Battery sell strategy
            if "energy_to_sell" in device_event["device_info"] and \
                    device_event["device_info"]["energy_to_sell"] > 0.0:
                batch_commands[device_event["area_uuid"]] = [
                    {"type": "delete_offer"},
                    {"type": "offer",
                     "price": self.batt_sell_strategy[i],
                     "energy": device_event["device_info"]["available_energy_kWh"]},
                    {"type": "list_offers"}]


    def on_trade(self, trade_info):
        logging.debug(f"Trade info: {trade_info}")

        # TODO print trade info on trade event, adapt from below
        # trade_price = trade_info['price']
        # trade_energy = trade_info['energy']
        # # buyer
        # if trade_info['buyer'] == self.device_id:
        #     trade_price_per_kWh = trade_price / trade_energy
        #     print(f'<-- {self.device_id} BOUGHT {round(trade_energy, 4)} kWh '
        #           f'at {round(trade_price_per_kWh, 2)}/kWh')
        #
        # # seller
        # if trade_info['seller'] == self.device_id:
        #     trade_price_per_kWh = trade_price / trade_energy
        #     print(f'--> {self.device_id} SOLD {round(trade_energy, 4)} kWh '
        #           f'at {round(trade_price_per_kWh, 2)}/kWh')

    def on_finish(self, finish_info):
        self.is_finished = True


# REGISTER FOR DEVICES AND MARKETS

# TODO allow connection through redis for locally running and training aggregator models
# TODO adapt structure to allow registration of markets and devices for local run

aggr = TestAggregator(
    simulation_id=simulation_id,
    domain_name=domain_name,
    aggregator_name="oracle",
    websockets_domain_name=websocket_domain_name
)

if RUN_ON_D3A_WEB:
    MarketClient = RestMarketClient
    DeviceClient = RestDeviceClient
else:
    MarketClient = RedisMarketClient
    DeviceClient = RedisDeviceClient

device_args = {
    "simulation_id": simulation_id,
    "domain_name": domain_name,
    "websockets_domain_name": websocket_domain_name,
    "autoregister": False,
    "start_websocket": False
}


def register_device_list(device_names, device_args):
    for d in device_names:
        uuid = get_area_uuid_from_area_name_and_collaboration_id(device_args["simulation_id"], d, device_args["domain_name"])
        device_args['device_id'] = uuid
        device = DeviceClient(**device_args)
        device.select_aggregator(aggr.aggregator_uuid)


register_device_list(load_names, device_args)
register_device_list(pv_names, device_args)
register_device_list(storage_names, device_args)


# TODO create register_market_list function
def register_market_list(market_names):
    pass

register_market_list()

# loop to allow persistence
from time import sleep
while not aggr.is_finished:
    sleep(0.5)
