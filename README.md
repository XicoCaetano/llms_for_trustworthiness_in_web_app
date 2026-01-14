# Java Code Trustworthiness Analysis with LLMs

This project is a robust tool for assessing the trustworthiness of Java source code, leveraging the power of Large Language Models (LLMs). The tool methodically analyzes Java functions from the **WSVD-Bench** dataset against **16 secure coding practices derived from OWASP**, primarily focusing on input validation.

The ultimate goal is to identify missing security practices and generate a quantitative **trustworthiness score** for each method, enabling a comparative analysis between different versions of the same software. The results are presented in an interactive dashboard for easy interpretation.

## Architecture and Workflow

The process is divided into four main phases, which transform Java source code into visualizable trustworthiness scores.

### Phase 1: Static Analysis with Joern

The first phase prepares the necessary context for the LLM's analysis.

1.  **Project Import**: The Java source code (located at `PROJECT_PATH`) is imported into a running **Joern** server.
2.  **CPG Generation**: Joern analyzes the code and builds a Code Property Graph (CPG), a data structure that semantically represents the code.
3.  **Called Method (Callee) Extraction**: For each target method, CPGQL queries are executed to identify all the methods it calls (known as _callees_).
4.  **Contextualization**: The result (`method -> [callees]`) is saved to a JSON file. This information is crucial for providing rich context to the LLM in the next phase, allowing it to analyze not only the method itself but also the functions it invokes.

_(Main components: `src/joern_processing/joern_processor.py`)_

### Phase 2: LLM-Based Practice Assessment

This is the core phase, where the LLM's intelligence is applied to evaluate the code.

1.  **Two-Step Prompting Strategy**: To ensure accuracy, the tool uses a sophisticated prompting approach:

    - **Applicability Check**: For each of the 16 security practices, the LLM receives the method's code and first determines if the practice is **applicable** to the method's context.
    - **Following Check**: If a practice is deemed applicable, a second prompt is sent to the LLM. This prompt contains the main method code and the LLM then assesses whether the method adheres to the security practice.

2.  **Result Generation**: The output for each method is a structured list representing the status of each of the 16 practices:

    - `0`: Practice correctly followed.
    - `1`: Practice applicable, but missing or incorrectly implemented (failure).
    - `NA`: Practice not applicable to the method.

3.  **Storage**: The detailed results are saved in a JSON file for later processing.

### Phase 3: Trustworthiness Score Calculation

In this phase, the raw results from the LLM are converted into a numerical score.

1.  **Weight Loading**: A `weights.json` file is loaded. This file assigns an importance weight to each of the 16 security practices.
2.  **Weighted Calculation**: A script processes the results (`[0, 1, NA]`) and calculates a trustworthiness score for each method. The score reflects the sum of the weights of the missing practices (`1`).
3.  **Intelligent Weight Redistribution**: A key feature of the calculation is that the weights of non-applicable practices (`NA`) are proportionally redistributed among the applicable practices. This ensures the final score is always fair and normalized, regardless of the number of relevant practices for a given method.
4.  **Consolidation**: The final scores, along with the raw practice data, are consolidated into several JSON files, which will serve as the data source for the dashboard.

### Phase 4: Dashboard Visualization

The final phase consists of presenting the data in a clear and interactive way.

1.  **Interactive Dashboard**: A web dashboard built with HTML, CSS, and **Plotly.js**.
2.  **Comparative Analysis**: The user can select the LLM, prompt version, and Java file to view a bar chart that compares the trustworthiness scores across different code versions (`Vx0`, `VxA`, etc.).
3.  **Comparison with Ground Truth**: The chart also displays the _ground truth_ scores (based on manual analysis), allowing for a direct assessment of the LLM's accuracy.
4.  **Vulnerability Highlighting**: The bars in the chart corresponding to methods known to be vulnerable in a specific version are highlighted in red, making it easier to identify security regressions or improvements.

_(Main components: `src/dashboard_llms/dashboard/`)_

## How to Run the Project

### Prerequisites

- Python 3.9+
- A Joern server instance running locally or remotely.
- Java Development Kit (JDK) (required by Joern).
- API credentials for an LLM service (e.g., OpenAI, Google Vertex AI).

### Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/seu-usuario/llms_for_trustworthiness_in_web_app.git
    cd llms_for_trustworthiness_in_web_app
    ```

2.  Install the Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  Create a `.env` file in the project root. You can use the `src/config.py` file as a reference for the required variables.
2.  Fill the `.env` file with your settings:

    ```env
    # .env example
    OPENAI_API_KEY="sk-..."
    MODEL_NAME="gpt-3.5-turbo"

    OPENAI_API_KEY_4="sk-..."
    MODEL_NAME_4="gpt-4o-mini"

    # Your Joern server endpoint
    JOERN_SERVER_ENDPOINT="http://localhost:9000"

    # Path to the Java project to be analyzed
    PROJECT_PATH="./Dataset/wsvd-bench/src/main/java/pt/uc/dei/wsvdbench"
    ```

### Running the Full Workflow

The tool offers two execution modes from the project root: a fully automatic one and an interactive one that allows for more granular control.

#### Automatic Execution (`main2.py`)

This mode is ideal for complete, batch assessments. The `main2.py` script iterates over all pre-configured combinations of LLMs and prompts, running the entire analysis and scoring pipeline without user intervention.

1.  **Execution**:

    ```bash
    python main2.py
    ```

2.  **Process**:
    - Runs the analysis for each LLM and prompt combination.
    - Generates the security practice assessment results.

#### Interactive Execution with Notifications (`main.py`)

This mode is perfect for testing, debugging, or focusing the analysis on a specific configuration. The `main.py` script guides the user through a menu to select the desired LLM and prompt.

1.  **Execution**:

    ```bash
    python main.py
    ```

2.  **Interactive Process**:

    - Upon starting, the script presents a menu to select the LLM model.
    - Next, it presents a menu to select the prompt version to use.
    - After selection, the pipeline is executed for the chosen combination.

3.  **Telegram Notifications**:
    A key feature of this mode is sending notifications to a Telegram chat, informing about the progress and completion of the analysis. To enable this feature, you need to configure the credentials in the `.env` file.

##### Configuring Telegram Notifications

To receive status notifications, follow these steps:

1.  **Create a Telegram Bot**: Start a conversation with `@BotFather` on Telegram, follow the instructions to create a new bot, and save the **API token** it provides.
2.  **Get Your Chat ID**:
    - Find your new bot on Telegram and send it a message (e.g., `/start`).
    - Open the following URL in your browser, replacing `<YOUR_TOKEN_HERE>` with your bot's token: `https://api.telegram.org/bot<YOUR_TOKEN_HERE>/getUpdates`.
    - In the JSON response, locate the `chat` object and copy the value of the `id` field. This is your `CHAT_ID`.
3.  **Update the `.env` File**: Add the token and chat ID to your `.env` file in the project root:
    ```env
    TOKEN="<YOUR_BOT_TOKEN_HERE>"
    CHAT_ID="<YOUR_CHAT_ID_HERE>"
    ```

### Visualizing the Results

Regardless of the chosen execution mode, the final step is always data visualization.

1.  **Open the Dashboard**: Open the `src/dashboard_llms/dashboard/index.html` file in a web browser.
2.  **Explore the Data**: Use the dropdown menus on the dashboard to select the LLM, prompt version, and Java file, allowing you to visually explore and compare the trustworthiness scores.

## Directory Structure

```
├── Dataset/                  # Contém o código-fonte Java do WSVD-Bench para análise.
├── additional-experiment/
│   └── results_process/      # Jons dos resultados das experiencias adicionais.
├── src/
│   ├── config.py             # Carrega as configurações a partir do ficheiro .env.
│   ├── dashboard_llms/       # Ficheiros do dashboard e scripts de processamento do ground truth.
│   ├── java_processing/      # Módulo para parsing de ficheiros Java.
│   ├── joern_processing/     # Módulo para interação com o servidor Joern.
│   ├── llms_and_prompts/     # Clientes de LLM (GPT, VertexAI) e ficheiros de system roles.
│   ├── template_processing/  # Lógica principal para avaliação com LLMs usando templates Jinja2.
│   ├── tests_results/        # Jsons todos guardados das execucoes e usados para criar a dashboard.
│   └── ...
└── README.md                 # Este ficheiro.
```

## Tecnologias Utilizadas

- **Backend**: Python
- **Análise de Código Estático**: Joern
- **Modelos de Linguagem**: OpenAI GPT-3.5/4, Google Vertex AI (Gemini)
- **Parsing de Java**: `javalang`
- **Manipulação de Dados**: `pandas`
- **Visualização**: `Plotly.js`
