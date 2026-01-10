function renderTable(containerId, data) {
  const columns = [
    "practice",
    "correct_na",
    "incorrect_na",
    "real_na",
    "correct_0",
    "incorrect_0",
    "real_0",
    "correct_1",
    "incorrect_1",
    "real_1",
  ];

  let html = "<table><tr>";
  columns.forEach((col) => {
    let cls = "";
    if (col.includes("NA") || col.includes("na")) cls = "na";
    else if (col.includes("0")) cls = "c0";
    else if (col.includes("1")) cls = "c1";
    html += `<th class="${cls}">${col}</th>`;
  });
  html += "</tr>";

  data.forEach((row) => {
    html += "<tr>";
    columns.forEach((col) => {
      let val = row[col] ?? "-";
      let style = "";

      const baseColor = "35,142,35";
      const baseColor2 = "255,44,44";
      const applyOpacity = (color, ratio) => {
        const opacity = Math.min(1, Math.max(0.1, ratio));
        return `background-color: rgba(${color}, ${opacity})`;
      };

      // --- Heatmap: correct vs incorrect ---
      if (col.startsWith("correct_")) {
        const classNum = col.split("_")[1];
        const correctKey = `correct_${classNum}`;
        const incorrectKey = `incorrect_${classNum}`;
        const correct = row[correctKey] ?? 0;
        const realKey = `real_${classNum}`;
        const real = row[realKey] ?? 0;

        if (correct > 0) {
          const ratio = correct / real;
          style = applyOpacity(baseColor, ratio);
        }
      }

      if (col.startsWith("incorrect_")) {
        const classNum = col.split("_")[1];
        const correctKey = `correct_${classNum}`;
        const incorrectKey = `incorrect_${classNum}`;
        const correct = row[correctKey] ?? 0;
        const incorrect = row[incorrectKey] ?? 0;
        const realKey = `real_${classNum}`;
        const real = row[realKey] ?? 0;

        if (incorrect > 0) {
          const ratio = incorrect / real;
          style = applyOpacity(baseColor2, ratio);
        }
      }

      // --- Heatmap: prática global ---
      if (col === "practice") {
        const totalCorrect =
          (row["correct_0"] ?? 0) +
          (row["correct_1"] ?? 0) +
          (row["correct_na"] ?? 0);
        const totalIncorrect =
          (row["incorrect_0"] ?? 0) +
          (row["incorrect_1"] ?? 0) +
          (row["incorrect_na"] ?? 0);
        const total = totalCorrect + totalIncorrect;
        if (total > 0) {
          const ratio = totalCorrect / total;
          style = applyOpacity(baseColor, ratio);
        }
      }

      let cls = "";
      if (col.includes("NA") || col.includes("na")) cls = "na";
      else if (col.includes("0")) cls = "c0";
      else if (col.includes("1")) cls = "c1";

      html += `<td class="${cls}" style="${style}">${val}</td>`;
    });
    html += "</tr>";
  });

  html += "</table>";

  // --- Legenda ---
  html += `
  <div class="legend">
    <div>
      <div class="gradient-bar gradient-success"></div>
      <span>Intensidade (Verde) representa a proporção de acertos (0 → 1)</span>
    </div>
    <div>
      <div class="gradient-bar gradient-danger"></div>
      <span>Intensidade (Vermelho) representa a proporção de erros (0 → 1)</span>
    </div>
  </div>
`;

  document.getElementById(containerId).innerHTML = html;
}

