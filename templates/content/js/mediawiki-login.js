function toggleScreenNameInput(par1,par2){
    if ($(this).is(':checked')){
        $('.optional-screen-name').show();
    }
    else {
        $('#id_screen_name').val('');
        $('.optional-screen-name').hide();
    }
}

function toggleScreenNameErrorMessage(e){
    var screen_name = $('#id_screen_name').val();
    if (screen_name != ''){
        $('.screen-name-error').hide(); 
    }
    else{
        $('.screen-name-error').show(); 
    }
}

$(document).ready( function(){
    var screen_name = $('#id_screen_name').val();
    var use_screen_name = $('#id_use_separate_screen_name').is(':checked');
    if (screen_name == '' && !use_screen_name){
        $('.optional-screen-name').hide();
    }
    $('#id_use_separate_screen_name').unbind('click').click(toggleScreenNameInput);
    $('#id_screen_name').unbind('keyup').keyup(toggleScreenNameErrorMessage);
});
