/* Keeps the mEO program working without a connection. It only handles mEO files, so the other programs are never served from here. */
var CACHE = "meo-v1";
var CORE = ["meo.html", "meo-data.json", "menu.js", "logo.png"];
function mine(url){
  var p = new URL(url).pathname.toLowerCase(), f = p.split("/").pop();
  return f === "meo.html" || f === "meo-data.json" || f === "menu.js" || f === "logo.png" || /^background\.(jpe?g|png|webp)$/.test(f) || f.indexOf("meo-") === 0;
}
self.addEventListener("install", function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){
    return Promise.all(CORE.map(function(u){ return c.add(new Request(u, {cache: "reload"})).catch(function(){}); }));
  }));
  self.skipWaiting();
});
self.addEventListener("activate", function(e){
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.filter(function(k){ return k !== CACHE; }).map(function(k){ return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});
self.addEventListener("fetch", function(e){
  var r = e.request;
  if(r.method !== "GET" || new URL(r.url).origin !== self.location.origin || !mine(r.url)) return;
  e.respondWith(caches.open(CACHE).then(function(c){
    var fromCache = function(){ return c.match(r, {ignoreSearch: true}); };
    var net = fetch(r).then(function(res){ if(res && res.ok) c.put(r, res.clone()); return res; });
    var slow = new Promise(function(resolve){ setTimeout(function(){ fromCache().then(function(h){ if(h) resolve(h); }); }, 4000); });
    return Promise.race([net.catch(function(){ return fromCache().then(function(h){ return h || Response.error(); }); }), slow]);
  }));
});
