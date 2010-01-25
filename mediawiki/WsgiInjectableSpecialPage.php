<?php

class WsgiInjectableSpecialPage extends SpecialPage {
    var $default_wsgi_command;
    function __construct($page_name,$default_wsgi_command,$css='',$scripts='',$wsgi_prefix=''){
        parent::__construct($page_name);
        wfLoadExtensionMessages($page_name);
        $this->default_wsgi_command = $default_wsgi_command;
        $this->css = $css;
        $this->scripts = $scripts;
        $this->wsgi_prefix = $wsgi_prefix;
    }
    function execute($par){
        global $wgWsgiScriptPath, $wgRequest, $wgOut, $wgHeader;
        $wgWsgiScriptPath = '';
        if ($this->wsgi_prefix != ''){
            $wsgi_call = $this->wsgi_prefix;
        }
        else {
            $wsgi_call = $wgWsgiScriptPath;
        }
            
        $this->setHeaders();

        if ($this->css != ''){
            if (is_array($this->css)){
                foreach($this->css as $css){
                    $wgHeader->addCSS($css);
                }
            }
            else{
                $wgHeader->addCSS($this->css);
            }
        }
        if ($this->scripts != ''){
            if (is_array($this->scripts)){
                foreach($this->scripts as $script){
                    $wgHeader->addScript($script);
                }
            }
            else{
                $wgHeader->addScript($this->css);
            }
        }

        #add command
        if (!is_null($wgRequest->getVal('command'))){
            $wsgi_call .= $wgRequest->getVal('command');
        }
        else {
            #why is this not working?
            $wsgi_call .= $this->default_wsgi_command;
        }
        #add session key
        $session_name = ini_get('session.name');#session_name();
        $session = '';
        if (array_key_exists($session_name, $_COOKIE)){
            $session = $_COOKIE[$session_name];
        }
        $wsgi_call .= "?session=${session}";

        #add posted request variables
        if ($wgRequest->wasPosted()){
            $data = $wgRequest->data;
            foreach ($data as $key => $value){
                if ($key != 'title'){
                    $wsgi_call .= "&${key}=${value}";
                }
            }
            $wsgi_call .= '&was_posted=true';
        }
        else {
            $wsgi_call .= '&was_posted=false';
        }

        #print the include statement called as GET request
        $wgOut->addHTML("<!--#include virtual=\"${wsgi_call}\"-->");
        #$wgOut->addHTML("<!-- ${wsgi_call} -->"); #print this only for debugging
    }
}
