"""
Copyright 2018 Grid Singularity
This file is part of D3A.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from typing import Dict  # NOQA
from pendulum import duration
from itertools import product
from d3a.models.strategy.load_hours import LoadHoursStrategy  # NOQA
from d3a_interface.constants_limits import GlobalConfig
from d3a.constants import DATE_TIME_FORMAT, FLOATING_POINT_TOLERANCE  # NOQA
from d3a_interface.sim_results.aggregate_results import merge_unmatched_load_results_to_global

DATE_HOUR_FORMAT = "YYYY-MM-DDTHH"


def get_number_of_unmatched_loads(indict):
    # use root dict:
    root = indict[list(indict.keys())[0]]
    no_ul = 0
    for parent in root.values():
        for value in parent['unmatched_loads'].values():
            no_ul += value['unmatched_count']
    return no_ul


def hour_list():
    if GlobalConfig.sim_duration > duration(days=1):
        return [GlobalConfig.start_date.add(days=day, hours=hour)
                for day, hour in product(range(GlobalConfig.sim_duration.days), range(24))]
    else:
        return [GlobalConfig.start_date.add(hours=hour) for hour in range(24)]


class ExportUnmatchedLoads:
    def __init__(self, area):
        self.hour_list = hour_list()
        self.name_uuid_map = {area['name']: area['uuid']}
        self.name_type_map = {area['name']: area['type']}
        self.area = area
        self.load_count = 0
        self.count_load_devices_in_setup(self.area)

    # @property
    # def latest_time_slot(self):
    #     return self.area.current_market.time_slot \
    #         if self.area.current_market is not None else self.hour_list[-1]

    def count_load_devices_in_setup(self, area):
        for child in area['children']:
            if child['type'] == "LoadHoursStrategy":
                self.load_count += 1
            if child['children']:
                self.count_load_devices_in_setup(child)

    def get_current_market_results(self, area={}, core_stats={}, all_past_markets=False):
        unmatched_loads = self.arrange_output(self.append_device_type(
            self.expand_to_ul_to_hours(
                self.expand_ul_to_parents(
                    self.find_unmatched_loads(area, core_stats, {},
                                              all_past_markets)[area['name']],
                    area['name'], {}
                ), all_past_markets)), area)

        return unmatched_loads, self.change_name_to_uuid(unmatched_loads)

    def find_unmatched_loads(self, area, core_stats, indict, all_past_markets: bool):
        """
        Aggregates list of times for each unmatched time slot for each load
        """
        indict[area['name']] = {}
        for child in area['children']:
            self.name_uuid_map[child['name']] = child['uuid']
            self.name_type_map[child['name']] = child['type']
            if child['children']:
                indict[area['name']] = self.find_unmatched_loads(
                    child, core_stats, indict[area['name']], all_past_markets
                )
            else:
                if child['type'] in ["LoadHoursStrategy", "DefinedLoadStrategy",
                                     "CellTowerLoadHoursStrategy"] and \
                        core_stats[child['uuid']] != {}:
                    indict[area['name']][child['name']] = \
                        self._calculate_unmatched_loads_leaf_area(child, core_stats)
        return indict

    @classmethod
    def _calculate_unmatched_loads_leaf_area(cls, area, core_stats):
        """
        actually determines the unmatched loads
        """
        unmatched_times = []
        time_slot = list(core_stats[area['uuid']].keys())[0]

        desired_energy_kWh = core_stats[area['uuid']][time_slot]['load_profile_kWh']
        traded_energy_kWh = sum(trade['energy']
                                for trade in core_stats[area['uuid']][time_slot]['trades'])
        deficit = desired_energy_kWh + traded_energy_kWh
        if deficit > FLOATING_POINT_TOLERANCE:
            unmatched_times.append(time_slot)
        return {"unmatched_times": unmatched_times}

    def change_name_to_uuid(self, indict):
        """
        postprocessing: changing area names to uuids
        """
        new = {}
        for k, v in indict.items():
            new[self.name_uuid_map[k]] = v
        return new

    def _accumulate_all_uls_in_branch(self, subdict, unmatched_list) -> list:
        """
        aggregate all unmatched loads times in one branch into one list
        """
        for key in subdict.keys():
            if key == "unmatched_times":
                return unmatched_list + subdict[key]
            else:
                unmatched_list = self._accumulate_all_uls_in_branch(subdict[key], unmatched_list)
        return unmatched_list

    def expand_ul_to_parents(self, subdict, parent_name, outdict):
        """
        expand unmatched loads times to all nodes including all unmatched loads times of the
        sub branch
        """

        for node_name, subsubdict in subdict.items():
            if isinstance(subsubdict, dict):
                # nodes
                ul_list = self._accumulate_all_uls_in_branch(subsubdict, [])
                sub_ul = sorted(list(set(ul_list)))
                if parent_name in outdict:
                    outdict[parent_name].update({node_name: sub_ul})
                else:
                    outdict[parent_name] = {node_name: sub_ul}
                outdict.update(self.expand_ul_to_parents(subsubdict, node_name, {}))
            else:
                # leafs
                outdict[parent_name] = {parent_name: subsubdict}

        return outdict

    @classmethod
    def _get_hover_info(cls, indict, slot_time):
        """
        returns dict of UL for each subarea for the hover the UL graph
        """
        hover_dict = {}
        ul_count = 0
        for child_name, child_ul_list in indict.items():
            for time in child_ul_list:
                if int(time[11:13]) == int(slot_time[11:13]) and \
                   int(time[8:10]) == int(slot_time[8:10]) and \
                   int(time[5:7]) == int(slot_time[5:7]) and \
                   int(time[:4]) == int(slot_time[:4]):
                    ul_count += 1
                    if child_name in hover_dict:
                        hover_dict[child_name].append(time)
                    else:
                        hover_dict[child_name] = [time]
        if hover_dict == {}:
            return {"unmatched_count": 0}
        else:
            return {"unmatched_count": ul_count, "unmatched_times": hover_dict}

    def expand_to_ul_to_hours(self, indict, all_past_markets=True):
        """
        Changing format to dict of hour time stamps
        """
        outdict = {}
        for node_name, subdict in indict.items():
            # print(f"node_name: {node_name}")
            # print(f"subdict: {subdict}")
            if all_past_markets:
                outdict[node_name] = {}
                for hour_time in self.hour_list:
                    if hour_time <= self.latest_time_slot:
                        outdict[node_name][hour_time] = \
                            self._get_hover_info(subdict, hour_time)
            else:
                outdict[node_name] = {}
                outdict[node_name][self.latest_time_slot] = \
                    self._get_hover_info(subdict, self.latest_time_slot)
        return outdict

    def append_device_type(self, indict):
        outdict = {}
        for name, unmatched_times in indict.items():
            outdict[name] = {
                "unmatched_loads": unmatched_times,
                "type": self.name_type_map[name]
            }
        return outdict

    def arrange_output(self, indict, area):
        if area['children']:
            indict[area['name']] = {}
            for child in area['children']:
                if child['children'] or \
                        child['type'] in ["LoadHoursStrategy", "DefinedLoadStrategy",
                                          "CellTowerLoadHoursStrategy"]:
                    if child['name'] in indict:
                        indict[area['name']][child['name']] = indict[child['name']]
                    self.arrange_output(indict, child)
        return indict


class MarketUnmatchedLoads:
    """
    This class is used for storing the current unmatched load results and to update them
    with new results whenever a market has been completed. It works in conjunction
    to the ExportUnmatchedLoads class, since it depends on the latter for calculating
    the unmatched loads for a market slot.
    """
    def __init__(self, area):
        self.unmatched_loads = {}
        self.last_unmatched_loads = {}
        self.export_unmatched_loads = ExportUnmatchedLoads(area)

    def write_none_to_unmatched_loads(self, area):
        self.unmatched_loads[area['name']] = None
        self.last_unmatched_loads[area['uuid']] = None
        for child in area['children']:
            self.write_none_to_unmatched_loads(child)

    def merge_unmatched_loads(self, current_results):
        """
        Merges unmatched loads for the last market to the global unmatched loads
        :param current_results: Output from ExportUnmatchedLoads.get_current_market_results()
        :param current_results_uuid: Output from ExportUnmatchedLoads.get_current_market_results()
        :return: Tuple with unmatched loads using area names and uuids
        """
        self.unmatched_loads = merge_unmatched_load_results_to_global(
            current_results, self.unmatched_loads
        )

    def update_unmatched_loads(self, area={}, core_stats={}, current_market_time_slot=None):
        if current_market_time_slot is None:
            return
        self.export_unmatched_loads.latest_time_slot = current_market_time_slot
        if self.export_unmatched_loads.load_count == 0:
            self.write_none_to_unmatched_loads(area)
        else:
            current_results, current_results_uuid = \
                self.export_unmatched_loads.get_current_market_results(area, core_stats)

            self.last_unmatched_loads = current_results_uuid
            self.merge_unmatched_loads(current_results)

        # print(f"self.last_unmatched_load: {self.last_unmatched_loads}")
        # print(f"self.unmatched_loads: {self.unmatched_loads}")
