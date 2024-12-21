import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM
from langchain.tools import tool
from tavily import TavilyClient
from dotenv import load_dotenv

# Function to set up environment and load API keys (ensure .streamlit/secrets.toml is setup correctly)
def setup_environment():
    load_dotenv()
    tavily_api_key = st.secrets["TAVILY_API_KEY"]
    cerebra_api_key = st.secrets["CEREBRA_API_KEY"]
    
    os.environ['GROQ_API_KEY'] = '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'

    client = TavilyClient(api_key=tavily_api_key)
    llm = LLM(api_key=cerebra_api_key, model="cerebras/llama-3.3-70b")

    return client, llm

# --- Tooling ---
@tool
def web_search(query):
    """Useful for when you need to search the web for information."""
    client, _ = setup_environment() # Get client for every tool call
    return client.search(query, search_depth="advanced")["results"]


@tool
def save_to_file(content, filename):
    """Useful for saving content to a file."""
    with open(filename, "w") as f:
        f.write(content)
    return f"File saved to {filename}"

# --- Agents ---
def create_agents(llm):
    research_agent = Agent(
        role='Market Research Analyst',
        goal="Conduct comprehensive market research on the given company and industry, identifying key trends, challenges, and strategic focuses. Generate a thorough understanding of the company and its sector. Provide detailed insights .",
        backstory="A meticulous market research analyst with a background in data analysis and industry trends. Known for gathering information from diverse sources and providing strategic insights. Focuses on delivering actionable research that informs strategic decisions.",
        verbose=True,
        llm=llm,
        tools=[web_search],
        memory=True,
        allow_delegation=True,
    )

    use_case_agent = Agent(
        role='AI and GenAI Solutions Architect',
        goal="Analyze industry trends and company-specific information to propose innovative and practical AI and GenAI use cases, focusing on enhancing operational efficiency and customer experiences. Prioritize GenAI solutions that can significantly improve current processes.",
        backstory="A highly skilled AI/ML engineer with expertise in machine learning, generative AI, and automation. Known for creating effective solutions from business needs and proposing use cases that drive value and improve efficiency.",
        verbose=True,
        llm=llm,
        tools=[web_search],
        memory=True,
        allow_delegation=True,
    )

    resource_agent = Agent(
        role='Data and Resource Curator',
        goal="Gather relevant datasets and resource links for proposed AI/GenAI use cases. Ensure the resources are reliable, up-to-date, and suitable for practical implementation. Use platforms like Kaggle, HuggingFace, and GitHub for datasets.",
        backstory="A detail-oriented data curator with expertise in data management and resource organization. Specializes in identifying relevant datasets and maintaining an accurate and useful resource library. Ensures resources are of high quality and easy to access.",
        verbose=True,
        llm=llm,
        tools=[web_search, save_to_file],
        memory=True,
        allow_delegation=True,
    )

    proposal_agent = Agent(
        role='Proposal Writer',
        goal="Craft a well-structured, comprehensive, and compelling proposal that effectively communicates the top AI/GenAI use cases, their benefits, and actionable recommendations, ensuring it is persuasive and easy to understand. Ensure the proposal includes references and clickable resource links.",
        backstory="An experienced proposal writer with a history of creating persuasive and high-impact business proposals. Expert at synthesizing complex information into clear, concise proposals that convince stakeholders.",
        verbose=True,
        llm=llm,
        tools=[save_to_file],
        memory=True,
        allow_delegation=True,
    )
    return research_agent, use_case_agent, resource_agent, proposal_agent

