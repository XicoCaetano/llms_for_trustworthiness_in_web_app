import argparse
from src.template_processing.individual_process.individual_practices import IndividualPractices
from tool.src.template_processing.universal_prompts.universal_processing import UniversalProcessing
from src.template_processing.saves.save_individual import SaveIndividual
from src.java_processing.java_processor import JavaProcessor
from src.config import PROJECT_PATH, OUTPUT_JSON_DIR
from jinja2 import Environment, FileSystemLoader
import os, json
import re, time
from src.llms_and_prompts.llm_chatgpt35_turbo import LLMChatGPT
from src.llms_and_prompts.llm_chatgpt4o_mini import LLMChatGPT4oMini
from src.llms_and_prompts.llm_chatgpt41_mini import LLMChatGPT41Mini
from src.llms_and_prompts.llm_chatgpt41 import LLMChatGPT41
from src.config import OPENAI_API_KEY_PROF, MODEL_NAME, OPENAI_API_KEY_PROF
from src.joern_processing.joern_processor import JoernProcessor


def template_def(template_name, env):
    """Lê o conteúdo do arquivo de template e retorna como uma string."""
    # Ensure the template name ends with .txt
    if not template_name.endswith(".txt"):
        template_name += ".txt"
    template_path = os.path.join(env.loader.searchpath[0], template_name)
    with open(template_path, 'r', encoding='utf-8') as file:
        template_content = file.read()
    return template_content


prompt_choices = {
    1: "1",
    2: "2",
    # 3: "3",
    # 4: "4",
    5: "5"
}

llm_paths = {
    1: "gpt-3.5-turbo",
    2: "gpt-4o-mini",
    3: "gpt-4.1",
    4: "gpt-4.1-mini"
}

def create_llm_1_2(version, valor, tipo):
    match version:
        case 1:
            return LLMChatGPT(OPENAI_API_KEY_PROF, MODEL_NAME, f"/system_roles/system_role_{valor}/rules_t{valor}_{tipo}")
        case 2:
            return LLMChatGPT4oMini(OPENAI_API_KEY_PROF, f"/system_roles/system_role_{valor}/rules_t{valor}_{tipo}")
        case 3:
            return LLMChatGPT41(OPENAI_API_KEY_PROF, f"/system_roles/system_role_{valor}/rules_t{valor}_{tipo}")
        case 4:
            return LLMChatGPT41Mini(OPENAI_API_KEY_PROF, f"/system_roles/system_role_{valor}/rules_t{valor}_{tipo}")


def create_llm_4_5(version, valor, tipo, p):
    match version:
        case 1:
            return LLMChatGPT(OPENAI_API_KEY_PROF, MODEL_NAME, f"/system_roles/system_role_{valor}/{tipo}/a/p{p}")
        case 2:
            return LLMChatGPT4oMini(OPENAI_API_KEY_PROF, f"/system_roles/system_role_{valor}/{tipo}/a/p{p}")
        case 3:
            return LLMChatGPT41(OPENAI_API_KEY_PROF, f"/system_roles/system_role_{valor}/{tipo}/a/p{p}")
        case 4:
            return LLMChatGPT41Mini(OPENAI_API_KEY_PROF, f"/system_roles/system_role_{valor}/{tipo}/a/p{p}")

def parse_llm_response(response):
    accepted_answers = {"yes;", "no;"}

    # Procurar o primeiro padrão tipo "1. Yes;" ou "1. No;"
    match = re.search(r'1\.\s*(yes;|no;)', response, re.IGNORECASE)
    if not match:
        print("[!] No valid first answer found — retrying...")
        return [], False

    ans = match.group(1).lower()
    if ans not in accepted_answers:
        print(f"[!] Invalid answer: {ans}")
        return [], False

    return [ans], True


def run(llm_version, code, prompt):

    llm_name = llm_paths.get(llm_version, "gpt-3.5-turbo")

    print(f"🚀 Running Individual Practices with LLM: {llm_name}")
    print(f"PROMPT: {prompt}")

    followed_path = f"./src/llms_and_prompts/prompts/{llm_name}/individual_practices_prompts/prompt_{prompt}/followed/a"
    applicable_path = f"./src/llms_and_prompts/prompts/{llm_name}/individual_practices_prompts/prompt_{prompt}/applicability/a"

    results_path = f"./src/additional-experiment/results_process/test_results/individual_practices/{llm_name}/score_1/"

    env1 = Environment(loader=FileSystemLoader(followed_path), autoescape=True)
    env2 = Environment(loader=FileSystemLoader(applicable_path), autoescape=True)

    save_individual = SaveIndividual(PROJECT_PATH, results_path)
    save_individual.structure_score_1(prompt)

    question_answers = {}
    applicable_list = []
    
    for i in range(1, 17):

        if prompt == 1 or prompt == 2:
            llm = create_llm_1_2(llm_version, prompt, "ap")
        else:
            llm = create_llm_4_5(llm_version, prompt, "applicability", i)

        template_name = f"p{i}.txt"
        template = template_def(template_name, env2)

        while True:
            response = llm.response_template_individual_practices(template, code)
            print("[DEBUG] Raw LLM Response:", repr(response))
            parsed, valid = parse_llm_response(response)
            if valid and parsed:
                ans = parsed[0]
                applicable_list.append(i if ans == "yes;" else 0)
                break
            time.sleep(5)

        question_answers["applicable"] = applicable_list

    print(f"[OK] Aplicable: {applicable_list}")

    # time.sleep(5)  # Wait before retrying

    followed(question_answers, prompt, llm_version, code, env1, save_individual)


