// Global state for plots
let allConsolidatedData = {};
let currentJsonKey = null;
let currentFile = null;
let currentScoreType = "qm";
let currentMethods = [];
let isNanScoreActive = false;

// JSON de vulnerabilidades
const vulnerabilities = {
  NewCustomer: {
    Vx0: [],
    Vx101: ["getAddressID"],
    Vx138: ["createAddress"],
    Vx158: ["getCOID"],
    Vx197: ["insertCostumer"],
    VxA: ["getAddressID", "getCOID", "createAddress", "insertCostumer"],
  },
  CreateNewCustomer: {
    Vx0: [],
    Vx078: ["createNewCustomer"],
    Vx103: ["enterAddress"],
    Vx113: ["enterAddress"],
    Vx132: ["enterAddress"],
    VxA: ["createNewCustomer", "enterAddress"],
  },
};

async function loadConsolidatedJSON(path, key) {
  const data = await fetchJSON(path);
  allConsolidatedData[key] = data;
  currentJsonKey = key;

  // Popular dropdown de filenames
  const fileSelect = document.getElementById("fileSelect");
  const baseNames = [
    ...new Set(Object.keys(data).map((fn) => fn.split("_")[0])),
  ];
  fileSelect.innerHTML = baseNames
    .map((fn) => `<option value="${fn}">${fn}</option>`)
    .join("");
  currentFile = baseNames[0];

  updateMainPlot();
}

// Função toggle para alternar entre score normal e com NaN
function toggleNanScore() {
  const btn = document.getElementById("btn-scoreNan");

  if (!isNanScoreActive) {
    // Carregar score com NaN
    const llm = document.getElementById("llm").value;
    const prompt = document.getElementById("prompt").value;
    const basePath = `../output/${prompt}/${llm}/`;
    loadConsolidatedJSON(
      `${basePath}score/score_consolidated.json`,
      `${llm}_${prompt}_nan`
    ).then(() => {
      isNanScoreActive = true;
      btn.textContent = "Score Without NAs";
    });
  } else {
    // Voltar ao score original
    const llm = document.getElementById("llm").value;
    const prompt = document.getElementById("prompt").value;
    const originalKey = `${llm}_${prompt}`;

    if (allConsolidatedData[originalKey]) {
      switchJSON(originalKey);
      isNanScoreActive = false;
      btn.textContent = "Score With NAs";
    }
  }
}

// Alternar entre JSONs carregados
function switchJSON(key) {
  if (!allConsolidatedData[key]) return;
  currentJsonKey = key;
  const data = allConsolidatedData[key];
  const fileSelect = document.getElementById("fileSelect");
  const baseNames = [
    ...new Set(Object.keys(data).map((fn) => fn.split("_")[0])),
  ];
  fileSelect.innerHTML = baseNames
    .map((fn) => `<option value="${fn}">${fn}</option>`)
    .join("");
  currentFile = baseNames[0];
  updateMainPlot();
}

