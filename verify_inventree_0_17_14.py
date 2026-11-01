"""Runtime compatibility probe executed inside the official InvenTree 0.17.14 image."""

from importlib.metadata import entry_points
from unittest.mock import patch

import django
from django.http import JsonResponse


django.setup()

from inventree_repairpro_brother.plugin import (  # noqa: E402
    RepairProBrotherQlDriver,
    RepairProBrotherQlPlugin,
)
from plugin.builtin.labels.inventree_machine import InvenTreeLabelPlugin  # noqa: E402
from plugin.machine.machine_types import LabelPrinterBaseDriver  # noqa: E402
from plugin.mixins import LabelPrintingMixin  # noqa: E402


assert RepairProBrotherQlPlugin.MIN_VERSION == '0.17.14'
assert RepairProBrotherQlPlugin.MAX_VERSION == '0.17.14'
assert RepairProBrotherQlPlugin().check_version() is True
assert issubclass(RepairProBrotherQlDriver, LabelPrinterBaseDriver)
assert issubclass(RepairProBrotherQlPlugin, LabelPrintingMixin)

plugin_entries = entry_points(group='inventree_plugins')
assert any(entry.value.endswith(':RepairProBrotherQlPlugin') for entry in plugin_entries)

driver = RepairProBrotherQlDriver()
assert driver.MACHINE_SETTINGS['MODEL']['default'] == 'QL-700'
assert driver.MACHINE_SETTINGS['LABEL']['default'] == '17x54'
assert driver.MACHINE_SETTINGS['ROTATION']['default'] == '0'
assert driver.MACHINE_SETTINGS['API_TOKEN']['protected'] is True
assert callable(driver.restart_machine)


class OutputProbe:
    """Minimal LabelOutput stand-in for the completion-state regression probe."""

    progress = 0
    complete = False

    def __init__(self):
        self.saved_fields = None

    def save(self, *, update_fields):
        self.saved_fields = update_fields


output = OutputProbe()
plugin = RepairProBrotherQlPlugin()

with (
    patch(
        'inventree_repairpro_brother.plugin.get_machine_and_driver',
        return_value=(object(), driver),
    ),
    patch.object(
        InvenTreeLabelPlugin,
        'print_labels',
        return_value=JsonResponse({'success': True}),
    ),
):
    plugin.print_labels(
        label=object(),
        output=output,
        items=[object()],
        request=object(),
        printing_options={'machine': 'probe'},
    )

assert output.progress == 100
assert output.complete is True
assert output.saved_fields == ['progress', 'complete']

print('INVENTREE_0_17_14_PLUGIN_IMPORT_OK')