def followed (question_answers, prompt, llm_version, code, env1, save):
    new_list = []

    for k in question_answers["applicable"]:
        if k == 0:
            new_list.append(2)
            continue

        template_name = f"p{k}.txt"

        if prompt == 1 or prompt == 2:
            llm = create_llm_1_2(llm_version, prompt, "f")
        elif prompt == 5:
            llm = create_llm_4_5(llm_version, prompt, "followed", k)


        template = template_def(template_name, env1)

        while True:
            response = llm.response_template_individual_practices(template, code)
            print("[DEBUG] Raw LLM Response:", repr(response))
            parsed, valid = parse_llm_response(response)
            if valid and parsed:
                ans = parsed[0]
                new_list.append(1 if ans == "yes;" else 0)
                break
            time.sleep(5)
                
    question_answers["results"] = new_list

    parent_file = "tpcw"
    file = "CreateNewCustomer_VxA.java"
    name = "enterAddress"
    print(question_answers)
    save.save_score_1(parent_file, file, name, question_answers, prompt)




if __name__ == "__main__":

    lista = [1,2,3,4]
    prompt = [1,2,5]

    code = """
    private int enterAddress(Connection con, String street1, String street2,
                        String city, String state, String zip, String country) {
        int addrId = 0;

        try {
            if (street1 == null || street2 == null || city == null || 
                state == null || zip == null || country == null) {
                throw new IllegalArgumentException("All address fields are required");
            }
            
            street1 = street1.trim();
            street2 = street2.trim();
            city = city.trim();
            state = state.trim();
            zip = zip.trim();
            country = country.trim();
            
            if (street1.length() > 100 || street2.length() > 100) {
                throw new IllegalArgumentException("Street address exceeds maximum length (100)");
            }
            if (city.length() > 50) {
                throw new IllegalArgumentException("City exceeds maximum length (50)");
            }
            if (state.length() > 50) {
                throw new IllegalArgumentException("State exceeds maximum length (50)");
            }
            if (zip.length() > 15) {
                throw new IllegalArgumentException("ZIP code exceeds maximum length (15)");
            }
            if (country.length() > 50) {
                throw new IllegalArgumentException("Country exceeds maximum length (50)");
            }
            
            if (street1.contains("\u0000") || street2.contains("\u0000") || 
                city.contains("\u0000") || state.contains("\u0000") || 
                zip.contains("\u0000") || country.contains("\u0000") ||
                street1.contains("%00") || street2.contains("%00") ||
                city.contains("%00") || state.contains("%00") ||
                zip.contains("%00") || country.contains("%00")) {
                throw new IllegalArgumentException("Input contains null bytes");
            }
            
            if (street1.contains("\r") || street1.contains("\n") || street1.contains("%0d") || street1.contains("%0a") ||
                street2.contains("\r") || street2.contains("\n") || street2.contains("%0d") || street2.contains("%0a") ||
                city.contains("\r") || city.contains("\n") || city.contains("%0d") || city.contains("%0a") ||
                state.contains("\r") || state.contains("\n") || state.contains("%0d") || state.contains("%0a") ||
                zip.contains("\r") || zip.contains("\n") || zip.contains("%0d") || zip.contains("%0a") ||
                country.contains("\r") || country.contains("\n") || country.contains("%0d") || country.contains("%0a")) {
                throw new IllegalArgumentException("Input contains newline characters");
            }
            
            if (street1.contains("../") || street1.contains("..\\") || street1.contains("%c0%ae%c0%ae") ||
                street2.contains("../") || street2.contains("..\\") || street2.contains("%c0%ae%c0%ae") ||
                city.contains("../") || city.contains("..\\") || city.contains("%c0%ae%c0%ae") ||
                state.contains("../") || state.contains("..\\") || state.contains("%c0%ae%c0%ae") ||
                zip.contains("../") || zip.contains("..\\") || zip.contains("%c0%ae%c0%ae") ||
                country.contains("../") || country.contains("..\\") || country.contains("%c0%ae%c0%ae")) {
                throw new IllegalArgumentException("Input contains path traversal characters");
            }
            
            String[] inputs = {street1, street2, city, state, zip, country};
            for (String input : inputs) {
                String lower = input.toLowerCase();
                if (lower.contains("--") || lower.contains("/*") || lower.contains("*/") ||
                    lower.contains("xp_") || lower.contains(";") || lower.contains("'") ||
                    lower.contains("\"") || lower.contains("drop ") || lower.contains("delete ") ||
                    lower.contains("insert ") || lower.contains("update ") || lower.contains("select ")) {
                    throw new IllegalArgumentException("Input contains potentially hazardous characters");
                }
            }
            
            if (!street1.matches("^[a-zA-Z0-9\\s.,-]+$") || !street2.matches("^[a-zA-Z0-9\\s.,-]+$")) {
                throw new IllegalArgumentException("Street contains invalid characters");
            }
            if (!city.matches("^[a-zA-Z\\s-]+$")) {
                throw new IllegalArgumentException("City contains invalid characters");
            }
            if (!state.matches("^[a-zA-Z\\s-]+$")) {
                throw new IllegalArgumentException("State contains invalid characters");
            }
            if (!zip.matches("^[0-9-]+$")) {
                throw new IllegalArgumentException("ZIP code contains invalid characters");
            }
            if (!country.matches("^[a-zA-Z\\s]+$")) {
                throw new IllegalArgumentException("Country contains invalid characters");
            }
            
        } catch (IllegalArgumentException e) {
            System.err.println("Validation error: " + e.getMessage());
            return 0;
        }

        PreparedStatement getCoIdStmt = null;
        PreparedStatement matchAddressStmt = null;
        PreparedStatement insertAddressStmt = null;
        PreparedStatement getMaxAddrIdStmt = null;
        ResultSet rs = null;

        try {

            String getCoIdQuery = "SELECT co_id FROM tpcw_country WHERE co_name = ?";
            getCoIdStmt = con.prepareStatement(getCoIdQuery);
            getCoIdStmt.setString(1, country);
            rs = getCoIdStmt.executeQuery();
            
            if (!rs.next()) {
                System.err.println("Country not found: " + country);
                return 0;
            }
            
            int addrCoId = rs.getInt("co_id");
            rs.close();
            rs = null;
            
            String matchQuery = "SELECT addr_id FROM tpcw_address " +
                                "WHERE addr_street1 = ? " +
                                "AND addr_street2 = ? " +
                                "AND addr_city = ? " +
                                "AND addr_state = ? " +
                                "AND addr_zip = ? " +
                                "AND addr_co_id = ?";
            
            matchAddressStmt = con.prepareStatement(matchQuery);
            matchAddressStmt.setString(1, street1);
            matchAddressStmt.setString(2, street2);
            matchAddressStmt.setString(3, city);
            matchAddressStmt.setString(4, state);
            matchAddressStmt.setString(5, zip);
            matchAddressStmt.setInt(6, addrCoId);
            
            rs = matchAddressStmt.executeQuery();
            
            if (!rs.next()) {
                synchronized (Address.class) {
                    // Get next ID
                    getMaxAddrIdStmt = con.prepareStatement(
                        "SELECT COALESCE(MAX(addr_id), 0) + 1 AS next_id FROM tpcw_address"
                    );
                    ResultSet rs2 = getMaxAddrIdStmt.executeQuery();
                    
                    if (rs2.next()) {
                        addrId = rs2.getInt("next_id");
                    }
                    rs2.close();
                    
                    String insertQuery = "INSERT INTO tpcw_address " +
                                        "(addr_id, addr_street1, addr_street2, addr_city, " +
                                        "addr_state, addr_zip, addr_co_id) " +
                                        "VALUES (?, ?, ?, ?, ?, ?, ?)";
                    
                    insertAddressStmt = con.prepareStatement(insertQuery);
                    insertAddressStmt.setInt(1, addrId);
                    insertAddressStmt.setString(2, street1);
                    insertAddressStmt.setString(3, street2);
                    insertAddressStmt.setString(4, city);
                    insertAddressStmt.setString(5, state);
                    insertAddressStmt.setString(6, zip);
                    insertAddressStmt.setInt(7, addrCoId);
                    
                    insertAddressStmt.executeUpdate();
                }
            } else {
                addrId = rs.getInt("addr_id");
            }
            
        } catch (SQLException ex) {
            System.err.println("Database error: " + ex.getMessage());
            addrId = 0;
        } finally {
            try {
                if (rs != null) rs.close();
                if (getCoIdStmt != null) getCoIdStmt.close();
                if (matchAddressStmt != null) matchAddressStmt.close();
                if (insertAddressStmt != null) insertAddressStmt.close();
                if (getMaxAddrIdStmt != null) getMaxAddrIdStmt.close();
            } catch (SQLException e) {
                System.err.println("Error closing resources: " + e.getMessage());
            }
        }

        return addrId;
        }
    """

    for i in lista:
        for k in prompt:
            run(i, code, k)