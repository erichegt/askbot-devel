var AskbotAskWidget = {
  element_id: "AskbotAskWidget",
  widgetToggle: function() {
    element = document.getElementById(this.element_id);
    element.style.visibility = (el.style.visibility == "visible") ? "hidden" : "visible";
  },
  toHtml: function() {
    document.write('<link rel="stylesheet" href="https://{{request.get_host}}/embed.css"/>');   
    {%if widget.outer_style %}
    document.write('<style>{{widget.outer_style}}</style>');   
    {%endif%}
    //creating the div
    document.write("<div id='" + this.element_id + "'>");
    document.write("<iframe src='{% url widget_ask %}' />");
    document.write("</div>");
  }
};

AskbotAskWidget.toHtml();
