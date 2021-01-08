// Set up Blockly toolbox and define blocks

Blockly.defineBlocksWithJsonArray([{
    "type": "on_command",
    "message0": "On command / %1 %2 %3 Return Message %4",
    "args0": [
        {
            "type": "field_input",
            "name": "command_name",
            "text": "command"
        },
        {
            "type": "input_dummy"
        },
        {
            "type": "input_statement",
            "name": "Code"
        },
        {
            "type": "input_value",
            "name": "Return",
            "check": "String"
        }
    ],
    "inputsInline": false,
    "colour": 230,
    "tooltip": "",
    "helpUrl": ""
}]);



Blockly.JavaScript['on_command'] = function(block) {
    var text_command_name = block.getFieldValue('command_name');
    var statements_code = Blockly.JavaScript.statementToCode(block, 'Code');
    var value_return = Blockly.JavaScript.valueToCode(block, 'Return', Blockly.JavaScript.ORDER_ATOMIC);
    var code = `function() {
${statements_code}
  return ${value_return};
}\n`;
    return code;
};


var toolbox = document.getElementById("toolbox");

var options = {
    toolbox : toolbox,
    collapse : false,
    comments : false,
    disable : false,
    maxBlocks : Infinity,
    trashcan : false,
    horizontalLayout : false,
    toolboxPosition : 'start',
    css : true,
    media : 'https://blockly-demo.appspot.com/static/media/',
    rtl : false,
    scrollbars : false,
    sounds : true,
    oneBasedIndex : true
};

window.LoopTrap = 1000;
Blockly.JavaScript.INFINITE_LOOP_TRAP = 'if(--window.LoopTrap == 0) throw "Infinite loop.";\n';


// Inject workspace
var workspace = Blockly.inject(document.getElementById('blocklyDiv'), options);


// Handle resize
var blocklyArea = document.getElementById('blocklyArea');
var blocklyDiv = document.getElementById('blocklyDiv');

var onresize = function(e) {
    // Compute the absolute coordinates and dimensions of blocklyArea.
    var element = blocklyArea;
    var x = 0;
    var y = 0;
    do {
        x += element.offsetLeft;
        y += element.offsetTop;
        element = element.offsetParent;
    } while (element);
    // Position blocklyDiv over blocklyArea.
    blocklyDiv.style.left = x + 'px';
    blocklyDiv.style.top = y + 'px';
    blocklyDiv.style.width = blocklyArea.offsetWidth + 'px';
    blocklyDiv.style.height = blocklyArea.offsetHeight + 'px';
    Blockly.svgResize(workspace);
};
window.addEventListener('resize', onresize, false);
onresize();
Blockly.svgResize(workspace);

workspace.addChangeListener(Blockly.Events.disableOrphans);

// JavaScript generation
function generateCode() {
    var xml = Blockly.Xml.workspaceToDom(workspace);
    // Find and remove all top blocks.
    var topBlocks = [];
    for (var i = xml.childNodes.length - 1, node; block = xml.childNodes[i]; i--) {
        if (block.tagName == 'block') {
            xml.removeChild(block);
            topBlocks.unshift(block);
        }
    }
    // Add each top block one by one and generate code.
    var allCode = {};
    for (var i = 0, block; block = topBlocks[i]; i++) {
        var headless = new Blockly.Workspace();
        if (block.attributes.type.value != "on_command") {
            continue;
        }
        var command_name = block.firstChild.innerHTML;
        xml.appendChild(block);
        Blockly.Xml.domToWorkspace(xml, headless);
        allCode[command_name] = Blockly.JavaScript.workspaceToCode(headless);
        headless.dispose();
        xml.removeChild(block);
    }
    return allCode;
}

function displayCode(event) {
    var code = generateCode();
    output = document.getElementById('commandsList');

    while (output.firstChild) {
        output.removeChild(output.firstChild);
    }

    for (const command in code) {
        var pre = document.createElement('li');
        pre.innerHTML = command;
        output.appendChild(pre);
    }
}

workspace.addChangeListener(displayCode);

// Autosave logic
var changedSinceSave = false;
var loaded = false;

function updateIndicator() {
    var saveIndicator = document.getElementById("saveIndicator");
    if (!loaded) {
        saveIndicator.innerHTML = "loading...";
    } else if (changedSinceSave) {
        saveIndicator.innerHTML = "saving...";
    } else {
        saveIndicator.innerHTML = "saved";
    }
}

function requestSave(event) {
    changedSinceSave = true;
    updateIndicator();
}

workspace.addChangeListener(requestSave);

function save() {
    let xml = Blockly.Xml.workspaceToDom(workspace);
    let xml_text = Blockly.Xml.domToText(xml);
    let xml_blob = new Blob([xml_text], { type: "text/xml"});

    let code = generateCode();
    let form = new FormData();

    for (const command in code) {
        let code_blob = new Blob([code[command]], { type: "text/javascript" });
        form.append("command", code_blob, `${command}.js`);
    }

    form.append("workspace", xml_blob, "workspace.xml");
    return fetch("/dashboard/save", {method: "POST", body: form});
}

function load() {
    fetch("/dashboard/load", {cache: "no-store"})
    .then(response => response.text())
    .then(xml_text => Blockly.Xml.textToDom(xml_text))
    .then(xml => Blockly.Xml.domToWorkspace(xml, workspace))
    .then(() => loaded = true)
    .then(() => updateIndicator());
}

function autosave() {
    if (loaded && changedSinceSave) {
        save().then(() => changedSinceSave = false)
        .then(() => updateIndicator());
    }
}

window.addEventListener('load', load);
setInterval(autosave, 5000);
