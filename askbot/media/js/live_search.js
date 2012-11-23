var SearchDropMenu = function() {
    WrappedElement.call(this);
    this._data = undefined;
}
inherits(SearchDropMenu, WrappedElement);

SearchDropMenu.prototype.setData = function(data) {
    this._data = data;
};

SearchDropMenu.prototype.setAskHandler = function(handler) {
    this._askHandler = handler;
};

/**
 * assumes that data is already set
 */
SearchDropMenu.prototype.render = function() {
    this._element.empty();
    var list = this._element;
    $.each(this._data, function(idx, item) {
        var listItem = $('<li></li>');
        var link = $('<a></a>');
        link.attr('href', item['url']);
        link.html(item['title']);
        listItem.append(link);
        list.append(listItem);
    });
    //add ask button, @todo: make into separate class?
    var listItem = this.makeElement('li');
    this._element.append(listItem);
    var button = this.makeElement('button');
    button.html(gettext('Ask Your Question'))
    listItem.append(button);
    var handler = this._askHandler;
    setupButtonEventHandlers(button, handler);
};

SearchDropMenu.prototype.createDom = function() {
    this._element = this.makeElement('ul');
    this._element.addClass('search-drop-menu');
    this._element.hide();
};

SearchDropMenu.prototype.show = function() {
    this._element.show();
};

SearchDropMenu.prototype.hide = function() {
    this._element.hide();
};

SearchDropMenu.prototype.reset = function() {
    this._data = undefined;
    this._element.empty();
    this._element.hide();
};

var TagWarningBox = function(){
    WrappedElement.call(this);
    this._tags = [];
};
inherits(TagWarningBox, WrappedElement);

TagWarningBox.prototype.createDom = function(){
    this._element = this.makeElement('div');
    this._element
        .css('display', 'block')
        .css('margin', '0 0 13px 2px');
    this._element.addClass('non-existing-tags');
    this._warning = this.makeElement('p');
    this._element.append(this._warning);
    this._tag_container = this.makeElement('ul');
    this._tag_container.addClass('tags');
    this._element.append(this._tag_container);
    this._element.append($('<div class="clearfix"></div>'));
    this._element.hide();
};

TagWarningBox.prototype.clear = function(){
    this._tags = [];
    if (this._tag_container){
        this._tag_container.empty();
    }
    this._warning.hide();
    this._element.hide();
};

TagWarningBox.prototype.addTag = function(tag_name){
   var tag = new Tag();
   tag.setName(tag_name);
   tag.setLinkable(false);
   tag.setDeletable(false);
   var elem = this.getElement();
   this._tag_container.append(tag.getElement());
   this._tag_container.css('display', 'block');
   this._tags.push(tag);
   elem.show();
};

TagWarningBox.prototype.showWarning = function(){
    this._warning.html(
        ngettext(
            'Sorry, this tag does not exist',
            'Sorry, these tags do not exist',
            this._tags.length
        )
    );
    this._warning.show();
};

/**
 * @constructor
 * provides full text search functionality
 * which re-draws contents of the main page
 * in response to the search query
 */
var FullTextSearch = function() {
    WrappedElement.call(this);
    this._running = false;
    this._baseUrl = askbot['urls']['questions'];
    this._q_list_sel = 'question-list';//id of question listing div
    /** @todo: the questions/ needs translation... */
    this._searchUrl = '/scope:all/sort:activity-desc/page:1/'
};
inherits(FullTextSearch, WrappedElement);

/**
 * @param {{boolean=}} optional, if given then function is setter
 * otherwise it is a getter
 * isRunning returns `true` when search is running
 */
FullTextSearch.prototype.isRunning = function(val) {
    if (val === undefined) {
        return this._running;
    } else {
        this._running = val;
    }
};

/**
 * @param {{string}} url for the page displaying search results
 */
FullTextSearch.prototype.setSearchUrl = function(url) {
    this._searchUrl = url;
};

FullTextSearch.prototype.getSearchUrl = function() {
    return this._searchUrl;
};

FullTextSearch.prototype.renderTagWarning = function(tag_list){
    if ( !tag_list ) {
        return;
    }
    var tagWarningBox = this._tag_warning_box;
    tagWarningBox.clear();
    $.each(tag_list, function(idx, tag_name){
        tagWarningBox.addTag(tag_name);
    });
    tagWarningBox.showWarning();
};

