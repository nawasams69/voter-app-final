import streamlit as st
from supabase import create_client, Client

# --- PAGE CONFIGURATION (UI POLISH) ---
st.set_page_config(
    page_title="Voter Search Portal",
    page_icon="🗳️",
    layout="centered"
)

# --- CUSTOM CSS (This makes it look original/custom) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa; 
    }
    .stButton>button {
        width: 100%;
        background-color: #0d6efd;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
    .voter-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border-left: 5px solid #0d6efd;
    }
    .voter-name { font-size: 1.2rem; font-weight: bold; color: #212529; }
    .voter-info { font-size: 0.9rem; color: #6c757d; }
    .highlight { color: #0d6efd; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- CONNECT TO DB ---
# We use st.secrets for security
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- APP UI ---
st.title("🗳️ ভোটার তথ্য যাচাইকরণ")
st.markdown("নিচের তথ্য দিয়ে ভোটার তালিকা অনুসন্ধান করুন।")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        area_code = st.text_input("এলাকা কোড (আবশ্যিক)", placeholder="যেমন: 2797")
    with col2:
        gender = st.selectbox("লিঙ্গ", ["পুরুষ", "মহিলা", "হিজড়া"])
    
    name_input = st.text_input("নাম বা পিতার নাম (ঐচ্ছিক)", placeholder="নামের যেকোনো অংশ...")
    
    search_btn = st.button("তথ্য খুঁজুন")

# --- LOGIC ---
if search_btn:
    if not area_code:
        st.warning("⚠️ দয়া করে ভোটার এলাকা কোড প্রদান করুন।")
    else:
        with st.spinner("ডাটাবেস অনুসন্ধান করা হচ্ছে..."):
            try:
                # Optimized Query
                query = supabase.table("voters")\
                    .select("*")\
                    .eq("area_code", area_code)\
                    .eq("gender", gender)
                
                if name_input:
                    # Case insensitive partial match
                    query = query.or_(f"name.ilike.%{name_input}%,father.ilike.%{name_input}%")
                
                # Fetch top 20 results
                response = query.limit(20).execute()
                data = response.data

                if not data:
                    st.error("❌ কোনো তথ্য পাওয়া যায়নি।")
                else:
                    st.success(f"✅ {len(data)} জন ভোটার পাওয়া গেছে")
                    
                    for voter in data:
                        # Professional HTML Card Design
                        st.markdown(f"""
                        <div class="voter-card">
                            <div class="voter-name">{voter['name']}</div>
                            <div class="voter-info">
                                পিতা: <b>{voter['father']}</b> <br>
                                ভোটার নং: <span class="highlight">{voter['voter_no']}</span> | সিরিয়াল: {voter['serial_no']}<br>
                                <small>ঠিকানা: {voter['address']}</small>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error connecting to database: {e}")