import streamlit as st
import httpx
import openai
import requests
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
import pandas as pd
from langchain_openai import OpenAI
import os
import re
openai.api_key = "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"
os.environ['OPENAI_API_KEY']="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"
SUPABASE_URL = "https://pvyzkqvjxotrmtfzmjko.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB2eXprcXZqeG90cm10ZnptamtvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcwNjk2MDU4NCwiZXhwIjoyMDIyNTM2NTg0fQ.nmg459IRipxJcu6x2a1xf_xEJb7hA--4tZv1mMqCcOM"
openai.api_key = "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"
MODEL_NAME = "gpt-3.5-turbo"
st.set_option('deprecation.showPyplotGlobalUse', False)
supabase = httpx.Client(base_url=SUPABASE_URL, headers={"apikey": SUPABASE_API_KEY})
def handle_openai_query(df, column_names):
    query = "The dataframe consists of profile matching job requirements. The profile matching score for skills,experience,profile,location are given in skills_matching_score, experience_matching_Score etc. Plot  matching_Scores with colors : #96be25,#2596be,#be4d25,#49be25 for four categories. Do not preprocess the data like filling null values and all. Take the data as such. Label the plot y as matching_scores, x as criteria"
    if query and query.strip() != "":
        prompt_content = f"""
        The dataset is ALREADY loaded into a DataFrame named 'df'. DO NOT load the data again.

        The DataFrame has the following columns: {column_names}

        Before plotting, ensure the data is ready:
        1. Check if columns that are supposed to be numeric are recognized as such. If not, attempt to convert them.
        2. Handle NaN values by filling with mean or median.

        Use package Pandas and Matplotlib ONLY.
        Provide SINGLE CODE BLOCK with a solution using Pandas and Matplotlib plots in a single figure to address the following query:

        {query}

        - USE SINGLE CODE BLOCK with a solution.
        - Do NOT EXPLAIN the code
        - DO NOT COMMENT the code.
        - ALWAYS WRAP UP THE CODE IN A SINGLE CODE BLOCK.
        - The code block must start and end with ```

        - Example code format ```code```

        - Colors to use for background and axes of the figure : #F0F0F6
        - Try to use the following color palette for coloring the plots : #8f63ee #ced5ce #a27bf6 #3d3b41

        """
        messages = [
            {
                "role": "system",
                "content": "You are a helpful Data Visualization assistant who gives a single block without explaining or commenting the code to plot. IF ANYTHING NOT ABOUT THE DATA, JUST politely respond that you don't know.",
            },
            {"role": "user", "content": prompt_content},
        ]
        response = []
        for chunk in openai.chat.completions.create(
            model=MODEL_NAME, messages=messages, stream=True
        ):
            text = chunk.choices[0].delta.content

            if text:
                response.append(text)
                result = "".join(response).strip()
        execute_openai_code(result, df, query)
def extract_code_from_markdown(md_text):
    code_blocks = re.findall(r"```(python)?(.*?)```", md_text, re.DOTALL)
    code = "\n".join([block[1].strip() for block in code_blocks])
    return code
def execute_openai_code(response_text: str, df: pd.DataFrame, query):

    code = extract_code_from_markdown(response_text)
    if code:
        try:
            st.write("Plot:")
            exec(code)
            st.pyplot()
        except Exception as e:
            error_message = str(e)

def scores_matching(job_description,df):
  job_description = {"skills" : 'Python', "profile" : "Python", "location" : "Hyderabad","experience": 5}
  match_scores = {'skills' : 0, 'profile' : 0, 'location' : 0,'experience' : 0}
  for index, row in df.iterrows():
      match_score = 0
      if 'skills' in job_description:
          k = dict(df['education'])
          for study in k[0]:
              print('study:',study)
              for skill in job_description['skills']:
                  if skill in study['description']:
                      match_scores['skills'] = match_scores.get('skills',0) + 1
      if 'skills' in job_description:
          k = dict(df['education'])
          for study in k[0]:
              if job_description['profile'] in study['description']:
                  match_scores['skills'] = match_scores.get('skills',0) + 1
      if 'location' in job_description and 'work_locations' in row:
          for loc in row['work_locations']:
              if job_description['location'] in loc:
                  match_scores['location'] = match_scores.get('location',0) + 1
      if row['experience_yrs'] >= job_description['experience'] :
          match_scores['experience'] = 1
      df.loc[index, 'skills_match_score'] = [match_scores['skills']]
      df.loc[index, 'profile_match_score'] = [match_scores['profile']]
      df.loc[index, 'location_match_score'] = [match_scores['location']]
      df.loc[index,'experience_match_score'] = [match_scores['experience']]

def insert_job_data(job_data):
    table_name = 'Job Data'
    response = supabase.post(f'/rest/v1/{table_name}', json=job_data)
    return response
def insert_profile_data(profile_data, job_id):
    table_name = 'Profiles'
    profile_data['job_id'] = job_id
    response = supabase.post(f'/rest/v1/{table_name}', json=profile_data)
    return response

