// --- CONFIGURAÇÃO GLOBAL ---
const ALL_PROMPTS = [
  { id: "prompt_1", label: "Prompt 1" },
  { id: "prompt_2", label: "Prompt 2" },
  { id: "prompt_4", label: "Prompt 3" }, 
  { id: "prompt_5", label: "Prompt 4" }
];

const LLM_CONFIGS = [
  { id: "gpt-3.5-turbo",    shortName: "(1)", fullName: "GPT-3.5 Turbo" },
  { id: "gpt-4o-mini",      shortName: "(2)", fullName: "GPT-4o Mini" },
  { id: "gemini-2.5-flash", shortName: "(3)", fullName: "Gemini 2.5 Flash" },
  { id: "gpt-4.1-mini",     shortName: "(4)", fullName: "GPT-4.1 Mini" }, 
  { id: "gpt-4.1",          shortName: "(5)", fullName: "GPT-4.1" }
];

const METRIC_TITLES = {
  "f1": "Macro F1 Score",
  "precision": "Macro Precision",
  "recall": "Macro Recall",
  "accuracy": "Macro Accuracy"
};

// --- FUNÇÃO PRINCIPAL (GERA TODOS) ---
async function generateAllHeatmaps() {
  const selectedMetric = document.getElementById("metricSelect").value;
  const mainContainer = document.getElementById("globalHeatmapContainer");
  const legendContainer = document.getElementById("heatmapLegend");

  // Limpa containers
  mainContainer.innerHTML = "";
  legendContainer.innerHTML = "A carregar dados...";

  // Cria a estrutura na página
  ALL_PROMPTS.forEach(prompt => {
    // 1. Cria o container do gráfico
    const div = document.createElement("div");
    div.id = `container_${prompt.id}`;
    div.style.height = "600px"; 
    
    // Se for o Prompt 3, damos menos margem em baixo para a nota ficar colada
    // Se forem os outros, damos 50px de espaço
    div.style.marginBottom = prompt.label === "Prompt 3" ? "5px" : "50px";
    
    div.innerHTML = `<div style="padding:50px; text-align:center;">A carregar ${prompt.label}...</div>`;
    mainContainer.appendChild(div);

    // 2. ADIÇÃO: Nota específica para o Prompt 3
    if (prompt.label === "Prompt 3") {
        const noteDiv = document.createElement("div");
        noteDiv.style.textAlign = "center";
        noteDiv.style.marginBottom = "50px"; // O espaço real fica depois da nota
        noteDiv.style.fontStyle = "italic";
        noteDiv.style.color = "#666";
        noteDiv.style.fontSize = "14px";
        noteDiv.innerHTML = "Note: The gemini-2.5-flash model could not be tested on this prompt due to excessive token requirements.";
        mainContainer.appendChild(noteDiv);
    }
  });

  // Dispara o carregamento dos gráficos
  const promises = ALL_PROMPTS.map(prompt => 
    renderSingleHeatmap(prompt, selectedMetric)
  );

  await Promise.all(promises);

  // Legenda Global
  const legendHTML = "<b>Models ID:</b> " + LLM_CONFIGS.map(c => 
    `<span style="margin-right: 15px;">${c.shortName} ${c.fullName}</span>`
  ).join("");
  legendContainer.innerHTML = legendHTML;
}

