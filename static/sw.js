const CACHE = "xexam-v2";
    const OFFLINE_URLS = ["/login", "/static/js/mascot.js"];
    
    self.addEventListener("install", e => {
      e.waitUntil(caches.open(CACHE).then(c => c.addAll(OFFLINE_URLS).catch(()=>{})));
      self.skipWaiting();
    });
    
    self.addEventListener("activate", e => {
      e.waitUntil(caches.keys().then(keys => 
        Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
      ));
      self.clients.claim();
    });
    
    self.addEventListener("fetch", e => {
      if (e.request.method !== "GET") return;
      e.respondWith(
        fetch(e.request).catch(() => caches.match(e.request))
      );
    });
    
    self.addEventListener("push", e => {
      const data = e.data ? e.data.json() : {title: "X-EXAM", body: "Co thong bao moi!"};
      e.waitUntil(self.registration.showNotification(data.title, {
        body: data.body, icon: "/static/icon.svg", badge: "/static/icon.svg",
        tag: "xexam-notif", renotify: true
      }));
    });