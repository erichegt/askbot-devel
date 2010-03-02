$(document).ready( function(){
    var options = {
                   success: function(a,b){$('.admin #action_status').html($.i18n._('changes saved'));},
                   dataType:'json',
                   timeout:5000,
                   url: scriptUrl + $.i18n._('moderate-user/') + viewUserID +  '/'
                    };
    var form = $('.admin #moderate_user_form').ajaxForm(options);
    var box = $('.admin input#id_is_approved').click(function(){ 
        $('.admin #action_status').html($.i18n._('sending data...'));
        form.ajaxSubmit(options);
    });
});
