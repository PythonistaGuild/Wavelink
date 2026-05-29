const classes = document.getElementsByClassName("class");
const tables =  document.getElementsByClassName('py-attribute-table');

for (let i = 0; i < classes.length; i++) {
   const parentSig = classes[i].getElementsByTagName('dt')[0];
   const table = tables[i];

   parentSig.classList.add(`parent-sig-${i}`);
   table.id = `attributable-${i}`
   parentSig.after(table);
}

function loadExternalScript(url) {
  const script = document.createElement('script');
  script.src = url;
  script.crossorigin = "anonymous";
  script.onload = () => console.log("External Script Loaded...");
  document.head.appendChild(script);
}

loadExternalScript("https://kit.fontawesome.com/347516fc15.js");