FullTextSearch.prototype.runTagSearch = function() {
    var search_tags = $('#ab-tag-search').val().split(/\s+/);
    if (search_tags.length === 0) {
        return;
    }
    var searchUrl = this.getSearchUrl();
    //add all tags to the url
    searchUrl = QSutils.add_search_tag(searchUrl, search_tags);
    var url = this._baseUrl + searchUrl;
    var me = this;
    $.ajax({
        url: url,
        dataType: 'json',
        success: function(data, text_status, xhr){
            me.renderFullTextResult(data, text_status, xhr);
            $('#ab-tag-search').val('');
        },
    });
    this.updateHistory(url);
};

FullTextSearch.prototype.updateHistory = function(url) {
    var context = { state:1, rand:Math.random() };
    History.pushState( context, "Questions", url );
    setTimeout(function(){
            /* HACK: For some weird reson, sometimes 
             * overrides the above pushState so we re-aplly it
             * This might be caused by some other JS plugin.
             * The delay of 10msec allows the other plugin to override the URL.
             */
            History.replaceState(context, "Questions", url);
        },
        10
    );
};

FullTextSearch.prototype.activateTagSearchInput = function() {
    //the autocomplete is set up in tag_selector.js
    var button = $('#ab-tag-search-add');
    if (button.length === 0){//may be absent
        return;
    }
    var me = this;
    var ac = new AutoCompleter({
        url: askbot['urls']['get_tag_list'],
        preloadData: true,
        minChars: 1,
        useCache: true,
        matchInside: true,
        maxCacheLength: 100,
        maxItemsToShow: 20,
        onItemSelect: function(){ this.runTagSearch(); },
        delay: 10
    });
    ac.decorate($('#ab-tag-search'));
    setupButtonEventHandlers(
        button,
        function() { me.runTagSearch() }
    );
    //var tag_search_input = $('#ab-tag-search');
    //tag_search_input.keydown(
    //    makeKeyHandler(13, run_tag_search)
    //);
};

FullTextSearch.prototype.sendTitleSearchQuery = function(query_text) {
    this.isRunning(true);
    this._prevText = query_text;
    var data = {query_text: query_text};
    var me = this;
    $.ajax({
        url: askbot['urls']['titleSearch'],
        data: data,
        dataType: 'json',
        success: function(data, text_status, xhr){
            me.renderTitleSearchResult(data, text_status, xhr);
        },
        complete: function(){
            me.isRunning(false);
            me.evalTitleSearchQuery();
        },
        cache: false
    });
    this.updateHistory(url);
};


FullTextSearch.prototype.sendFullTextSearchQuery = function(query_text) {
    this.isRunning(true);
    var searchUrl = this.getSearchUrl();
    var prevText = this._prevText;
    if(!prevText && query_text && askbot['settings']['showSortByRelevance']) {
        /* If there was no query but there is some
         * query now - and we support relevance search
         * - then switch to it
         */
        searchUrl = QSutils.patch_query_string(
                        searchUrl, 'sort:relevance-desc'
                    );
    }
    this._prevText = this.updateQueryString(query_text);

    /* if something has changed, then reset the page no. */
    searchUrl = QSutils.patch_query_string(searchUrl, 'page:1');
    var url = this._baseUrl + searchUrl;
    var me = this;
    $.ajax({
        url: url,
        dataType: 'json',
        success: function(data, text_status, xhr){
            me.renderFullTextSearchResult(data, text_status, xhr);
        },
        complete: function(){
            me.isRunning(false);
        },
        cache: false
    });
    this.updateHistory(url);
};

FullTextSearch.prototype.refresh = function() {
    this.sendFullTextSearchQuery();/* used for tag search, maybe not necessary */
};

FullTextSearch.prototype.getSearchQuery = function() {
    return $.trim(this._query.val());
};

/**
 * renders title search result in the dropdown under the search input
 */
FullTextSearch.prototype.renderTitleSearchResult = function(data) {
    var menu = this._dropMenu;
    menu.setData(data);
    menu.render();
    menu.show();
};

