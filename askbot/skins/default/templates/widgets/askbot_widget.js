var AskbotAskWidget = {
  element_id: "AskbotAskWidget",
  widgetToggle: function() {
    element = document.getElementById(AskbotAskWidget.element_id);
    element.style.visibility = (element.style.visibility == "visible") ? "hidden" : "visible";
  },
  toHtml: function() {
    var html = AskbotAskWidget.createButton();
    var link = document.createElement('link');
    link.setAttribute("rel", "stylesheet");
    link.setAttribute("href", 'http://{{host}}/static/default/media/style/askbot-modal.css');

    //creating the div
    var motherDiv = document.createElement('div');
    motherDiv.setAttribute("id", AskbotAskWidget.element_id);

    var containerDiv = document.createElement('div');
    motherDiv.appendChild(containerDiv);

    {%if widget.outer_style %}
    outerStyle = document.createElement('style');
    outerStyle.innerText = "{{widget.outer_style}}";
    motherDiv.appendChild(outerStyle);
    {%endif%}

    var closeButton = document.createElement('a');
    closeButton.setAttribute('href', '#');
    closeButton.setAttribute('id', 'AskbotModalClose');
    closeButton.setAttribute('onClick', 'AskbotAskWidget.widgetToggle();');
    closeButton.innerText = 'Close';

    containerDiv.appendChild(closeButton);

    var iframe = document.createElement('iframe');
    iframe.setAttribute('src', 'http://{{host}}{% url ask_by_widget widget.id %}');

    containerDiv.appendChild(iframe);

    var body = document.getElementsByTagName('body')[0];
    if (body){
      body.insertBefore(motherDiv, body.firstChild);
      body.insertBefore(link, body.firstChild);
    }
  },
  createButton: function() {
    var label="{{widget.title}}"; //TODO: add to the model
    var buttonDiv = document.createElement('div');
    buttonDiv.setAttribute('id', "AskbotAskButton");

    var closeButton = document.createElement('button');
    closeButton.setAttribute('onClick', 'AskbotAskWidget.widgetToggle();');
    closeButton.innerText = label;

    buttonDiv.appendChild(closeButton);
    
    return buttonDiv;
  }
};


window.onload = AskbotAskWidget.toHtml;
document.write(AskbotAskWidget.createButton().outerHTML);
