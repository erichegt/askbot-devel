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

HideableWidget.prototype.show = function() {
    this.setState('shown');
};

HideableWidget.prototype.hide = function() {
    this.setState('hidden');
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

MessageComposer.prototype.onAfterSend = function(handler) {
    if (handler) {
        this._onAfterSend = handler;
    } else {
        return this._onAfterSend();
    }
};

MessageComposer.prototype.cancel = function() {
    this._textarea.val('');
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

MessageComposer.prototype.send = function() {
    var url = this._sendUrl;
    var data = this.getPostData();
    var me = this;
    data['text'] = this._textarea.val();
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: url,
        data: data,
        cache: false,
        success: function() { me.onAfterSend(); }
    });
};

MessageComposer.prototype.createDom = function() {
    this._element = this.makeElement('div');
    this.hide();
    this._element.addClass('message-composer');
    //create textarea
    var textarea = this.makeElement('textarea');
    this._element.append(textarea);
    this._element.append(this.makeElement('br'));
    this._textarea = textarea;
    //send button
    var me = this;
    var sendBtn = this.makeButton(
                        gettext('send'),
                        function() { me.send(); }
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

    var me = this;
    //create editor
    var editor = new MessageComposer();
    this._secondCol.append(editor.getElement());
    editor.setSendUrl(element.data('createThreadUrl'));
    editor.onAfterCancel(function() { me.setState('show-list') });
    editor.onAfterSend(function() { 
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
