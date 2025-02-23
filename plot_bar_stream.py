import os
import pandas as pd
import streamlit as st
from io import BytesIO
import zipfile
import plotly.graph_objects as go

def wrap_title(title, width=40):
    # wrap the title
    return "<br>".join([title[i:i+width] for i in range(0, len(title), width)])

def plot_bar_graph(df: pd.DataFrame, age_group_column: str, question_column: str, answer_column: str) -> go.Figure:
    # make folder for output
    temp_dir = "output"
    os.makedirs(temp_dir, exist_ok=True)

    # make file name list
    file_name_list = []

    # make age group column
    # age_group_column = "年齢区分"
    # df[age_group_column] = pd.cut(df[age_column], bins=range(20, 71, 10), right=False, labels=[f"{i}-{i+9}" for i in range(20, 70, 10)])

    # color code for each age group
    color_palette = [
    "#8fd0ff", "#589fef", "#0071bc", "#00468b", "#00215d", 
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
    ]

    # get unique questions
    unique_questions = df[question_column].unique()

    for question in unique_questions:
        # filter data by question
        question_data = df[df[question_column] == question]
        
        # count the number of responses for each answer
        grouped = question_data.groupby([answer_column])[age_group_column].value_counts().unstack(fill_value=0)
        
        # create a bar graph
        fig = go.Figure()
        for idx, response in enumerate(grouped.columns):
            fig.add_trace(go.Bar(
                x=grouped.index,
                y=grouped[response],
                name=f"{str(response).split('-')[0]}代",
                marker_color=color_palette[idx % len(color_palette)],
                text=grouped[response],
                textposition="inside"
            ))
        
        # update layout
        fig.update_layout(
            title=wrap_title(question),
            xaxis_title="評価",
            yaxis_title="回答数",
            barmode="stack",
            legend_title="年齢区分",
            xaxis=dict(
                tickvals=[1, 2, 3, 4, 5],  # labels of the x-axis
                ticktext=["1", "2", "3", "4", "5"],  # custom tick text
                range=[0.5,5.5]
            )
        )
        
        # save the figure
        fig.write_html(f"{temp_dir}/{question[:50]}.html")
        file_name_list.append([f"{question[:50]}.html", question])
    
    # create a file name excel file
    file_name_df = pd.DataFrame(file_name_list, columns=["file_name", "question"])
    file_name_df.to_excel(f"{temp_dir}/file_name.xlsx", index=False)

     # create a zip file
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.basename(file_path))
    
    # remove the temporary directory
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)
    
    zip_buffer.seek(0)
    return zip_buffer

def open_file(file):
    if file.name.split('.')[-1] == 'csv':
        return pd.read_csv(file)
    elif file.name.split('.')[-1] == 'xlsx':
        return pd.read_excel(file)
    else:
        return None
    
def fill_null(df):
    # fill null data
    # fill null data with average value if it is numerical data, else fill with 0
    for column in df.columns:
        if df[column].dtype in ['int64', 'float64']:
            df[column] = df[column].fillna(df[column].mean())
        else:
            df[column] = df[column].fillna(0)
    return df

def streamlit_app():
    st.title("Bar Graph Generator")
    input_file = st.file_uploader("Upload CSV", type=['csv', 'xlsx'])
    if input_file is not None:
        df: pd.DataFrame = open_file(input_file)

        # for null data
        df = fill_null(df)
        
        # show the first 5 rows of the data
        st.write(df.head())

        # select box for age column
        age_column = st.radio("Select the age column", df.columns)
        # select box for question column
        question_column = st.radio("Select the question column", df.columns)
        # select box for answer column
        answer_column = st.radio("Select the answer column", df.columns)

        # button to generate bar graph
        if st.button("Generate Bar Graph"):
            if age_column == question_column or age_column == answer_column or question_column == answer_column:
                st.error("Please select different columns for age, question, and answer.")
                return
            # if not selected, show error message
            if age_column is None or question_column is None or answer_column is None:
                st.error("Please select columns for age, question, and answer.")
                return
            zip_file = plot_bar_graph(df, age_column, question_column, answer_column)
            st.success("Bar graphs are generated!")
            
            # download the zip file
            st.write("Download the folder")
            st.download_button(
                label="Download",
                data=zip_file,
                file_name="graphs.zip",
                mime="application/zip"
            )
        
if __name__ == "__main__":
    streamlit_app()

