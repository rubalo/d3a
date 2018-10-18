from d3a.models.appliance.switchable import SwitchableAppliance
from d3a.models.area import Area
from d3a.models.strategy.storage import StorageStrategy
from d3a.models.strategy.load_hours_fb import LoadHoursStrategy, CellTowerLoadHoursStrategy
from d3a.models.appliance.pv import PVAppliance
from d3a.models.strategy.pv import PVStrategy


def get_setup(config):
    area = Area(
        'Grid',
        [
            Area(
                'Street 1',
                spawn_process=True,
                children=[
                    *[Area(
                        f'S1 House {i}',
                        children=[
                            Area(f'S1 H{i} General Load',
                                 strategy=LoadHoursStrategy(avg_power_W=50,
                                                            hrs_per_day=6,
                                                            hrs_of_day=list(
                                                                range(12, 18)),
                                                            max_energy_rate=35),
                                 appliance=SwitchableAppliance()),
                            Area(f'S1 H{i} Storage1',
                                 strategy=StorageStrategy(battery_capacity=10, initial_capacity=6),
                                 appliance=SwitchableAppliance()),
                            Area(f'S1 H{i} Storage2',
                                 strategy=StorageStrategy(battery_capacity=10, initial_capacity=6),
                                 appliance=SwitchableAppliance()),
                        ]
                    ) for i in range(50)]
                ]
            ),
            Area(
                'Street 2',
                spawn_process=True,
                children=[
                    *[Area(
                        f'S2 House {i}',
                        children=[
                            Area(f'S2 H{i} General Load',
                                 strategy=LoadHoursStrategy(avg_power_W=200,
                                                            hrs_per_day=4,
                                                            hrs_of_day=list(
                                                                range(12, 16)),
                                                            max_energy_rate=35),
                                 appliance=SwitchableAppliance()),
                            Area(f'S2 H{i} Storage1',
                                 strategy=StorageStrategy(battery_capacity=10, initial_capacity=6),
                                 appliance=SwitchableAppliance()),
                            Area(f'S2 H{i} Storage2',
                                 strategy=StorageStrategy(battery_capacity=10, initial_capacity=6),
                                 appliance=SwitchableAppliance()),

                        ]
                    ) for i in range(50)]
                ]
            ),
            Area(
                'Street 3',
                spawn_process=True,
                children=[
                    *[Area(
                        f'S3 House {i}',
                        children=[
                            Area(f'S3 H{i} General Load',
                                 strategy=LoadHoursStrategy(avg_power_W=200,
                                                            hrs_per_day=4,
                                                            hrs_of_day=list(
                                                                range(12, 16)),
                                                            max_energy_rate=35),
                                 appliance=SwitchableAppliance()),
                            Area(f'S3 H{i} PV', strategy=PVStrategy(4, 80),
                                 appliance=PVAppliance()),

                        ]
                    ) for i in range(50)]
                ]
            ),
            Area(
                'Street 4',
                spawn_process=True,
                children=[
                    *[Area(
                        f'S4 House {i}',
                        children=[
                            Area(f'S4 H{i} General Load',
                                 strategy=LoadHoursStrategy(avg_power_W=200,
                                                            hrs_per_day=4,
                                                            hrs_of_day=list(
                                                                range(12, 16)),
                                                            max_energy_rate=35),
                                 appliance=SwitchableAppliance()),
                            Area(f'S4 H{i} PV', strategy=PVStrategy(4, 80),
                                 appliance=PVAppliance()),

                        ]
                    ) for i in range(50)]
                ]
            ),
            Area('Cell Tower', strategy=CellTowerLoadHoursStrategy(avg_power_W=100,
                                                                   hrs_per_day=24,
                                                                   hrs_of_day=list(range(0, 24)),
                                                                   max_energy_rate=35),
                 appliance=SwitchableAppliance())
        ],
        config=config
    )
    return area
