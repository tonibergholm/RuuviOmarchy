function rows(report, favoritesOnly) {
    return (report && Array.isArray(report.sensors) ? report.sensors : []).filter(function(s) {
        return !favoritesOnly || s.favorite;
    });
}
function primary(sensors, identity) {
    if (identity) return sensors.find(function(s) { return s.id.toUpperCase() === identity.toUpperCase(); }) || null;
    return sensors.find(function(s) { return s.favorite; }) || sensors[0] || null;
}
function value(number, metric) {
    if (number === null || number === undefined || !Number.isFinite(number)) return "—";
    var units = {temperature: "°C", humidity: "%", pressure: " hPa", voltage: " V"};
    return number.toFixed(metric === "voltage" ? 2 : 1) + (units[metric] || "");
}
function metric(candidate) {
    return ["temperature", "humidity", "pressure"].indexOf(candidate) >= 0 ? candidate : "temperature";
}
function age(seconds) {
    if (seconds === null || seconds === undefined) return "No timestamp";
    if (seconds < 60) return Math.floor(seconds) + "s ago";
    if (seconds < 3600) return Math.floor(seconds / 60) + "m ago";
    if (seconds < 86400) return Math.floor(seconds / 3600) + "h ago";
    return Math.floor(seconds / 86400) + "d ago";
}
