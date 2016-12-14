// Copyright 2016 The Wazo Authors  (see the AUTHORS file)
// SPDX-License-Identifier: GPL-3.0+

// ==UserScript==
// @name      Wazo Autologin
// @namespace http://wazo.community
// @description
// @include   https*
// @grant     none
// ==/UserScript==

// Automatically login on Wazo web interface.
// You should change the login and password below before using this script.

var login = 'root';
var password = 'password';

var footers = document.getElementsByTagName('footer');
if (footers.length == 0) {
    exit();
}
var footer = footers[0];
if (footer == null) {
    exit();
}
var is_wazo = footer.textContent.indexOf('Wazo') != -1;
if (! is_wazo) {
    exit();
}

var login_input = document.getElementById('it-login');
var pass_input = document.getElementById('it-password');
var submit_input = document.getElementById('it-submit');

var is_login_page = login_input != null && pass_input != null && submit_input != null;

if (! is_login_page) {
    exit();
}

login_input.value = login;
pass_input.value = password;
submit_input.click();
