const classes = document.getElementsByClassName("class");
const tables =  document.getElementsByClassName('py-attribute-table');

for (let i = 0; i < classes.length; i++) {
   const parentSig = classes[i].getElementsByTagName('dt')[0];
   const table = tables[i];

   parentSig.classList.add(`parent-sig-${i}`);
   table.id = `attributable-${i}`

   $(`#attributable-${i}`).insertAfter( `.parent-sig-${i}` );
}


function dynamicallyLoadScript(url) {
    let script = document.createElement("script");
    script.src = url;
    script.crossOrigin = 'anonymous'

    document.head.appendChild(script);
}


dynamicallyLoadScript('https://kit.fontawesome.com/12146b1c3e.js');
