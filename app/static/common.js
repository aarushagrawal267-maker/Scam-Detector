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

  // Make these available to the other scripts as window.ScamUI.getLang() etc.
  window.ScamUI = { getLang: getLang, setLang: setLang };

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
