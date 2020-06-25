"""
This is a template which represent a community of 28 houses. Only the devices of house 1 can be controlled with an external connection

This configuration can be subject to modifications (PV & storage capacity, adding/deleting energy assets and areas)

We recommend to train your smart agents on multiple configurations to achieve better result during the hackathon
"""
# flake8: noqa
import os
import platform
from d3a.models.appliance.pv import PVAppliance
from d3a.models.appliance.simple import SimpleAppliance
from d3a.models.appliance.switchable import SwitchableAppliance
from d3a.models.area import Area
from d3a.models.strategy.market_maker_strategy import MarketMakerStrategy
from d3a.models.strategy.predefined_load import DefinedLoadStrategy
from d3a.models.strategy.pv import PVStrategy
from d3a_interface.constants_limits import ConstSettings
from d3a.models.strategy.infinite_bus import InfiniteBusStrategy
from d3a.models.strategy.storage import StorageStrategy
from d3a.models.strategy.load_hours import LoadHoursStrategy
from d3a.models.strategy.predefined_pv import PVUserProfileStrategy
from d3a.models.strategy.external_strategies.pv import PVUserProfileExternalStrategy
from d3a.models.strategy.external_strategies.load import LoadProfileExternalStrategy
from d3a.models.strategy.external_strategies.storage import StorageExternalStrategy
from random import random

current_dir = os.path.dirname(__file__)
print(current_dir)

VARIANCE_RATES = 0.2  # variance against starting rate (0.8 to 1.2 times starting if set to 0.2)


load_data = []
pv_data = []
chp_data = []
for i in range(0, 30):
    load = os.path.join(current_dir, "resources/Load_Feb/Load_Feb_" + str(i) + ".csv")  # path to your csv file
    load_data.append(load)
    pv = os.path.join(current_dir, "resources/PV_Feb/PV_Feb_" + str(i) + ".csv")
    pv_data.append(pv)
    chp = os.path.join(current_dir, "resources/CHP_Feb/CHP_Feb_" + str(i) + ".csv")
    chp_data.append(chp)

