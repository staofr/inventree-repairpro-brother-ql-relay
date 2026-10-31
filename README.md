# InvenTree RepairPro Brother QL Relay

Temporary public installation source for the `RepairPro Brother QL Relay`
plugin.

## Compatibility

- InvenTree: exactly `0.17.14`
- Printer: Brother `QL-700`
- Label media: Brother `DK-11204`, `17mm x 54mm die-cut` (`17x54`)
- Rotation: `0°`, `90°`, `180°`, or `270°`
- Transport: authenticated HTTP(S) requests to a separately deployed
  `repairpro-print-server` relay

The plugin deliberately declares both `MIN_VERSION` and `MAX_VERSION` as
`0.17.14`.

## Install

In **InvenTree > Settings > Plugins > Install Plugin**, use:

- Package name: `inventree-repairpro-brother-ql-relay`
- Source URL: the pinned `git+https` URL for the reviewed commit in this
  repository

After installation, enable **RepairPro Brother QL Relay** and create a Label
Printer machine using **RepairPro Brother QL-700 Relay Driver**.

Version `0.1.1` restores the machine to **Connected** after an InvenTree
restart action and sends the selected `17x54` media to the relay. The matching
relay version must support the `labelMedia` request field.

No credentials, relay tokens, printer data, or private RepairPro source are
included in this repository.
