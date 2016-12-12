// Copyright (C) 2015 Avencall
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>

// ==UserScript==
// @name        Wazo Autologin
// @namespace   http://wazo.community
// @description Automatically login on Wazo web interface.
// @include     https*
// @grant       none
// ==/UserScript==

// You should change the login and password below before using this script.

var login = 'root';
var password = 'password';



var is_xivo = document.getElementById('version-copyright') != null &&
              document.getElementById('version-copyright').textContent.indexOf('XIVO') != -1;

if ( ! is_xivo) {
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
