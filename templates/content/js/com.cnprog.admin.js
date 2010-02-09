$().ready( function(){
    var options = {
                   success: function(a,b){$('.admin #action_status').html($.i18n._('changes saved'));},
                   dataType:'json',
                   timeout:5000,
<<<<<<< HEAD:templates/content/js/com.cnprog.admin.js
                   url: $.i18n._('/') + $.i18n._('moderate-user/') + viewUserID +  '/'
=======
                   url: scriptUrl + $.i18n._('moderate-user/') + viewUserID +  '/'
>>>>>>> 82d35490db90878f013523c4d1a5ec3af2df8b23:templates/content/js/com.cnprog.admin.js
                    };
    var form = $('.admin #moderate_user_form').ajaxForm(options);
    var box = $('.admin input#id_is_approved').click(function(){ 
        $('.admin #action_status').html($.i18n._('sending data...'));
        form.ajaxSubmit(options);
    });
});
