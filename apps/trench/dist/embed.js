if (window.self !== window.top || new URLSearchParams(window.location.search).has("embed")) {
  document.documentElement.dataset.embedded = "";
}
