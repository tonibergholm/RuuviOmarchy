# RuuviTags for the Omarchy bar

A native Omarchy 4 / Quickshell shell plugin for [RuuviLinux](https://github.com/tonibergholm/RuuviLinux). Your favorite sensor's reading appears in the bar; click it for all tags, temperature, humidity, pressure, battery voltage and last-seen status. Saved names and favorites are shared with the desktop app.

## Install

Install **RuuviLinux 0.4.0 or newer** first, using its [Omarchy installer](https://github.com/tonibergholm/RuuviLinux#install-on-omarchy--arch-linux). Then:

```sh
omarchy plugin add https://github.com/tonibergholm/RuuviOmarchy.git --enable
```

The widget starts on the left of the bar. Omarchy's plugin controls can move it, disable it, or change its settings. Update with `omarchy plugin update tonibergholm.ruuvi`; remove with `omarchy plugin remove tonibergholm.ruuvi`.

## Use

- Left-click: open the readings panel. Escape or an outside click closes it.
- Right-click or **Open RuuviLinux**: show the existing desktop app for charts, names, favorites, MQTT settings and tag-history downloads.
- Middle-click or **Refresh**: refresh saved readings immediately. Otherwise the widget refreshes every five seconds.
- The bar selects a favorite first, then the first tag by name. Missing measurements show `—`. The bar dims and the panel says **No recent signal** after 30 seconds without a fresh reading; old saved data stays visible.

RuuviLinux's installer enables a separate **ruuvilinux-collector.service** user daemon. It keeps collecting when the desktop app is closed; the widget displays the same SQLite data. The GUI uses that daemon and pauses it briefly during Bluetooth tag-history downloads. No desktop window or Qt process is required for background collection. Opening RuuviLinux reuses an existing window rather than launching another one.

The panel footer shows the collector's live status, or warns when it is offline. When RuuviLinux 0.5 publishes to [Home Assistant](https://www.home-assistant.io/), the footer also shows that status, for example **Home Assistant · publishing**. Home Assistant is configured in RuuviLinux, not in this widget; see its [Home Assistant section](https://github.com/tonibergholm/RuuviLinux#home-assistant-v05). The widget only asks the collector's user-only local socket for status; it never receives broker settings or passwords.

Use `systemctl --user status ruuvilinux-collector.service` to check it, or `systemctl --user disable --now ruuvilinux-collector.service` to stop automatic collection. The user service starts at login; the machine must remain awake and logged in. The widget itself does not scan or connect to tags. Other connected apps must release the tag before downloading its stored history in the desktop app.

## Settings

Settings are inline on the `tonibergholm.ruuvi` entry in `~/.config/omarchy/shell.json`, following the [official shell-plugin contract](https://omarchy.org/manual/shell-plugins/).

| Setting | Default | Meaning |
|---|---|---|
| `metric` | `temperature` | Bar reading: `temperature`, `humidity` or `pressure` |
| `primaryTag` | empty | Sensor MAC for the bar; empty selects a favorite first |
| `showName` | `false` | Include the sensor name in the horizontal bar |
| `favoritesOnly` | `false` | Filter the panel and selection to favorite tags |
| `database` | empty | Custom database path; also passed to the app launcher |

For example, to show humidity with the favorite sensor's name:

```sh
omarchy bar set tonibergholm.ruuvi metric humidity
omarchy bar set tonibergholm.ruuvi showName true
```

The default database is `${XDG_DATA_HOME:-~/.local/share}/ruuvilinux/sensors.sqlite3`. The widget's Python helper opens it **read-only**, returns at most 128 sensors, skips malformed rows and treats missing/future timestamps as stale. A missing database is not created by the reader. RuuviLinux owns Bluetooth/MQTT collection and writes. MQTT readings appear here when the app is connected to your broker; the daemon defaults to Bluetooth after restart. MQTT settings selected in the app continue in the daemon after the window closes. See the RuuviLinux README for unattended broker configuration.

## Development

Python 3's standard library is the only reader dependency. Omarchy provides Quickshell, Qt and its shared themed controls.

```sh
python3 -m unittest discover -s tests -v
node --test tests/model.test.cjs
omarchy plugin validate .
```

The JavaScript tests use Node only for development. Runtime does not require Node. The source includes no install hook, credentials, network fetches or firmware updates. Omarchy shell plugins execute with the user's privileges, as documented by Omarchy.

## License

MIT. This is an independent community project, not an official Ruuvi or Omarchy product. The QML and reader are original code written against Omarchy's public UI contract. No Ruuvi logos, libraries or firmware are distributed here. Icons use the existing Omarchy Nerd Font.
