// stats.js - the public "Impact so far" dashboard.
//
// It asks the server for anonymous counts (GET /api/stats?public=1) and draws
// simple horizontal bars with plain HTML + CSS (no chart library, so the page
// stays tiny and fast on slow internet).
//
// Every bar has its number written next to it, and all bars are the same
// colour, so the chart works for colour-blind users and screen readers.
(function () {
  "use strict";

  var MIN_FEEDBACK = 20; // below this, a percentage would be misleading

  // Friendly names for the codes the server uses, in both languages.
  var NAMES = {
    verdict: {
      scam: { en: "🔴 SCAM", hi: "🔴 धोखा (स्कैम)" },
      suspicious: { en: "🟡 SUSPICIOUS", hi: "🟡 संदिग्ध" },
      likely_safe: { en: "🟢 LIKELY SAFE", hi: "🟢 शायद सुरक्षित" }
    },
    category: {
      fake_bank_kyc: { en: "Fake bank / KYC alert", hi: "नकली बैंक / KYC मैसेज" },
      otp_theft: { en: "OTP / PIN theft", hi: "OTP / PIN चोरी" },
      lottery_prize: { en: "Fake lottery or prize", hi: "नकली लॉटरी या इनाम" },
      job_offer: { en: "Fake job offer", hi: "नकली नौकरी" },
      family_impersonation: { en: "Someone pretending to be family", hi: "परिवार का सदस्य बनकर धोखा" },
      delivery_fee: { en: "Fake parcel / delivery fee", hi: "नकली पार्सल / डिलीवरी फीस" },
      investment_crypto: { en: "Investment or crypto scam", hi: "निवेश या क्रिप्टो धोखा" },
      romance: { en: "Romance scam", hi: "दोस्ती या प्यार के नाम पर धोखा" },
      government_impersonation: { en: "Fake police / 'digital arrest'", hi: "नकली पुलिस / 'डिजिटल अरेस्ट'" },
      electricity_bill: { en: "Fake electricity bill", hi: "नकली बिजली बिल" },
      loan_offer: { en: "Fake loan offer", hi: "नकली लोन" },
      remote_access: { en: "Screen-sharing app trick", hi: "स्क्रीन शेयर / रिमोट ऐप धोखा" },
      phishing_link: { en: "Dangerous link (phishing)", hi: "खतरनाक लिंक (फ़िशिंग)" },
      unknown: { en: "Type unclear", hi: "प्रकार साफ़ नहीं" },
      none: { en: "No scam type (likely safe)", hi: "कोई प्रकार नहीं (शायद सुरक्षित)" }
    },
    language: {
      en: { en: "English", hi: "अंग्रेज़ी" },
      hi: { en: "Hindi", hi: "हिंदी" },
      hinglish: { en: "Hinglish (Hindi in English letters)", hi: "हिंग्लिश (अंग्रेज़ी अक्षरों में हिंदी)" }
    },
    channel: {
      web: { en: "Website (pasted text)", hi: "वेबसाइट (पेस्ट किया टेक्स्ट)" },
      "web-image": { en: "Website (screenshot)", hi: "वेबसाइट (स्क्रीनशॉट)" },
      bot: { en: "Chat bot", hi: "चैट बॉट" },
      telegram: { en: "Chat bot (Telegram)", hi: "चैट बॉट (Telegram)" },
      "telegram-image": { en: "Chat bot (screenshot)", hi: "चैट बॉट (स्क्रीनशॉट)" }
    },
    // The server groups tiny counts together under this key (privacy).
    other: { en: "Other (small groups hidden)", hi: "अन्य (छोटे समूह छुपाए गए)" }
  };

  var TEXT = {
    loading: { en: "Loading the numbers…", hi: "आंकड़े लोड हो रहे हैं…" },
    error: { en: "Could not load the numbers. Please try again later.", hi: "आंकड़े लोड नहीं हो सके। कृपया बाद में फिर कोशिश करें।" },
    empty: { en: "No checks yet.", hi: "अभी तक कोई जांच नहीं।" },
    fewer: { en: "< 5", hi: "5 से कम" },
    notEnough: {
      en: "Not enough feedback yet ({n} answers so far). We show a percentage after {min} answers.",
      hi: "अभी पर्याप्त जवाब नहीं हैं (अब तक {n} जवाब)। {min} जवाबों के बाद प्रतिशत दिखाया जाएगा।"
    },
    accuracy: {
      en: "{pct}% of {n} people who answered said the result was right.",
      hi: "जवाब देने वाले {n} लोगों में से {pct}% ने कहा कि नतीजा सही था।"
    }
  };

  var data = null; // the last response from the server, kept for re-drawing

  function lang() {
    return window.ScamUI ? window.ScamUI.getLang() : "en";
  }

  function fmt(n) {
    // Indian digit grouping, e.g. 1,00,000
    return Number(n || 0).toLocaleString("en-IN");
  }

  function nameFor(group, key) {
    if (key.indexOf("other") === 0) return NAMES.other[lang()];
    var table = NAMES[group] || {};
    return table[key] ? table[key][lang()] : key;
  }

  function fill(template, values) {
    return template.replace(/\{(\w+)\}/g, function (_, k) {
      return values[k];
    });
  }

  function setText(id, value) {
    document.getElementById(id).textContent = value;
  }

  // Draw one list of bars. `rows` is an array of [label, count].
  function drawBars(listId, rows) {
    var list = document.getElementById(listId);
    while (list.firstChild) list.removeChild(list.firstChild);

    if (!rows.length) {
      var li = document.createElement("li");
      li.className = "empty";
      li.textContent = TEXT.empty[lang()];
      list.appendChild(li);
      return;
    }

    var total = rows.reduce(function (sum, r) { return sum + r[1]; }, 0);
    var max = Math.max.apply(null, rows.map(function (r) { return r[1]; }));

    rows.forEach(function (row) {
      var item = document.createElement("li");
      item.className = "bar-row";

      var label = document.createElement("div");
      label.className = "bar-label";
      var name = document.createElement("span");
      name.textContent = row[0];
      var count = document.createElement("span");
      var pct = total ? Math.round((row[1] / total) * 100) : 0;
      count.textContent = fmt(row[1]) + " (" + pct + "%)";
      label.appendChild(name);
      label.appendChild(count);

      // The bar itself is only decoration; the number above says it in words.
      var track = document.createElement("div");
      track.className = "bar-track";
      track.setAttribute("aria-hidden", "true");
      var bar = document.createElement("div");
      bar.className = "bar-fill";
      // Setting .style from JavaScript is allowed by our security policy
      // (only style="" written inside the HTML file is blocked).
      bar.style.width = (max ? (row[1] / max) * 100 : 0) + "%";
      track.appendChild(bar);

      item.appendChild(label);
      item.appendChild(track);
      list.appendChild(item);
    });
  }

  // Turn {"scam": 4, "suspicious": 2} into [["🔴 SCAM", 4], ...]
  function rowsFrom(obj, group) {
    return Object.keys(obj || {}).map(function (key) {
      return [nameFor(group, key), obj[key]];
    });
  }

  function shortDate(iso) {
    var p = iso.split("-"); // "2026-11-17" -> local date (avoids time-zone shifts)
    var d = new Date(Number(p[0]), Number(p[1]) - 1, Number(p[2]));
    return d.toLocaleDateString(lang() === "hi" ? "hi-IN" : "en-IN", { day: "numeric", month: "short" });
  }

  // A verdict tile: the public stats hide groups smaller than 5 (privacy), so a
  // missing number does not always mean zero. Say "fewer than 5" in that case.
  function verdictTile(verdicts, key) {
    if (verdicts[key] !== undefined) return fmt(verdicts[key]);
    var hidden = Object.keys(verdicts).some(function (k) { return k.indexOf("other") === 0; });
    return hidden ? TEXT.fewer[lang()] : "0";
  }

  function render() {
    if (!data) return;
    var verdicts = data.by_verdict || {};
    setText("t-total", fmt(data.total_checks));
    setText("t-scam", verdictTile(verdicts, "scam"));
    setText("t-sus", verdictTile(verdicts, "suspicious"));
    setText("t-workshops", fmt(data.workshops && data.workshops.count));
    setText("t-people", fmt(data.workshops && data.workshops.participants));

    drawBars("bars-verdict", rowsFrom(verdicts, "verdict"));
    drawBars("bars-category", rowsFrom(data.by_category, "category"));
    drawBars("bars-language", rowsFrom(data.by_language, "language"));
    drawBars("bars-channel", rowsFrom(data.by_channel, "channel"));
    drawBars(
      "bars-day",
      (data.by_day || []).slice(-14).map(function (d) {
        return [shortDate(d.date), d.count];
      })
    );

    var weekly = data.weekly_bot_users || [];
    document.getElementById("weekly-section").hidden = weekly.length === 0;
    drawBars(
      "bars-weekly",
      weekly.map(function (w) {
        return [w.week, w.users];
      })
    );

    var n = data.user_reported_accuracy_n || 0;
    var fb = document.getElementById("feedback-text");
    if (n < MIN_FEEDBACK || data.user_reported_accuracy === null) {
      fb.textContent = fill(TEXT.notEnough[lang()], { n: fmt(n), min: MIN_FEEDBACK });
    } else {
      fb.textContent = fill(TEXT.accuracy[lang()], {
        pct: Math.round(data.user_reported_accuracy * 100),
        n: fmt(n)
      });
    }
  }

  function load() {
    var status = document.getElementById("stats-status");
    status.textContent = TEXT.loading[lang()];
    status.classList.add("loading");
    fetch("/api/stats?public=1")
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (json) {
        data = json;
        status.textContent = "";
        document.getElementById("stats-body").hidden = false;
        render();
      })
      .catch(function () {
        status.textContent = TEXT.error[lang()];
      })
      .finally(function () {
        status.classList.remove("loading");
      });
  }

  document.addEventListener("DOMContentLoaded", load);
  document.addEventListener("langchange", render); // re-draw names in the new language
})();
