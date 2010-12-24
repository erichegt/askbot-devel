var prevSortMethod = sortMethod;
$(document).ready(function(){
    var query = $('input#keywords');
    var prev_text = $.trim(query.val());
    var running = false;
    var q_list_sel = 'listA';//id of question listing div

    var refresh_x_button = function(){
        if ($.trim(query.val()).length > 0){
            if (query.attr('class') == 'searchInput'){
                query.attr('class', 'searchInputCancelable');
                x_button = $('<input class="cancelSearchBtn" type="button" name="reset_query"/>');
                //x_button.click(reset_query);
                x_button.val('x');
                x_button.click(
                    function(){
                        query.val('');
                        if (sortMethod == 'relevance-desc'){
                            sortMethod = prevSortMethod;
                        }
                        reset_query(sortMethod);
                    }
                );
                query.after(x_button);
            }
        }
        else {
            $('input[name=reset_query]').remove();
            query.attr('class', 'searchInput');
        }
    };

    var eval_query = function(){
        cur_text = $.trim(query.val());
        if (cur_text != prev_text && running === false){
            if (cur_text.length >= minSearchWordLength){
                if (prev_text.length === 0 && showSortByRelevance){
                    if (sortMethod == 'activity-desc'){
                        prevSortMethod = sortMethod;
                        sortMethod = 'relevance-desc';
                    }
                }
                send_query(cur_text, sortMethod);
                running = true;
            }
            else if (cur_text.length === 0){
                if (sortMethod == 'relevance-desc'){
                    sortMethod = prevSortMethod;
                }
                reset_query(sortMethod);
                running = true;
            }
        }
    }

    var listen = function(){
        running = false;
        refresh_x_button();
        query.keydown(function(e){
            refresh_x_button();
            if (running === false){
                setTimeout(eval_query, 50);
            }
        });
        query.keyup(function(){
            refresh_x_button();
        });
    }

    var render_counter = function(count, word, counter_class){
        var output = '<div class="votes">' +
                    '<span class="item-count ' + counter_class + '">' +
                        count;
        if (counter_class == 'accepted'){
            output += '&#10003;'
        }
        output +=   '</span>' +
                    '<div>' + word + '</div>' +
                '</div>';
        return output;
    }

    var render_title = function(result){
        return '<h2>' +
                    '<a title="' + result['summary'] + '" ' +
                        'href="' + 
                            askbot['urls']['question_url_template']
                            .replace('{{QuestionID}}', result['id']) +
                    '">' +
                        result['title'] +
                    '</a>' +
                '</h2>';
    };

    var render_user_link = function(result){
        if (result['u_id'] !== false){
            var u_slug = result['u_name'].toLowerCase().replace(/ +/g, '-');
            return '<a ' +
                        'href="' + 
                            askbot['urls']['user_url_template']
                            .replace('{{user_id}}', result['u_id'])
                            .replace('{{slug}}', u_slug) +
                    '">' +
                        result['u_name'] +
                    '</a> ';
        }
        else {
            return '';
        }
    };

    var render_badge = function(result, key){
        return '<span ' + 
                    'title="' + result[key + '_title'] + '"' +
                '>' +
                '<span ' +
                    'class="' + result[key + '_css_class'] + '"' +
                '>' + result[key + '_badge_symbol'] + '</span>' +
                '<span class="badgecount">' + result[key] + '</span>';
    };

    var render_user_badge_and_karma = function(result){
        var rep_title = result['u_rep'] + ' ' + result['u_rep_word'];
        var html = '<span ' +
                        'class="reputation-score" ' +
                        'title="' + rep_title + '"' +
                    '>' + result['u_rep'] + '</span>';
        if (result['u_gold'] > 0){
            html += render_badge(result, 'u_gold');
        }
        if (result['u_silver'] > 0){
            html += render_badge(result, 'u_silver');
        }
        if (result['u_bronze'] > 0){
            html += render_badge(result, 'u_bronze');
        }
        return html;
    };

    var render_user_info = function(result){
        var user_html = 
        '<div class="userinfo">' +
            '<span class="relativetime" ' +
                'title="' + result['timestamp'] + '"' +
            '>' +
            result['timesince'] +
            '</span> ' +
            render_user_link(result) +
            //render_user_badge_and_karma(result) +
        '</div>';
        return user_html;
    };

    var render_tag = function(tag_name){
        var url = askbot['urls']['questions'] +
                    '?tags=' + encodeURI(tag_name);
        var tag_title = $.i18n._(
                            "see questions tagged '{tag}'"
                        ).replace(
                            '{tag}',
                            tag_name
                        );
        return '<a ' +
                    'href="' + url + '" ' + 
                    'title="' + tag_title + '" rel="tag"' +
                '>' + tag_name + '</a>';
    };

    var render_tags = function(tags){
        var tags_html = '<div class="tags">';
        for (var i=0; i<tags.length; i++){
            tags_html += render_tag(tags[i]);
        }
        tags_html += '</div>';
        return tags_html;
    };

    var render_question = function(question){
        var entry_html = 
        '<div class="short-summary">' + 
            '<div class="counts">' +
                render_counter(
                    question['votes'],
                    question['votes_word'],
                    question['votes_class']
                ) +
                render_counter(
                    question['answers'],
                    question['answers_word'],
                    question['answers_class']
                ) +
                render_counter(
                    question['views'],
                    question['views_word'],
                    question['views_class']
                ) +
            '</div>' + 
            render_title(question) +
            render_user_info(question) +
            render_tags(question['tags']) +
        '</div>';
        return entry_html;
    };

    var render_question_list = function(questions){
        var output = '';
        for (var i=0; i<questions.length; i++){
            output += render_question(questions[i]);
        }
        return output;
    };

    var render_faces = function(faces){
        if (faces.length === 0){
            return;
        }
        $('#contrib-users>a').remove();
        var html = '';
        for (var i=0; i<faces.length; i++){
            html += faces[i];
        }
        $('#contrib-users').append(html);
    };

    var render_related_tags = function(tags){
        if (tags.length === 0){
            return;
        }
        var html = '';
        for (var i=0; i<tags.length; i++){
            html += render_tag(tags[i]['name']);
            html += '<span class="tag-number">&#215; ' +
                        tags[i]['used_count'] +
                    '</span>' +
                    '<br />';
        }
        $('#related-tags').html(html);
    };

    var render_paginator = function(paginator){
        var pager = $('#pager');
        if (paginator === ''){
            pager.hide();
            return;
        }
        else {
            pager.show();
            pager.html(paginator);
        }
    };

    var set_question_count = function(count_html){
        $('#question-count').html(count_html);
    };

    var create_relevance_tab = function(){
        relevance_tab = $('<a></a>');
        relevance_tab.attr('href', '?sort=relevance-desc');
        relevance_tab.attr('id', 'by_relevance');
        relevance_tab.html(sortButtonData['relevance']['label']);
        return relevance_tab;
    }

    var set_active_sort_tab = function(sort_method){
        var tabs = $('#sort_tabs>a');
        tabs.attr('class', 'off');
        tabs.each(function(index, element){
            var tab = $(element);
            var tab_name = tab.attr('id').replace(/^by_/,'');
            if (tab_name in sortButtonData){
                tab.attr(
                    'href',
                    '?sort=' + tab_name + '-desc'
                );
                tab.attr(
                    'title',
                    sortButtonData[tab_name]['desc_tooltip']
                );
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

    var render_relevance_sort_tab = function(){
        if (showSortByRelevance === false){
            return;
        }
        var relevance_tab = $('#by_relevance');
        if (prev_text && prev_text.length > 0){
            if (relevance_tab.length == 0){
                relevance_tab = create_relevance_tab();
                $('#sort_tabs>span').after(relevance_tab);
            }
        }
        else {
            if (relevance_tab.length > 0){
                relevance_tab.remove();
            }
        }
    };

    var render_result = function(data, text_status, xhr){
        var old_list = $('#' + q_list_sel);
        var new_list = $('<div></div>');
        if (data['questions'].length > 0){
            new_list.html(render_question_list(data['questions']));
            old_list.hide();
            old_list.after(new_list);
            old_list.remove();
            //rename new div to old
            new_list.attr('id', q_list_sel);
            render_paginator(data['paginator']);
            set_question_count(data['question_counter']);
            render_faces(data['faces']);
            render_related_tags(data['related_tags']);
            render_relevance_sort_tab();
            set_active_sort_tab(sortMethod);
            query.focus();
        }
        //show new div
    }

    var try_again = function(){
        running = false;
        eval_query();
    }

    var send_query = function(query_text, sort_method){
        var post_data = {query: query_text};
        $.ajax({
            url: askbot['urls']['questions'],
            data: {query: query_text, sort: sort_method},
            dataType: 'json',
            success: render_result,
            complete: try_again
        });
        prev_text = query_text;
    }

    var reset_query = function(sort_method){
        refresh_x_button();
        $.ajax({
            url: askbot['urls']['questions'],
            data: {reset_query: true, sort: sort_method},
            dataType: 'json',
            success: render_result,
            complete: try_again
        });
        prev_text = '';
    }

    listen();
});
