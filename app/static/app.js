// app.js - the "Check a message" page.
//
// What it does:
//   1. sends the pasted text (or a screenshot) to our server's API
//   2. shows the verdict, the reasons, the link check and the advice
//   3. sends "Was this right? Yes/No" feedback (counts only, no message text)
//
// Safety rule used everywhere below: text that comes from the server is put on
// the page with .textContent, NEVER .innerHTML. That way, even if a scam
// message contains HTML or <script> tags, the browser shows it as plain text
// and never runs it (this prevents "XSS" attacks).
(function () {
  "use strict";

  // ------------------------------------------------------------------
  // Settings you can change
  // ------------------------------------------------------------------
  var CONFIG = {
    // Put your Telegram bot link here, for example "https://t.me/YourBotName".
    // While it is empty, the "Open the chat bot" button stays hidden.
    TELEGRAM_BOT_URL: "",
    MAX_TEXT_CHARS: 10000,          // the server refuses anything longer
    MAX_IMAGE_BYTES: 6 * 1024 * 1024, // 6 MB, same limit as the server
    TIMEOUT_MS: 45000               // give up after 45 seconds
  };

  // Words that JavaScript writes on the page, in both languages.
  var STRINGS = {
    en: {
      checking: "Checking the message…",
      reading: "Reading your screenshot… this can take up to 30 seconds.",
      done: "Done. The result is below.",
      empty: "Please paste a message first.",
      tooLong: "This message is very long. Please paste only the suspicious part.",
      tooMany: "Too many checks in a short time. Please wait one minute and try again.",
      noOcr: "Reading screenshots is not available right now. Please copy and paste the message text instead.",
      tooBig: "That picture is too big. Please use a screenshot smaller than 6 MB.",
      noText: "We could not find any text in that picture. Please paste the message text instead.",
      badType: "Please choose a PNG or JPG screenshot.",
      badImage: "We could not read that picture. Please try a clearer screenshot, or paste the text.",
      network: "Could not connect. Please check your internet and try again.",
      generic: "Something went wrong. Please try again.",
      cleared: "Cleared. You can paste a new message.",
      noFlags: "No specific warning signs found.",
      type: "Type",
      thisLink: "This link ",
      officialSite: "This looks like the company's real website. Still, open the website yourself instead of using a link from a message.",
      thanks: "Thank you! Your answer helps us improve.",
      fbError: "Sorry, we could not save your answer.",
      langNote: "This result is in Hindi. Press Check again to see it in English."
    },
    hi: {
      checking: "मैसेज की जांच हो रही है…",
      reading: "आपका स्क्रीनशॉट पढ़ा जा रहा है… इसमें 30 सेकंड तक लग सकते हैं।",
      done: "हो गया। नतीजा नीचे है।",
      empty: "पहले कोई मैसेज पेस्ट करें।",
      tooLong: "यह मैसेज बहुत लंबा है। कृपया सिर्फ़ संदिग्ध हिस्सा पेस्ट करें।",
      tooMany: "कम समय में बहुत ज़्यादा जांच हो गईं। एक मिनट रुककर फिर कोशिश करें।",
      noOcr: "अभी स्क्रीनशॉट पढ़ने की सुविधा उपलब्ध नहीं है। कृपया मैसेज का टेक्स्ट कॉपी करके पेस्ट करें।",
      tooBig: "यह तस्वीर बहुत बड़ी है। कृपया 6 MB से छोटा स्क्रीनशॉट इस्तेमाल करें।",
      noText: "इस तस्वीर में कोई टेक्स्ट नहीं मिला। कृपया मैसेज का टेक्स्ट पेस्ट करें।",
      badType: "कृपया PNG या JPG स्क्रीनशॉट चुनें।",
      badImage: "यह तस्वीर पढ़ी नहीं जा सकी। साफ़ स्क्रीनशॉट लें या टेक्स्ट पेस्ट करें।",
      network: "कनेक्ट नहीं हो सका। अपना इंटरनेट जांचें और फिर कोशिश करें।",
      generic: "कुछ गड़बड़ हो गई। कृपया फिर कोशिश करें।",
      cleared: "साफ़ हो गया। आप नया मैसेज पेस्ट कर सकते हैं।",
      noFlags: "कोई खास चेतावनी का निशान नहीं मिला।",
      type: "प्रकार",
      thisLink: "यह लिंक ",
      officialSite: "यह कंपनी की असली वेबसाइट लगती है। फिर भी मैसेज के लिंक की जगह वेबसाइट खुद खोलें।",
      thanks: "धन्यवाद! आपके जवाब से हमें सुधार करने में मदद मिलती है।",
      fbError: "माफ़ करें, आपका जवाब सेव नहीं हो सका।",
      langNote: "यह नतीजा अंग्रेज़ी में है। हिंदी में देखने के लिए फिर से 'जांचें' दबाएं।"
    }
  };

  // Remember the last result so feedback and the language note can use it.
  var last = { verdict: null, lang: null };

  // Short helper: find an element by its id.
  function $(id) {
    return document.getElementById(id);
  }

  function uiLang() {
    return window.ScamUI ? window.ScamUI.getLang() : "en";
  }

  // Get a word in the current page language.
  function s(key, lang) {
    var table = STRINGS[lang || uiLang()] || STRINGS.en;
    return table[key] || STRINGS.en[key] || "";
  }

  // ------------------------------------------------------------------
  // Status line, errors and the "busy" state
  // ------------------------------------------------------------------
  function setStatus(message, loading) {
    var el = $("status");
    el.textContent = message || "";
    el.classList.toggle("loading", !!loading);
  }

  function showError(message) {
    var el = $("error");
    el.textContent = message;
    el.hidden = false;
    setStatus("");
  }

  function hideError() {
    $("error").hidden = true;
    $("error").textContent = "";
  }

  // While a check is running, disable the buttons so nobody presses twice.
  function setBusy(busy) {
    $("check-btn").disabled = busy;
    $("clear-btn").disabled = busy;
    $("screenshot").disabled = busy;
  }

  // Turn an HTTP error code from the server into a friendly sentence.
  function messageForStatus(status, isImage) {
    if (status === 429) return s("tooMany");
    if (status === 501) return s("noOcr");
    if (status === 413) return s("tooBig");
    if (status === 415) return s("badType");
    if (status === 422) return isImage ? s("noText") : s("tooLong");
    if (status === 400) return isImage ? s("badImage") : s("empty");
    return s("generic");
  }

  // fetch() with a time limit, so a slow connection doesn't hang forever.
  function fetchWithTimeout(url, options) {
    var controller = new AbortController();
    var timer = setTimeout(function () {
      controller.abort();
    }, CONFIG.TIMEOUT_MS);
    options.signal = controller.signal;
    return fetch(url, options).finally(function () {
      clearTimeout(timer);
    });
  }

  // ------------------------------------------------------------------
  // Showing the result
  // ------------------------------------------------------------------
  function clearChildren(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  function addItem(list, text) {
    var li = document.createElement("li");
    li.textContent = text;
    list.appendChild(li);
    return li;
  }

  function renderResult(result, extractedText) {
    var lang = result.reply_language === "hi" ? "hi" : "en";
    last.verdict = result.verdict;
    last.lang = lang;

    // 1. Verdict box: colour comes from the CSS class, plus emoji + word.
    var box = $("verdict");
    box.className = "verdict verdict-" + result.verdict;
    box.lang = lang;
    $("verdict-emoji").textContent = result.emoji || "";
    $("verdict-label").textContent = result.label || "";
    $("verdict-headline").textContent = result.headline || "";
    var cat = $("verdict-category");
    if (result.category_label) {
      cat.textContent = s("type", lang) + ": " + result.category_label;
      cat.hidden = false;
    } else {
      cat.hidden = true;
    }

    // 2. Text read from a screenshot (so the user can see what we checked).
    if (extractedText) {
      $("extracted-text").textContent = extractedText;
      $("extracted-box").hidden = false;
    } else {
      $("extracted-box").hidden = true;
    }

    // 3. Red flags ("Why?")
    var flags = $("flags");
    clearChildren(flags);
    flags.lang = lang;
    var redFlags = result.red_flags || [];
    if (redFlags.length === 0) {
      addItem(flags, s("noFlags", lang));
    } else {
      redFlags.forEach(function (flag) {
        addItem(flags, flag.text);
      });
    }

    // 4. Links. The server already "defanged" them (hxxp://example[.]com),
    //    and we show them as plain text, never as clickable links.
    var links = $("links");
    clearChildren(links);
    links.lang = lang;
    var linkData = result.links || [];
    linkData.forEach(function (link) {
      var li = document.createElement("li");
      li.className = "link-item risk-" + (link.risk || "low");

      var url = document.createElement("p");
      url.className = "link-url";
      url.textContent = link.url;
      li.appendChild(url);

      var risk = document.createElement("p");
      var strong = document.createElement("strong");
      strong.textContent = link.risk_label || link.risk;
      risk.appendChild(strong);
      li.appendChild(risk);

      var reasons = link.reason_text || [];
      if (reasons.length) {
        var ul = document.createElement("ul");
        reasons.forEach(function (reason) {
          addItem(ul, s("thisLink", lang) + reason);
        });
        li.appendChild(ul);
      }
      if (link.official_domain) {
        var note = document.createElement("p");
        note.textContent = s("officialSite", lang);
        li.appendChild(note);
      }
      links.appendChild(li);
    });
    $("links-box").hidden = linkData.length === 0;

    // 5. Advice ("What should I do?")
    var advice = $("advice");
    clearChildren(advice);
    advice.lang = lang;
    (result.advice || []).forEach(function (tip) {
      addItem(advice, tip);
    });

    // 6. Disclaimer: a result is never a guarantee.
    $("disclaimer").textContent = result.disclaimer || "";
    $("disclaimer").lang = lang;

    // 7. Reset the feedback buttons for this new result.
    $("fb-yes").disabled = false;
    $("fb-no").disabled = false;
    $("fb-thanks").hidden = true;

    updateLangNote();
    var section = $("result");
    section.hidden = false;
    // Move keyboard/screen-reader focus to the result (this also scrolls to it).
    section.focus();
  }

  // If the user switches language after a check, explain that the result is
  // still in the old language (we don't re-check automatically, so the
  // statistics don't count the same message twice).
  function updateLangNote() {
    var note = $("lang-note");
    if (!last.lang || $("result").hidden || last.lang === uiLang()) {
      note.hidden = true;
      return;
    }
    note.textContent = s("langNote");
    note.lang = uiLang();
    note.hidden = false;
  }

  // ------------------------------------------------------------------
  // Talking to the server
  // ------------------------------------------------------------------
  function checkText(event) {
    event.preventDefault();
    hideError();
    var text = $("message").value.trim();
    if (!text) {
      showError(s("empty"));
      $("message").focus();
      return;
    }
    if (text.length > CONFIG.MAX_TEXT_CHARS) {
      showError(s("tooLong"));
      return;
    }

    setBusy(true);
    setStatus(s("checking"), true);
    fetchWithTimeout("/api/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, lang: uiLang() })
    })
      .then(function (response) {
        if (!response.ok) throw { status: response.status };
        return response.json();
      })
      .then(function (result) {
        setStatus(s("done"));
        renderResult(result, null);
      })
      .catch(function (err) {
        showError(err && err.status ? messageForStatus(err.status, false) : s("network"));
      })
      .finally(function () {
        setBusy(false);
      });
  }

  function checkScreenshot() {
    var input = $("screenshot");
    var file = input.files && input.files[0];
    if (!file) return;
    hideError();

    // Check type and size here first, so we don't upload something useless.
    if (["image/png", "image/jpeg", "image/webp"].indexOf(file.type) === -1) {
      showError(s("badType"));
      input.value = "";
      return;
    }
    if (file.size > CONFIG.MAX_IMAGE_BYTES) {
      showError(s("tooBig"));
      input.value = "";
      return;
    }

    var form = new FormData();
    form.append("file", file);
    form.append("lang", uiLang());

    setBusy(true);
    setStatus(s("reading"), true);
    fetchWithTimeout("/api/check-image", { method: "POST", body: form })
      .then(function (response) {
        if (!response.ok) throw { status: response.status };
        return response.json();
      })
      .then(function (data) {
        setStatus(s("done"));
        renderResult(data.result, data.extracted_text);
      })
      .catch(function (err) {
        showError(err && err.status ? messageForStatus(err.status, true) : s("network"));
      })
      .finally(function () {
        setBusy(false);
        input.value = ""; // so choosing the same picture again still works
      });
  }

  function sendFeedback(kind) {
    if (!last.verdict) return;
    $("fb-yes").disabled = true;
    $("fb-no").disabled = true;
    var thanks = $("fb-thanks");
    // Only the verdict and "correct"/"wrong" are sent - never the message.
    fetchWithTimeout("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ verdict: last.verdict, kind: kind })
    })
      .then(function (response) {
        if (!response.ok) throw { status: response.status };
        thanks.textContent = s("thanks");
      })
      .catch(function () {
        thanks.textContent = s("fbError");
        $("fb-yes").disabled = false;
        $("fb-no").disabled = false;
      })
      .finally(function () {
        thanks.hidden = false;
      });
  }

  function clearAll() {
    $("message").value = "";
    $("result").hidden = true;
    hideError();
    last = { verdict: null, lang: null };
    setStatus(s("cleared"));
    $("message").focus();
  }

  // ------------------------------------------------------------------
  // Start-up: connect buttons to the functions above
  // ------------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", function () {
    $("check-form").addEventListener("submit", checkText);
    $("clear-btn").addEventListener("click", clearAll);
    $("screenshot").addEventListener("change", checkScreenshot);
    $("fb-yes").addEventListener("click", function () {
      sendFeedback("correct");
    });
    $("fb-no").addEventListener("click", function () {
      sendFeedback("wrong");
    });
    document.addEventListener("langchange", updateLangNote);

    if (CONFIG.TELEGRAM_BOT_URL) {
      $("bot-link").href = CONFIG.TELEGRAM_BOT_URL;
      $("bot-box").hidden = false;
    }
  });
})();
