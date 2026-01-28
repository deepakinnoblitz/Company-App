function f(s){var i,n,c,o;if(!s)return s;let r=s.replace(/<[^>]*>/g," ").replace(/\s+/g," ").trim();if(r=r.replace(/^Error:\s*/i,""),r.includes("Collection exceeds Invoice Amount")){const e=(i=r.match(/Grand Total:\s*([\d.]+)/))==null?void 0:i[1],t=(n=r.match(/Already Collected:\s*([\d.]+)/))==null?void 0:n[1],a=(c=r.match(/Trying to Add:\s*([\d.]+)/))==null?void 0:c[1],l=(o=r.match(/Remaining Balance:\s*([\d.]+)/))==null?void 0:o[1];if(e&&l&&a)return`Collection Amount Exceeds Invoice Balance!

Invoice Total: ₹${parseFloat(e).toLocaleString()}
Already Collected: ₹${parseFloat(t||"0").toLocaleString()}
Remaining Balance: ₹${parseFloat(l).toLocaleString()}

You tried to collect ₹${parseFloat(a).toLocaleString()}, but only ₹${parseFloat(l).toLocaleString()} is remaining.`}if(r.includes("MandatoryError")){const e=r.split(":"),t=e[e.length-1];if(t)return`Mandatory Fields Required: ${t.split(",").map(d=>d.trim()).filter(Boolean).map(d=>d.split("_").map(p=>p.charAt(0).toUpperCase()+p.slice(1)).join(" ")).join(", ")}`}return r}function g(s,r="An error occurred"){if(!s)return r;const i=[];if(s._server_messages)try{const e=JSON.parse(s._server_messages);Array.isArray(e)&&e.forEach(t=>{try{const a=typeof t=="string"?JSON.parse(t):t;a.message&&i.push(a.message)}catch{typeof t=="string"&&i.push(t)}})}catch(e){console.error("Failed to parse _server_messages",e)}if(s.exception){const e=s.exception,t=e.indexOf(":");if(t!==-1){const a=e.substring(t+1).trim();i.push(a)}else{const a=e.split(`
`);a[0]&&i.push(a[0])}}s.message&&typeof s.message=="string"&&i.push(s.message);const n=i.map(e=>f(e)),c=n.some(e=>e.startsWith("Mandatory Fields Required")),o=n.filter((e,t)=>!(n.indexOf(e)!==t||c&&e.toLowerCase().includes("value missing")));return o.length>0?o.join(`
`):r}export{g as h};
