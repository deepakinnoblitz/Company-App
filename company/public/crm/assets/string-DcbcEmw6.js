function t(e){if(!e)return"";let n=e.replace(/<br\s*\/?>/gi,`
`);return n=n.replace(/<\/p>/gi,`
`),n=n.replace(/<\/div>/gi,`
`),n=n.replace(/<[^>]*>?/gm,""),n.split(`
`).map(r=>r.trim()).join(`
`).replace(/\n{2,}/g,`
`).trim()}function i(e){return typeof e=="object"&&e!==null?e.name||e.label||String(e):e==null?"":String(e)}export{i as g,t as s};
