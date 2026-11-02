# Installation and operation

1. In Home Assistant OS open **Settings → Apps** (called **Add-ons** in older
   versions), open the store, then **Repositories** from the menu.
2. Add `https://github.com/5310H/suslik`. The add-on files must be on the
   repository's default branch to appear; a feature branch alone is not installed
   by adding that URL. For pre-merge testing copy `suslik-addon` into HA's local
   add-ons directory and reload the store.
3. Install **Suslik** on an amd64 system. Installation downloads the large CPU
   image with its models. ARM boards are unsupported and will not show the add-on.
4. Under Configuration optionally set `frigate_url`, for example
   `http://frigate-host:5000`. Use a reachable address, not `localhost` (which is
   Suslik's own container). Keep credentials out of the URL.
5. The web port is disabled initially. Under Network assign container port 8199
   a free host port, for example 8199, **only on a trusted LAN**. Save and Start.
   Open Web UI or visit `http://<HA-host>:8199/` and finish Suslik's setup wizard.
   Suslik's UI has no authentication supplied by this add-on. For remote access
   use an authenticated reverse proxy at its own URL root; do not forward this
   port from your router. Ingress is unavailable because root-relative UI URLs
   are incompatible with its path prefix. There is no proxy-header workaround
   in this release.

## Options

```yaml
frigate_url: "http://frigate-host:5000"
poll_interval: 10
cpu_threads: 0
```

Only `frigate_url` is present by default. Empty means keep the current UI/wizard
value; it does not erase an existing URL. `poll_interval` is optional, 5–300
seconds, relevant to polling only. `cpu_threads` is optional, 0–64, with 0 for
Suslik's automatic choice. Omit optional values to keep UI settings. Values
present in add-on options are reapplied at every restart and override the same
UI setting. Save and restart after changing options. Backend is always CPU.

Configure cameras, zones, Frigate username/password and TLS verification,
MQTT and notifications in **Suslik's UI**. Existing source supports Frigate
login on 8971; use HTTPS for credentials. Authentication failures and unreachable
Frigate need correction in those settings; they do not justify deleting /data.
No Supervisor or Home Assistant API token is injected automatically. Existing
MQTT integration and manually configured HA/Telegram features remain available.

## Storage, backups, updates

All settings, credentials, reference faces, learning records and runtime state
are in private `/data`, preserved by Supervisor on restart/recreation/update.
No shared folder or Home Assistant configuration mount is needed. Credentials
and face pictures are sensitive: protect backups and exported diagnostics.
The upstream application controls permissions for files it writes.

Select Suslik when creating a Home Assistant backup. The add-on requests a cold
backup so Supervisor stops it for consistency. Restore the add-on and its data
from that backup to recover it. These backups include caches and may be large.
Suslik's own System page offers portable full backup/restore for moving between
standalone and HAOS deployments; use that rather than replacing options.json.

Before updating make a backup, then choose Update and check the startup log.
Version updates do not delete or reinitialize the config store. Upstream data
migrations may run; restore the pre-update backup for rollback. Suslik does not
update itself. Use Stop/Start/Restart in the add-on panel for service control.

## Troubleshooting and limits

Read the add-on Log tab for validation messages and Suslik's startup self-check.
An invalid options/store JSON or unwritable/full data volume stops startup
without replacing the existing store. Fix the settings or restore a valid backup.
The adapter never prints options or credential values. Treat application debug
logs as sensitive and redact them before sharing.

For connectivity errors check the URL, DNS, port and Frigate availability from
the add-on network. Frigate must be reachable over the network; no host networking
is requested. Optional streams, brokers and notification endpoints also need
connectivity. Failed credentials should be corrected in Suslik, not included in
an issue report. /health is used by Supervisor's optional Watchdog; only enable
Watchdog after initial setup and Frigate connection are working. This is an HTTP
liveness check: upstream /health returns 200 even when JSON `ok` is false.
Inspect that field and the logs for processing and dependency failures.

CPU analysis needs substantial RAM and CPU time; a small HA appliance may not be
suitable. GPU variants and aarch64 require separate dependency/hardware testing.
CI is Docker simulation. Real HAOS install, Frigate recognition and HA backup
restore must be validated before treating this experimental add-on as production.
