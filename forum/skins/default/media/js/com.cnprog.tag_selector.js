//var scriptUrl, interestingTags, ignoredTags, tags, $;
function pickedTags(){

    var sendAjax = function(tagname, reason, action, callback){
        var url = scriptUrl;
        if (action == 'add'){
            url += $.i18n._('mark-tag/');
            if (reason == 'good'){
                url += $.i18n._('interesting/');
            }
            else {
                url += $.i18n._('ignored/');
            }
        }
        else {
            url += $.i18n._('unmark-tag/');
        }
        url = url + tagname + '/';

        var call_settings = {
            type:'POST',
            url:url
        };
        if (callback !== false){
            call_settings.success = callback;
        }
        $.ajax(call_settings);
    };


    var unpickTag = function(from_target ,tagname, reason, send_ajax){
        //send ajax request to delete tag
        var deleteTagLocally = function(){
            from_target[tagname].remove();
            delete from_target[tagname];
        };
        if (send_ajax){
            sendAjax(tagname,reason,'remove',deleteTagLocally);
        }
        else {
            deleteTagLocally();
        }

    };

    var setupTagDeleteEvents = function(obj,tag_store,tagname,reason,send_ajax){
        obj.unbind('mouseover').bind('mouseover', function(){
            $(this).attr('src', mediaUrl('media/images/close-small-hover.png'));
        });
        obj.unbind('mouseout').bind('mouseout', function(){
            $(this).attr('src', mediaUrl('media/images/close-small-dark.png'));
        });
        obj.click( function(){
            unpickTag(tag_store,tagname,reason,send_ajax);
        });
    };

    var handlePickedTag = function(obj,reason){
        var tagname = $.trim($(obj).prev().attr('value'));
        var to_target = interestingTags;
        var from_target = ignoredTags;
        var to_tag_container;
        if (reason == 'bad'){
            to_target = ignoredTags;
            from_target = interestingTags;
            to_tag_container = $('div .tags.ignored');
        }
        else if (reason != 'good'){
            return;
        }
        else {
            to_tag_container = $('div .tags.interesting');
        }

        if (tagname in from_target){
            unpickTag(from_target,tagname,reason,false);
        }

        if (!(tagname in to_target)){
            //send ajax request to pick this tag

            sendAjax(tagname,reason,'add',function(){
                var new_tag = $('<span></span>');
                new_tag.addClass('deletable-tag');
                var tag_link = $('<a></a>');
                tag_link.attr('rel','tag');
                tag_link.attr('href', scriptUrl + $.i18n._('tags/') + tagname);
                tag_link.html(tagname);
                var del_link = $('<img></img>');
                del_link.addClass('delete-icon');
                del_link.attr('src', mediaUrl('/media/images/close-small-dark.png'));

                setupTagDeleteEvents(del_link, to_target, tagname, reason, true);

                new_tag.append(tag_link);
                new_tag.append(del_link);
                to_tag_container.append(new_tag);

                to_target[tagname] = new_tag;
            });
        }
    };

    var collectPickedTags = function(){
        var good_prefix = 'interesting-tag-';
        var bad_prefix = 'ignored-tag-';
        var good_re = RegExp('^' + good_prefix);
        var bad_re = RegExp('^' + bad_prefix);
        interestingTags = {};
        ignoredTags = {};
        $('.deletable-tag').each(
            function(i,item){
                var item_id = $(item).attr('id');
                var tag_name, tag_store;
                if (good_re.test(item_id)){
                    tag_name = item_id.replace(good_prefix,'');
                    tag_store = interestingTags;
                    reason = 'good';
                }
                else if (bad_re.test(item_id)){
                    tag_name = item_id.replace(bad_prefix,'');
                    tag_store = ignoredTags;
                    reason = 'bad';
                } 
                else {
                    return;
                }
                tag_store[tag_name] = $(item);
                setupTagDeleteEvents($(item).find('img'),tag_store,tag_name,reason,true);
            }
        );
    };

    var setupHideIgnoredQuestionsControl = function(){
        $('#hideIgnoredTagsCb').unbind('click').click(function(){
            $.ajax({
                        type: 'POST',
                        dataType: 'json',
                        cache: false,
                        url: scriptUrl + $.i18n._('command/'),
                        data: {command:'toggle-ignored-questions'}
                    });
        });
    };
    return {
        init: function(){
            collectPickedTags();
            setupHideIgnoredQuestionsControl();
            $("#interestingTagInput, #ignoredTagInput").autocomplete(tags, {
                minChars: 1,
                matchContains: true,
                max: 20,
                multiple: true,
                multipleSeparator: " ",
                formatItem: function(row, i, max) {
                    return row.n + " ("+ row.c +")";
                },
                formatResult: function(row, i, max){
                    return row.n;
                }

            });
            $("#interestingTagAdd").click(function(){handlePickedTag(this,'good');});
            $("#ignoredTagAdd").click(function(){handlePickedTag(this,'bad');});
        }
    };
}

$(document).ready( function(){
    pickedTags().init();
});
