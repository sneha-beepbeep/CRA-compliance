// One-time time-zone banner (option D). Pre-selects the browser's IANA zone.
// No network request: the user still confirms with a normal form POST, so
// nothing here touches the idle timer. Without JS the user picks from the list.
(function () {
  "use strict";
  document.addEventListener("DOMContentLoaded", function () {
    var banner = document.getElementById("tz-banner");
    if (!banner) return;
    var zone = "";
    try { zone = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) { zone = ""; }
    var select = banner.querySelector("select[name=time_zone]");
    var detected = banner.querySelector("input[name=detected]");
    if (!zone || !select) return;
    var match = Array.prototype.some.call(select.options, function (o) { return o.value === zone; });
    if (!match) return;  // not a zone we offer: keep the current (UTC) selection
    select.value = zone;
    if (detected) detected.value = zone;
    var name = document.getElementById("tz-detected-name");
    if (name) name.textContent = zone;
    var note = document.getElementById("tz-detected");
    if (note) note.hidden = false;
  });
})();
