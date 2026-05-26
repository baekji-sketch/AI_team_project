import streamlit as st
import random
from menu_db import MENU_DB

# =========================================
# 1. 세션 상태(Session State) 초기화 (강의안 5p)
# ==========================================
# 페이지가 새로고침(Rerun)되어도 대화 내역과 피드백이 지워지지 않도록 유지합니다.
if "messages" not in st.session_state:
    st.session_state.messages = []  # 채팅 메시지 저장용 리스트

if "feedback" not in st.session_state:
    st.session_state.feedback = ""  # 현재 저장된 사용자 피드백 상태

if "feedback_text" not in st.session_state:
    st.session_state.feedback_text = ""  

if "api_key" not in st.session_state:
    st.session_state.api_key = ""  # 사용자 입력 API 키 저장
if "category_choice" not in st.session_state:
    st.session_state.category_choice = "전체"
if "delivery_choice" not in st.session_state:
    st.session_state.delivery_choice = "전체"
if "recent_recommendations" not in st.session_state:
    st.session_state.recent_recommendations = []
if "last_filter_signature" not in st.session_state:
    st.session_state.last_filter_signature = None

SPICY_OPTIONS = ["안매움", "살짝 매움", "보통", "매움"]
HUNGER_OPTIONS = ["가벼움", "조금 배고픔", "보통", "배고픔", "엄청 배고픔"]
PRICE_OPTIONS = ["저렴함", "보통", "조금 비쌈", "비쌈", "고급"]
CATEGORY_OPTIONS = ["전체", "식사", "음료", "간식"]
DELIVERY_OPTIONS = ["전체", "배달 가능", "매장 전용"]

# ------------------------------------------
# 채팅 피드백을 해석해서 필터에 반영하는 도우미 함수
# ------------------------------------------
def _shift_option(value, options, amount):
    try:
        idx = options.index(value)
    except ValueError:
        idx = 0
    idx = min(max(idx + amount, 0), len(options) - 1)
    return options[idx]


def apply_feedback_to_filters(feedback, spicy_level, hunger_level, price_level):
    lower = feedback.lower()
    spicy_up = ["매워", "더 맵", "매운", "얼얼", "매콤", "더 강", "강하게", "불닭", "화끈"]
    spicy_down = ["안매워", "맵지", "순하게", "순한", "부담스러", "덜 매", "순한 맛", "매운 거 안"]
    hunger_up = ["허기", "배고파", "배고픔", "더 배", "배가 고파", "양이 적", "모자라", "더 먹고 싶"]
    hunger_down = ["포만", "배불", "배부", "배불러", "많이 못", "적당", "충분"]
    price_down = ["비싸", "가격", "부담", "고가", "비용", "비용 부담", "가격대가 높", "가격 부담"]
    price_up = ["고급", "조금 비쌈", "비쌈", "프리미엄", "특별", "고급스", "럭셔리"]
    cheap = ["싼", "저렴", "알뜰", "가성비", "가볍게", "저렴하게"]

    if any(word in lower for word in spicy_up):
        spicy_level = _shift_option(spicy_level, SPICY_OPTIONS, 1)
    if any(word in lower for word in spicy_down):
        spicy_level = _shift_option(spicy_level, SPICY_OPTIONS, -1)

    if any(word in lower for word in hunger_up):
        hunger_level = _shift_option(hunger_level, HUNGER_OPTIONS, 1)
    if any(word in lower for word in hunger_down):
        hunger_level = _shift_option(hunger_level, HUNGER_OPTIONS, -1)

    if any(word in lower for word in price_down) and "저렴" not in lower:
        price_level = _shift_option(price_level, PRICE_OPTIONS, -1)
    if any(word in lower for word in price_up) and "싼" not in lower:
        price_level = _shift_option(price_level, PRICE_OPTIONS, 1)
    if any(word in lower for word in cheap) and "비싼" not in lower:
        price_level = _shift_option(price_level, PRICE_OPTIONS, -1)

    return spicy_level, hunger_level, price_level


def is_negative_feedback(feedback):
    lower = feedback.lower()
    negative_keywords = ["별로", "아쉬워", "싫", "불만", "최악", "다시", "다른", "안좋", "못", "아니", "변경"]
    return any(keyword in lower for keyword in negative_keywords)


