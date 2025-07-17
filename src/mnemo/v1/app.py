import gc
import json
import os
import time
from collections import defaultdict
from pathlib import Path

import streamlit as st
from sentence_transformers import SentenceTransformer

from mnemo.v1.scripts.app_funcs import *

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["FAISS_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"


@st.cache_resource
def load_embedding_model():
    """load the embedding model from the specified path"""
    with open(os.path.join(str(Path(__file__).parent.joinpath("config").absolute()), "config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)
    embedding_model_path = os.path.join(str(Path(__file__).parents[3].absolute()), "embedding_models", config["embedding_model_name"])
    model = SentenceTransformer(embedding_model_path)
    return model


def stop():
    """stop the process by setting the session state"""
    st.session_state.stop_flag = True


def increase_display_count():
    """increase the number of displayed results by 5"""
    st.session_state.display_count += 5


# ========= start here ===========
# set the page configuration
st.set_page_config(page_title="ThatsNotMyName", layout="wide")

# set the custom CSS for the app
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
    }
    .stSidebar [data-baseweb="radio"] {
        margin-top: 1rem;
    }
    .stSlider > div > div {
        margin-top: 1rem;
    }
    .stRadio {
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    .stButton {
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# pre-load the embedding model
embedding_model = load_embedding_model()

# initialize the session state variables
if "running" not in st.session_state:
    st.session_state.running = False
if "stop_flag" not in st.session_state:
    st.session_state.stop_flag = False

# ================= sidebar =================
with st.sidebar:
    st.caption('--------------------------------')
    choice = st.radio(
        "Choose a task:", ("search", "organize", "initialize"),
        help="`search`: find files based on your query, `organize`: embedding files to database for future search, `initialize`: initialize the database")
    st.markdown("<br>" * 2, unsafe_allow_html=True)

    st.caption('--------------------------------')
    if "llm_model_choice" not in st.session_state:
        st.session_state.llm_model_choice = "quality"  # 默认值
    llm_model_choice = st.radio(
        "Chooose LLM model:", ("quality", "speed"),
        help="`quality`: use Mistral-Small-3.2-24B-Instruct-2506_Q4_K_M model, `speed`: use Nous-Hermes-2-Mistral-7B-DPO_Q4_K_M model")
    st.session_state.llm_model_choice = llm_model_choice
    st.markdown("<br>" * 2, unsafe_allow_html=True)

    st.caption('--------------------------------')
    st.caption("Click the button if you want to stop the process when running")
    st.button("Stop", on_click=stop, type="secondary", use_container_width=True)

# ================ title ==============
st.logo(os.path.join(str(Path(__file__).parent.joinpath("assets").absolute()), "image-removebg-preview.png"), size="large")
st.title("Mnemo v1.0")
st.caption('💭 Help you organize and search local files')
st.caption('--------------------------------')

# ================= main content =================
input_col, _, output_col = st.columns([4, 0.5, 8], gap="medium")

if choice == "search":  # search files based on the query

    with input_col:
        with st.form("query", border=False):
            if "top_k" not in st.session_state:
                st.session_state.top_k = 10  # 默认值
            top_k = st.slider("Max search results", min_value=5, max_value=30, value=st.session_state.top_k, step=5,
                                help="Maximum number of results to return from the search")
            st.session_state.top_k = top_k

            st.markdown("")

            st.markdown("#### Please enter your query:")
            query = st.text_area("query", height=100, label_visibility="collapsed")
            query_submitted = st.form_submit_button("Search", type="primary")

        if query and query_submitted:
            st.session_state.display_count = 5
            st.session_state.running = True
            st.session_state.stop_flag = False

    with output_col:
        if query:

            with st.spinner("Searching ..."):
                results = search_files(query=query, top_k=top_k, embedding_model=embedding_model)

            if results:
                st.success(f"Found following files:")

                for file in results[:st.session_state.display_count]:
                    name = file["file_name"]
                    path = file["file_path"]
                    st.button(cut_text(name), on_click=open_file_in_finder, args=(path, ), key=name + "_link", type="tertiary")

                if st.session_state.display_count < len(results):
                    st.button("Show more", on_click=increase_display_count, type="tertiary")

        else:
            st.info('Waiting for input ...')

elif choice == "organize":

    with input_col:
        with st.form("file_folder", border=False):
            load_ppt = st.checkbox("PPT", value=True, help="load PowerPoint files (.pptx) from the folder")
            load_pdf = st.checkbox("PDF", value=True, help="load PDF files (.pdf) from the folder")

            st.markdown("")

            st.markdown("#### Please enter the file folder path:")
            st.caption('Program will try to organize all files in the folder except for the ones already in the database.')

            file_folder = st.text_area("file_folder", height=100, label_visibility="collapsed")
            file_submitted = st.form_submit_button("Start", type="primary")

        if file_folder and file_submitted:
            st.session_state.running = True
            st.session_state.stop_flag = False

    with output_col:
        if file_folder and file_submitted:
            # list all files in the folder
            if not os.path.isdir(file_folder):
                st.warning("The specified folder does not exist or is not a directory.")
                st.session_state.stop_flag = True
                full_files_lst = []
            else:
                full_files_lst = os.listdir(file_folder)

            # check included file types
            chosen_types = []
            if load_ppt:
                chosen_types.append(".pptx")
            if load_pdf:
                chosen_types.append(".pdf")

            # determine llm model name based on user choice
            if llm_model_choice == "quality":
                summarize_llm_model_name = "Mistral-Small-3.2-24B-Instruct-2506_Q4_K_M"
            elif llm_model_choice == "speed":
                summarize_llm_model_name = "Nous-Hermes-2-Mistral-7B-DPO_Q4_K_M"
            else:
                summarize_llm_model_name = "Mistral-Small-3.2-24B-Instruct-2506_Q4_K_M"

            # filter files by the specified types and not already indexed
            file_lst = filter_files_by_type(full_files_lst=full_files_lst, incl_file_types=chosen_types)

            if not file_lst:
                st.warning("No valid files found in this folder or all files have been indexed already.")
                st.session_state.stop_flag = True
            else:
                # start to summarize files
                placeholder = st.empty()  # placeholder for the progress info
                batch_size = 10  # number of files to process in each batch
                skipped_files = defaultdict(list)  # to store files that are skipped due to errors
                num_processed_files = 0  # to count the number of sucessfully processed files
                start_time = time.time()  # record the start time

                if len(file_lst) > batch_size:
                    # when there are more than batch_size files, process them in batches
                    batches = [file_lst[i:i + batch_size] for i in range(0, len(file_lst), batch_size)]

                    for batch in batches:
                        doc_metadata_list = []  # to store metadata of processed files in the current batch
                        progress_bar = st.progress(0, text=f"Progress: 0 / {len(batch)} files")  # progress bar for the current batch

                        for i, file_name in enumerate(batch):
                            if st.session_state.stop_flag:
                                break  # stop the process if the stop button is clicked

                            placeholder.markdown(f"🔄 {file_name} …")  # show file name in the placeholder
                            output_tag, keywords, summary = summarize_file(file_folder, file_name, embedding_model,
                                                                            summarize_llm_model_name)  # summarize the file
                            progress_bar.progress((i + 1) / len(batch), text=f"Progress: {i + 1} / {len(batch)} files")  # update the progress bar

                            if output_tag.endswith("error"):
                                skipped_files[output_tag].append(file_name)  # add the file to the skipped files list
                            else:
                                doc_metadata_list.append({
                                    "file_name": file_name,
                                    "file_path": str(os.path.join(file_folder, file_name)),
                                    "keywords": keywords,
                                    "summary": summary
                                })  # add the metadata to the list
                                num_processed_files += 1  # update the count of processed files

                        if len(doc_metadata_list) > 0:  # if there are metadata to organize in this batch
                            placeholder.markdown(f"🔄 Embedding …")
                            organize_status_str, failed_organized_files = organize_files(doc_metadata_list, embedding_model=embedding_model)
                            doc_metadata_list.clear()
                            gc.collect()
                            if organize_status_str.endswith("error"):
                                st.warning(f"WARNING: A fatal {organize_status_str} has occurred! ")
                                st.session_state.stop_flag = True
                            elif len(failed_organized_files) > 0:
                                skipped_files["embedding_error"].extend(failed_organized_files)  # add the failed files to the skipped files list
                            else:
                                pass
                        else:
                            pass

                    if num_processed_files == 0:  # if no files are processed successfully in all batches
                        all_errors = ", ".join(skipped_files.keys())
                        st.warning(f"All files in the folder are skipped due to errors {all_errors}, please check the folder path and file types.")
                        st.session_state.stop_flag = True

                else:
                    doc_metadata_list = []  # to store metadata of processed files
                    progress_bar = st.progress(0, text=f"Progress: 0 / {len(file_lst)} files")  # progress bar for all files

                    for i, file_name in enumerate(file_lst):
                        if st.session_state.stop_flag:
                            break  # stop the process if the stop button is clicked

                        placeholder.markdown(f"🔄 {file_name} …")  # show file name in the placeholder
                        output_tag, keywords, summary = summarize_file(file_folder, file_name, embedding_model,
                                                                        summarize_llm_model_name)  # summarize the file
                        progress_bar.progress((i + 1) / len(file_lst), text=f"Progress: {i + 1} / {len(file_lst)} files")

                        if output_tag.endswith("error"):
                            skipped_files[output_tag].append(file_name)
                        else:
                            doc_metadata_list.append({
                                "file_name": file_name,
                                "file_path": str(os.path.join(file_folder, file_name)),
                                "keywords": keywords,
                                "summary": summary
                            })
                            num_processed_files += 1

                    if len(doc_metadata_list) > 0:  # if there are metadata to organize in this batch
                        placeholder.markdown(f"🔄 Embedding …")
                        organize_status_str, failed_organized_files = organize_files(doc_metadata_list, embedding_model=embedding_model)
                        doc_metadata_list.clear()
                        gc.collect()
                        if organize_status_str.endswith("error"):
                            st.warning(f"WARNING: A fatal {organize_status_str} has occurred! ")
                            st.session_state.stop_flag = True
                        elif len(failed_organized_files) > 0:
                            skipped_files["embedding_error"].extend(failed_organized_files)  # add the failed files to the skipped files list
                        else:
                            pass
                    else:
                        all_errors = ", ".join(skipped_files.keys())
                        st.warning(f"All files in the folder are skipped due to errors {all_errors}, please check the folder path and file types.")
                        st.session_state.stop_flag = True

                end_time = time.time()
                if not st.session_state.stop_flag:
                    placeholder.success(f"✅ Processed {num_processed_files} files successfully, took {((end_time - start_time)/60):.2f} mins.")
                    if skipped_files:
                        all_skipped_files = [fname for files in skipped_files.values() for fname in files]
                        all_errors = ", ".join(skipped_files.keys())
                        st.warning(f"⚠️ Skipped {len(all_skipped_files)} files due to errors {all_errors}: {', '.join(all_skipped_files)}")
        else:
            st.info("Waiting for input ...")

elif choice == "initialize":

    # set the initialized state to False
    st.session_state.initialized = False

    with input_col:
        # prompt the user for a folder path to initialize the database, use a form to get the input
        with st.form("init", border=False):
            st.markdown("#### Please enter the database folder path:")
            st.caption('Database files will be saved in this folder. If the folder does not exist, it will be created automatically.')
            database_folder = st.text_area("database_folder", height=100, label_visibility="collapsed")
            init_submitted = st.form_submit_button("Initialize", type="primary")

        # if the form is submitted and the folder path is provided, initialize the database
        if init_submitted and database_folder:
            initialize_config(database_folder)
            st.session_state.initialized = True

    with output_col:
        # display the status of the initialization
        if st.session_state.initialized:
            st.success("The database has been initialized successfully!")
        else:
            st.info("Waiting for input ...")

else:
    st.write("Please select a valid option from the sidebar.")