def get_setup(config):

    ConstSettings.GeneralSettings.DEFAULT_UPDATE_INTERVAL = 1
    ConstSettings.IAASettings.MARKET_TYPE = 2
    ConstSettings.GeneralSettings.DEFAULT_MARKET_MAKER_RATE = 26

    Houses_initial_buying_rate = 11
    PV_initial = 27
    PV_final = 11

    area = Area(
        'Grid',
        [
            Area(
                'ZIP code',
                [
                    Area(
                        'Community A',
                        [
                            Area(
                                'H1',
                                [
                                    Area('Load 1', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[1],
                                                                                           initial_buying_rate=Houses_initial_buying_rate,
                                                                                           use_market_maker_rate=True),
                                                                                           appliance=SwitchableAppliance()),

                                    Area('PV 1', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[1],
                                                                                           initial_selling_rate=PV_initial,
                                                                                           final_selling_rate=PV_final),
                                                                                           appliance=PVAppliance()),

                                    Area('Storage 1', strategy=StorageExternalStrategy(initial_soc=10,
                                                                               min_allowed_soc=10,
                                                                               battery_capacity_kWh=13.5,
                                                                               max_abs_battery_power_kW=5),
                                                                               appliance=SwitchableAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H2',
                                [
                                    Area('Load 2', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[2],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 2', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[2],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                    Area('Storage 2', strategy=StorageExternalStrategy(initial_soc=10,
                                                                                       min_allowed_soc=10,
                                                                                       battery_capacity_kWh=13.5,
                                                                                       max_abs_battery_power_kW=5),
                                         appliance=SwitchableAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H3',
                                [
                                    Area('Load 3', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[3],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 3', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[3],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                    Area('Storage 3', strategy=StorageExternalStrategy(initial_soc=10,
                                                                                       min_allowed_soc=10,
                                                                                       battery_capacity_kWh=13.5,
                                                                                       max_abs_battery_power_kW=5),
                                         appliance=SwitchableAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H4',
                                [
                                    Area('Load 4', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[4],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 4', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[4],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                    Area('Storage 4', strategy=StorageExternalStrategy(initial_soc=10,
                                                                                       min_allowed_soc=10,
                                                                                       battery_capacity_kWh=13.5,
                                                                                       max_abs_battery_power_kW=5),
                                         appliance=SwitchableAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H5',
                                [
                                    Area('Load 5', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[5],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 5', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[5],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H6',
                                [
                                    Area('Load 6', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[6],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),


                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H7',
                                [
                                    Area('Load 7', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[7],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 7', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[7],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                    Area('Storage 7', strategy=StorageExternalStrategy(initial_soc=10,
                                                                                       min_allowed_soc=10,
                                                                                       battery_capacity_kWh=13.5,
                                                                                       max_abs_battery_power_kW=5),
                                         appliance=SwitchableAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H8',
                                [
                                    Area('Load 8', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[8],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 8', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[8],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),


                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H10',
                                [
                                    Area('Load 10', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[10],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 10', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[10],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                    Area('Storage 10', strategy=StorageExternalStrategy(initial_soc=10,
                                                                                       min_allowed_soc=10,
                                                                                       battery_capacity_kWh=13.5,
                                                                                       max_abs_battery_power_kW=5),
                                         appliance=SwitchableAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H11',
                                [
                                    Area('Load 11', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[11],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 11', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[11],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H12',
                                [
                                    Area('Load 12', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[12],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 12', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[12],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                    Area('Storage 12', strategy=StorageExternalStrategy(initial_soc=10,
                                                                                       min_allowed_soc=10,
                                                                                       battery_capacity_kWh=13.5,
                                                                                       max_abs_battery_power_kW=5),
                                         appliance=SwitchableAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H13',
                                [
                                    Area('Load 13', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[13],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H14',
                                [
                                    Area('Load 14', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[14],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 14', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[14],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H15',
                                [
                                    Area('Load 15', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[15],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H16',
                                [
                                    Area('Load 16', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[16],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 16', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[16],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H17',
                                [
                                    Area('Load 17', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[17],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 17', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[17],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H18',
                                [
                                    Area('Load 18', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[18],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 18', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[18],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                    Area('Storage 18', strategy=StorageExternalStrategy(initial_soc=10,
                                                                                       min_allowed_soc=10,
                                                                                       battery_capacity_kWh=13.5,
                                                                                       max_abs_battery_power_kW=5),
                                         appliance=SwitchableAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H19',
                                [
                                    Area('Load 19', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[19],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 19', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[19],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                    Area('CHP 19', strategy=PVUserProfileExternalStrategy(power_profile=chp_data[6],
                                                                                         initial_selling_rate=PV_initial,
                                                                                         final_selling_rate=PV_final),
                                         appliance=PVAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H20',
                                [
                                    Area('Load 20', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[20],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 20', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[20],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                    Area('Storage 20', strategy=StorageExternalStrategy(initial_soc=10,
                                                                                       min_allowed_soc=10,
                                                                                       battery_capacity_kWh=13.5,
                                                                                       max_abs_battery_power_kW=5),
                                         appliance=SwitchableAppliance()),
                                    Area('CHP 20', strategy=PVUserProfileExternalStrategy(power_profile=chp_data[21],
                                                                                         initial_selling_rate=PV_initial,
                                                                                         final_selling_rate=PV_final),
                                         appliance=PVAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H21',
                                [
                                    Area('Load 21', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[21],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H22',
                                [
                                    Area('Load 22', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[22],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H24',
                                [
                                    Area('Load 24', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[24],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 24', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[24],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),


                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H25',
                                [
                                    Area('Load 25', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[25],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                    Area('PV 25', strategy=PVUserProfileExternalStrategy(power_profile=pv_data[25],
                                                                                        initial_selling_rate=PV_initial,
                                                                                        final_selling_rate=PV_final),
                                         appliance=PVAppliance()),

                                    Area('Storage 25', strategy=StorageExternalStrategy(initial_soc=10,
                                                                                       min_allowed_soc=10,
                                                                                       battery_capacity_kWh=13.5,
                                                                                       max_abs_battery_power_kW=5),
                                         appliance=SwitchableAppliance()),
                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                        ], grid_fee_percentage=0, transfer_fee_const=4, external_connection_available=True
                    ),
                    Area(
                        'Community B',
                        [
                            Area(
                                'H1b',
                                [
                                    Area('Load 1b', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[1],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H2b',
                                [
                                    Area('Load 2b', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[2],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H3b',
                                [
                                    Area('Load 3b', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[3],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H4b',
                                [
                                    Area('Load 4b', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[4],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H5b',
                                [
                                    Area('Load 5b', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[5],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H6b',
                                [
                                    Area('Load 6b', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[6],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H7b',
                                [
                                    Area('Load 7b', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[7],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H8b',
                                [
                                    Area('Load 8b', strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[8],
                                                                                        initial_buying_rate=Houses_initial_buying_rate,
                                                                                        use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H10b',
                                [
                                    Area('Load 10b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[10],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H11b',
                                [
                                    Area('Load 11b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[11],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H12b',
                                [
                                    Area('Load 12b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[12],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H13b',
                                [
                                    Area('Load 13b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[13],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H14b',
                                [
                                    Area('Load 14b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[14],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H15b',
                                [
                                    Area('Load 15b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[15],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H16b',
                                [
                                    Area('Load 16b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[16],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H17b',
                                [
                                    Area('Load 17b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[17],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H18b',
                                [
                                    Area('Load 18b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[18],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H19b',
                                [
                                    Area('Load 19b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[19],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H20b',
                                [
                                    Area('Load 20b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[20],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H21b',
                                [
                                    Area('Load 21b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[21],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H22b',
                                [
                                    Area('Load 22b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[22],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H24b',
                                [
                                    Area('Load 24b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[24],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                            Area(
                                'H25b',
                                [
                                    Area('Load 25b',
                                         strategy=LoadProfileExternalStrategy(daily_load_profile=load_data[25],
                                                                              initial_buying_rate=Houses_initial_buying_rate,
                                                                              use_market_maker_rate=True),
                                         appliance=SwitchableAppliance()),

                                ], grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=True
                            ),
                        ], grid_fee_percentage=0, transfer_fee_const=4, external_connection_available=True
                    ),
                ]
            ),


            Area('Feed-in tariff', strategy=LoadHoursStrategy(avg_power_W=100000000, hrs_per_day=24, hrs_of_day=list(range(0, 24)),
                                                              initial_buying_rate=11,
                                                              final_buying_rate=11),
                 appliance=SwitchableAppliance()),


            Area('Market Maker', strategy=MarketMakerStrategy(energy_rate=ConstSettings.GeneralSettings.DEFAULT_MARKET_MAKER_RATE, grid_connected=True), appliance=SimpleAppliance()),


        ],
        config=config, grid_fee_percentage=0, transfer_fee_const=0, external_connection_available=False
    )
    return area