def detect_style_preferences(feedback):
    lower = feedback.lower()
    return {
        "youth": any(keyword in lower for keyword in ["젊", "힙", "트렌디", "인싸", "MZ", "요즘", "밀레니얼", "Z세대", "젊은 세대", "젊은이"]),
        "sweet": any(keyword in lower for keyword in ["달달", "단맛", "디저트", "케이크", "초코", "달콤", "사탕", "꿀", "시럽", "마카롱", "빙수", "와플", "팬케이크"]),
        "fresh": any(keyword in lower for keyword in ["상큼", "산뜻", "시트러스", "레몬", "자몽", "청포도", "유자", "샐러드", "프레시", "톡 쏘", "상쾌"]),
    }


def detect_food_type_preference(feedback):
    lower = feedback.lower()
    meal_keywords = [
        "식사", "점심", "저녁", "아침", "밥", "국", "면", "덮밥", "국밥", "찌개", "정식", "스테이크", "파스타", "리조또", "피자", "치킨", "한식", "양식", "중식", "일식", "아시안", "볶음", "구이", "탕", "전골"
    ]
    drink_keywords = [
        "음료", "커피", "티", "에이드", "스무디", "주스", "라떼", "아메리카노", "콜드브루", "모히또", "버블티", "차", "맥주", "칵테일", "밀크티", "아인슈페너"
    ]
    snack_keywords = [
        "간식", "디저트", "케이크", "쿠키", "도넛", "빵", "와플", "마카롱", "빙수", "떡", "타르트", "푸딩", "파르페", "아포가토", "스콘", "브라우니", "츄러스", "타피오카", "간식", "카페"
    ]

    if any(keyword in lower for keyword in meal_keywords):
        return "meal"
    if any(keyword in lower for keyword in drink_keywords):
        return "drink"
    if any(keyword in lower for keyword in snack_keywords):
        return "snack"
    return None


def is_delivery_menu(menu):
    if menu.get("delivery") is not None:
        return menu["delivery"]
    lower = f"{menu['name']} {menu['desc']}".lower()
    delivery_keywords = [
        "치킨", "피자", "버거", "떡볶이", "김밥", "도시락", "배달", "라면", "짜장", "짬뽕", "우동", "돈까스", "햄버거", "샌드위치", "핫도그", "감자튀김", "깁밥", "중국집", "분식", "치즈볼", "소떡소떡"
    ]
    return any(word in lower for word in delivery_keywords)


def classify_menu_category(menu):
    text = f"{menu['name']} {menu['desc']}".lower()
    if any(word in text for word in ["커피", "티", "에이드", "스무디", "주스", "라떼", "아메리카노", "콜드브루", "모히또", "버블티", "차", "맥주", "칵테일", "음료"]):
        return "drink"
    if any(word in text for word in ["디저트", "케이크", "쿠키", "도넛", "빵", "와플", "마카롱", "빙수", "떡", "타르트", "푸딩", "파르페", "아포가토", "스콘", "브라우니", "츄러스", "타피오카", "간식"]):
        return "snack"
    return "meal"


def dedupe_menus(menus):
    seen = set()
    unique = []
    for menu in menus:
        name = menu.get("name")
        if name not in seen:
            seen.add(name)
            unique.append(menu)
    return unique


def style_score(menu, style_prefs):
    text = f"{menu['name']} {menu['desc']}".lower()
    score = 0
    if style_prefs.get("youth"):
        youth_keywords = ["버거", "피자", "떡볶이", "치킨", "와플", "스무디", "샌드위치", "케이크", "크로플", "마카롱", "빙수", "타코", "브런치", "프리미엄", "플래터", "파티"]
        if any(keyword in text for keyword in youth_keywords):
            score += 2
    if style_prefs.get("sweet"):
        sweet_keywords = ["달콤", "달달", "케이크", "초코", "시럽", "허니", "마카롱", "빙수", "와플", "푸딩", "파르페", "쿠키", "타르트", "브라우니", "카라멜"]
        if any(keyword in text for keyword in sweet_keywords):
            score += 2
    if style_prefs.get("fresh"):
        fresh_keywords = ["상큼", "샐러드", "유자", "레몬", "자몽", "청포도", "시트러스", "오렌지", "연어", "싱그러운", "아보카도", "에이드", "스무디", "샐러드"]
        if any(keyword in text for keyword in fresh_keywords):
            score += 2
    return score


