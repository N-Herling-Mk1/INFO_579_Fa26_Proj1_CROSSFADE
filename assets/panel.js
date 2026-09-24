/* Shared helpers for panels. Every panel loads ../data/site_data.js first. */
var CF = (function () {
  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") n.textContent = attrs[k];
      else if (k === "html") n.innerHTML = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { if (c) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  function genreColor(i) { return "var(--g" + i + ")"; }
  function table(name) {
    return window.SITE.tables.filter(function (t) { return t.name === name; })[0];
  }
  function kb(bytes) { return bytes < 1024 ? bytes + " B" : (bytes / 1024).toFixed(1) + " KB"; }
  // key roles per table, matching the requirements analysis (Table 6)
  var KEYS = {
    "Artist": { "Artist ID": "PK" },
    "Track": { "Track ID": "PK", "Artist ID": "FK" },
    "Genre": { "Genre ID": "PK" },
    "Listener": { "Listener ID": "PK" },
    "Scoring Model": { "Model ID": "PK" },
    "Station": { "Station ID": "PK", "Listener ID": "FK", "Model ID": "FK" },
    "Track Score": { "Track ID": "PK FK", "Model ID": "PK FK", "Genre ID": "FK" },
    "Genre Probability": { "Track ID": "PK FK", "Model ID": "PK FK", "Genre ID": "PK FK" },
    "Station Blend": { "Station ID": "PK FK", "Genre ID": "PK FK" },
    "Play": { "Listener ID": "PK FK", "Track ID": "PK FK", "Played At": "PK", "Station ID": "FK" }
  };
  return { el: el, genreColor: genreColor, table: table, kb: kb, KEYS: KEYS };
})();
