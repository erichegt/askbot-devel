//var interestingTags, ignoredTags, tags, $;
var TagDetailBox = function(box_type){
    this.box_type = box_type;
    this.__is_blank = true;
    this.wildcard = undefined;
};

TagDetailBox.prototype.belongs_to = function(wildcard){
    return (this.wildcard === wildcard);
};

TagDetailBox.prototype.is_blank = function(){
    return (this.__is_blank);
};

TagDetailBox.prototype.clear = function(){
    if (this.is_blank()){
        return;
    }
    this.__is_blank = true;
    this.__tags.remove();
};

TagDetailBox.prototype.load_tags = function(wildcard, callback){
    $.ajax({
        type: 'POST',
        dataType: 'json',
        cache: false,
        url: askbot['urls']['load_wildcard_tags'],
        data: { wildcard: wildcard },
        success: callback
    });
};

TagDetailBox.prototype.render = function(){
};

TagDetailBox.prototype.render_for = function(wildcard){
    this.load_tags(
        wildcard,
        this.render
    );
}

function pickedTags(){
    
    var interestingTags = {};
    var ignoredTags = {};
    var interestingTagDetailBox = new TagDetailBox('interesting');
    var ignoredTagDetailBox = new TagDetailBox('ignored');

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
        obj.click( function(){
            unpickTag(tag_store,tagname,reason,send_ajax);
        });
    };

    var getWildcardTagDetailBox = function(reason){
        if (reason === 'good'){
            return interestingTagDetailBox;
        } else {
            return ignoredTagDetailBox;
        }
    };

    var handleWildcardTagClick = function(tag_name, reason){
        var detail_box = getWildcardTagDetailBox(reason);
        if (detail_box.is_blank()){
            detail_box.render_for(tag_name);
        } else if (detail_box.belongs_to(tag_name)){
            detail_box.clear();
        } else {
            detail_box.clear();
            detail_box.render_for(tag_name);
        }
    };

    var renderNewTags = function(
                                    clean_tag_names,
                                    reason,
                                    to_target,
                                    to_tag_container
                                ){
        $.each(clean_tag_names, function(idx, tag_name){
            var tag = new Tag();
            tag.setName(tag_name);
            tag.setDeletable(true);

            if (/\*$/.test(tag_name)){
                tag.setLinkable(false);
                tag.setHandler(function(){
                    handleWildcardClick(tag_name, reason);
                });
            }
            tag.setDeleteHandler(function(){
                unpickTag(to_target, tag_name, reason, true);
            });

            var tag_element = tag.getElement();
            to_tag_container.append(tag_element);
            to_target[tag_name] = tag_element;
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

    var collectPickedTags = function(section){
        if (section === 'interesting'){
            var reason = 'good';
            var tag_store = interestingTags;
        }
        else if (section === 'ignored'){
            var reason = 'bad';
            var tag_store = ignoredTags;
        }
        else {
            return;
        }
        $('.' + section + '.tags.marked-tags a.tag').each(
            function(i,item){
                var tag_name = $(item).html().replace('\u273d','*');
                tag_store[tag_name] = $(item).parent();
                setupTagDeleteEvents(
                    $(item).parent().find('.delete-icon'),
                    tag_store,
                    tag_name,
                    reason,
                    true
                );
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
            collectPickedTags('interesting');
            collectPickedTags('ignored');
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