def detect_meeting_context(message):
    lower = message.lower()
    if any(word in lower for word in ["소개팅", "첫 만남", "데이트", "첫 데이트", "소개팅이"]):
        return "date"
    if any(word in lower for word in ["비즈니스", "비지니스", "회의", "회식", "미팅", "업무", "출장", "거래처", "영업"]):
        return "business"
    if any(word in lower for word in ["친구", "파티", "모임", "술자리", "여럿", "같이", "단체", "친구들", "회식"]):
        return "friends"
    return "general"


def menu_context_score(menu, context):
    text = f"{menu['name']} {menu['desc']}".lower()
    score = 0
    if context == "date":
        elegant = ["초밥", "사시미", "스테이크", "리조또", "샤브샤브", "파스타", "샐러드", "브런치", "에그 베네딕트", "카르보", "봉골레"]
        casual = ["떡볶이", "바비큐", "치킨", "전골", "피자", "튀김", "매운", "폭립", "플래터"]
        if any(word in text for word in elegant):
            score += 2
        if any(word in text for word in casual):
            score -= 1
    elif context == "business":
        classy = ["한정식", "일식", "초밥", "스테이크", "샤브샤브", "리조또", "샐러드", "코스", "프리미엄"]
        noisy = ["떡볶이", "치킨", "바비큐", "튀김", "매운", "전골"]
        if any(word in text for word in classy):
            score += 2
        if any(word in text for word in noisy):
            score -= 1
    elif context == "friends":
        share = ["플래터", "피자", "전골", "떡볶이", "치킨", "바비큐", "파티", "볶음", "샐러드", "샌드위치"]
        if any(word in text for word in share):
            score += 2
    return score


def describe_menu_flavor(menu):
    text = f"{menu['name']} {menu['desc']}".lower()
    if any(word in text for word in ["스테이크", "립", "돈까스", "포크", "차돌", "안심"]):
        return "미디엄 웰던에 가까운 촉촉한 육질과 겉은 살짝 크러스트가 살아 있는 풍미가 특징입니다."
    if any(word in text for word in ["초밥", "사시미", "회덮밥", "연어", "사케동"]):
        return "신선한 생선의 부드러운 식감과 은은한 간장, 밥의 균형이 조화를 이룹니다."
    if any(word in text for word in ["파스타", "리조또", "까르보", "봉골레", "알리오", "토마토"]):
        return "쫄깃한 면발과 크리미하거나 가벼운 소스가 입안을 감싸면서 풍부한 식감을 줍니다."
    if any(word in text for word in ["피자", "와플", "버거", "샌드위치", "케이크", "디저트"]):
        return "겉은 바삭하고 속은 부드러운 대비감이 살아 있어, 먹는 재미가 큽니다."
    if any(word in text for word in ["샐러드", "스무디", "에이드", "유자", "자몽", "레몬", "청포도"]):
        return "상큼하고 아삭한 식감이 입 안을 개운하게 정리해 줍니다."
    if any(word in text for word in ["떡볶이", "매운", "청양", "불닭", "마라"]):
        return "쫄깃한 식감과 감칠맛이 도는 매콤함이 어우러져 자꾸 손이 가는 맛입니다."
    return "균형 잡힌 풍미와 부드러운 식감으로 부담 없이 즐기실 수 있는 메뉴입니다."


def generate_persona_response(menus, context, style_note, feedback_message, feedback_adjusted, recommendation_note):
    top3 = menus[:3]
    if context == "date":
        intro = "소개팅 자리라니, 제가 다 설레네요! 첫 만남에는 깔끔하게 즐길 수 있는 메뉴가 참 중요하죠."
        closing = "소개팅 자리라면 담백한 일식과 세련된 양식 중 어느 쪽이 더 끌리시나요?"
    elif context == "business":
        intro = "비즈니스 미팅이라면 품격 있는 맛과 조용한 분위기가 핵심입니다."
        closing = "조용한 룸이 있는 고급 메뉴와 부담 없는 플레이팅 중 어느 쪽을 더 선호하시나요?"
    elif context == "friends":
        intro = "친구들과 함께라면 분위기와 나눠 먹기 좋은 메뉴가 포인트죠."
        closing = "친구들과 즐기기 좋은 풍성한 플래터와 포인트 있는 매운 메뉴, 어느 쪽이 더 끌리시나요?"
    else:
        intro = "오늘 기분과 취향을 바탕으로 최적의 메뉴를 골라드릴게요."
        closing = "부드러운 식감과 아삭한 식감 중 어떤 쪽을 더 선호하시나요?"

    response_text = f"{intro}\n\n"
    response_text += "### 추천 메뉴 2~3가지와 이유\n"
    for menu in top3:
        reason = f"{menu['desc']}"
        texture = describe_menu_flavor(menu)
        response_text += f"- **{menu['name']}**\n"
        response_text += f"  - 이유: {reason}\n"
        response_text += f"  - 맛/식감: {texture}\n\n"

    if style_note:
        response_text += f"*{style_note}*\n\n"
    if feedback_message:
        response_text += f"*요청하신 피드백을 반영해 추천을 다시 구성했습니다.*\n\n"
    if feedback_adjusted:
        response_text += f"*{recommendation_note}*\n\n"

    response_text += closing
    return response_text


