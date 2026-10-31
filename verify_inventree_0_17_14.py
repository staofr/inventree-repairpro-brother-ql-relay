"""Runtime compatibility probe executed inside the official InvenTree 0.17.14 image."""

from importlib.metadata import entry_points

import django


django.setup()

from inventree_repairpro_brother.plugin import (  # noqa: E402
    RepairProBrotherQlDriver,
    RepairProBrotherQlPlugin,
)
from plugin.machine.machine_types import LabelPrinterBaseDriver  # noqa: E402


assert RepairProBrotherQlPlugin.MIN_VERSION == '0.17.14'
assert RepairProBrotherQlPlugin.MAX_VERSION == '0.17.14'
assert RepairProBrotherQlPlugin().check_version() is True
assert issubclass(RepairProBrotherQlDriver, LabelPrinterBaseDriver)

plugin_entries = entry_points(group='inventree_plugins')
assert any(entry.value.endswith(':RepairProBrotherQlPlugin') for entry in plugin_entries)

driver = RepairProBrotherQlDriver()
assert driver.MACHINE_SETTINGS['MODEL']['default'] == 'QL-700'
assert driver.MACHINE_SETTINGS['API_TOKEN']['protected'] is True

print('INVENTREE_0_17_14_PLUGIN_IMPORT_OK')
