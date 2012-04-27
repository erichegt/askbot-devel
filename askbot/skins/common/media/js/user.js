$(document).ready(function(){

    var getSelected = function(){

        var id_list = new Array();
        var elements = $('#responses input:checked').parent();

        elements.each(function(index, element){
            var id = $(element).attr('id').replace(/^re_/,'');
            id_list.push(id);
        });

        if (id_list.length === 0){
            alert(gettext('Please select at least one item'));
        }

        return {id_list: id_list, elements: elements};
    };

    var submit = function(id_list, elements, action_type){
        if (action_type == 'delete' || action_type == 'mark_new' || action_type == 'mark_seen' || action_type == 'remove_flag' || action_type == 'delete_post'){
            $.ajax({
                type: 'POST',
                cache: false,
                dataType: 'json',
                data: JSON.stringify({memo_list: id_list, action_type: action_type}),
                url: askbot['urls']['manageInbox'],
                success: function(response_data){
                    if (response_data['success'] == true){
                        if (action_type == 'delete' || action_type == 'remove_flag' || action_type == 'delete_post'){
                            elements.remove();
                        }
                        else if (action_type == 'mark_new'){
                            elements.addClass('highlight');
                            elements.addClass('new');
                            elements.removeClass('seen');
                        }
                        else if (action_type == 'mark_seen'){
                            elements.removeClass('highlight');
                            elements.addClass('seen');
                            elements.removeClass('new');
                        }
                    }
                    else {
                        showMessage($('#responses'), response_data['message']);
                    }
                }
            });
        }
    };

    var startAction = function(action_type){
        var data = getSelected();
        if (data['id_list'].length === 0){
            return;
        }
        if (action_type == 'delete'){
            msg = ngettext('Delete this notification?',
					'Delete these notifications?', data['id_list'].length);
            if (confirm(msg) === false){
                return;
            }
        }
        if (action_type == 'close'){
            msg = ngettext('Close this entry?',
                    'Close these entries?', data['id_list'].length);
            if (confirm(msg) === false){
                return;
            }
        }
        if (action_type == 'remove_flag'){
            msg = ngettext(
                    'Remove all flags and approve this entry?',
                    'Remove all flags and approve these entries?',
                    data['id_list'].length
                );
            if (confirm(msg) === false){
                return;
            }
        }
        submit(data['id_list'], data['elements'], action_type);
    };
    setupButtonEventHandlers($('#re_mark_seen'), function(){startAction('mark_seen')});
    setupButtonEventHandlers($('#re_mark_new'), function(){startAction('mark_new')});
    setupButtonEventHandlers($('#re_dismiss'), function(){startAction('delete')});
    setupButtonEventHandlers($('#re_remove_flag'), function(){startAction('remove_flag')});
    //setupButtonEventHandlers($('#re_close'), function(){startAction('close')});
    setupButtonEventHandlers(
                    $('#sel_all'),
                    function(){
                        setCheckBoxesIn('#responses .new', true);
                        setCheckBoxesIn('#responses .seen', true);
                    }
    );
    setupButtonEventHandlers(
                    $('#sel_seen'),
                    function(){
                        setCheckBoxesIn('#responses .seen', true);
                    }
    );
    setupButtonEventHandlers(
                    $('#sel_new'),
                    function(){
                        setCheckBoxesIn('#responses .new', true);
                    }
    );
    setupButtonEventHandlers(
                    $('#sel_none'),
                    function(){
                        setCheckBoxesIn('#responses .new', false);
                        setCheckBoxesIn('#responses .seen', false);
                    }
    );

    var reject_post_dialog = new RejectPostDialog();
    reject_post_dialog.decorate($('#reject-edit-modal'));
    setupButtonEventHandlers(
        $('#re_delete_post'),
        function(){
            var data = getSelected();
            if (data['id_list'].length === 0){
                return;
            }
            reject_post_dialog.setSelectedEditIds(data);
            reject_post_dialog.show();
        }
    );
    //setupButtonEventHandlers($('.re_expand'),
    //                function(e){
    //                    e.preventDefault();
    //                    var re_snippet = $(this).find(".re_snippet:first")
    //                    var re_content = $(this).find(".re_content:first")
    //                    $(re_snippet).slideToggle();
    //                    $(re_content).slideToggle();
    //                }
    //);

    $('.badge-context-toggle').each(function(idx, elem){
        var context_list = $(elem).parent().next('ul');
        if (context_list.children().length > 0){
            $(elem).addClass('active');
            var toggle_display = function(){
                if (context_list.css('display') == 'none'){
                    $('.badge-context-list').hide();
                    context_list.show();
                } else {
                    context_list.hide();
                }
            };
            $(elem).click(toggle_display);
        }
    });
});

/**
 * @constructor
 * manages post/edit reject reasons
 * in the post moderation view
 */
var RejectPostDialog = function(){
    WrappedElement.call(this);
    this._selected_edit_ids = null;
    this._state = null;//'select', 'preview', 'add-new'
};
inherits(RejectPostDialog, WrappedElement);