function renderMatrixTable(containerId, data) {
  const classes = ["na", "0", "1"]; // ajusta se tiveres mais classes
  let html =
    "<table class='matrix-table'><thead><tr><th rowspan='3' class='practice-header'>practice</th>";
  classes.forEach((cls, idx) => {
    const separatorClass =
      idx < classes.length - 1 ? "group-separator" : "";
    html += `<th colspan="3" class="c${cls} class-group-header ${separatorClass}">Class ${cls.toUpperCase()}</th>`;
  });
  html += "</tr><tr>";
  // Segunda linha de cabeçalho - TP/FP e Real
  classes.forEach((cls, idx) => {
    const separatorClass =
      idx < classes.length - 1 ? "group-separator" : "";
    html += `<th class="c${cls} sub-header-separator">TP</th><th class="c${cls} ${separatorClass}">FN</th><th rowspan='2' class="c${cls} class-group-header ${separatorClass} real-value">Real</th>`;
  });
  html += "</tr><tr>";
  // Terceira linha de cabeçalho - FN/TN
  classes.forEach((cls, idx) => {
    const separatorClass =
      idx < classes.length - 1 ? "group-separator" : "";
    html += `<th class="c${cls} sub-header-separator class-group-header">FP</th><th class="c${cls} class-group-header ${separatorClass}">TN</th>`;
  });
  html += "</tr></thead><tbody>";

  const baseGreen = "112, 159, 37";
  const baseRed = "197, 50, 39";
  const applyOpacity = (color, ratio) =>
    `background-color: rgba(${color}, ${Math.min(
      1,
      Math.max(0.1, ratio)
    )})`;

  data.forEach((row, index) => {
    // Linha 1: practice (rowspan=2) + TP/FP + Real (rowspan=2)
    const rowSeparatorClass = index > 0 ? "row-separator-top" : "";
    html += `<tr><td rowspan='2' class='practice-header ${rowSeparatorClass}'>${row.practice}</td>`;

    classes.forEach((cls, idx) => {
      const TP = row[`TP_${cls}`] ?? 0;
      const FN = row[`FN_${cls}`] ?? 0;
      const real = row[`real_${cls}`] ?? 0;
      const separatorClass =
        idx < classes.length - 1 ? "group-separator" : "";

      html += `
        <td class="c${cls} sub-header-separator ${rowSeparatorClass}" style="${
        TP > 0 ? applyOpacity(baseGreen, TP / Math.max(1, real)) : ""
      }">${TP}</td>
        <td class="c${cls} ${separatorClass} ${rowSeparatorClass}" style="${
        FN > 0 ? applyOpacity(baseRed, FN / Math.max(1, real)) : ""
      }">${FN}</td>
    <td rowspan='2' class="c${cls} ${separatorClass} ${rowSeparatorClass} real-value">${real}</td>
`;
    });
    html += "</tr>";

    // Linha 2: FN/TN
    html += "<tr>";
    classes.forEach((cls, idx) => {
      const FP = row[`FP_${cls}`] ?? 0;
      const TN = row[`TN_${cls}`] ?? 0;
      const real = row[`real_${cls}`] ?? 0;
      const separatorClass =
        idx < classes.length - 1 ? "group-separator" : "";

      html += `
  <td class="c${cls} sub-header-separator" style="${
        FP > 0 ? applyOpacity(baseRed, FP / Math.max(1, real)) : ""
      }">${FP}</td>
  <td class="c${cls} ${separatorClass}" style="${
        TN > 0 ? applyOpacity(baseGreen, TN / Math.max(1, real)) : ""
      }">${TN}</td>
`;
    });
    html += "</tr>";
  });

  html += "</tbody></table>";

  // Legenda
  html += `
  <div class="legend">
    <div>
      <div class="gradient-bar gradient-success"></div>
      <span>Verde = TP/TN (acertos)</span>
    </div>
    <div>
      <div class="gradient-bar gradient-danger"></div>
      <span>Vermelho = FP/FN (erros)</span>
    </div>
  </div>
`;

  document.getElementById(containerId).innerHTML = html;
}

function renderPracticeMetrics(title, data) {
  if (!data || data.length === 0)
    return `<h3>${title}</h3><p>No data</p>`;

  // Obter as colunas (assumindo que todas as rows têm as mesmas chaves)
  let columns = Object.keys(data[0]);

  let html = `<h3>${title}</h3><table><tr>`;
  columns.forEach((col) => {
    html += `<th>${col}</th>`;
  });
  html += "</tr>";

  data.forEach((row) => {
    html += "<tr>";
    columns.forEach((col) => {
      let val = row[col];
      let style = "";
      html += `<td>${val}</td>`;
    });
    html += "</tr>";
  });

  html += "</table>";
  return html;
}

function renderMetricsTable(title, data) {
  if (!data || data.length === 0)
    return `<h3>${title}</h3><p>No data</p>`;
  let row = data[0];
  let html = `<h3>${title}</h3><table><tr><th>Metric</th><th>Value</th></tr>`;
  for (const [key, value] of Object.entries(row)) {
    html += `<tr><td>${key}</td><td>${value}</td></tr>`;
  }
  html += "</table>";
  return html;
}

function renderCategoryTable(title, data) {
  if (!data || data.length === 0)
    return `<h3>${title}</h3><p>No data</p>`;

  // Obter as colunas (assumindo que todas as rows têm as mesmas chaves)
  let columns = Object.keys(data[0]);

  let html = `<h3>${title}</h3><table><tr>`;
  columns.forEach((col) => {
    html += `<th>${col}</th>`;
  });
  html += "</tr>";

  data.forEach((row) => {
    html += "<tr>";
    columns.forEach((col) => {
      let val = row[col];
      let style = "";

      // Se for métrica numérica (entre 0 e 1), aplicar heatmap
      if (typeof val === "number" && val >= 0 && val <= 1) {
        if (val > 0.85)
          style = "background-color: rgba(0,200,0,0.5)"; // verde (bom)
        else if (val > 0.6)
          style = "background-color: rgba(255,200,0,0.5)";
        // amarelo (médio)
        else style = "background-color: rgba(255,0,0,0.4)"; // vermelho (mau)
      }

      html += `<td>${val}</td>`;
    });
    html += "</tr>";
  });

  html += "</table>";
  return html;
}

