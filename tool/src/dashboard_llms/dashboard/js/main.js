let basePrompt = null;

async function loadData() {
  const llm = document.getElementById("llm").value;
  const prompt = document.getElementById("prompt").value;
  const basePath = `../output/${prompt}/${llm}/`;

  const geralMatriz = `${basePath}geral/matrix.json`;

  const classe0Path = `${basePath}classe 0/classe0_metrics.json`;
  const classe1Path = `${basePath}classe 1/classe1_metrics.json`;
  const naPath = `${basePath}classe NA/json_na_metrics.json`;

  const practiceMetricsPath0 = `${basePath}/classe 0/classe0_individual_metrics.json`;
  const practiceMetricsPath1 = `${basePath}/classe 1/classe1_individual_metrics.json`;
  const practiceMetricsPath_na = `${basePath}/classe NA/json_na_individual_metrics.json`;

  const categoryMetricsPath_na = `${basePath}category/category_classe_na.json`;
  const categoryMetricsPath_classe0 = `${basePath}category/category_classe0.json`;
  const categoryMetricsPath_classe1 = `${basePath}category/category_classe1.json`;

  try {
    document.getElementById("generalResultsContainer").style.display = "block";

    const geralMatrizData = await fetchJSON(geralMatriz);
    renderMatrixTable("matrixTable", geralMatrizData);

    document.getElementById("matrixTable").style.display = "block";

    const na = await fetchJSON(naPath);
    const classe0 = await fetchJSON(classe0Path);
    const classe1 = await fetchJSON(classe1Path);

    let classHtml = "";
    classHtml += renderMetricsTable("Class NA", na);
    classHtml += renderMetricsTable("Class 0", classe0);
    classHtml += renderMetricsTable("Class 1", classe1);

    document.getElementById("classMetrics").innerHTML = classHtml;
    document.getElementById("classMetrics").style.display = "block";

    // Carregar e renderizar métricas por categoria
    const category_na = await fetchJSON(categoryMetricsPath_na);
    const category_classe0 = await fetchJSON(categoryMetricsPath_classe0);
    const category_classe1 = await fetchJSON(categoryMetricsPath_classe1);
    let classHtml1 = "";
    classHtml1 += renderCategoryTable("Class NA", category_na);
    classHtml1 += renderCategoryTable("Class 0", category_classe0);
    classHtml1 += renderCategoryTable("Class 1", category_classe1);

    document.getElementById("categoryMetrics").innerHTML = classHtml1;
    document.getElementById("categoryMetrics").style.display = "block";

    // Carregar métricas por prática
    const practiceMetrics0 = await fetchJSON(practiceMetricsPath0);
    const practiceMetrics1 = await fetchJSON(practiceMetricsPath1);
    const practiceMetrics_na = await fetchJSON(practiceMetricsPath_na);
    let classHtml2 = "";
    classHtml2 += renderPracticeMetrics("Class NA", practiceMetrics_na);
    classHtml2 += renderPracticeMetrics("Class 0", practiceMetrics0);
    classHtml2 += renderPracticeMetrics("Class 1", practiceMetrics1);

    document.getElementById("practiceMetrics").innerHTML = classHtml2;
    document.getElementById("practiceMetrics").style.display = "block";

    // The "Trustworthiness Score Table" (lspTable) was commented out in the HTML,
    // so the code to populate it is also commented out to prevent errors.
    // const lspPath = `${basePath}score/score_comparison.json`;
    // const lspData = await fetchJSON(lspPath);
    // renderLspTable("lspTable", lspData);
    //
    // document.getElementById("lspTable").style.display = "block";

    loadConsolidatedJSON(
      `${basePath}score/new_score_consolidated.json`,
      `${llm}_${prompt}`
    );
  } catch (err) {
    alert("Error loading data: " + err.message);
  }
}

async function loadMetrics(llm, classe, prompt) {
  const basePath = `../output/${prompt}/${llm}/`;
  const map = {
    "classe 0": "classe 0/classe0_metrics.json",
    "classe 1": "classe 1/classe1_metrics.json",
    "classe NA": "classe NA/json_na_metrics.json",
  };
  return await fetchJSON(basePath + map[classe]);
}

async function compareSelected() {
  const llm1 = document.getElementById("llm1").value;
  const llm2 = document.getElementById("llm2").value;
  const prompt = document.getElementById("promptCompare").value;
  const prompt2 = document.getElementById("promptCompare2").value;

  const data1_classe0 = await loadMetrics(llm1, "classe 0", prompt);
  const data2_classe0 = await loadMetrics(llm2, "classe 0", prompt2);

  const data1_classe1 = await loadMetrics(llm1, "classe 1", prompt);
  const data2_classe1 = await loadMetrics(llm2, "classe 1", prompt2);

  const data1_na = await loadMetrics(llm1, "classe NA", prompt);
  const data2_na = await loadMetrics(llm2, "classe NA", prompt2);

  const html_na = compareMetrics(data1_na, data2_na, llm1, llm2, "classe NA");
  const html_classe0 = compareMetrics(data1_classe0, data2_classe0, llm1, llm2, "classe 0");
  const html_classe1 = compareMetrics(data1_classe1, data2_classe1, llm1, llm2, "classe 1");

  document.getElementById("comparisonResult").innerHTML =
    html_na + html_classe0 + html_classe1;
}

document.addEventListener("DOMContentLoaded", () => {
  setupCollapsibles();
});