RejectPostDialog.prototype.setSelectedEditIds = function(ids){
    this._selected_edit_ids = ids;
};

RejectPostDialog.prototype.setState = function(state){
    this._state = state;
    if (this._element){
        this._selector.hide();
        this._adder.hide();
        this._previewer.hide();
        if (state === 'select'){
            this._selector.show();
        } else if (state === 'preview'){
            this._previewer.show();
        } else if (state === 'add-new'){
            this._adder.show();
        }
    }
};

RejectPostDialog.prototype.show = function(){
    $(this._element).modal('show');
};

RejectPostDialog.prototype.addReason = function(title, description){
    $(this._adder).find('.select-other-reason').show();
};

RejectPostDialog.prototype.decorate = function(element){
    this._element = element;
    //set default state according to the # of available reasons
    this._selector = $(element).find('#reject-edit-modal-select');
    this._adder = $(element).find('#reject-edit-modal-add-new');
    this._previewer = $(element).find('#reject-edit-modal-preview');
    if (this._selector.find('li').length > 0){
        this.setState('select');
    } else {
        this.setState('add-new');
        $(this._adder).find('.select-other-reason').hide();
    }

    //var select_box = new SelectBox();
    //select_box.decorate($(this._selector.find('.select-box')));

    //setup tipped-inputs
    var me = this;
    setupButtonEventHandlers(
        element.find('.select-other-reason'),
        function(){ me.setState('select') }
    )
    setupButtonEventHandlers(
        element.find('.add-new-reason'),
        function(){ me.setState('add-new') }
    );
    setupButtonEventHandlers(
        element.find('.cancel'),
        function() { $(element).modal('hide') }
    );
};

/**
 * @constructor
 * allows to follow/unfollow users
 */
var FollowUser = function(){
    WrappedElement.call(this);
    this._user_id = null;
    this._user_name = null;
};
inherits(FollowUser, WrappedElement);

/**
 * @param {string} user_name
 */
FollowUser.prototype.setUserName = function(user_name){
    this._user_name = user_name;
};

FollowUser.prototype.decorate = function(element){
    this._element = element;
    this._user_id = parseInt(element.attr('id').split('-').pop());
    this._available_action = element.children().hasClass('follow') ? 'follow':'unfollow';
    var me = this;
    setupButtonEventHandlers(this._element, function(){ me.go() });
};

FollowUser.prototype.go = function(){
    if (askbot['data']['userIsAuthenticated'] === false){
        var message = gettext('Please <a href="%(signin_url)s">signin</a> to follow %(username)s');
        var message_data = {
            signin_url: askbot['urls']['user_signin'] + '?next=' + window.location.href,
            username: this._user_name
        }
        message = interpolate(message, message_data, true);
        showMessage(this._element, message);
        return;
    }
    var user_id = this._user_id;
    if (this._available_action === 'follow'){
        var url = askbot['urls']['follow_user'];
    } else {
        var url = askbot['urls']['unfollow_user'];
    }
    var me = this;
    $.ajax({
        type: 'POST',
        cache: false,
        dataType: 'json',
        url: url.replace('{{userId}}', user_id),
        success: function(){ me.toggleState() }
    });
};

FollowUser.prototype.toggleState = function(){
    if (this._available_action === 'follow'){
        this._available_action = 'unfollow';
        var unfollow_div = document.createElement('div'); 
        unfollow_div.setAttribute('class', 'unfollow');
        var red_div = document.createElement('div');
        red_div.setAttribute('class', 'unfollow-red');
        red_div.innerHTML = interpolate(gettext('unfollow %s'), [this._user_name]);
        var green_div = document.createElement('div');
        green_div.setAttribute('class', 'unfollow-green');
        green_div.innerHTML = interpolate(gettext('following %s'), [this._user_name]);
        unfollow_div.appendChild(red_div);
        unfollow_div.appendChild(green_div);
        this._element.html(unfollow_div);
    } else {
        var follow_div = document.createElement('div'); 
        follow_div.innerHTML = interpolate(gettext('follow %s'), [this._user_name]);
        follow_div.setAttribute('class', 'follow');
        this._available_action = 'follow';
        this._element.html(follow_div);
    }
};

/**
 * @constructor
 * @param {string} name
 */
var UserGroup = function(name){
    WrappedElement.call(this);
    this._name = name;
};
inherits(UserGroup, WrappedElement);

UserGroup.prototype.getDeleteHandler = function(){
    var group_name = this._name;
    var me = this;
    var groups_container = me._groups_container;
    return function(){
        var data = {
            user_id: askbot['data']['viewUserId'],
            group_name: group_name,
            action: 'remove'
        };
        $.ajax({
            type: 'POST',
            dataType: 'json',
            data: data,
            cache: false,
            url: askbot['urls']['edit_group_membership'],
            success: function(){
                groups_container.removeGroup(me);
            }
        });
    };
};

UserGroup.prototype.getName = function(){
    return this._name;
};

UserGroup.prototype.setGroupsContainer = function(container){
    this._groups_container = container;
};

