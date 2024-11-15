from flask import Flask, render_template, request, redirect, url_for
import json
from  flask import session
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'b1e9a8f45c3d12f7d8e6faef3b52a742'
@app.route('/')
def home():
    return render_template('index.html')
# Tải dữ liệu ngành nghề và trường học từ file JSON
def load_data():
    with open('D:\\career_guidance_website\\flask backend\\data1.json', 'r', encoding='utf-8') as f:
        career_data = json.load(f)
    with open('D:\\career_guidance_website\\flask backend\\data2.json', 'r', encoding='utf-8') as f:
        school_data = json.load(f)
    return career_data, school_data

# Hàm xử lý học phí
def parse_tuition(tuition_str):
    if tuition_str == 0 or tuition_str == "0" or tuition_str.strip() == "":
        return (0, 0)
    tuition_str = tuition_str.replace(",", "").strip()
    try:
        if ">" in tuition_str:
            return int(tuition_str.replace(">", "").strip()), float('inf')
        elif "<" in tuition_str:
            return 0, int(tuition_str.replace("<", "").strip())
        elif "-" in tuition_str:
            low, high = map(int, tuition_str.split('-'))
            return low, high
        else:
            value = int(tuition_str)
            return value, value
    except ValueError:
        print(f"Warning: Unable to parse tuition value from '{tuition_str}'. Defaulting to (0, 0).")
        return (0, 0)

# Lọc trường học theo học phí
def filter_school_by_tuition(school_data, max_tuition):
    filtered_schools = []
    for school in school_data:
        min_tuition, max_tuition_in_data = parse_tuition(school["tuition"])
        if min_tuition == 0 and max_tuition_in_data == 0:
            continue
        if min_tuition <= max_tuition and max_tuition_in_data <= max_tuition:
            filtered_schools.append(school)
    return filtered_schools
# Lọc trường học theo ngành học
def filter_school_by_major(school_data, majors):
    filtered_schools = []
    for school in school_data:
        school_majors = school.get("majors", [])
        if any(major in school_majors for major in majors):
            filtered_schools.append(school)
    return filtered_schools
# Lọc trường học theo khu vực
def filter_school_by_region(school_data, region):
    region = f"Miền {region.capitalize()}"
    # Chuyển đổi chuỗi thành danh sách các vùng miền, loại bỏ khoảng trắng
    return [school for school in school_data if school["region"] == region]

# Hàm tìm ngành nghề theo MBTI
def find_careers(mbti_type, career_data):
    unique_industries = set()
    careers = []
    for career in career_data:
        if mbti_type in career["mbti_type"].split(", "):
            industry = career["industries"]
            if industry not in unique_industries:
                unique_industries.add(industry)
                careers.append(industry)
    return careers

# Hàm tìm ngành học theo MBTI
def find_majors(mbti_type, major_data):
    unique_majors = set()
    majors = []
    for major in major_data:
        if mbti_type in major["mbti_type"].split(", "):
            major_name = major["majors"]
            if major_name not in unique_majors:
                unique_majors.add(major_name)
                majors.append(major_name)
    return majors

# Hàm tính toán MBTI từ câu trả lời
def calculate_mbti(answers):
    scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
    for answer in answers:
        if answer == 'E':
            scores['E'] += 1
        elif answer == 'I':
            scores['I'] += 1
        elif answer == 'S':
            scores['S'] += 1
        elif answer == 'N':
            scores['N'] += 1
        elif answer == 'T':
            scores['T'] += 1
        elif answer == 'F':
            scores['F'] += 1
        elif answer == 'J':
            scores['J'] += 1
        elif answer == 'P':
            scores['P'] += 1

    mbti_type = (
        ("E" if scores["E"] >= scores["I"] else "I") +
        ("S" if scores["S"] >= scores["N"] else "N") +
        ("T" if scores["T"] >= scores["F"] else "F") +
        ("J" if scores["J"] >= scores["P"] else "P")
    )
    print(f"check {mbti_type}")
    return mbti_type
# Route hiển thị trang bài test MBTI
@app.route('/mini_test', methods=['GET', 'POST'])
def mini_test():
    with open('D:\\career_guidance_website\\flask backend\\questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    if request.method == 'POST':
        answers = [request.form.get(f'answer_{i}') for i in range(len(questions))]
        mbti_type = calculate_mbti(answers)
        session['mbti_type'] = mbti_type  # Lưu MBTI type vào session
        print(f"MBTI type trong /mini_test: {mbti_type}")
        return redirect(url_for('submit'))  # Không cần truyền mbti_type qua URL
    
    return render_template('mini_test.html', questions=questions)
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    mbti_type = session.get('mbti_type')  # Lấy MBTI type từ session
    if not mbti_type:
        return "Không tìm thấy MBTI type. Vui lòng làm lại bài test."
    
    if request.method == 'POST':
        # Lấy các giá trị từ form
        name = request.form['name']
        age = request.form['age']
        max_tuition = int(request.form['tuition'])
        region = request.form['region']
        
        # Tải dữ liệu và tìm ngành nghề, ngành học
        career_data, school_data = load_data()
        careers = find_careers(mbti_type, career_data) or ["Không tìm thấy ngành nghề phù hợp."]
        majors = find_majors(mbti_type, career_data) or ["Không tìm thấy ngành học phù hợp."]
        
        # Lọc trường học
        schools_by_tuition = filter_school_by_tuition(school_data, max_tuition)
        schools_by_region = filter_school_by_region(schools_by_tuition, region)
        suitable_schools = filter_school_by_major(schools_by_region, majors) or [{"name": "Không tìm thấy trường đại học phù hợp.", "tuition": "", "region": ""}]
        
        # Lưu kết quả và trả về kết quả
        result = {
            "name": name,
            "age": age,
            "mbti_type": mbti_type,
            "careers": careers,
            "majors": majors,
            "suitable_schools": suitable_schools,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_test_results(result)
        return render_template('result.html', result=result)
    
    return render_template('submit.html', mbti_type=mbti_type)

# Lưu kết quả vào file JSON
def save_test_results(result):
    with open('D:\\career_guidance_website\\flask backend\\test_results.json', 'a', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)
        f.write("\n")
# Hàm lưu phản hồi vào file JSON
def save_feedback(name, feedback, rating):
    feedback_entry = {
        "name": name,
        "feedback": feedback,
        "rating": rating,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open('D:\\career_guidance_website\\feedback.json', 'a', encoding='utf-8') as f:
        json.dump(feedback_entry, f, ensure_ascii=False)
        f.write("\n")
        
# Route hiển thị trang phản hồi
@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

# Route xử lý phản hồi sau khi người dùng gửi
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    name = request.form['name']
    feedback = request.form['feedback']
    rating = request.form['rating']
    
    # Lưu phản hồi vào file JSON
    save_feedback(name, feedback, rating)
    
    # Chuyển hướng về trang cảm ơn hoặc thông báo đã gửi thành công
    return redirect(url_for('thank_you'))

# Trang cảm ơn sau khi gửi phản hồi
@app.route('/thank_you')
def thank_you():
    return "<h1>Cảm ơn bạn đã phản hồi!</h1><p>Phản hồi của bạn đã được lưu thành công.</p>"      
if __name__ == '__main__':
    app.run(debug=True)