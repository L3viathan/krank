function makePlayer(id) {
    id = id.toLowerCase();
    elem = document.createElement("span");
    elem.innerText = id;
    elem.className = "player";
    elem.setAttribute("title", id);
    elem.style.backgroundImage = "url(avatars/" + id + ".jpeg)";
    return elem;
}

function putPlayerInInput(id) {
    size = document.querySelectorAll(".playerinput .player").length;
    if (size == 4) { return; }
    inpt = document.querySelector("input");
    container = document.querySelector(".playerinput");
    elem = makePlayer(id);
    container.appendChild(elem);
    size++;
    if (size < 2) {
        container.appendChild(inpt);
        inpt.focus();
    } else if (size == 2) {
        sep = document.createElement("span");
        sep.className = "seperator";
        sep.innerHTML = "&mdash;";
        container.appendChild(sep);
        container.appendChild(inpt);
        inpt.focus();
    } else if (size < 4) {
        container.appendChild(inpt);
        inpt.focus();
    } else {
        container.appendChild(inpt);
    }
}

function addRow(id, score, i=0) {
    player = makePlayer(id);
    row = document.createElement("tr");
    td1 = document.createElement("td");
    td2 = document.createElement("td");

    td1.appendChild(player);
    td2.innerText = score;
    row.appendChild(td1);
    row.appendChild(td2);
    document.querySelector("table").appendChild(row);
    unfade(row, i);
}

function focus() {
    document.querySelector("input").focus();
}

function unfade(element, i) {
    var op = 0.1;  // initial opacity
    var timer = setInterval(function () {
        if (op >= 1){
            clearInterval(timer);
        }
        element.style.opacity = op;
        op += op * (0.02+0.01*i);
    }, 10);
}

function keyDown(e) {
    var k = e.keyCode;
    var s = String.fromCharCode(e.keyCode);
    var i = document.querySelector("input");
    if (k >= 65 && k <= 90 || k >= 48 && k <= 57 || k == 46 || k == 17) { // A-Z, 0-9,BS/DEL
    }
    else if (k == 188 || k == 32 || k == 9 || k == 13) {
        var text = i.value
        i.value = "";
        console.log(text);
        putPlayerInInput(text);
        e.preventDefault();
    }
    else if (k == 8) {
        if (i.value == "") {
            plys = document.querySelectorAll(".playerinput .player");
            if (plys.length == 0) { return; }
            last = plys[plys.length-1];
            i.value = last.innerText;
            container.removeChild(last);
            if (plys.length == 2) {
                container.removeChild(document.querySelector(".seperator"));
            }
            e.preventDefault();
        } else {
            // do nothing
        }
    }
    else {
        // alert(k);
        e.preventDefault();
    }
}

function clickButton() {
    container = document.querySelector(".playerinput");
    players = document.querySelectorAll(".playerinput .player");
    data = [];
    for (var i = 0; i < players.length; i++) {
        data.push(players[i].innerText);
        container.removeChild(players[i]);
    }
    container.removeChild(document.querySelector(".seperator"));
    sendMatchToAPI(data);
}

function sendMatchToAPI(data) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "//steckoverflow.com/");
    xhr.onreadystatechange = function(e) {
        if (xhr.readyState == 4) {
            fillDataFromAPI();
            fillLogsFromAPI();
        }
    };
    xhr.setRequestHeader("Content-type", "application/json");
    var data = "winners="+data[0]+","+data[1]+"&losers="+data[2]+","+data[3];
    xhr.send(data);
}

function fillDataFromAPI() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "https://steckoverflow.com/table");
    xhr.onreadystatechange = function(e) {
        if (xhr.readyState == 4 && xhr.status == 200) {
            ranks = JSON.parse(xhr.responseText);
            updateTable(ranks);
        }
    };
    xhr.send();
}

function fillLogsFromAPI() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "https://steckoverflow.com/logs.html");
    xhr.onreadystatechange = function(e) {
        if (xhr.readyState == 4 && xhr.status == 200) {
            updateLogs(xhr.responseText);
        }
    };
    xhr.send();
}

function updateLogs(logs) {
    l = document.querySelector("#log");
    l.innerHTML = logs;
}

function updateTable(ranks) {
    t = document.querySelector("table");
    t.innerHTML = "";
    var sortable = []
    for (var name in ranks) {
        sortable.push([name, ranks[name]])
    }
    sortable.sort(function(a, b) {
        return b[1] - a[1];
    });
    for (var i=0; i<sortable.length; i++) {
        addRow(sortable[i][0], sortable[i][1], i);
    }
}

document.addEventListener("DOMContentLoaded", function() {
    var i = document.querySelector("input");
    i.addEventListener('keydown', keyDown);
    document.querySelector(".playerinput").addEventListener("click", focus);
    document.querySelector("button").addEventListener("click", clickButton);
    fillDataFromAPI();
    fillLogsFromAPI();
    setInterval(function() {
        fillDataFromAPI();
        fillLogsFromAPI();
    }, 60000);
});