function renderLspTable(containerId, data) {
  if (!data || data.length === 0) {
    document.getElementById(containerId).innerHTML =
      "<p>No data available</p>";
    return;
  }

  // Obter as colunas (assumindo que todas as rows têm as mesmas chaves)
  let columns = Object.keys(data[0]);

  let html = "<table><tr>";
  columns.forEach((col) => {
    html += `<th>${col}</th>`;
  });
  html += "</tr>";

  data.forEach((row) => {
    html += "<tr>";
    columns.forEach((col) => {
      let val = row[col];

      let cls = "";
      if (col.includes("_qm")) cls = "na";
      else if (col.includes("_equal_")) cls = "c0";
      else if (col.includes("_paper")) cls = "c1";

      html += `<td class="${cls}">${val}</td>`;
    });
    html += "</tr>";
  });

  html += "</table>";
  document.getElementById(containerId).innerHTML = html;
}

function compareMetrics(metrics1, metrics2, title1, title2, classe) {
  if (
    !metrics1 ||
    metrics1.length === 0 ||
    !metrics2 ||
    metrics2.length === 0
  ) {
    return `<h3>Comparison ${title1} vs ${title2}</h3><p>Incomplete data for comparison.</p>`;
  }

  const m1 = metrics1[0];
  const m2 = metrics2[0];
  const keys = new Set([...Object.keys(m1), ...Object.keys(m2)]);

  let html = `<h3>Comparison ${title1} vs ${title2}: ${classe}</h3><table>`;
  html +=
    "<tr><th>Metric</th><th>" +
    title1 +
    "</th><th>" +
    title2 +
    "</th><th>Difference</th></tr>";

  for (const key of keys) {
    const val1 = m1[key];
    const val2 = m2[key];
    let diffClass = "";
    let diffText = "";

    if (val1 === undefined) {
      diffClass = "diff-added";
      diffText = "Added";
    } else if (val2 === undefined) {
      diffClass = "diff-removed";
      diffText = "Removed";
    } else if (val1 !== val2) {
      diffClass = "diff-changed";
      const numVal1 = parseFloat(val1);
      const numVal2 = parseFloat(val2);
      if (!isNaN(numVal1) && !isNaN(numVal2)) {
        const diff = numVal2 - numVal1;
        const percentDiff = (diff / Math.abs(numVal1)) * 100;
        diffText = `${diff > 0 ? "+" : ""}${diff.toFixed(
          4
        )} (${percentDiff.toFixed(2)}%)`;
      } else {
        diffText = "Changed";
      }
    } else {
      diffText = "Equal";
    }

    html += `<tr>
    <td class="metric-name">${key}</td>
    <td>${val1 !== undefined ? val1 : "-"}</td>
    <td>${val2 !== undefined ? val2 : "-"}</td>
    <td class="${diffClass}">${diffText}</td>
  </tr>`;
  }

  html += "</table>";
  return html;
}

function renderDetailTable(practices, version, method, scoreType) {
  // garante que practices tem o que precisamos
  if (!practices) {
    document.getElementById("detailTable").innerHTML =
      "<div>No data</div>";
    document.getElementById("detailTitle").style.display = "none";
    return;
  }

  if (scoreType === "equal_weights") {
    scoreType = "manual";
  }
  const gt = practices["groundtruth"] || {}; // Groundtruth
  const selectedPractices = practices[scoreType] || {};

  // Cabeçalho
  let html = `<h3>Method Details: ${method} | Version: ${version}</h3>
              <table class="practice-table">
                <thead>
                  <tr>
                    <th>Source</th>`;
  for (const p of Object.keys(selectedPractices)) {
    const i = p.split(" ")[1];
    html += `<th>P${i}</th>`;
  }
  html += `</tr></thead><tbody>`;

  // LLM Output Row
  html += `<tr><td class="metric-name">LLM Output</td>`;
  for (const [p, s] of Object.entries(selectedPractices)) {
    html += `<td>${s !== null && s !== undefined ? s : "NA"}</td>`;
  }
  html += `</tr>`;

  // Groundtruth Row
  html += `<tr><td class="metric-name">Groundtruth</td>`;
  for (const p of Object.keys(selectedPractices)) {
    const gtVal = gt[p];
    html += `<td>${
      gtVal !== null && gtVal !== undefined ? gtVal : "NA"
    }</td>`;
  }
  html += `</tr></tbody></table>`;

  const detailTableContainer = document.getElementById("detailTable");
  detailTableContainer.innerHTML = html;
  document.getElementById("detailTitle").style.display = "block";

  // Recalculate the max-height of the collapsible section to fit the new content
  const collapsibleContent = detailTableContainer.closest(
    ".collapsible-content"
  );
  if (collapsibleContent && collapsibleContent.style.maxHeight) {
    collapsibleContent.style.maxHeight =
      collapsibleContent.scrollHeight + "px";
  }
}