def is_recommend_request(message):
    lower = message.lower()
    return any(keyword in lower for keyword in ["추천해줘", "추천", "recommend", "menu", "메뉴"])

# ==========================================
# 2. 사이드바 - 사용자 조건 입력 폼 (강의안 7p)
# ==========================================
# st.form을 사용하면 버튼들을 누를 때마다 화면이 계속 리런(Rerun)되는 것을 방지합니다.
with st.sidebar:
    st.header("🍔 메뉴 추천 필터")
    
    api_key = st.text_input(
        "🔑 OpenAI API 키 입력",
        value=st.session_state.api_key,
        type="password",
        help="AI 추천 서비스 연동 시 사용할 API 키를 입력하세요."
    )
    if api_key != st.session_state.api_key:
        st.session_state.api_key = api_key

    with st.form("filter_form"):
        spicy_level = st.radio("🌶️ 맵기 단계 선택", SPICY_OPTIONS)
        hunger_level = st.select_slider("🤤 허기 정도 선택", options=HUNGER_OPTIONS)
        price_level = st.select_slider("💵 가격대 선택", options=PRICE_OPTIONS)
        category_choice = st.radio(
            "🍽️ 메뉴 유형 선택",
            CATEGORY_OPTIONS,
            index=CATEGORY_OPTIONS.index(st.session_state.category_choice),
        )
        delivery_choice = st.radio(
            "🚚 배달 여부 선택",
            DELIVERY_OPTIONS,
            index=DELIVERY_OPTIONS.index(st.session_state.delivery_choice),
        )
        
        # 폼 제출 버튼
        submit_button = st.form_submit_button("🎯 이 조건으로 추천받기")

    if category_choice != st.session_state.category_choice:
        st.session_state.category_choice = category_choice
    if delivery_choice != st.session_state.delivery_choice:
        st.session_state.delivery_choice = delivery_choice

    if not st.session_state.api_key:
        st.info("API 키를 입력하면 외부 AI/메뉴 연동 시 활용 시 활용할 수 있습니다.")

    st.write("---")
    
    # 🔥 [아이디어 반영] 대화 내역 전부 삭제 버튼 (강의안 5p 세션 삭제 참고)
    if st.button("🗑️ 대화 내역 전부 삭제", type="primary"):
        st.session_state.messages = []  # 대화 내역 비우기
        st.session_state.feedback = ""   # 피드백 초기화
        st.rerun()                      # 화면 새로고침

# ==========================================
# 3. 메인 화면 - 챗봇 인터페이스 (강의안 13~14p)
# ==========================================
st.title("🤖 AI 맞춤형 메뉴 추천 챗봇")
st.write("왼쪽 사이드바에서 조건을 선택한 후 버튼을 누르거나 채팅창에 입력해주세요!")

# 기존 대화 내역이 있다면 화면에 먼저 다 그려주기 (강의안 13p 표준 패턴)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 4. 메뉴 추천 및 피드백 반영 로직
# ==========================================
# 사이드바의 '추천받기' 버튼을 누르거나 하단 채팅창(st.chat_input)에 입력을 받았을 때 작동
user_chat = st.chat_input("추천을 원하시면 '메뉴 추천해줘'를 입력하세요.")

