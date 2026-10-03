pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui
import "Model.js" as Model

Panel {
    id: root
    moduleName: "tonibergholm.ruuvi"
    manageIpc: false
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight
    readonly property bool vertical: bar ? bar.vertical : false

    property var report: ({sensors: [], error: "Loading sensors…"})
    readonly property var sensors: Model.rows(report, setting("favoritesOnly", false))
    readonly property var primarySensor: Model.primary(sensors, String(setting("primaryTag", "")))
    readonly property string metric: Model.metric(setting("metric", "temperature"))
    readonly property string readerPath: decodeURIComponent(String(Qt.resolvedUrl("read-sensors.py")).replace(/^file:\/\//, ""))
    readonly property string databasePath: String(setting("database", ""))
    readonly property string executable: Quickshell.env("HOME") + "/.local/bin/ruuvilinux"
    readonly property color foreground: Color.popups.text
    readonly property string fontFamily: Style.font.family

    function refresh() { if (!reader.running) reader.running = true; }
    function launch() {
        var args = [executable];
        if (databasePath) args.push("--database", databasePath);
        Quickshell.execDetached(args);
        close();
    }
    onDatabasePathChanged: refresh()
    Component.onCompleted: {
        refresh();
    }
    Timer { interval: 5000; running: true; repeat: true; onTriggered: root.refresh(); }
    Process {
        id: reader
        command: ["python3", root.readerPath, "--database", root.databasePath]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var parsed = JSON.parse(text);
                    if (parsed.version !== 1 || !Array.isArray(parsed.sensors)) throw new Error("Invalid report");
                    root.report = parsed;
                } catch (error) {
                    root.report = {sensors: [], error: "Could not read sensors. Open RuuviLinux to check."};
                }
            }
        }
    }

    WidgetButton {
        id: button
        anchors.fill: parent
        bar: root.bar
        text: "󰔏 " + (root.primarySensor
              ? ((root.setting("showName", false) && !root.vertical ? root.primarySensor.name + " " : "")
                 + Model.value(root.primarySensor[root.metric], root.metric)) : "Ruuvi")
        dimmed: !root.primarySensor || root.primarySensor.stale || !!root.report.error
        tooltipText: "RuuviTags · click for readings · right-click to open app"
        onPressed: function(mouseButton) {
            if (mouseButton === Qt.RightButton) root.launch(false);
            else if (mouseButton === Qt.MiddleButton) root.refresh();
            else { root.refresh(); root.toggle(); }
        }
    }

    KeyboardPanel {
        id: popup
        anchorItem: button
        owner: root
        bar: root.bar
        open: root.opened
        focusTarget: keyCatcher
        contentWidth: popup.fittedContentWidth(Style.space(380))
        contentHeight: popup.fittedContentHeight(content.implicitHeight, Style.space(540))
        PanelKeyCatcher {
            id: keyCatcher
            anchors.fill: parent
            onCloseRequested: root.close()
            onTabRequested: function(direction) { root.switchPanel(direction); }
            onActivateRequested: root.launch(false)
            Flickable {
                id: flick
                anchors.fill: parent
                clip: true
                contentWidth: width
                contentHeight: content.implicitHeight
                boundsBehavior: Flickable.StopAtBounds
                flickableDirection: Flickable.VerticalFlick
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                Column {
                    id: content
                    width: flick.width
                    spacing: Style.space(12)
                    Text {
                        width: parent.width
                        text: "RuuviTags"
                        textFormat: Text.PlainText
                        color: root.foreground
                        font.family: root.fontFamily
                        font.pixelSize: Style.font.heading
                        font.bold: true
                    }
                    Text {
                        width: parent.width
                        visible: !!root.report.error || root.sensors.length === 0
                        text: root.report.error || (root.setting("favoritesOnly", false) ? "No favorite tags. Mark a favorite in RuuviLinux." : "No tags yet. Open RuuviLinux to start scanning.")
                        textFormat: Text.PlainText
                        wrapMode: Text.WordWrap
                        color: root.foreground
                        font.family: root.fontFamily
                        font.pixelSize: Style.font.body
                    }
                    Repeater {
                        model: root.sensors
                        Rectangle {
                            id: card
                            required property var modelData
                            width: content.width
                            implicitHeight: details.implicitHeight + Style.space(20)
                            color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, .05)
                            radius: Style.cornerRadius
                            Column {
                                id: details
                                x: Style.space(10); y: Style.space(10)
                                width: parent.width - Style.space(20)
                                spacing: Style.space(5)
                                Text {
                                    width: parent.width
                                    text: (card.modelData.favorite ? "★ " : "") + card.modelData.name
                                    textFormat: Text.PlainText
                                    elide: Text.ElideRight
                                    color: root.foreground
                                    font.family: root.fontFamily
                                    font.pixelSize: Style.font.body
                                    font.bold: true
                                }
                                Text {
                                    width: parent.width
                                    text: Model.value(card.modelData.temperature, "temperature") + "   ·   " + Model.value(card.modelData.humidity, "humidity") + "   ·   " + Model.value(card.modelData.pressure, "pressure")
                                    textFormat: Text.PlainText
                                    color: root.foreground
                                    font.family: root.fontFamily
                                    font.pixelSize: Style.font.body
                                }
                                Text {
                                    width: parent.width
                                    text: (card.modelData.stale ? "No recent signal · " : "Live · ") + Model.age(card.modelData.age) + " · " + Model.value(card.modelData.voltage, "voltage") + (card.modelData.rssi !== null ? " · " + card.modelData.rssi + " dBm" : "")
                                    textFormat: Text.PlainText
                                    wrapMode: Text.WordWrap
                                    color: root.foreground
                                    opacity: .65
                                    font.family: root.fontFamily
                                    font.pixelSize: Style.font.bodySmall
                                }
                            }
                        }
                    }
                    Row {
                        spacing: Style.space(8)
                        Button { text: "Open RuuviLinux"; onClicked: root.launch(false); }
                        Button { text: "Refresh"; onClicked: root.refresh(); }
                    }
                    Text {
                        width: parent.width
                        text: "The background collector keeps updating while the app is closed."
                        textFormat: Text.PlainText
                        wrapMode: Text.WordWrap
                        color: root.foreground
                        opacity: .65
                        font.family: root.fontFamily
                        font.pixelSize: Style.font.bodySmall
                    }
                }
            }
        }
    }
}
