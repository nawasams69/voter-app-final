import streamlit as st
from supabase import create_client

# --- পেজ কনফিগারেশন ---
st.set_page_config(page_title="ভোটার অনুসন্ধান", page_icon="🗳️", layout="centered")

# --- কাস্টম CSS (সুন্দর UI এর জন্য) ---
st.markdown("""
    <style>
    .stButton button { width: 100%; }
    .result-box {
        padding: 15px; border: 1px solid #ddd; border-radius: 10px;
        background-color: #f9f9f9; margin-bottom: 10px;
    }
    .result-name { font-size: 18px; font-weight: bold; color: #0d6efd; }
    .detail-row { border-bottom: 1px solid #eee; padding: 5px 0; display: flex; justify-content: space-between; }
    .detail-label { font-weight: bold; color: #555; }
    </style>
""", unsafe_allow_html=True)

# --- ডাটাবেস কানেকশন ---
@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("Supabase Secrets পাওয়া যায়নি! Advanced Settings চেক করুন।")
        st.stop()

supabase = init_connection()

# --- পপ-আপ ফাংশন (Details Popup) ---
@st.dialog("ভোটার বিস্তারিত তথ্য")
def show_details(voter):
    # ২০টি কলাম সুন্দর করে সাজানো
    details = {
        "নাম": voter.get('name'),
        "সিরিয়াল নং": voter.get('serial_no'),
        "ভোটার নং": voter.get('voter_no'),
        "লিঙ্গ": voter.get('gender'),
        "পিতা": voter.get('father'),
        "মাতা": voter.get('mother'),
        "পেশা": voter.get('profession'),
        "জন্ম তারিখ": voter.get('dob'),
        "মোবাইল/ফোন": "N/A", # যদি ডাটাবেসে না থাকে
        "ঠিকানা": voter.get('address'),
        "ভোটার এলাকা": f"{voter.get('voter_area_name')} ({voter.get('area_code')})",
        "জেলা": voter.get('district'),
        "উপজেলা/থানা": voter.get('upazila'),
        "সিটি কর্পোরেশন": voter.get('city_corp'),
        "ওয়ার্ড (ইউনিয়ন)": voter.get('ward_union'),
        "ইউনিয়ন/ওয়ার্ড": voter.get('union_ward'),
        "পোস্ট অফিস": voter.get('post_office'),
        "পোস্টকোড": voter.get('postcode'),
        "অঞ্চল": voter.get('region'),
        "ভোটকেন্দ্র": voter.get('polling_center')
    }

    for key, value in details.items():
        st.markdown(f"""
        <div class="detail-row">
            <span class="detail-label">{key}</span>
            <span>{value if value else '-'}</span>
        </div>
        """, unsafe_allow_html=True)

# --- মেইন UI ---
st.title("🗳️ ভোটার তথ্য যাচাইকরণ")

# ১. লোকেশন সিলেকশন (Location Specification)
st.subheader("১. এলাকা নির্বাচন")
area_code = st.text_input("ভোটার এলাকা কোড (Area Code)", placeholder="যেমন: 2797")

# ২. ব্যক্তি শনাক্তকরণ (Person Specification)
st.subheader("২. ব্যক্তি শনাক্তকরণ")
col1, col2 = st.columns(2)
with col1:
    gender = st.selectbox("লিঙ্গ (বাধ্যতামূলক)", ["পুরুষ", "মহিলা", "হিজড়া"], index=0)
with col2:
    dob = st.text_input("জন্ম তারিখ (ঐচ্ছিক)", placeholder="DD/MM/YYYY")

col3, col4 = st.columns(2)
with col3:
    name_input = st.text_input("নাম (ঐচ্ছিক)", placeholder="নামের অংশ...")
with col4:
    parent_input = st.text_input("পিতা/মাতার নাম (ঐচ্ছিক)", placeholder="নামের অংশ...")

search_btn = st.button("অনুসন্ধান করুন", type="primary")

# --- লজিক ---
if search_btn:
    # ভ্যালিডেশন লজিক
    if not area_code:
        st.warning("⚠️ দয়া করে ভোটার এলাকা কোড প্রদান করুন।")
    elif not (dob or name_input or parent_input):
        st.error("⚠️ লিঙ্গের সাথে অন্তত একটি তথ্য দিতে হবে: নাম, পিতা/মাতার নাম অথবা জন্ম তারিখ।")
    else:
        with st.spinner("তথ্য খোঁজা হচ্ছে..."):
            try:
                # কুয়েরি তৈরি
                query = supabase.table("voters").select("*")
                
                # ফিল্টার
                query = query.eq("area_code", area_code) # লোকেশন
                query = query.eq("gender", gender)       # জেন্ডার (বাধ্যতামূলক)

                # অপশনাল ফিল্টার (যেকোনো একটি মিললেই হবে এমন লজিক অথবা সব ফিল্টার অ্যাপ্লাই)
                # ব্যবহারকারীর ইনপুট অনুযায়ী ন্যারো ডাউন করা হচ্ছে
                if dob:
                    query = query.ilike("dob", f"%{dob}%")
                if name_input:
                    query = query.ilike("name", f"%{name_input}%")
                if parent_input:
                    # পিতা অথবা মাতা যেকোনো একটায় মিললেই হবে
                    query = query.or_(f"father.ilike.%{parent_input}%,mother.ilike.%{parent_input}%")

                # ১০০ রেজাল্ট লিমিট
                response = query.limit(100).execute()
                data = response.data

                if not data:
                    st.error("❌ কোনো তথ্য পাওয়া যায়নি।")
                else:
                    st.success(f"✅ {len(data)} জন ভোটার পাওয়া গেছে")
                    
                    # লিস্ট দেখানো
                    for voter in data:
                        # কার্ড ডিজাইন
                        with st.container():
                            col_info, col_btn = st.columns([0.7, 0.3])
                            
                            with col_info:
                                st.markdown(f"""
                                <div class="result-name">{voter.get('name', 'নাম নেই')}</div>
                                <small>পিতা: {voter.get('father', '-')} | ভোটার নং: {voter.get('voter_no', '-')}</small>
                                """, unsafe_allow_html=True)
                            
                            with col_btn:
                                # বাটনে ক্লিক করলে পপ-আপ ওপেন হবে
                                if st.button("বিস্তারিত", key=voter['voter_no']):
                                    show_details(voter)
                            
                            st.divider()

            except Exception as e:
                st.error(f"সার্ভার এরর: {e}")
