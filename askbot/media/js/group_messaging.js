var HideableWidget = function() {
    Widget.call(this);
};
inherits(HideableWidget, Widget);

HideableWidget.prototype.setState = function(state) {
    this._state = state;
    if (this._element) {
        if (state === 'shown') {
            this._element.show();
        } else if (state === 'hidden') {
            this._element.hide();
        }
    }
};

HideableWidget.prototype.onAfterShow = function() {};

HideableWidget.prototype.show = function() {
    this.setState('shown');
    this.onAfterShow();
};

HideableWidget.prototype.hide = function() {
    this.setState('hidden');
};

HideableWidget.prototype.decorate = function(element) {
    this._element = element;
};

/**
 * @constructor
 */
var MessageComposer = function() {
    HideableWidget.call(this);
};
inherits(MessageComposer, HideableWidget);

MessageComposer.prototype.send = function() {
};

MessageComposer.prototype.onAfterCancel = function(handler) {
    if (handler) {
        this._onAfterCancel = handler;
    } else {
        return this._onAfterCancel();
    }
};

/** override these two 
 * @param {object} data - the response data
 * these functions will run after .send() receives
 * the response
 */
MessageComposer.prototype.onSendSuccessInternal = function(data) {};
MessageComposer.prototype.onSendErrorInternal = function(data) {};

MessageComposer.prototype.onSendSuccess = function(callback) {
    if (callback) {
        this._onSendSuccess = callback;
    } else if (this._onSendSuccess) {
        this._onSendSuccess();
    }
};

MessageComposer.prototype.onSendError = function(callback) {
    if (callback) {
        this._onSendError = callback;
    } else if (this._onSendError) {
        this._onSendError();
    }
};

MessageComposer.prototype.onAfterShow = function() {
    this._textarea.focus();
};

MessageComposer.prototype.cancel = function() {
    this._textarea.val('');
    this._textareaError.html('');
    this.hide();
    this.onAfterCancel();
};

MessageComposer.prototype.setPostData = function(data) {
    this._postData = data;
};

MessageComposer.prototype.getPostData = function() {
    return this._postData;
};

MessageComposer.prototype.setSendUrl = function(url) {
    this._sendUrl = url;
};

MessageComposer.prototype.getInputData = function() {
    return {'text': this._textarea.val()};
};

MessageComposer.prototype.dataIsValid = function() {
    var text = $.trim(this._textarea.val());
    if (text === '') {
        this._textareaError.html(gettext('required'));
        return false;
    }
    return true;
};

MessageComposer.prototype.send = function() {
    var url = this._sendUrl;
    var data = this.getPostData() || {};
    var inputData = this.getInputData();
    $.extend(data, inputData);
    var me = this;
    data['text'] = this._textarea.val();
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: url,
        data: data,
        cache: false,
        success: function(data) {
            if (data['success']) {
                me.onSendSuccessInternal(data);
                me.onSendSuccess();
            } else {
                me.onSendErrorInternal(data);
                me.onSendError();
            }
        }
    });
};

MessageComposer.prototype.createDom = function() {
    this._element = this.makeElement('div');
    this.hide();
    this._element.addClass('message-composer');
    //create textarea
    var label = this.makeElement('label');
    label.html(gettext('Your message:'));
    this._element.append(label);
    var error = this.makeElement('label');
    error.addClass('errors');
    this._element.append(error);
    this._element.append($('<br/>'));
    this._textareaError = error;
    var textarea = this.makeElement('textarea');
    this._element.append(textarea);
    this._textarea = textarea;
    //send button
    var me = this;
    var sendBtn = this.makeButton(
                        gettext('send'),
                        function() {
                            if (me.dataIsValid()){
                                me.send();
                            }
                        }
                    );
    sendBtn.addClass('submit');
    this._element.append(sendBtn);

    //cancel button
    var cancelBtn = this.makeButton(
                        gettext('cancel'),
                        function() { me.cancel(); }
                    );
    cancelBtn.addClass('submit');
    this._element.append(cancelBtn);
};


/**
 * @constructor
 */
