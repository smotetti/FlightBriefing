/* Side menu shared by every page. Adds a three-bar button to the page header and a drawer with the programs. */
(function(){
  var ITEMS = [
    ["dow.html", "DOW and DOI calculator"],
    ["briefing.html", "Flight briefing"],
    ["meo.html", "mEO, single engine departures"]
  ];
  var here = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  var css = [
    ".mn-btn{flex:none;width:52px;height:52px;border:0;border-radius:12px;background:rgba(18,35,43,.12);cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;padding:0;color:#12232b}",
    ".mn-btn span{display:block;width:26px;height:3.5px;border-radius:2px;background:currentColor}",
    ".mn-btn.mn-float{position:fixed;top:max(12px,env(safe-area-inset-top));left:max(12px,env(safe-area-inset-left));z-index:900;background:#b4c3c9}",
    ".mn-ov{position:fixed;inset:0;background:rgba(5,12,15,.55);opacity:0;pointer-events:none;transition:opacity .2s;z-index:1000}",
    ".mn-ov.open{opacity:1;pointer-events:auto}",
    ".mn-dr{position:fixed;top:0;bottom:0;left:0;width:min(330px,86vw);background:var(--panel,#fff);color:var(--ink,#12232b);z-index:1001;transform:translateX(-102%);transition:transform .22s ease;",
    "padding:max(16px,env(safe-area-inset-top)) 16px max(16px,env(safe-area-inset-bottom)) max(16px,env(safe-area-inset-left));display:flex;flex-direction:column;gap:6px;overflow:auto;border-right:1px solid var(--line,#c6d2d6);font:17px/1.4 var(--body,-apple-system,Helvetica,Arial,sans-serif)}",
    ".mn-dr.open{transform:none}",
    ".mn-dr h2{margin:6px 8px 10px;font-size:15px;font-weight:600;color:var(--muted,#566a72)}",
    ".mn-dr a{display:flex;align-items:center;min-height:56px;padding:0 14px;border-radius:12px;color:inherit;text-decoration:none;font-size:19px}",
    ".mn-dr a[aria-current=page]{background:var(--teal,#0e7a7a);color:var(--on-teal,#fff);font-weight:650}",
    ".mn-dr hr{border:0;border-top:1px solid var(--line,#c6d2d6);margin:8px 0;width:100%}"
  ].join("\n");
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  var btn = document.createElement("button");
  btn.type = "button"; btn.className = "mn-btn"; btn.setAttribute("aria-label", "Open menu"); btn.setAttribute("aria-expanded", "false");
  btn.innerHTML = "<span></span><span></span><span></span>";
  var top = document.querySelector(".top");
  if(top) top.insertBefore(btn, top.firstChild); else { btn.className += " mn-float"; document.body.appendChild(btn); }

  var ov = document.createElement("div"); ov.className = "mn-ov";
  var dr = document.createElement("nav"); dr.className = "mn-dr"; dr.setAttribute("aria-label", "Programs");
  var h = '<h2>Programs</h2>' + ITEMS.map(function(it){
    return '<a href="' + it[0] + '"' + (here === it[0] ? ' aria-current="page"' : '') + '>' + it[1] + '</a>';
  }).join("") + '<hr><a href="index.html"' + (here === "index.html" ? ' aria-current="page"' : '') + '>Home</a>';
  dr.innerHTML = h;
  document.body.appendChild(ov); document.body.appendChild(dr);

  function setOpen(o){
    ov.classList.toggle("open", o); dr.classList.toggle("open", o);
    btn.setAttribute("aria-expanded", o ? "true" : "false");
  }
  btn.addEventListener("click", function(){ setOpen(!dr.classList.contains("open")); });
  ov.addEventListener("click", function(){ setOpen(false); });
  document.addEventListener("keydown", function(e){ if(e.key === "Escape") setOpen(false); });
})();