st.title("AI Recruitment Agent")
st.header("Job Specifications")
profile = st.text_input("Profile:")
experience = st.slider("Experience (in years):", 0, 20, 5)
skills = st.text_input("Skills:")
location = st.text_input("Location:")
description = st.text_area("Job Description:")
filtered_text = description
user_job_description = f"Given the job description below, extract key parameters related to skills, experience, and location. Just give one word answers for example if its skills then you might want to generate 'skills : python,ssis,automation'. Job Description : {filtered_text}"

job_data = {
        'profile': profile,
        'experience': experience,
        'skills': skills,
        'location': location,
        'job_description': description
    }
if st.button("Submit"):
  response = insert_job_data(job_data)
  if response.status_code == 201:
      st.success("Job specifications submitted successfully!")
      response = supabase.get(f'/rest/v1/Job Data')

      if response.status_code == 200:
        data = response.json()
        row_count = data[-1]['id']
        job_id = row_count
        google_api_key = "AIzaSyBWYnRdccVVSW-QeRvyt2Efifox0h8zhuc"
        skills = skills.replace("#","")
        custom_search_engine_id = "96e73954503ff483f"
        search_query = f"site:linkedin.com/in/ AND {location} AND Profile : {profile} AND Skills : {skills} AND Experience : {experience} "
        google_api_url = f"https://www.googleapis.com/customsearch/v1?q={search_query}&key={google_api_key}&cx={custom_search_engine_id}"
        response = requests.get(google_api_url)
        if response.status_code == 200:
            data = response.json()
            profiles = [item['link'] for item in data.get('items', [])]
            for profile_link in profiles[:5]:
              profile_data = {}
              publications = []
              experience = []
              studies = []
              experience_yrs = 0
              work_locations = []
              url = "https://linkedin-profiles1.p.rapidapi.com/extract"
              querystring = {"url": profile_link,"html":"1"}

              headers = {
                "X-RapidAPI-Key": "2d93fb7044msh0c9b59bbe5b6d4ep1f3fc7jsn198aafde1dea",
                "X-RapidAPI-Host": "linkedin-profiles1.p.rapidapi.com"
              }
              response = requests.get(url, headers=headers, params=querystring)
              data = response.json()
              if data:
                if 'graph' in data:
                  for item in data['graph']['@graph']:
                    if '@type' in item and item['@type'] == 'PublicationIssue':
                        pub = {}
                        pub['name'] = item['name']
                        pub['description'] = item['description']
                        publications.append(pub)
                    if '@type' in item and item['@type'] == 'Person':
                        name = item.get('name', 'N/A')
                        contact_url = item.get('url', 'N/A')

                    if 'alumniOf' in item:
                      for education in item['alumniOf']:
                          degree = education['member'].get('description', 'N/A')
                          university = education.get('name', 'N/A')
                          start_date = education['member'].get('startDate', 'N/A')
                          end_date = education['member'].get('endDate', 'N/A')
                          studies.append({ 'university': university,'description' : degree, 'start_date' : start_date, 'end_date' : end_date})
                    if 'worksFor' in item:
                      experience_yrs = (len(item['worksFor']))
                      for role in item["worksFor"]:
                        if 'name' in role:
                          if '*' not in role['name']:
                            experience.append(role['name'])
                        if 'location' in role:
                          if role['location'] not in work_locations:
                            work_locations.append(role['location'])



                  profile_data = {'name' : name,'contact_url' : contact_url, 'education' : studies,'experience' : experience,'experience_yrs' : experience_yrs,'work_locations' : work_locations,'publications' : publications}
                  st.write("Name : " + profile_data["name"])
                  st.write("Linkedin Url : " + profile_data["contact_url"])
                  response_profile = insert_profile_data(profile_data, job_id)
                  df = pd.DataFrame.from_dict([profile_data], orient='columns')
                  scores_matching(job_data,df)
                  agent = create_pandas_dataframe_agent(
                                  ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613"),
                                  df,
                                  verbose=True,
                                  agent_type=AgentType.OPENAI_FUNCTIONS,
                              )
                  response = agent.run(f"Each row in dataframe represents a profile. job description : skills - job_data['skills'], profile - job_data['profile'], location - job_data['location'],experience - job_data['experience']. Give me analysis of matching criteria. All the details regarding matching criteria's will be in skills_match_score for skills, experience_match_score for experience etc. Note : Do not say anything related to dataframe do not detail anything about what is skills_match_score and all. Give the values of the match scores. Generate in descriptive manner like person has matched with the location as he has worked in the location before something like that and for skills it can be like person has done course work regarding domains in the skills and profile it can be like during course work person has focussed mainly on the that profile something like that. Do not generate any extra information like please note and all. Just generate what was asked")
                  st.write(response)

                  if df is not None:
                      column_names = ", ".join(df.columns)
                      if not df.empty:
                          handle_openai_query(df, column_names)
                  if response_profile.status_code == 200:
                    st.write("Successfully inserted into profiles")
                  else:
                    st.write(response_profile.text)
                else:
                  st.write("NO GRAPH")

  else:
        st.error(f"Failed to insert data. Status code: {response.status_code}")
        st.write(response.text)
