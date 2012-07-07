/**
 * @constructor
 */
var PerThreadTagModerator = function() {
    WrappedElement.call(this);
    this._tagId = undefined;
    this._threadId = undefined;
};
inherits(PerThreadTagModerator, WrappedElement);

PerThreadTagModerator.prototype.setTagId = function(id) {
    this._tagId = id;
};

PerThreadTagModerator.prototype.decorate = function(element) {
    this._element = element;
    this._threadId = element.data('threadId');

    var acceptBtn = element.find('button.accept');
    var rejectBtn = element.find('button.reject');

    var mouseEnterHandler = function() {
        acceptBtn.fadeIn('fast');
        rejectBtn.fadeIn('fast');
        return false;
    };
    var mouseLeaveHandler = function() {
        acceptBtn.stop().hide();
        rejectBtn.stop().hide();
        return false;
    };

    element.mouseenter(mouseEnterHandler);
    element.mouseleave(mouseLeaveHandler);
    //threadInfo.hover(mouseEnterHandler, mouseLeaveHandler);
    //element.hover(mouseEnterHandler, mouseLeaveHandler);
};

var AllThreadsTagModerator = function() {
    WrappedElement.call(this);
    this._controls_template = undefined;
};
inherits(AllThreadsTagModerator, WrappedElement);

AllThreadsTagModerator.prototype.decorate = function(element) {
    this._element = element;

    //var controls = new TagModerationControls();
    //controls.setParent(this);

    //var tagId = $(element).data('tagId');
    //controls.setTagId(tagId);

    var threads_data = [];
    $(element).find('.thread-info').each(function(idx, element) {
        var id = $(element).data('threadId');
        var title = $(element).data('threadTitle');
        threads_data.push([id, title]);
    });

    var buttons = element.find('button');
    /*element.prev().hover(
        function(){ buttons.show();},
        function(){ buttons.hide() }
    );*/
    //controls.setThreadsData(threads_data);
    //add data to controls

    //var controls_element = $(element).find('controls');
    //controls_element.append(controls.getElement());

};

(function() {
    $('.suggested-tag-row').each(function(idx, element) {
        var tagEntry = $(element);
        var tagId = tagEntry.data('tagId');

        var mod = new AllThreadsTagModerator();
        mod.decorate(tagEntry.next());

        $('.thread-info').each(function(idx, element) {
            var mod = new PerThreadTagModerator();
            mod.setTagId(tagId);
            mod.decorate($(element));
        });

    });
})();
