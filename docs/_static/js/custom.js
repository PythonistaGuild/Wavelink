function loadExternalScript(url) {
  const script = document.createElement('script');
  script.src = url;
  script.crossorigin = "anonymous";
  script.onload = () => console.log("External Script Loaded...");
  document.head.appendChild(script);
}

loadExternalScript("https://kit.fontawesome.com/347516fc15.js");