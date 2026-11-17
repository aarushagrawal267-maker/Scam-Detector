// lang-init.js - runs in <head>, BEFORE the page is drawn, so the user never
// sees the wrong language flash on screen.
//
// It picks the language in this order:
//   1. what the user chose last time (saved in localStorage on this device)
//   2. the phone/browser language (Hindi phones get Hindi)
//   3. English
// and writes it on <html data-ui-lang="..." lang="...">. The CSS then hides
// every element in the other language (see "Language switching" in styles.css).
(function () {
  var lang = "en";
  try {
    // localStorage can be blocked (private mode), so always wrap it in try/catch.
    var saved = window.localStorage.getItem("scamCheckerLang");
    if (saved === "en" || saved === "hi") {
      lang = saved;
    } else if ((navigator.language || "").toLowerCase().indexOf("hi") === 0) {
      lang = "hi";
    }
  } catch (e) {
    /* storage blocked: keep the default */
  }
  document.documentElement.setAttribute("data-ui-lang", lang);
  document.documentElement.lang = lang;
})();
