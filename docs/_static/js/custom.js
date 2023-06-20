const classes = document.getElementsByClassName("class");
const tables =  document.getElementsByClassName('py-attribute-table');

for (let i = 0; i < classes.length; i++) {
   const parentSig = classes[i].getElementsByTagName('dt')[0];
   const table = tables[i];

   parentSig.classList.add(`parent-sig-${i}`);
   table.id = `attributable-${i}`

   $(`#attributable-${i}`).insertAfter( `.parent-sig-${i}` );
}


const metaTitle = document.head.querySelector('meta[property="og:title"]')
const metaDesc = document.head.querySelector('meta[property="og:description"]')


if (metaTitle.content === '<no title>') {
   metaTitle.remove();
}

if (metaDesc.content.startsWith('Getting Started::')) {
   metaDesc.remove();
}