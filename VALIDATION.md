# Validation — October 7, 2026

## 0.2.0 — collector and Home Assistant status

- Eight Python reader tests and three JavaScript model tests passed locally;
  Omarchy's plugin validator accepted the manifest. New tests cover an offline
  collector, Home Assistant publishing status, an older collector without that
  field and malformed socket replies.
- The reader queried the actual running RuuviLinux 0.4 collector on this
  machine and reported its scanning status with no Home Assistant field. End-to-end
  Home Assistant publishing was validated in RuuviLinux 0.5 against a temporary
  Home Assistant container; see RuuviLinux `VALIDATION.md`.

## 0.1.0 — October 3, 2026

- Four Python reader tests and two JavaScript model tests passed locally and in
  [public CI](https://github.com/tonibergholm/RuuviOmarchy/actions/runs/37119478941).
  They cover read-only SQLite access, missing databases, malformed readings,
  stale timestamps, favorite selection and display formatting.
- Omarchy's official plugin validator accepted the manifest. The plugin was
  installed and enabled through the official CLI on the actual Omarchy 4
  machine. Existing bar entries and user configuration were retained.
- The user moved the widget to the center of the bar. Its dropdown rendered
  correctly there, showing a physical tag's live measurements, saved name,
  favorite, freshness, battery voltage and signal strength.
- Activating the dropdown's app launcher with Enter opened RuuviLinux; repeating
  it reused the same window and process. The app showed the background collector
  status and existing charts and tag-history download control.
- Closing the desktop window left the collector running. Fresh BLE readings
  and minute-spaced history continued without a desktop app process.
- Runtime screenshots contain personal sensor data and are not published.
  Visual verification covered the actual horizontal bar; vertical layouts and
  multiple monitors were not physically tested.

RuuviLinux 0.4.0 provides the independent collector and shared database. The
widget reads data only; it does not own Bluetooth or MQTT connections.
