DNS-Proxy
=========
Modern websites use Content Delivery Networks (CDNs) to speed up the delivery of static content. However, we show that DNS-based load-balancing of CDN servers fails to fully deliver on the speedup of CDNs. We propose DNS-Proxy (dp), a client-side process that shares load-balancing functionality with CDNs by choosing from among resolved CDN servers based on last mile network performance. Our measurement study of CDN infrastructure deployed by Akamai and Google shows that dp reduces webpage load time by 29% on average. If dp has already resolved the domain, the reduction in webpage load time is 40% on average. Finally, dp reduces the download time of individual static Web objects by as much as 43%. We argue that dp enables a more effective use of existing content delivery infrastructure and represents a complementary strategy to a continual increase of geographic content availability.

[Read more...](docs/GoelDnsProxyICCCN15.pdf)



Installation
============

We also make DNS-Proxy available as an npm-module at https://www.npmjs.com/package/dns_proxy

1. To download DNS-Proxy, run 
      npm install dns_proxy
2. To start DNS-Proxy server, run
      sudo node node_modules/dns_proxy/dns_proxy.js
3. Once the dns_proxy has been started, configure your device to use localhost (127.0.0.1) as the default DNS server.