var NewThreadComposer = function() {
    MessageComposer.call(this);
};
inherits(NewThreadComposer, MessageComposer);

NewThreadComposer.prototype.cancel = function() {
    this._toInput.val('');
    this._toInputError.html('');
    NewThreadComposer.superClass_.cancel.call(this);
};

NewThreadComposer.prototype.onAfterShow = function() {
    this._toInput.focus();
};

NewThreadComposer.prototype.onSendErrorInternal = function(data) {
    var missingUsers = data['missing_users']
    if (missingUsers) {
        var errorTpl = ngettext(
                            'user {{str}} does not exist',
                            'users {{str}} do not exist',
                            missingUsers.length
                        )
        error = errorTpl.replace('{{str}}', joinAsPhrase(missingUsers));
        this._toInputError.html(error);
    }
};

NewThreadComposer.prototype.getInputData = function() {
    var data = NewThreadComposer.superClass_.getInputData.call(this);
    data['to_usernames'] = $.trim(this._toInput.val());
    return data;
};

NewThreadComposer.prototype.dataIsValid = function() {
    var superIsValid = NewThreadComposer.superClass_.dataIsValid.call(this);
    var to = $.trim(this._toInput.val());
    if (to === '') {
        this._toInputError.html(gettext('required'));
        return false;
    }
    return superIsValid;
};

NewThreadComposer.prototype.createDom = function() {
    NewThreadComposer.superClass_.createDom.call(this);
    var element = this.getElement();

    var toInput = this.makeElement('input');
    toInput.addClass('recipients');
    element.prepend(toInput);
    this._toInput = toInput;

    var userSelectHandler = function() {};

    var usersAc = new AutoCompleter({
        url: '/get-users-info/',//askbot['urls']['get_users_info'],
        preloadData: true,
        minChars: 1,
        useCache: true,
        matchInside: true,
        maxCacheLength: 100,
        delay: 10,
        onItemSelect: userSelectHandler
    });

    usersAc.decorate(toInput);

    var label = this.makeElement('label');
    label.html(gettext('Recipient:'));
    element.prepend(label);
    var error = this.makeElement('label');
    this._element.append($('<br/>'));
    error.addClass('errors');
    this._toInputError = error;
    label.after(error);
};


/**
 * @constructor
 */
var ThreadsList = function() {
    HideableWidget.call(this);
};
inherits(ThreadsList, HideableWidget);


/**
 * @constructor
 */
var Message = function() {
    Widget.call(this);
};
inherits(Message, Widget);


/**
 * @constructor
 */
var Thread = function() {
    HideableWidget.call(this);
};
inherits(Thread, HideableWidget);


/**
 * @contsructor
 */
var MessageCenter = function() {
    Widget.call(this);
};
inherits(MessageCenter, Widget);

MessageCenter.prototype.setState = function(state) {
    this._editor.hide();
    this._threadsList.hide();
    //this._thread.hide();
    if (state === 'compose') {
        this._editor.show();
    } else if (state === 'show-list') {
        this._threadsList.show();
    } else if (state === 'show-thread') {
        this._thread.show();
    }
};

MessageCenter.prototype.decorate = function(element) {
    this._element = element;
    this._firstCol = element.find('.first-col');
    this._secondCol = element.find('.second-col');
    //read sender list
    //read message list
    var threads = new ThreadsList();
    threads.decorate($('.threads-list'));
    this._threadsList = threads;

    var me = this;
    //create editor
    var editor = new NewThreadComposer();
    this._secondCol.append(editor.getElement());
    editor.setSendUrl(element.data('createThreadUrl'));
    editor.onAfterCancel(function() { me.setState('show-list') });
    editor.onSendSuccess(function() {
        me.setState('show-list');
        notify.show(gettext('message sent'), true);
    });
    this._editor = editor;

    //activate compose button
    var btn = element.find('button.compose');
    this._composeBtn = btn;
    setupButtonEventHandlers(btn, function(){ me.setState('compose') });
};

var msgCtr = new MessageCenter();
msgCtr.decorate($('.group-messaging'));
