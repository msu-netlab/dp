DNS-Proxy
=========
Modern websites use Content Delivery Networks (CDNs) to speed up the delivery of static content. However, we show that DNS-based load-balancing of CDN servers fails to fully deliver on the speedup of CDNs. We propose DNS-Proxy (dp), a client-side process that shares load-balancing functionality with CDNs by choosing from among resolved CDN servers based on last mile network performance. Our measurement study of CDN infrastructure deployed by Akamai and Google shows that dp reduces webpage load time by 29% on average. If dp has already resolved the domain, the reduction in webpage load time is 37% on average. Finally, dp reduces the download time of individual static Web objects by as much as 40%. We argue that dp enables a more effective use of existing content delivery infrastructure and represents a complementary strategy to a continual increase of geographic content availability.

Dependencies
============

1. Node.js
2. 'raw-socket' module for Node.js
3. 'object-sizeof' module for Node.js
4. 'ip' module for Node.js
