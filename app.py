def inject_branding():
    st.set_page_config(page_title="HausMate Match", layout="wide")

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {HM_BG};
        }}

        .block-container {{
            padding-top: 2rem;
        }}

        .hm-header {{
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 30px;
        }}

        .hm-title {{
            font-size: 36px;
            font-weight: 800;
            color: {HM_WHITE};
            margin: 0;
        }}

        .hm-sub {{
            font-size: 16px;
            color: {HM_WHITE};
            opacity: 0.9;
            margin: 0;
        }}

        .hm-card {{
            background: {HM_CARD};
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.08);
        }}

        div.stButton > button {{
            background-color: {HM_PRIMARY_DARK};
            color: white;
            border-radius: 12px;
            border: none;
            padding: 10px 20px;
            font-weight: 600;
        }}

        div.stButton > button:hover {{
            background-color: {HM_PRIMARY};
        }}

        .hm-pill {{
            display: inline-block;
            padding: 8px 14px;
            border-radius: 999px;
            background: {HM_PRIMARY};
            color: white;
            font-weight: 600;
            margin: 5px;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )
