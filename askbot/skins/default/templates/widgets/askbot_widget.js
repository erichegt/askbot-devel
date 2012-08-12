var AskbotAskWidget = {
  element_id: "AskbotAskWidget",
  widgetToggle: function() {
    element = document.getElementById(this.element_id);
    element.style.visibility = (element.style.visibility == "visible") ? "hidden" : "visible";
  },
  toHtml: function() {
    //document.write('<link rel="stylesheet" href="http://{{host}}{{STATIC_URL}}askbot-modal.css"/>');   
    document.write(this.createButton());
    document.write('<link rel="stylesheet" href="http://{{host}}/static/default/media/style/askbot-modal.css"/>');   
    {%if widget.outer_style %}
    document.write('<style>{{widget.outer_style}}</style>');   
    {%endif%}
    //creating the div
    document.write("<div id='" + this.element_id + "'>");
    document.write("<a href='#' id='AskbotModalCLose' onClick='AskbotAskWidget.widgetToggle();'>Close</a>");
    document.write("<div>");
    document.write("<iframe src='http://{{host}}{% url ask_by_widget widget.id %}' />");
    document.write("</div>");
    document.write("</div>");
  },
  createButton: function() {
    var label="{{widget.title}}"; //TODO: add to the model
    var button = '<div id="AskbotAskButton"><a href="#" onClick="AskbotAskWidget.widgetToggle();">' + label + '</a></div>';
    //document.write(button);
    return button;
  }
};

AskbotAskWidget.toHtml();

