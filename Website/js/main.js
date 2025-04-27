// GLOBAL VARIABLES
let globalHeaders = null;
let globalData = null;
// END GLOBAL VARIABLES


// NAVBAR
$(document).ready(function() {

    // Nastavenie "active" class + "smooth scroll"
    $('.nav-link').on('click', function(event) {
        event.preventDefault();
        $('.nav-item').removeClass('active');
        $(this).parent('.nav-item').addClass('active');
        var target = $(this).attr('href');
        $('html, body').animate({
            scrollTop: $(target).offset().top - 80
        }, 800);

        // Zatvorenie navbar menu po kliknutí na link
        $('.navbar-collapse').collapse('hide');
    });

    // Povolenie responzívneho navbar tlačidla
    $('.navbar-toggler').click(function() {
        $('.navbar-collapse').collapse('toggle');
    });

});
// END NAVBAR


// HEATMAP
document.getElementById('fileInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            resetHeatmap();  // Vymazanie starej teplotnej mapy
            parseCSV(content);
        };
        reader.readAsText(file);
    }
});

function parseCSV(csv) {
    const rows = csv.trim().split("\n").map(row => row.split(",").map(val => val.trim()));
    const headers = rows[0].slice(1);
    const data = rows.slice(1)
        .map(row => row.slice(1).map(val => val ? parseFloat(val) : 0))
        .filter(row => row.length === headers.length);

    // Uloženie do globálnych premenných
    globalHeaders = headers;
    globalData = data;

    createHeatmapButton(headers, data);
}

function resetHeatmap() {
    const heatmapDiv = document.getElementById('heatmap');
    if (heatmapDiv) {
        heatmapDiv.innerHTML = ""; // Vymazanie existujúcej teplotnej mapy
    }

    const heatmapButton = document.getElementById('heatmapButton');
    if (heatmapButton) {
        heatmapButton.remove(); // Odstránenie tlačidla
    }
}

function createHeatmapButton(headers, data) {
    const button = document.createElement("button");
    button.id = "heatmapButton";
    button.innerText = "Zobraziť tepelnú mapu";
    button.classList.add("button", "mt-3");
    button.onclick = () => drawHeatmap(headers, data);
    document.getElementById('output').appendChild(button);
}

function drawHeatmap(headers, data) {
    resetHeatmap();

    const heatmapDiv = document.createElement("div");
    heatmapDiv.id = "heatmap";
    document.getElementById('heatmaps').appendChild(heatmapDiv);

    const heatmapData = [{
        z: data,
        x: headers,
        y: headers,
        type: 'heatmap',
        colorscale: 'Portland',
        zmin: -1,
        zmax: 1
    }];

    const layout = {
        title: 'Korelačná tepelná mapa',
        yaxis: {
            tickvals: [...Array(headers.length).keys()],
            ticktext: headers,
            automargin: true
        },
        margin: { l: 120, r: 20, t: 50, b: 120 }
    };

    Plotly.newPlot('heatmap', heatmapData, layout);
}
// END HEATMAP


// 3D GRAPH
document.getElementById('htmlInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            create3DGraphButton(content);
        };
        reader.readAsText(file);
    }
});

function create3DGraphButton(htmlContent) {
    reset3DGraph();

    const button = document.createElement("button");
    button.id = "graphButton";
    button.innerText = "Zobraziť 3D graf";
    button.classList.add("button", "mt-3");
    button.onclick = () => show3DGraph(htmlContent);
    
    document.getElementById('3doutput').appendChild(button);
}

function show3DGraph(htmlContent) {
    reset3DGraph();

    const graphContainer = document.createElement("div");
    graphContainer.id = "graphContainer";
    graphContainer.classList.add("col-8");
    document.getElementById('attr').classList.remove("hidden");
    document.getElementById('attr').classList.add("d-flex");

    const iframe = document.createElement("iframe");
    iframe.id = "graphFrame";
    iframe.width = "100%";
    iframe.height = "600px";
    iframe.style.border = "none";

    const blob = new Blob([htmlContent], { type: "text/html" });
    iframe.src = URL.createObjectURL(blob);

    graphContainer.appendChild(iframe);
    document.getElementById('graph').appendChild(graphContainer);

    // Naplnenie dropdown menu
    if (globalHeaders && globalData) {
        populateDropdowns(globalHeaders, globalData);
        document.getElementById("csvInput").style.display = "none";
        document.getElementById("csvReminder").style.display = "block";
    }
}


function reset3DGraph() {
    const graphButton = document.getElementById("graphButton");
    if (graphButton) {
        graphButton.remove();
    }

    const graphContainer = document.getElementById("graphContainer");
    if (graphContainer) {
        graphContainer.remove();
    }
}
// END 3D GRAPH


// SELECTING ATTRIBUTES
document.getElementById('csvInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            processCSV(content);
        };
        reader.readAsText(file);
    }
});

function processCSV(csv) {
    const rows = csv.trim().split("\n").map(row => row.split(",").map(val => val.trim()));
    const headers = rows[0].slice(1); // Prvé pole obsahuje názvy atribútov (okrem prvého prázdneho)
    const data = rows.slice(1).map(row => row.slice(1).map(val => parseFloat(val) || 0));

    populateDropdowns(headers, data);
}

function populateDropdowns(headers, correlationData) {
    const dropdown1 = document.getElementById("dropdown1");
    const dropdown2 = document.getElementById("dropdown2");
    dropdown1.innerHTML = "";
    dropdown2.innerHTML = "";

    headers.forEach((header, index) => {
        const option1 = document.createElement("option");
        const option2 = document.createElement("option");
        option1.value = index;
        option2.value = index;
        option1.textContent = header;
        option2.textContent = header;
        dropdown1.appendChild(option1);
        dropdown2.appendChild(option2);
    });

    dropdown1.addEventListener("change", function() {
        calculateCorrelation(this.value, dropdown2.value, headers, correlationData);
    });

    dropdown2.addEventListener("change", function() {
        calculateCorrelation(dropdown1.value, this.value, headers, correlationData);
    });

    document.getElementById("attr").classList.remove("hidden");
}

function calculateCorrelation(index1, index2, headers, correlationData) {
    if (index1 === "" || index2 === "") return;

    const correlation = correlationData[index1][index2];
    const outputDiv = document.getElementById("correlationOutput");
    outputDiv.innerHTML = `<h5>Korelácia medzi <b>${headers[index1]}</b> a <b>${headers[index2]}</b>: ${correlation.toFixed(2)}</h5>`;
}
// END SELECTING ATTRIBUTES
