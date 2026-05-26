from menu_bot.menu_db import MENU_DB
existing_names = {m['name'] for m in MENU_DB}
spicy_opts = ['안매움','살짝 매움','매움']
hunger_opts = ['보통','배고픔','엄청 배고픔']
price_opts = ['저렴함','보통','조금 비쌈','비쌈']
proteins = ['두부','닭가슴살','소고기','불고기','해산물','치킨','삼겹살','베이컨','새우','돼지고기','버섯','소시지','감자','호박','채소','버터','트러플']
formats = [
    ('돌솥', '볶음밥'),
    ('그릴드', '덮밥'),
    ('크리미', '파스타'),
    ('토마토', '스튜'),
    ('카레', '라이스'),
    ('치즈', '그라탕'),
    ('버터', '찜'),
    ('매콤', '볶음밥'),
]
items=[]
generated_names = set()
for i in range(100):
    protein = proteins[i % len(proteins)]
    fmt, dish = formats[i % len(formats)]
    variant = i // 25
    if variant == 0:
        name = f'{fmt} {protein} {dish}'
    elif variant == 1:
        name = f'{protein} {fmt} {dish}'
    elif variant == 2:
        name = f'{fmt} {dish} {protein} 스페셜'
    else:
        name = f'{protein} {dish} 플래터'
    if name in existing_names or name in generated_names:
        name = f'{name} {i}'
    generated_names.add(name)
    desc = f'{fmt} 향과 {protein}의 풍미가 어우러진 든든한 {dish} 메뉴입니다.'
    items.append({
        'name': name,
        'spicy': spicy_opts[i % len(spicy_opts)],
        'hunger': hunger_opts[i % len(hunger_opts)],
        'price': price_opts[i % len(price_opts)],
        'desc': desc,
    })
print(items[0])
print(items[1])
print(items[2])
print(len(items), len({item['name'] for item in items}))