UserGroup.prototype.decorate = function(element){
    this._element = element;
    this._name = $.trim(element.html());
    var deleter = new DeleteIcon();
    deleter.setHandler(this.getDeleteHandler());
    deleter.setContent('x');
    this._element.append(deleter.getElement());
    this._delete_icon = deleter;
};

UserGroup.prototype.createDom = function(){
    var element = this.makeElement('li');
    element.html(this._name + ' ');
    this._element = element;
    this.decorate(element);
};

UserGroup.prototype.dispose = function(){
    this._delete_icon.dispose();
    this._element.remove();
};

/**
 * @constructor
 */
var GroupsContainer = function(){
    WrappedElement.call(this);
};
inherits(GroupsContainer, WrappedElement);

GroupsContainer.prototype.decorate = function(element){
    this._element = element;
    var groups = [];
    var group_names = [];
    var me = this;
    //collect list of groups
    $.each(element.find('li'), function(idx, li){
        var group = new UserGroup();
        group.setGroupsContainer(me);
        group.decorate($(li));
        groups.push(group);
        group_names.push(group.getName());
    });
    this._groups = groups;
    this._group_names = group_names;
};

GroupsContainer.prototype.addGroup = function(group_name){
    if ($.inArray(group_name, this._group_names) > -1){
        return;
    }
    var group = new UserGroup(group_name);
    group.setGroupsContainer(this);
    this._groups.push(group);
    this._group_names.push(group_name);
    this._element.append(group.getElement());
};

GroupsContainer.prototype.removeGroup = function(group){
    var idx = $.inArray(group, this._groups);    
    if (idx === -1){
        return;
    }
    this._groups.splice(idx, 1);
    this._group_names.splice(idx, 1);
    group.dispose();
};

var GroupAdderWidget = function(){
    WrappedElement.call(this);
    this._state = 'display';//display or edit
};
inherits(GroupAdderWidget, WrappedElement);

/**
 * @param {string} state
 */
GroupAdderWidget.prototype.setState = function(state){
    if (state === 'display'){
        this._element.html(gettext('add group'));
        this._input.hide();
        this._input.val('');
        this._button.hide();
    } else if (state === 'edit'){
        this._element.html(gettext('cancel'));
        this._input.show();
        this._input.focus();
        this._button.show();
    } else {
        return;
    }
    this._state = state;
};

GroupAdderWidget.prototype.getValue = function(){
    return this._input.val();
};

GroupAdderWidget.prototype.addGroup = function(group){
    this._groups_container.addGroup(group);
};

GroupAdderWidget.prototype.getAddGroupHandler = function(){
    var me = this;
    return function(){
        var group_name = me.getValue();
        var data = {
            group_name: group_name,
            user_id: askbot['data']['viewUserId'],
            action: 'add'
        };
        $.ajax({
            type: 'POST',
            dataType: 'json',
            data: data,
            cache: false,
            url: askbot['urls']['edit_group_membership'],
            success: function(data){
                if (data['success'] == true){
                    me.addGroup(group_name);
                    me.setState('display');
                } else {
                    var message = data['message'];
                    showMessage(me.getElement(), message, 'after');
                }
            }
        });
    };
};

GroupAdderWidget.prototype.setGroupsContainer = function(container){
    this._groups_container = container;
};

GroupAdderWidget.prototype.toggleState = function(){
    if (this._state === 'display'){
        this.setState('edit');
    } else if (this._state === 'edit'){
        this.setState('display');
    }
};

GroupAdderWidget.prototype.decorate = function(element){
    this._element = element;
    var input = this.makeElement('input');
    this._input = input;

    var groupsAc = new AutoCompleter({
        url: askbot['urls']['get_groups_list'],
        preloadData: true,
        minChars: 1,
        useCache: true,
        matchInside: false,
        maxCacheLength: 100,
        delay: 10
    });
    groupsAc.decorate(input);

    var button = this.makeElement('button');
    button.html(gettext('add'));
    this._button = button;
    element.before(input);
    input.after(button);
    this.setState('display');
    setupButtonEventHandlers(button, this.getAddGroupHandler());
    var me = this;
    setupButtonEventHandlers(
        element,
        function(){ me.toggleState() }
    );
};

/**
 * @constructor
 * allows editing user groups
 */
var UserGroupsEditor = function(){
    WrappedElement.call(this);
};
inherits(UserGroupsEditor, WrappedElement);

UserGroupsEditor.prototype.decorate = function(element){
    this._element = element;
    var add_link = element.find('#add-group');
    var adder = new GroupAdderWidget();
    adder.decorate(add_link);

    var groups_container = new GroupsContainer();
    groups_container.decorate(element.find('ul'));
    adder.setGroupsContainer(groups_container);
    //todo - add group deleters
};

(function(){
    var fbtn = $('.follow-toggle');
    if (fbtn.length === 1){
        var follow_user = new FollowUser();
        follow_user.decorate(fbtn);
        follow_user.setUserName(askbot['data']['viewUserName']);
    }
    if (askbot['data']['userIsAdminOrMod']){
        var group_editor = new UserGroupsEditor();
        group_editor.decorate($('#user-groups'));
    } else {
        $('#add-group').remove();
    }
})();