# --- Main Execution Function ---
def generate_proposal(company_name, industry_name):
    client, llm = setup_environment() # Setup Environment
    research_agent, use_case_agent, resource_agent, proposal_agent = create_agents(llm) # Create Agents

    # --- Tasks ---
    research_task = Task(
        description=f"""
            Conduct detailed market research on the {industry_name} industry and {company_name}.
            Use a web browser tool to understand the industry's landscape and the segment {company_name} operates in (e.g., Automotive, Manufacturing, Finance, Retail, Healthcare).
            Identify {company_name}'s key offerings, strategic focus areas (operations, supply chain, customer experience), and provide its vision and product information.
             Refer to reports and insights on AI and digital transformation from sources such as McKinsey, Deloitte, or Nexocode.
            Search for industry-specific use cases. For example, “how is the retail industry leveraging AI and ML” or “AI applications in automotive manufacturing.”
            Your analysis should be detailed and supported by references from reliable sources.
            """,
        agent=research_agent,
        expected_output="A detailed report summarizing the company’s industry, key offerings, strategic focuses, and vision with clear product overview. Include references from sources like McKinsey, Deloitte, and Nexocode."
    )
    
    market_standards_task = Task(
         description=f"""
            Analyze industry trends and standards within the {industry_name} sector related to AI, ML, and automation, based on the research you conducted for {company_name}.
            Propose at least 8 innovative and practical use cases where {company_name} can leverage GenAI, LLMs, and ML technologies to improve processes, enhance customer satisfaction, and boost operational efficiency.
           For each use case:
             - Describe the use case and how it addresses a specific business problem or opportunity for {company_name}.
              - Explain how GenAI, LLMs, or other ML technologies would be applied.
              - Search for current Generative AI trends and technologies and how they can be integrated.
            - Detail the expected outcomes and benefits.
           - Include realistic examples of how it would work in practice.
            - Ensure that the proposal is better than the current methodology.
             Your use cases should be innovative, feasible, and provide tangible benefits.
          """,
        agent=use_case_agent,
        context=[research_task],
        expected_output="A detailed list of at least 8 use cases proposals in markdown format, each clearly describing the problem, technologies involved, expected outcomes, practical examples, and comparison to the status quo."
    )
    
    resource_task = Task(
        description=f"""
            Collect the use cases from the previous step and search for relevant datasets on platforms like Kaggle, HuggingFace, and GitHub.
             Save the resource links fetched in a text or markdown file. Ensure these links are clickable.
             Ensure that each provided resource is directly related to the proposed use cases. Include any usage instructions if available
           """,
        agent=resource_agent,
        context=[market_standards_task],
        expected_output="A single markdown file with clickable resource links for all use cases defined, with descriptions and usage instructions."
    )
    
    final_proposal_task = Task(
        description=f"""
             List down the top use cases to be delivered to the customer, ensuring they are aligned with the company’s goals and operational needs.
             Ensure that all the suggested use cases are added with links to the resources
             Add references to the reports and analysis made to suggest these use cases.
               Prepare a well-structured, and compelling proposal, including:
            - A concise introduction that outlines the project's objectives and the overall approach.
            - A summary of the key findings from the market research and {company_name}'s specific strategic areas.
            - A detailed presentation of the top AI/GenAI use cases, including their descriptions, benefits, and required technologies.
            - Explicit, clickable links to the dataset resources and instructions on their usage.
             - Clear, actionable insights and recommendations, aligned with {company_name}'s goals and operational needs.
             - Proper citations and references to support the use case proposals and resource links.
            The proposal must be well-written, organized, and persuasive, presenting the information in a manner easily understandable for stakeholders.
            """,
        agent=proposal_agent,
        context=[resource_task],
        expected_output="A single final, persuasive proposal in markdown format with actionable insights, clear recommendations, and clickable resource links. Include references and a list of top use cases aligned with the company's goals."
        )

    # --- Crew ---
    crew = Crew(
        agents=[research_agent, use_case_agent, resource_agent, proposal_agent],
        tasks=[research_task, market_standards_task, resource_task, final_proposal_task],
        process=Process.sequential,
        verbose=True,
        memory=True
    )

    # --- Execute Crew ---
    results = crew.kickoff()
    # Extracting final proposal and resource file
    proposal = None
    resources = None
    for task_output in crew.get_task_outputs():
        if task_output.task == final_proposal_task:
            proposal = task_output.output
        if task_output.task == resource_task:
            resources = task_output.output
    return proposal, resources

# --- Streamlit App ---
st.set_page_config(page_title="AI/ML Proposal Generator", layout="wide")
st.title("AI/ML Proposal Generator")
st.markdown("Enter your company and industry to generate a customized AI/ML proposal.")

col1, col2 = st.columns(2)
with col1:
    company_name = st.text_input("Company Name")
with col2:
    industry_name = st.text_input("Industry")

if st.button("Generate Proposal"):
    if company_name and industry_name:
        with st.spinner("Generating Proposal..."):
            proposal, resources = generate_proposal(company_name, industry_name)
            st.header("Generated Proposal:")
            st.markdown(proposal)
            st.header("Resources:")
            st.markdown(resources)
    else:
        st.error("Please enter both company name and industry.")