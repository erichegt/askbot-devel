<?php
class UserRegister extends WsgiInjectableSpecialPage {
    function __construct() {
            parent::__construct( 'UserRegister', 
                                '/backend/account/nmr-wiki/signup/',
                                array(0=>'/backend/content/style/mediawiki-login.css'),
                                array(
                                    0=>'/backend/content/js/jquery-1.2.6.min.js',
                                    1=>'/backend/content/js/mediawiki-login.js'
                                    )
                                );
    }
}

