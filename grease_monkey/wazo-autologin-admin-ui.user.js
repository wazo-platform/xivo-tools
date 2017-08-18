// ==UserScript==
// @name        Wazo Autologin admin-ui
// @namespace   http://wazo.community
// @include     https://*/admin/login/
// @version     1
// @grant       none
// ==/UserScript==

// Automatically login on wazo-admin-ui web interface.
// You should change the login and password below before using this script.

var login = 'root';
var password = 'password';

var titles = document.getElementsByTagName('title');
if (titles.length == 0) {
    exit();
}
var title = titles[0];
if (title == null) {
    exit();
}
var is_wazo = title.textContent.indexOf('Wazo administration') != -1;
if ( ! is_wazo) {
    exit();
}

var login_input = document.getElementById('username');
var pass_input = document.getElementById('password');
var submit_input = document.getElementById('submit');

var is_login_page = login_input != null && pass_input != null && submit_input != null;

if (! is_login_page) {
    exit();
}

login_input.value = login;
pass_input.value = password;
submit_input.click();
