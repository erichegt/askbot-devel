var prevSortMethod = sortMethod;

var liveSearch = function(command, query_string) {
    var query = $('input#keywords');
    var query_val = function () {return $.trim(query.val());}
    var prev_text = query_val();
    var running = false;
    var q_list_sel = 'question-list';//id of question listing div
    var search_url = askbot['urls']['questions'];
    var current_url = search_url + query_string;
    var x_button = $('input[name=reset_query]');

    x_button.click(function(){
        query.val('');
        if (sortMethod === 'relevance-desc'){
            sortMethod = prevSortMethod;
        }
        refresh_x_button();
        new_url = remove_from_url(search_url, 'query')
        search_url = askbot['urls']['questions'] + 'reset_query:true/';
        reset_query(new_url,sortMethod);
    });

    var refresh_x_button = function(){
        if(query_val().length > 0){
            if (query.hasClass('searchInput')){
                query.attr('class', 'searchInputCancelable');
                x_button.show();
            }
        } else {
            x_button.hide();
            query.attr('class', 'searchInput');
        }
    };

    var reset_sort_method = function(){
        if (sortMethod === 'relevance-desc'){
            sortMethod = prevSortMethod;
            if (sortMethod === 'relevance-desc'){
                sortMethod = 'activity-desc';
            }
        } else {
            sortMethod = 'activity-desc';
            prevSortMethod = 'activity-desc';
        }
    };

    var process_query = function(){
        if (prev_text.length === 0 && showSortByRelevance){
            if (sortMethod === 'activity-desc'){
                prevSortMethod = sortMethod;
                sortMethod = 'relevance-desc';
            }
        }
        if (current_url !== undefined){
            search_url = '/'; //resetting search_url every times
            query_string = current_url;
        }
        else {
            search_url = askbot['urls']['questions']; //resetting search_url every times
        }
        params = query_string.split('/')
        for (var i = 0; i < params.length; i++){
            if (params[i] !== ''){
                if (params[i].substring(0, 5) == "sort:"){ //change the sort method
                    search_url += 'sort:'+sortMethod+'/'
                    search_url += 'query:'+ encodeURIComponent(cur_text); //cur_text.split(' ').join('+') + '/' //we add the query here
                }
                else{
                    search_url += params[i] + '/';
                }
            }
        }
        send_query(cur_text);
    };

    var restart_query = function() {
        reset_sort_method();
        refresh_x_button();
        new_url = remove_from_url(search_url, 'query')
        search_url = askbot['urls']['questions'] + 'reset_query:true/';
        reset_query(new_url, sortMethod);
        running = true;
    };

    var eval_query = function(){
        cur_text = query_val();
        if (cur_text !== prev_text && running === false){
            if (cur_text.length >= minSearchWordLength){
                process_query();
                running = true;
            } else if (cur_text.length === 0){
                restart_query();
            }
        }
    };

    var main_page_search_listen = function(){
        running = false;
        refresh_x_button();
        var main_page_eval_handle;
        query.keyup(function(e){
            refresh_x_button();
            if (running === false){
                clearTimeout(main_page_eval_handle);
                main_page_eval_handle = setTimeout(eval_query, 400);
            }
        });
    };

    /* *********************************** */

    var render_related_tags = function(tags, query_string){
        if (tags.length === 0) return;

        var html_list = [];
        for (var i=0; i<tags.length; i++){
            var tag = new Tag();
            tag.setName(tags[i]['name']);
            tag.setDeletable(true);
            tag.setLinkable(false);
            tag.setUrlParams(query_string);

            html_list.push(tag.getElement().outerHTML());
            html_list.push('<span class="tag-number">&#215; ');
            html_list.push(tags[i]['used_count'])
            html_list.push('</span>');
            html_list.push('<br />');
        }
        $('#related-tags').html(html_list.join(''));
    };

    var render_search_tags = function(tags, query_string){
        var search_tags = $('#searchTags');
        search_tags.empty();
        if (tags.length === 0){
            $('#listSearchTags').hide();
            $('#search-tips').hide();//wrong - if there are search users
        } else {
            $('#listSearchTags').show();
            $('#search-tips').show();
            var tags_html = '';
            $.each(tags, function(idx, tag_name){
                var tag = new Tag();
                tag.setName(tag_name);
                tag.setDeletable(true);
                tag.setLinkable(false);
                tag.setDeleteHandler(
                    function(){
                        remove_search_tag(tag_name, query_string);
                    }
                );
                search_tags.append(tag.getElement());
            });
        }
    };

    var create_relevance_tab = function(query_string){
        relevance_tab = $('<a></a>');
        href = '/questions/' + replace_in_url(query_string, 'sort:relevance-desc')
        relevance_tab.attr('href', href);
        relevance_tab.attr('id', 'by_relevance');
        relevance_tab.html('<span>' + sortButtonData['relevance']['label'] + '</span>');
        return relevance_tab;
    }

    var replace_in_url = function (query_string, param){
        values = param.split(':')
        type = values[0]
        value = values[1]
        params = query_string.split('/')
        url=""

        for (var i = 0; i < params.length; i++){
            if (params[i] !== ''){
                if (params[i].substring(0, type.length) == type){
                    url += param + '/'
                }
                else{
                    url += params[i] + '/'
                }
            }
        }
        return url   
    }

    var remove_from_url = function (query_string, type){
        params = query_string.split('/')
        url=""
        for (var i = 0; i < params.length; i++){
            if (params[i] !== ''){
                if (params[i].substring(0, type.length) !== type){
                    url += params[i] + '/'
                }
            }
        }
        return '/'+url   
    }

    var remove_tag_from_url =function (query_string, tag){
        url = askbot['urls']['questions'];
        flag = false
        author = ''
        if (query_string !== null){
            params = query_string.split('/')
            for (var i = 0; i < params.length; i++){
                if (params[i] !== ''){
                    if (params[i].substring(0, 5) == "tags:"){
                        tags = params[i].substr(5).split('+');
                        new_tags = ''
                        for(var j = 0; j < tags.length; j++){
                            if(encodeURIComponent(tags[j]) !== encodeURIComponent(tag)){
                                if (new_tags !== ''){
                                    new_tags += '+'
                                }
                                new_tags += encodeURIComponent(tags[j]);
                            }
                        }
                        if(new_tags !== ''){
                            url += 'tags:'+new_tags+'/'
                        }
                        flag = true
                    }
                    else if (params[i].substring(0, 7) == "author:"){
                        author = params[i];
                    }
                    else{
                        url += params[i] + '/';
                    }
                }
            }
            if (author !== '') {
                url += author+'/'
            }
        }
        return url

    }

    var set_section_tabs = function(query_string){
        var tabs = $('#section_tabs > a'); /* TODO: This doesn't point to anything now */
        tabs.each(function(index, element){
            var tab = $(element);
            var tab_name = tab.attr('id').replace(/^by_/,'');
            href = '/questions/' + replace_in_url(query_string, 'section:'+tab_name)
            tab.attr('href', href);
        });
    };

    var set_active_sort_tab = function(sort_method, query_string){
        var tabs = $('#sort_tabs > a');
        tabs.attr('class', 'off');
        tabs.each(function(index, element){
            var tab = $(element);
            var tab_name = tab.attr('id').replace(/^by_/,'');
            if (tab_name in sortButtonData){
                href = '/questions/' + replace_in_url(query_string, 'sort:'+tab_name+'-desc')
                tab.attr('href', href);
                tab.attr('title', sortButtonData[tab_name]['desc_tooltip']);
                tab.html(sortButtonData[tab_name]['label']);
            }
        });
        var bits = sort_method.split('-', 2);
        var name = bits[0];
        var sense = bits[1];//sense of sort
        var antisense = (sense == 'asc' ? 'desc':'asc');
        var arrow = (sense == 'asc' ? ' &#9650;':' &#9660;');
        var active_tab = $('#by_' + name);
        active_tab.attr('class', 'on');
        active_tab.attr('title', sortButtonData[name][antisense + '_tooltip']);
        active_tab.html(sortButtonData[name]['label'] + arrow);
    };

    var render_relevance_sort_tab = function(query_string){
        if (showSortByRelevance === false){
            return;
        }
        var relevance_tab = $('#by_relevance');
        if (prev_text && prev_text.length > 0){
            if (relevance_tab.length == 0){
                relevance_tab = create_relevance_tab(query_string);
                $('#sort_tabs>span').after(relevance_tab);
            }
        }
        else {
            if (relevance_tab.length > 0){
                relevance_tab.remove();
            }
        }
    };

    var remove_search_tag = function(tag_name, query_string){
        $.ajax({
            url: askbot['urls']['questions']+'remove_tag:'+encodeURIComponent(tag_name)+'/',
            dataType: 'json',
            success: render_result,
            complete: try_again
        });
        search_url = remove_tag_from_url(query_string, tag_name)
        current_url = search_url;
        var context = { state:1, rand:Math.random() };
        var title = "Questions";
        var query = search_url;
        History.pushState( context, title, query );
    };

    var render_result = function(data, text_status, xhr){
        var old_list = $('#' + q_list_sel);
        var new_list = $('<div></div>').hide();
        if (data['questions'].length > 0){
            old_list.stop(true);

            new_list.html(data['questions']);
            //old_list.hide();
            old_list.after(new_list);
            //old_list.remove();
            //rename new div to old
            $('#pager').toggle(data['paginator'] === '' ? false : true).html(data['paginator']);
            $('#questionCount').html(data['question_counter']);
            render_search_tags(data['query_data']['tags'], data['query_string']);
            if(data['faces'].length > 0) {
                $('#contrib-users > a').remove();
                $('#contrib-users').append(data['faces'].join(''));
            }
            render_related_tags(data['related_tags'], data['query_string']);
            render_relevance_sort_tab(data['query_string']);
            set_active_sort_tab(sortMethod, data['query_string']);
            set_section_tabs(data['query_string']);
            if(data['feed_url']){
                // Change RSS URL
                $("#ContentLeft a.rss:first").attr("href", data['feed_url']);
            }

            query.focus();

            //show new div with a fadeIn effect
            old_list.fadeOut(200, function() {
                old_list.remove();
                new_list.attr('id', q_list_sel);
                new_list.fadeIn(400);            
            });
        }
    }

    /* *********************************** */

    var try_again = function(){
        running = false;
        eval_query();
    }

    var send_query = function(query_text){
        $.ajax({
            url: search_url,
            dataType: 'json',
            success: render_result,
            complete: try_again,
            cache: false
        });
        prev_text = query_text;
        var context = { state:1, rand:Math.random() };
        var title = "Questions";
        var query = search_url;
        History.pushState( context, title, query );
    }

    var reset_query = function(new_url, sort_method){
        $.ajax({
            url: search_url,
            //data: {reset_query: true, sort: sort_method},
            dataType: 'json',
            success: render_result,
            complete: try_again
        });
        prev_text = '';
        var context = { state:1, rand:Math.random() };
        var title = "Questions";
        var query = new_url;
        History.pushState( context, title, query );
    }

    var refresh_main_page = function (){
        $.ajax({
            url: askbot['urls']['questions'],
            data: {preserve_state: true},
            dataType: 'json',
            success: render_result
        });

        var context = { state:1, rand:Math.random() };
        var title = "Questions";
        var query = askbot['urls']['questions'];
        History.pushState( context, title, query );
    };

    /* *************************************** */

    var activate_search_tags = function(query_string){
        var search_tags = $('#searchTags .tag-left');
        $.each(search_tags, function(idx, element){
            var tag = new Tag();
            tag.decorate($(element));
            //todo: setDeleteHandler and setHandler
            //must work after decorate & must have getName
            tag.setDeleteHandler(
                    function(){
                        remove_search_tag(tag.getName(), query_string);
                    }
            );
        });
    };

    if(command === 'refresh') {
        query = $('input#keywords');
        refresh_main_page();
    } else if(command === 'init') {
        //live search for the main page
        activate_search_tags(query_string);
        main_page_search_listen();
    }
};
