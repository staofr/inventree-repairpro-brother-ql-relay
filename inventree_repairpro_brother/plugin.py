"""InvenTree 0.17.14 machine driver for the RepairPro Brother QL-700 relay."""

import base64
import io
import uuid

import requests
from django.db import models
from django.utils.translation import gettext_lazy as _
from plugin import InvenTreePlugin
from plugin.builtin.labels.inventree_machine import (
    InvenTreeLabelPlugin,
    get_machine_and_driver,
)
from plugin.machine import BaseMachineType
from plugin.machine.machine_types import LabelPrinterBaseDriver, LabelPrinterMachine
from plugin.mixins import LabelPrintingMixin
from report.models import LabelTemplate
from rest_framework.exceptions import ValidationError

from . import PLUGIN_VERSION


class RepairProBrotherQlPlugin(LabelPrintingMixin, InvenTreePlugin):
    """Register the QL-700 driver and own its label-output lifecycle."""

    AUTHOR = 'MASTER SUN'
    DESCRIPTION = 'Send InvenTree labels to a remote RepairPro Brother QL-700 relay'
    VERSION = PLUGIN_VERSION
    MIN_VERSION = '0.17.14'
    MAX_VERSION = '0.17.14'
    NAME = 'RepairPro Brother QL Relay'
    SLUG = 'repairpro-brother-ql-relay'
    TITLE = 'RepairPro Brother QL-700 Relay'

    PrintingOptionsSerializer = InvenTreeLabelPlugin.PrintingOptionsSerializer

    def print_labels(self, label, output, items, request, **kwargs):
        """Delegate printing and mark this exact output complete after success."""
        printing_options = kwargs.get('printing_options', {})
        machine, driver = get_machine_and_driver(
            printing_options.get('machine', '')
        )

        if (
            machine is None
            or getattr(driver, 'SLUG', None) != RepairProBrotherQlDriver.SLUG
        ):
            raise ValidationError(
                _('Select a machine using the RepairPro Brother QL-700 driver')
            )

        response = InvenTreeLabelPlugin.print_labels(
            self, label, output, items, request, **kwargs
        )

        output.progress = 100
        output.complete = True
        output.save(update_fields=['progress', 'complete'])

        return response


class RepairProBrotherQlDriver(LabelPrinterBaseDriver):
    """Render labels in InvenTree and send PNG data to repairpro-print-server."""

    SLUG = 'repairpro-brother-ql-700'
    NAME = 'RepairPro Brother QL-700 Relay Driver'
    DESCRIPTION = 'Brother QL-700 USB printing through repairpro-print-server'
    USE_BACKGROUND_WORKER = True

    def __init__(self, *args, **kwargs):
        self.MACHINE_SETTINGS = {
            'RELAY_URL': {
                'name': _('Relay URL'),
                'description': _('Full HTTPS URL ending in /api/brother-ql/print'),
                'default': '',
                'required': True,
            },
            'API_TOKEN': {
                'name': _('Relay API Token'),
                'description': _('Bearer token configured by repairpro-print-server'),
                'default': '',
                'required': True,
                'protected': True,
            },
            'PRINTER_NAME': {
                'name': _('Windows Printer Name'),
                'description': _('Exact QL-700 printer name shown by Windows'),
                'default': 'Brother QL-700',
                'required': True,
            },
            'MODEL': {
                'name': _('Printer Model'),
                'description': _('This verified driver is intentionally restricted to QL-700'),
                'choices': [('QL-700', 'QL-700')],
                'default': 'QL-700',
                'required': True,
            },
            'LABEL': {
                'name': _('Label Media'),
                'description': _('Brother DK-11204: 17mm x 54mm die-cut'),
                'choices': [('17x54', '17mm x 54mm die-cut')],
                'default': '17x54',
                'required': True,
            },
            'ROTATION': {
                'name': _('Rotation'),
                'description': _('Rotate the rendered label counter-clockwise before printing'),
                'choices': [('0', '0°'), ('90', '90°'), ('180', '180°'), ('270', '270°')],
                'default': '0',
                'required': True,
            },
            'TIMEOUT_SECONDS': {
                'name': _('Request Timeout'),
                'description': _('Maximum time to wait for the local relay'),
                'validator': int,
                'default': 30,
                'required': True,
            },
            'VERIFY_TLS': {
                'name': _('Verify TLS Certificate'),
                'description': _('Verify the HTTPS certificate presented by the relay domain'),
                'validator': bool,
                'default': True,
                'required': True,
            },
        }
        super().__init__(*args, **kwargs)

    def init_machine(self, machine: BaseMachineType):
        """Mark the configured relay machine as ready for queued printing."""
        machine.set_status(LabelPrinterMachine.MACHINE_STATUS.CONNECTED)

    def restart_machine(self, machine: BaseMachineType):
        """Restore the ready state after InvenTree resets the machine status."""
        self.init_machine(machine)

    def print_label(
        self,
        machine: LabelPrinterMachine,
        label: LabelTemplate,
        item: models.Model,
        **kwargs,
    ) -> None:
        """Render one InvenTree label at 300 DPI and send it to the QL-700 relay."""
        options = kwargs.get('printing_options', {})
        copies = int(options.get('copies', 1))
        if copies < 1 or copies > 10:
            raise ValueError('Brother QL copies must be between 1 and 10')

        label_image = self.render_to_png(label, item, dpi=300)
        if label_image is None:
            raise RuntimeError('InvenTree did not render a PNG label')

        rotation = int(machine.get_setting('ROTATION', 'D') or 0)
        if rotation:
            label_image = label_image.rotate(rotation, expand=True, fillcolor='white')

        image_stream = io.BytesIO()
        label_image.save(image_stream, format='PNG')

        relay_url = str(machine.get_setting('RELAY_URL', 'D') or '').strip()
        api_token = str(machine.get_setting('API_TOKEN', 'D') or '').strip()
        printer_name = str(machine.get_setting('PRINTER_NAME', 'D') or '').strip()
        model = str(machine.get_setting('MODEL', 'D') or '').strip()
        label_media = str(machine.get_setting('LABEL', 'D') or '').strip()
        timeout = int(machine.get_setting('TIMEOUT_SECONDS', 'D') or 30)
        verify_tls = bool(machine.get_setting('VERIFY_TLS', 'D'))

        if not relay_url.endswith('/api/brother-ql/print'):
            raise ValueError('Relay URL must end with /api/brother-ql/print')
        if not api_token:
            raise ValueError('Relay API token is not configured')

        item_name = item._meta.label_lower.replace('.', '-')
        item_pk = getattr(item, 'pk', 'unknown')
        job_id = f'inventree-{item_name}-{item_pk}-{uuid.uuid4().hex}'
        payload = {
            'jobId': job_id,
            'printerName': printer_name,
            'model': model,
            'labelMedia': label_media,
            'copies': copies,
            'imagePngBase64': base64.b64encode(image_stream.getvalue()).decode('ascii'),
        }

        try:
            response = requests.post(
                relay_url,
                json=payload,
                headers={'Authorization': f'Bearer {api_token}'},
                timeout=timeout,
                verify=verify_tls,
            )
            response.raise_for_status()
            result = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise RuntimeError(f'Brother QL relay request failed: {exc}') from exc

        if result.get('ok') is not True or result.get('printed') is not True:
            error = result.get('error') or 'relay did not confirm physical printing'
            raise RuntimeError(f'Brother QL relay rejected the print job: {error}')
