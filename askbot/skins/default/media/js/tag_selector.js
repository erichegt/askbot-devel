//var interestingTags, ignoredTags, tags, $;
function pickedTags(){

    var sendAjax = function(tagnames, reason, action, callback){
        var url = '';
        if (action == 'add'){
            if (reason == 'good'){
                url = askbot['urls']['mark_interesting_tag'];
            }
            else {
                url = askbot['urls']['mark_ignored_tag'];
            }
        }
        else {
            url = askbot['urls']['unmark_tag'];
        }

        var call_settings = {
            type:'POST',
            url:url,
            data: JSON.stringify({tagnames: tagnames}),
            dataType: 'json'
        };
        if (callback !== false){
            call_settings.success = callback;
        }
        $.ajax(call_settings);
    };

    var unpickTag = function(from_target, tagname, reason, send_ajax){
        //send ajax request to delete tag
        var deleteTagLocally = function(){
            from_target[tagname].remove();
            delete from_target[tagname];
        };
        if (send_ajax){
            sendAjax([tagname], reason, 'remove', deleteTagLocally);
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

    var renderNewTags = function(
                                    clean_tagnames,
                                    reason,
                                    to_target,
                                    to_tag_container
                                ){
        $.each(clean_tagnames, function(idx, tagname){
            var new_tag = $('<span></span>');
            new_tag.addClass('deletable-tag');
            var tag_link = $('<a></a>');
            tag_link.attr('rel','tag');
            var tag_url = askbot['urls']['questions'] + '?tags=' + tagname;
            tag_link.attr('href', tag_url);
            tag_link.html(tagname);
            var del_link = $('<img></img>');
            del_link.addClass('delete-icon');
            del_link.attr('src', mediaUrl('media/images/close-small-dark.png'));

            setupTagDeleteEvents(del_link, to_target, tagname, reason, true);

            new_tag.append(tag_link);
            new_tag.append(del_link);
            to_tag_container.append(new_tag);

            to_target[tagname] = new_tag;
        });
    };

    var handlePickedTag = function(obj,reason){
        var tagnames = getUniqueWords($(obj).prev().attr('value'));
        var to_target = interestingTags;
        var from_target = ignoredTags;
        var to_tag_container;
        if (reason == 'bad'){
            to_target = ignoredTags;
            from_target = interestingTags;
            to_tag_container = $('div .tags.ignored');
        }
        else if (reason == 'good'){
            to_tag_container = $('div .tags.interesting');
        }
        else {
            return;
        }

        $.each(tagnames, function(idx, tagname){
            if (tagname in from_target){
                unpickTag(from_target,tagname,reason,false);
            }
        });

        var clean_tagnames = [];
        $.each(tagnames, function(idx, tagname){
            if (!(tagname in to_target)){
                clean_tagnames.push(tagname);
            }
        });

        if (clean_tagnames.length > 0){
            //send ajax request to pick this tag

            sendAjax(
                clean_tagnames,
                reason,
                'add',
                function(){ 
                    renderNewTags(
                        clean_tagnames,
                        reason,
                        to_target,
                        to_tag_container
                    );
                }
            );
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
                        url: askbot['urls']['command'],
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