FullTextSearch.prototype.renderFullTextSearchResult = function(data) {
    if (data['questions'].length === 0) {
        return;
    }

    $('#pager').toggle(data['paginator'] !== '').html(data['paginator']);
    $('#questionCount').html(data['question_counter']);
    this.renderSearchTags(data['query_data']['tags'], data['query_string']);
    if(data['faces'].length > 0) {
        $('#contrib-users > a').remove();
        $('#contrib-users').append(data['faces'].join(''));
    }
    this.renderRelatedTags(data['related_tags'], data['query_string']);
    this.renderRelevanceSortTab(data['query_string']);
    this.renderTagWarning(data['non_existing_tags']);
    this.setActiveSortTab(
        data['query_data']['sort_order'],
        data['query_string']
    );
    if(data['feed_url']){
        // Change RSS URL
        $("#ContentLeft a.rss:first").attr("href", data['feed_url']);
    }

    // Patch scope selectors
    var baseUrl = this._baseUrl;
    $('#scopeWrapper > a.scope-selector').each(function(index) {
        var old_qs = $(this).attr('href').replace(baseUrl, '');
        var scope = QSutils.get_query_string_selector_value(old_qs, 'scope');
        qs = QSutils.patch_query_string(data['query_string'], 'scope:' + scope);
        $(this).attr('href', baseUrl + qs);
    });

    // Patch "Ask your question"
    var askButton = $('#askButton');
    var askHrefBase = askButton.attr('href').split('?')[0];
    askButton.attr(
        'href',
        askHrefBase + data['query_data']['ask_query_string']
    ); /* INFO: ask_query_string should already be URL-encoded! */

    this._query.focus();

    var old_list = $('#' + this._q_list_sel);
    var new_list = $('<div></div>').hide().html(data['questions']);
    new_list.find('.timeago').timeago();

    var q_list_sel = this._q_list_sel;
    old_list.stop(true).after(new_list).fadeOut(200, function() {
        //show new div with a fadeIn effect
        old_list.remove();
        new_list.attr('id', q_list_sel);
        new_list.fadeIn(400);            
    });
};

FullTextSearch.prototype.evalTitleSearchQuery = function() {
    var cur_query = this.getSearchQuery();
    var prevText = this._prevText;
    if (cur_query !== prevText && this.isRunning() === false){
        if (cur_query.length >= askbot['settings']['minSearchWordLength']){
            this.sendTitleSearchQuery(cur_query);
        } else if (cur_query.length === 0){
            this._query.val('');
            this.refreshXButton();
            this._dropMenu.reset();
        }
    }
};

FullTextSearch.prototype.reset = function() {
    this._prevText = '';
    this._dropMenu.reset();
    this._element.val('');
    this._element.focus();
};

FullTextSearch.prototype.refreshXButton = function() {
    if(this.getSearchQuery().length > 0){
        if (this._query.hasClass('searchInput')){
            $('#searchBar').attr('class', 'cancelable');
            this._x_button.show();
        }
    } else {
        this._x_button.hide();
        $('#searchBar').removeClass('cancelable');
    }
};

FullTextSearch.prototype.updateQueryString = function(query_text) {
    if (query_text === undefined) { // handle missing parameter
        query_text = this.getSearchQuery();
    }
    var newUrl = QSutils.patch_query_string(
        this._searchUrl,
        'query:' + encodeURIComponent(query_text),
        query_text === ''   // remove if empty
    );
    this.setSearchUrl(newUrl);
    return query_text;
};

FullTextSearch.prototype.renderRelatedTags = function(tags, query_string){
    if (tags.length === 0) return;

    var html_list = [];
    for (var i=0; i<tags.length; i++){
        var tag = new Tag();
        tag.setName(tags[i]['name']);
        tag.setDeletable(false);
        tag.setLinkable(true);
        tag.setUrlParams(query_string);

        html_list.push(tag.getElement().outerHTML());
        html_list.push('<span class="tag-number">&#215; ');
        html_list.push(tags[i]['used_count']);
        html_list.push('</span>');
        html_list.push('<br />');
    }
    $('#related-tags').html(html_list.join(''));
};

FullTextSearch.prototype.renderSearchTags = function(tags, query_string){
    var search_tags = $('#searchTags');
    search_tags.empty();
    var me = this;
    if (tags.length === 0){
        $('#listSearchTags').hide();
        $('#search-tips').hide();//wrong - if there are search users
    } else {
        $('#listSearchTags').show();
        $('#search-tips').show();
        $.each(tags, function(idx, tag_name){
            var tag = new Tag();
            tag.setName(tag_name);
            tag.setLinkable(false);
            tag.setDeletable(true);
            tag.setDeleteHandler(
                function(){
                    this.removeSearchTag(tag_name, query_string);
                }
            );
            search_tags.append(tag.getElement());
        });
    }
};

FullTextSearch.prototype.createRelevanceTab = function(query_string){
    var relevance_tab = $('<a></a>');
    href = this._baseUrl + QSutils.patch_query_string(query_string, 'sort:relevance-desc');
    relevance_tab.attr('href', href);
    relevance_tab.attr('id', 'by_relevance');
    relevance_tab.html(
        '<span>' + askbot['data']['sortButtonData']['relevance']['label'] + '</span>'
    );
    return relevance_tab;
};