// Atualizar gráfico principal
function updateMainPlot() {
  if (!currentJsonKey) return;
  const consolidatedData = allConsolidatedData[currentJsonKey];

  currentFile = document.getElementById("fileSelect").value;
  currentScoreType = "qm"; // Hardcoded to QM score

  const versions = Object.keys(consolidatedData[currentFile]).sort();
  currentMethods = new Set();
  versions.forEach((v) => {
    Object.keys(
      consolidatedData[currentFile][v]["score_" + currentScoreType]
    ).forEach((m) => currentMethods.add(m));
  });
  currentMethods = Array.from(currentMethods);

  const colors = [
    "#4978E0",
    "#56E0D1",
    "#BBE6A1",
    "#59A14F",
    "#9C87E0",
    "#D302DE",
  ];
  const traces = [];

  currentMethods.forEach((method, index) => {
    const colorMethod = colors[index % colors.length];

    const mainScores = versions.map((v) => {
      const val =
        consolidatedData[currentFile][v]["score_" + currentScoreType][
          method
        ];
      return val !== undefined ? val : 0;
    });
    const groundtruthScores = versions.map((v) => {
      const val = consolidatedData[currentFile][v]["score_paper"][method];
      return val !== undefined ? val : 0;
    });

    const isVulnerable = versions.map(
      (v) =>
        vulnerabilities[currentFile] &&
        vulnerabilities[currentFile][v] &&
        vulnerabilities[currentFile][v].includes(method)
    );

    const diffPositive = groundtruthScores.map((ps, i) =>
      ps - mainScores[i] > 0 ? ps - mainScores[i] : 0
    );
    const diffNegative = groundtruthScores.map((ps, i) =>
      ps - mainScores[i] < 0 ? ps - mainScores[i] : 0
    );

    const borderColors = isVulnerable.map((v) =>
      v ? "red" : colorMethod
    );
    const borderWidths = isVulnerable.map((v) => (v ? 2 : 0));

    // Barra principal
    traces.push({
      x: versions,
      y: mainScores,
      type: "bar",
      name: method,
      customdata: versions.map((v, i) => ({
        method,
        version: v,
        vulnerable: isVulnerable[i],
      })),
      hovertemplate: `Version: %{x}<br>Method: ${method}<br>Score: %{y}<extra></extra>`,
      marker: {
        color: colorMethod,
        line: { color: borderColors, width: borderWidths },
      },
      offsetgroup: method,
    });

    // Sobreposição positiva
    traces.push({
      x: versions,
      y: diffPositive,
      type: "bar",
      name: method + " (groundtruth difference)",
      marker: { color: "rgba(255, 215, 0, 0.4)" },
      offsetgroup: method,
      base: mainScores,
      showlegend: false,
      hovertemplate: `Version: %{x}<br>Method: ${method}<br>Groundtruth Difference: %{y}<extra></extra>`,
    });

    // Sobreposição negativa
    traces.push({
      x: versions,
      y: diffNegative.map((d) => Math.abs(d)),
      type: "bar",
      name: method + " (negative groundtruth difference)",
      marker: { color: `rgba(255, 215, 0, 0.4)` },
      offsetgroup: method,
      base: groundtruthScores,
      showlegend: false,
      hovertemplate: `Version: %{x}<br>Method: ${method}<br>Groundtruth Score: %{y}<extra></extra>`,
    });
  });

  const layout = {
    barmode: "group",
    title: `Scores for ${currentFile} (${
      currentScoreType === "qm"
        ? "LSP Quality Model"
        : "Equal Weighted"
    })`,
    xaxis: { title: "Versions", type: "category" },
    yaxis: { title: "Score", range: [0, 1.05] },
    legend: { orientation: "h", y: -0.2 },
    hovermode: "closest",
    bargap: 0.3,
    bargroupgap: 0.2,
  };

  Plotly.react("mainPlot", traces, layout).then(() => {
    const mainPlot = document.getElementById("mainPlot");

    mainPlot.removeAllListeners("plotly_click");
    mainPlot.on("plotly_click", function (data) {
      const point = data.points[0];
      const info = point.customdata;
      if (!info) return;
      const version = info.version;
      const method = info.method;
      const versionData = consolidatedData[currentFile][version];
      if (
        !versionData ||
        !versionData.practices ||
        !versionData.practices[method]
      )
        return;
      const practices = versionData.practices[method];
      renderDetailTable(practices, version, method, currentScoreType);
    });

    // Toggle Paper
    const btn = document.getElementById("togglePaperBtn");
    let showPaper = false;
    const paperIndices = traces
      .map((t, idx) =>
        t.name &&
        (t.name.includes("groundtruth difference") ||
          t.name.includes("negative groundtruth difference"))
          ? idx
          : null
      )
      .filter((i) => i !== null);
    Plotly.restyle(mainPlot, { visible: "legendonly" }, paperIndices);

    btn.onclick = () => {
      showPaper = !showPaper;
      btn.textContent = showPaper
        ? "Hide Groundtruth Comparison"
        : "Show Groundtruth Comparison";
      const visibility = showPaper ? true : "legendonly";
      Plotly.restyle(mainPlot, { visible: visibility }, paperIndices);
    };
  });
}

async function loadData2() {
  const llm = document.getElementById("llm_score_1").value;
  const prompt = document.getElementById("prompt_score_1").value;
  const scoreType = document.getElementById("scoreSelect_1").value;
  const basePath = `../output_score_1/unic_json.json`;

  try {
    // Carregar JSON
    const data = await fetchJSON(basePath);

    // Navegar na estrutura: data[llm][prompt][filename][version][method]
    const promptData = data[llm]?.[prompt];

    if (!promptData) {
      alert(`Dados não encontrados para ${llm} - ${prompt}`);
      return;
    }

    // Coletar todos os scores
    const versions = [];
    const scores = [];
    const colors = [];

    // Iterar por todos os ficheiros
    for (const [filename, versionData] of Object.entries(promptData)) {
      for (const [version, methodData] of Object.entries(versionData)) {
        for (const [method, sourceData] of Object.entries(methodData)) {
          // Se for Vx1, pegar score "input"
          if (version === "Vx1" && sourceData.input) {
            versions.push(`${version}`);
            scores.push(sourceData.input.score);
            colors.push("#FF6B6B"); // Vermelho para input
          }

          // Pegar score do tipo selecionado (qm ou manual)
          if (sourceData[scoreType]) {
            versions.push(`${version}`);
            scores.push(sourceData[scoreType].score);
            colors.push(version === "Vx1" ? "#4ECDC4" : "#45B7D1"); // Azul claro para Vx1, azul para outras
          }
        }
      }
    }

    // Criar o gráfico
    const trace = {
      x: versions,
      y: scores,
      type: "bar",
      marker: {
        color: colors,
        line: {
          color: "rgba(0,0,0,0.3)",
          width: 1,
        },
      },
      text: scores.map((s) => s.toFixed(3)),
      textposition: "outside",
      hovertemplate: "<b>%{x}</b><br>Score: %{y:.4f}<extra></extra>",
    };

    const layout = {
      title: {
        text: `Score Comparison - ${llm} - ${prompt}`,
        font: { size: 18 },
      },
      xaxis: {
        title: "Versions",
        tickangle: 0,
      },
      yaxis: {
        title: "Score",
        range: [0, 1],
      },
      showlegend: false,
      height: 700,
      margin: {
        b: 150,
      },
    };

    Plotly.newPlot("score_1_Plot", [trace], layout, { responsive: true });
    document.getElementById("score_1_Plot").style.display = "block";
  } catch (err) {
    alert("Error loading data: " + err.message);
    console.error(err);
  }
}

// UI-facing functions that trigger plot updates
function loadScoreGraphic() {
  updateMainPlot();
}

function loadWithNanScore() {
  toggleNanScore();
}