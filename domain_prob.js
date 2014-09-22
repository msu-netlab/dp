var page = require('webpage').create();
var time = 0;
var domainArray = ["http://www.google.com/?gws_rd=ssl", "http://www.huffingtonpost.com", "http://www.amazon.com", "https://www.facebook.com"];

iterate(domainArray[0]);

function iterate(domain) {
  var start = Date.now();
  page.open(domain, function(status) {
    time = Date.now() - start;
    console.log(domain + "=====" + time + ', ');
    domainArray.splice(0, 1);
    if (domainArray.length > 0)
      iterate(domainArray[0]);
  });
}