FullTextSearch.prototype.removeSearchTag = function(tag) {
    var searchUrl = this.getSearchUrl()
    searchUrl = QSutils.remove_search_tag(searchUrl, tag);
    this.setSearchUrl(searchUrl);
    this.sendFullTextSearchQuery();
};

FullTextSearch.prototype.setActiveSortTab = function(sort_method, query_string){
    var tabs = $('#sort_tabs > a');
    tabs.attr('class', 'off');
    var baseUrl = this._baseUrl;
    tabs.each(function(index, element){
        var tab = $(element);
        if ( tab.attr('id') ) {
            var tab_name = tab.attr('id').replace(/^by_/,'');
            if (tab_name in askbot['data']['sortButtonData']){
                href = baseUrl + QSutils.patch_query_string(
                                        query_string,
                                        'sort:' + tab_name + '-desc'
                                    );
                tab.attr('href', href);
                tab.attr(
                    'title',
                    askbot['data']['sortButtonData'][tab_name]['desc_tooltip']
                );
                tab.html(
                    askbot['data']['sortButtonData'][tab_name]['label']
                );
            }
        }
    });
    var bits = sort_method.split('-', 2);
    var name = bits[0];
    var sense = bits[1];//sense of sort
    var antisense = (sense == 'asc' ? 'desc':'asc');
    var arrow = (sense == 'asc' ? ' &#9650;':' &#9660;');
    var active_tab = $('#by_' + name);
    active_tab.attr('class', 'on');
    active_tab.attr(
        'title',
        askbot['data']['sortButtonData'][name][antisense + '_tooltip']
    );
    active_tab.html(
        askbot['data']['sortButtonData'][name]['label'] + arrow
    );
};

FullTextSearch.prototype.renderRelevanceSortTab = function(query_string) {
    if (askbot['settings']['showSortByRelevance'] === false){
        return;
    }
    var relevance_tab = $('#by_relevance');
    var prevText = this._prevText;
    if (prevText && prevText.length > 0){
        if (relevance_tab.length == 0){
            relevance_tab = this.createRelevanceTab(query_string);
            $('#sort_tabs>span').after(relevance_tab);
        }
    } else {
        if (relevance_tab.length > 0){
            relevance_tab.remove();
        }
    }
};

FullTextSearch.prototype.makeAskHandler = function() {
    var me = this;
    return function() {
        var query = me.getSearchQuery();
        window.location.href = askbot['urls']['ask'] + '?title=' + query;
    };
};

FullTextSearch.prototype.decorate = function(element) {
    this._element = element;/* this is a bit artificial we don't use _element */
    this._query = element;
    this._x_button = $('input[name=reset_query]');
    this._prevText = this.getSearchQuery();
    this._tag_warning_box = new TagWarningBox();

    var dropMenu = new SearchDropMenu();
    dropMenu.setAskHandler(this.makeAskHandler());
    this._dropMenu = dropMenu;
    element.after(this._dropMenu.getElement());

    var menuCloser = function(){
        dropMenu.reset();
    };
    $(element).click(function(e){ return false });
    $(document).click(menuCloser);

    //the tag search input is optional in askbot
    $('#ab-tag-search').parent().before(
        this._tag_warning_box.getElement()
    );

    // make search tags functional
    var search_tags = $('#searchTags .tag-left');
    var searchUrl = this.getSearchUrl();
    var me = this;
    $.each(search_tags, function(idx, element){
        var tag = new Tag();
        tag.decorate($(element));
        //todo: setDeleteHandler and setHandler
        //must work after decorate & must have getName
        tag.setDeleteHandler(
            function(){
                me.removeSearchTag(tag.getName(), searchUrl);
            }
        );
    });
    // enable x button (search reset)
    this._x_button.click(function () {
        /* wrapped in closure because it's not yet defined at this point */
        me.reset();
    });
    this.refreshXButton();

    // enable query box
    var main_page_eval_handle;
    this._query.keyup(function(e){
        me.refreshXButton();
        if (me.isRunning() === false){
            clearTimeout(main_page_eval_handle);
            main_page_eval_handle = setTimeout(
                function() { me.evalTitleSearchQuery() },
                400
            );
        }
    });

    this.activateTagSearchInput();

    var baseUrl = this._baseUrl;
    var searchUrl = this.getSearchUrl();
    $("form#searchForm").submit(function(event) {
        // if user clicks the button the s(h)e probably wants page reload,
        // so provide that experience but first update the query string
        event.preventDefault();
        me.updateQueryString();
        window.location.href = baseUrl + searchUrl;
    });
};
