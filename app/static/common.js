// common.js - small helpers shared by every page.
//
//  * the EN / हिंदी language button in the header
//  * the "Print" button on the printable guide
//
// Other scripts (app.js, stats.js) listen for the "langchange" event to
// re-draw text that JavaScript created.
(function () {
  "use strict";

  var STORAGE_KEY = "scamCheckerLang";

  function getLang() {
    return document.documentElement.getAttribute("data-ui-lang") === "hi" ? "hi" : "en";
  }

  function setLang(lang) {
    if (lang !== "en" && lang !== "hi") return;
    document.documentElement.setAttribute("data-ui-lang", lang);
    document.documentElement.lang = lang;
    try {
      window.localStorage.setItem(STORAGE_KEY, lang);
    } catch (e) {
      /* storage blocked: the choice just won't be remembered */
    }
    // Tell other scripts on the page that the language changed.
    document.dispatchEvent(new CustomEvent("langchange", { detail: { lang: lang } }));
  }

  // Verdict shapes, so a verdict never depends on colour alone:
  // octagon = scam, triangle = suspicious, circle = likely safe.
  // Each is [element, attributes] drawn on a 24x24 grid; the second part is
  // the white mark inside the shape. Colours come from styles.css.
  var SVG_NS = "http://www.w3.org/2000/svg";
  var GLYPHS = {
    scam: [["path", { d: "M8 2h8l6 6v8l-6 6H8l-6-6V8z" }], ["path", { d: "M7.5 12h9" }]],
    suspicious: [["path", { d: "M12 2.5 22.5 21h-21z" }], ["path", { d: "M12 9v5M12 17.5v.01" }]],
    likely_safe: [["circle", { cx: "12", cy: "12", r: "10" }], ["path", { d: "m7.5 12.5 3 3 6-6.5" }]]
  };

  // Returns an <svg> for the verdict (decorative: the word next to it says it).
  function verdictGlyph(verdict) {
    var parts = GLYPHS[verdict];
    if (!parts) return null;
    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", "glyph glyph-" + verdict);
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    parts.forEach(function (part, i) {
      var el = document.createElementNS(SVG_NS, part[0]);
      Object.keys(part[1]).forEach(function (k) {
        el.setAttribute(k, part[1][k]);
      });
      if (i === 1) el.setAttribute("class", "glyph-mark");
      svg.appendChild(el);
    });
    return svg;
  }

  // Put text into an element, setting every "1930" (the cyber-fraud helpline)
  // as the same figure plate used across the site.
  function setTextWithHelpline(el, text) {
    String(text).split(/(\b1930\b)/).forEach(function (part) {
      if (part === "1930") {
        var plate = document.createElement("span");
        plate.className = "helpline";
        plate.textContent = part;
        el.appendChild(plate);
      } else if (part) {
        el.appendChild(document.createTextNode(part));
      }
    });
  }

  // Make these available to the other scripts as window.ScamUI.getLang() etc.
  window.ScamUI = {
    getLang: getLang,
    setLang: setLang,
    verdictGlyph: verdictGlyph,
    setTextWithHelpline: setTextWithHelpline
  };

  document.addEventListener("DOMContentLoaded", function () {
    var toggle = document.getElementById("lang-toggle");
    if (toggle) {
      toggle.addEventListener("click", function () {
        setLang(getLang() === "hi" ? "en" : "hi");
      });
    }

    // Buttons with data-action="print" open the browser's print dialog.
    // (We can't use onclick="..." in the HTML: the security policy blocks inline code.)
    var printButtons = document.querySelectorAll('[data-action="print"]');
    for (var i = 0; i < printButtons.length; i++) {
      printButtons[i].addEventListener("click", function () {
        window.print();
      });
    }
  });
})();