if submit_button or user_chat:
    user_message = ""
    prompt_text = f"⚙️ **[선택 조건]** 맵기: {spicy_level} | 허기: {hunger_level} | 가격: {price_level}"
    feedback_message = ""
    feedback_adjusted = False
    recommendation_note = ""

    if user_chat:
        user_message = user_chat.strip()
        st.chat_message("user").markdown(user_message)
        st.session_state.messages.append({"role": "user", "content": user_message})

        if is_recommend_request(user_message):
            if any(keyword in user_message.lower() for keyword in ["별로", "아쉬워", "싫어", "불만", "다시", "다른"]) or any(detect_style_preferences(user_message).values()):
                st.session_state.feedback_text = user_message
            prompt_text = f"{prompt_text} \n\n💬 추가 요청: {user_message}"
        else:
            st.session_state.feedback_text = user_message
            feedback_message = user_message
            prompt_text = f"💬 사용자 피드백: {user_message}"
    else:
        st.chat_message("user").markdown(prompt_text)
        st.session_state.messages.append({"role": "user", "content": prompt_text})

    if st.session_state.feedback_text:
        new_spicy, new_hunger, new_price = apply_feedback_to_filters(
            st.session_state.feedback_text,
            spicy_level,
            hunger_level,
            price_level,
        )
        if (new_spicy, new_hunger, new_price) != (spicy_level, hunger_level, price_level):
            feedback_adjusted = True
            recommendation_note = (
                f"사용자 피드백을 반영하여 필터를 다음과 같이 조정했습니다: "
                f"맵기={new_spicy}, 허기={new_hunger}, 가격={new_price}."
            )
        spicy_level, hunger_level, price_level = new_spicy, new_hunger, new_price

    filter_signature = (
        spicy_level,
        hunger_level,
        price_level,
        category_choice,
        delivery_choice,
        st.session_state.feedback_text.strip(),
    )
    if filter_signature != st.session_state.last_filter_signature:
        st.session_state.recent_recommendations = []
        st.session_state.last_filter_signature = filter_signature

    matched_menus = [
        m for m in MENU_DB
        if m["spicy"] == spicy_level and m["hunger"] == hunger_level and m["price"] == price_level
    ]
    matched_menus = dedupe_menus(matched_menus)

    category_map = {
        "식사": "meal",
        "음료": "drink",
        "간식": "snack",
    }
    if category_choice != "전체":
        selected_type = category_map[category_choice]
        matched_menus = [m for m in matched_menus if classify_menu_category(m) == selected_type]
        strict_selection = True
    else:
        selected_type = None
        strict_selection = False

    if delivery_choice != "전체":
        delivery_flag = delivery_choice == "배달 가능"
        if delivery_flag:
            matched_menus = [m for m in matched_menus if is_delivery_menu(m)]
        else:
            matched_menus = [m for m in matched_menus if not is_delivery_menu(m)]
    else:
        delivery_flag = None

    context = detect_meeting_context(st.session_state.feedback_text or feedback_message or user_message)
    type_preference = selected_type or detect_food_type_preference(st.session_state.feedback_text or feedback_message or user_message)
    if matched_menus:
        scored_menus = []
        for m in matched_menus:
            score = style_score(m, detect_style_preferences(st.session_state.feedback_text or feedback_message))
            score += menu_context_score(m, context)
            if type_preference:
                menu_type = classify_menu_category(m)
                if menu_type == type_preference:
                    score += 3
                elif type_preference == "meal" and menu_type == "snack":
                    score -= 2
                elif type_preference == "drink" and menu_type != "drink":
                    score -= 1
                elif type_preference == "snack" and menu_type == "meal":
                    score -= 1
            scored_menus.append((score, m))
        scored_menus.sort(key=lambda item: item[0], reverse=True)
        matched_menus = [m for score, m in scored_menus]

    style_prefs = detect_style_preferences(st.session_state.feedback_text or feedback_message)
    style_note = ""
    if any(style_prefs.values()) and matched_menus:
        style_labels = [key for key, value in style_prefs.items() if value]
        if style_labels:
            style_note = f"사용자 요청에 따라 {' / '.join(style_labels)} 스타일 메뉴를 우선 추천합니다."

    type_note = ""
    if type_preference and matched_menus:
        if type_preference == "meal":
            type_note = "사용자 요청에 따라 식사류 메뉴를 우선 추천합니다."
        elif type_preference == "drink":
            type_note = "사용자 요청에 따라 음료류 메뉴를 우선 추천합니다."
        elif type_preference == "snack":
            type_note = "사용자 요청에 따라 간식류 메뉴를 우선 추천합니다."

    delivery_note = ""
    if delivery_choice != "전체" and matched_menus:
        if delivery_choice == "배달 가능":
            delivery_note = "배달 가능한 메뉴만 추천했습니다."
        else:
            delivery_note = "매장 전용 메뉴만 추천했습니다."

    # 새 추천 요청 시마다 다른 메뉴를 보여주기 위해 최종 후보를 구성합니다.
    if len(matched_menus) < 5:
        all_other_menus = [m for m in MENU_DB if m not in matched_menus]
        needed = 5 - len(matched_menus)
        if type_preference:
            preferred_menus = [m for m in all_other_menus if classify_menu_category(m) == type_preference]
            added = preferred_menus[:needed]
            matched_menus += added
            needed -= len(added)
            if needed > 0 and not strict_selection:
                remaining = [m for m in all_other_menus if m not in added]
                matched_menus += random.sample(remaining, min(needed, len(remaining)))
        elif not strict_selection:
            matched_menus += random.sample(all_other_menus, min(needed, len(all_other_menus)))

    matched_menus = dedupe_menus(matched_menus)
    if type_preference:
        preferred_first = [m for m in matched_menus if classify_menu_category(m) == type_preference]
        others = [m for m in matched_menus if classify_menu_category(m) != type_preference]
        matched_menus = preferred_first + others

    candidate_menus = [
        m for m in matched_menus
        if m["name"] not in st.session_state.recent_recommendations
    ]
    if not candidate_menus:
        candidate_menus = matched_menus

    final_recommendation = random.sample(candidate_menus, min(5, len(candidate_menus))) if candidate_menus else []
    if final_recommendation:
        st.session_state.recent_recommendations = (
            st.session_state.recent_recommendations + [m["name"] for m in final_recommendation]
        )[-15:]

    response_text = generate_persona_response(
        final_recommendation,
        context,
        style_note,
        feedback_message,
        feedback_adjusted,
        recommendation_note,
    )
    for idx, menu in enumerate(final_recommendation, 1):
        response_text += f"**{idx}. {menu['name']}**\n"
        response_text += f"- 🔍 **설명/유래:** {menu['desc']}\n\n"

    if feedback_message:
        response_text += f"*사용자 피드백을 반영해 다시 추천드렸습니다: \"{feedback_message}\"*\n\n"
    if feedback_adjusted:
        response_text += f"*{recommendation_note}*\n\n"
    if type_note:
        response_text += f"*{type_note}*\n\n"
    if delivery_note:
        response_text += f"*{delivery_note}*\n\n"
    if style_note:
        response_text += f"*{style_note}*\n\n"
    if st.session_state.feedback:
        response_text += f"*(이전 추천에 대해 **[{st.session_state.feedback}]** 피드백을 주셔서 이를 고려해 구성했습니다!)*"

    with st.chat_message("assistant"):
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})

