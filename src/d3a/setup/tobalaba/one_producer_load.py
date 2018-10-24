from d3a.models.appliance.simple import SimpleAppliance
from d3a.models.appliance.switchable import SwitchableAppliance
from d3a.models.area import Area
from d3a.models.strategy.finite_power_plant import FinitePowerPlant
from d3a.models.strategy.permanent import PermanentLoadStrategy
# from d3a.models.appliance.pv import PVAppliance
# from d3a.models.strategy.pv import PVStrategy


def get_setup(config):
    area = Area(
        'Grid',
        [
            Area('Cell Tower', strategy=PermanentLoadStrategy(),
                 appliance=SwitchableAppliance()),
            Area('Commercial Energy Producer',
                 strategy=FinitePowerPlant(energy_rate=30,
                                           max_available_power_kW=100),
                 appliance=SimpleAppliance()
                 ),

        ],
        config=config
    )
    return area
