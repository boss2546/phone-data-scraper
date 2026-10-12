(function(modules){var installed={};function __require__(id){if(installed[id])return installed[id].exports;var m=installed[id]={exports:{}};modules[id](m,m.exports,__require__);return m.exports}return __require__(0)})([
function(m,e,r){
  var api=r(1);
  var parser=r(2);
  function fetchPrices(model){
    return api.request("/api/v2/prices?item="+encodeURIComponent(model)).then(parser.parseResponse);
  }
  e.fetchPrices=fetchPrices;
},
function(m,e,r){
  e.request=function(url){
    return fetch("https://store.example.com"+url,{headers:{"X-Client-Signature":"sha256-abc12345"}});
  };
},
function(m,e,r){
  e.parseResponse=function(res){
    return res.json().then(function(d){return d.items.map(function(x){return {name:x.title,price:x.current_price,in_stock:x.qty>0}})});
  };
}
]);