# ==========================================
# 5. [아이디어 반영] 만족도 아이콘 평가 버튼
# ==========================================
# 대화가 시작된 이후에만 평가 버튼이 나타나도록 설정
if st.session_state.messages:
    st.write("---")
    st.write("### 📢 이번 추천 메뉴는 마음에 드셨나요? 버튼을 눌러 평가해주세요!")
    
    # 화면을 가로로 6분할하여 버튼 배치
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1:
        if st.button("💩"):
            st.session_state.feedback = "최악"
            st.toast("피드백 반영 완료: 다음엔 다른 스타일로 갈게요! 💩")
    with c2:
        if st.button("🥲"):
            st.session_state.feedback = "아쉬움"
            st.toast("피드백 반영 완료: 다음엔 좀 더 신경 쓸게요 🥲")
    with c3:
        if st.button("😐"):
            st.session_state.feedback = "보통"
            st.toast("피드백 반영 완료: 평범했군요! 😐")
    with c4:
        if st.button("🙂"):
            st.session_state.feedback = "좋음"
            st.toast("피드백 반영 완료: 맛있게 드세요! 🙂")
    with c5:
        if st.button("🤤"):
            st.session_state.feedback = "군침"
            st.toast("피드백 반영 완료: 탁월한 선택이 되길 바랍니다! 🤤")
    with c6:
        if st.button("😍"):
            st.session_state.feedback = "최고"
            st.toast("피드백 반영 완료: 대만족 하셨다니 기쁩니다! 😍")