// --- FUNÇÃO DE RENDERIZAÇÃO INDIVIDUAL ---
async function renderSingleHeatmap(promptConfig, metricType) {
  const containerId = `container_${promptConfig.id}`;
  const container = document.getElementById(containerId);
  const practices = Array.from({ length: 16 }, (_, i) => i + 1);
  const currentMetricTitle = METRIC_TITLES[metricType];

  // FILTRO PROMPT 3: Remove o Gemini da lista
  let currentLLMs = LLM_CONFIGS;
  if (promptConfig.label === "Prompt 3") {
      currentLLMs = LLM_CONFIGS.filter(c => c.id !== "gemini-2.5-flash");
  }

  try {
    const promises = currentLLMs.flatMap((config) => {
      const basePath = `../output/${promptConfig.id}/${config.id}`; 
      return [
        fetch(`${basePath}/classe 0/classe0_individual_metrics.json`).then(r => r.ok ? r.json() : null),
        fetch(`${basePath}/classe 1/classe1_individual_metrics.json`).then(r => r.ok ? r.json() : null),
        fetch(`${basePath}/classe NA/json_na_individual_metrics.json`).then(r => r.ok ? r.json() : null),
      ];
    });

    const rawResults = await Promise.all(promises);

    const zValues = [];
    const annotations = [];

    for (let i = 0; i < currentLLMs.length; i++) {
      const rowValues = [];
      const config = currentLLMs[i];
      
      const dataClass0 = rawResults[i * 3];
      const dataClass1 = rawResults[i * 3 + 1];
      const dataClassNA = rawResults[i * 3 + 2];

      for (let j = 0; j < practices.length; j++) {
        const practiceID = practices[j];
        
        const m_0 = calculateMetric(dataClass0, practiceID, metricType);
        const m_1 = calculateMetric(dataClass1, practiceID, metricType);
        const m_na = calculateMetric(dataClassNA, practiceID, metricType);
        
        const macroVal = (m_0 + m_1 + m_na) / 3;
        rowValues.push(macroVal);

        const textColor = macroVal > 0.5 ? 'white' : 'black';
        annotations.push({
          xref: 'x', yref: 'y',
          x: practiceID.toString(),
          y: config.shortName, 
          text: macroVal.toFixed(2),
          showarrow: false,
          font: { family: 'Arial', size: 11, color: textColor }
        });
      }
      zValues.push(rowValues);
    }

    container.innerHTML = ""; 

    const data = [{
      z: zValues,
      x: practices.map(String),
      y: currentLLMs.map(c => c.shortName), 
      type: 'heatmap',
      colorscale: 'YlGnBu', 
      reversescale: true, 
      showscale: true,
      zmin: 0, zmax: 1,
      xgap: 1, ygap: 1
    }];

    const layout = {
      title: `${currentMetricTitle} - ${promptConfig.label}`, 
      annotations: annotations,
      xaxis: { title: 'Practice ID', dtick: 1 },
      yaxis: { 
          title: 'LLM Model', 
          automargin: true,
          tickfont: { size: 14, color: 'black' }
      },
      margin: { l: 100, b: 50, t: 50, r: 50 }
    };

    Plotly.newPlot(containerId, data, layout);

  } catch (error) {
    console.error(`Erro no ${promptConfig.label}:`, error);
    container.innerHTML = `<p style="color:red; text-align:center;">Erro ao carregar ${promptConfig.label}: ${error.message}</p>`;
  }
}

// --- FUNÇÃO MATEMÁTICA ---
function calculateMetric(dataset, practiceID, metricType) {
    if (!dataset) return 0;
    const item = dataset.find(p => parseInt(p.practice) === practiceID);
    if (!item) return 0;

    const tp = parseFloat(item.tp || item.TP || item.true_positives || 0);
    const fp = parseFloat(item.fp || item.FP || item.false_positives || 0);
    const fn = parseFloat(item.fn || item.FN || item.false_negatives || 0);
    const tn = parseFloat(item.tn || item.TN || item.true_negatives || 0);

    // Se TP=FP=FN=0, o modelo acertou o "vazio". F1, Recall e Precision devem ser 1.0.
    if (tp === 0 && fp === 0 && fn === 0 && metricType !== 'accuracy') {
        return 1.0; 
    }

    switch (metricType) {
        case 'f1':
            const f1Denom = (2 * tp) + fp + fn;
            return f1Denom === 0 ? 0 : (2 * tp) / f1Denom;
        case 'precision':
            if (tp + fp === 0) return 1.0; 
            return tp / (tp + fp);
        case 'recall':
            if (tp + fn === 0) return 1.0;
            return tp / (tp + fn);
        case 'accuracy':
            const total = tp + fp + fn + tn;
            if (total === 0) return 0; 
            return (tp + tn) / total;
        default: return 0;
    }
}