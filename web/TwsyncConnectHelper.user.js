// ==UserScript==
// @name        TwsyncConnectHelper
// @namespace   twsync
// @description Login twsync every time when you open weibo.com, so the auth will never expire.
// @exclude     http://twsync.zhirui.org/*
// @version     0.1
// @grant       GM_getValue
// @grant       GM_setValue
// @grant       GM_xmlhttpRequest
// ==/UserScript==
var HOUR = 3600;
var now = Math.floor(new Date().getTime() / 1000);
if (now - GM_getValue('lastTimeLogin', 0) > HOUR) {
  console.log('login twsync');
  GM_xmlhttpRequest({
    method: "GET",
    url:    "http://twsync.zhirui.org/login",
    onload: function (response) {
              console.log(response.status,
                          response.responseText.substring(0, 80)
                         );
            }
  });
  GM_setValue('lastTimeLogin', now);
}
