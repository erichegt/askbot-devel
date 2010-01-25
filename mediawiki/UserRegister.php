<?php
# Alert the user that this is not a valid entry point to MediaWiki if they try to access the special pages file directly.
if (!defined('MEDIAWIKI')) {
        echo <<<EOT
Not a valid entry point.
EOT;
        exit( 1 );
}
 
$wgExtensionCredits['specialpage'][] = array(
	'name' => 'User Registration',
	'author' => 'Evgeny Fadeev',
	'url' => 'none',
	'description' => 'Creates new user account for the Wiki and Q&A forum',
	'descriptionmsg' => 'people-page-desc',
	'version' => '0.0.0',
);
 
$dir = dirname(__FILE__) . '/';
 
$wgAutoloadClasses['UserRegister'] = $dir . 'UserRegister.body.php'; # Tell MediaWiki to load the extension body.
$wgExtensionMessagesFiles['UserRegister'] = $dir . 'UserRegister.i18n.php';
$wgExtensionAliasesFiles['UserRegister'] = $dir . 'UserRegister.alias.php';
$wgSpecialPages['UserRegister'] = 'UserRegister'; # Let MediaWiki know about your new special page.
