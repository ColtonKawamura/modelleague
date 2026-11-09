/* ModelLeague password gate.
 *
 * The inline head script decides, before first paint, whether this page
 * starts gated (no "modelleague-auth" flag in sessionStorage). This file
 * handles the lock screen: it hashes the entered password with SHA-256 and
 * compares it against the hash embedded by the build (window.__ML_GATE__).
 * The plaintext password never appears in the page.
 *
 * On success it sets sessionStorage "modelleague-auth" = "1", so the rest of
 * the browser session (all tabs of the page session) stays unlocked until
 * the browser session ends.
 */
(function () {
  "use strict";
  var g = window.__ML_GATE__ || { enabled: false, sha256: null };
  if (!g.enabled || !g.sha256) { return; }

  var form = document.getElementById("ml-gate-form");
  var pass = document.getElementById("ml-gate-pass");
  var err = document.getElementById("ml-gate-error");
  if (!form || !pass || !err) { return; }

  if (!document.documentElement.classList.contains("gated")) { return; }

  if (!window.crypto || !window.crypto.subtle) {
    err.textContent = "Password checking is unavailable in this browser — use a modern one over https.";
    err.hidden = false;
    return;
  }

  function sha256(text) {
    var data = new TextEncoder().encode(text);
    return window.crypto.subtle.digest("SHA-256", data).then(function (buf) {
      var bytes = new Uint8Array(buf);
      var out = "";
      for (var i = 0; i < bytes.length; i++) {
        out += ("0" + bytes[i].toString(16)).slice(-2);
      }
      return out;
    });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var value = pass.value;
    if (!value) { return; }
    sha256(value).then(function (hash) {
      if (hash === g.sha256) {
        try { sessionStorage.setItem("modelleague-auth", "1"); } catch (e) {}
        document.documentElement.classList.remove("gated");
        pass.value = "";
      } else {
        err.hidden = false;
        pass.value = "";
        pass.focus();
        form.classList.remove("shake");
        void form.offsetWidth; /* restart the animation */
        form.classList.add("shake");
      }
    });
  });

  pass.focus();
})();
