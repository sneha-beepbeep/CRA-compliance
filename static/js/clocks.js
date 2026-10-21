// Clock strip behaviour (about 100 lines; technical plan "Architecture").
// * Countdowns come from server time; between polls they count down from the
//   last known server time (design 11.1 "Connection lost").
// * Tab title shows the next deadline (OQ-D11): passive display, not an alert.
// * Device clock differing from the server by more than 60 s is pointed out.
// * A polite live region announces tier changes only, never every minute.
(function () {
  "use strict";
  var offsetMs = 0;            // server time minus device time
  var lastSync = null;
  var tiers = {};

  function fmt(mins) {
    var d = Math.floor(mins / 1440), h = Math.floor((mins % 1440) / 60), m = mins % 60;
    var pad = function (n) { return (n < 10 ? "0" : "") + n; };
    if (d) return d + "d " + pad(h) + "h " + pad(m) + "m";
    if (h) return h + "h " + pad(m) + "m";
    return m + "m";
  }

  function tick() {
    var now = Date.now() + offsetMs;
    document.querySelectorAll("[data-due]").forEach(function (el) {
      var due = Date.parse(el.getAttribute("data-due"));
      var mins = Math.floor((due - Math.floor(now / 60000) * 60000) / 60000);
      el.textContent = mins >= 0 ? fmt(mins) : "Overdue by " + fmt(-mins);
    });
  }

  function adopt(root) {
    var strip = root.querySelector ? (root.id === "clock-strip" ? root : root.querySelector("#clock-strip")) : null;
    if (!strip) return;
    var server = Date.parse(strip.getAttribute("data-server-now"));
    if (!isNaN(server)) {
      offsetMs = server - Date.now();
      lastSync = new Date(server);
      var skew = document.getElementById("clock-skew");
      if (skew) skew.hidden = Math.abs(offsetMs) <= 60000;
    }
    var title = strip.getAttribute("data-tab-title");
    if (title) document.title = title;
    var live = document.getElementById("clock-live");
    strip.querySelectorAll("[data-event][data-tier]").forEach(function (li) {
      var id = li.getAttribute("data-event"), tier = li.getAttribute("data-tier");
      if (tiers[id] && tiers[id] !== tier && live) {
        live.textContent = li.getAttribute("data-announce") || "";
      }
      tiers[id] = tier;
    });
    var note = document.getElementById("sync-note");
    if (note) note.hidden = true;
    tick();
  }

  document.addEventListener("DOMContentLoaded", function () {
    adopt(document);
    setInterval(tick, 30000);
  });
  document.body && document.body.addEventListener("htmx:afterSwap", function (e) { adopt(e.detail.target); });
  document.addEventListener("htmx:afterSwap", function (e) { adopt(e.detail.target); });
  document.addEventListener("htmx:sendError", function () {
    var note = document.getElementById("sync-note");
    if (note && lastSync) {
      var hh = ("0" + lastSync.getUTCHours()).slice(-2), mm = ("0" + lastSync.getUTCMinutes()).slice(-2);
      note.textContent = "Not synced since " + hh + ":" + mm + " UTC – reconnecting";
      note.hidden = false;
    }
  });
  document.addEventListener("htmx:responseError", function (e) {
    if (e.detail.xhr && e.detail.xhr.status === 401) {
      document.title = "Signed out – deadlines hidden";
      document.body.innerHTML = "";
      window.location.assign("/signed-out/?reason=expired");
    }
  });
})();
